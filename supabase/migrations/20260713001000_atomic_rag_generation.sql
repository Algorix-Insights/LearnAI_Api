BEGIN;

CREATE OR REPLACE FUNCTION public.persist_generated_flashcards(
    p_actor_id UUID,
    p_notebook_id UUID,
    p_items JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    item JSONB;
    question_text TEXT;
    answer_text TEXT;
    created_question_id UUID;
    created_flashcard_id UUID;
    result JSONB := '[]'::JSONB;
BEGIN
    IF p_actor_id IS NULL
       OR p_notebook_id IS NULL
       OR NOT EXISTS (
           SELECT 1
           FROM public.users u
           WHERE u.user_id = p_actor_id
             AND u.status = 'active'
       ) THEN
        RAISE EXCEPTION 'resource not found' USING ERRCODE = 'P0002';
    END IF;
    IF NOT (
        EXISTS (
            SELECT 1 FROM public.personal_notebooks pn
            WHERE pn.user_id = p_actor_id
              AND pn.notebook_id = p_notebook_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.room_notebooks rn
            JOIN public.members_rooms mr ON mr.room_id = rn.room_id
            JOIN public.study_members sm ON sm.member_id = mr.member_id
            WHERE rn.notebook_id = p_notebook_id
              AND sm.user_id = p_actor_id
              AND mr.role = 'admin'
        )
    ) THEN
        RAISE EXCEPTION 'resource not found' USING ERRCODE = 'P0002';
    END IF;
    IF p_items IS NULL
       OR jsonb_typeof(p_items) <> 'array'
       OR jsonb_array_length(p_items) NOT BETWEEN 1 AND 20 THEN
        RAISE EXCEPTION 'invalid generated flashcards' USING ERRCODE = '22023';
    END IF;

    FOR item IN SELECT value FROM jsonb_array_elements(p_items)
    LOOP
        question_text := BTRIM(item->>'question');
        answer_text := BTRIM(item->>'answer');
        IF COALESCE(LENGTH(question_text), 0) NOT BETWEEN 1 AND 1000
           OR COALESCE(LENGTH(answer_text), 0) NOT BETWEEN 1 AND 2000 THEN
            RAISE EXCEPTION 'invalid generated flashcard' USING ERRCODE = '22023';
        END IF;

        INSERT INTO public.questions (type, statement, expected_answer)
        VALUES ('open', question_text, answer_text)
        RETURNING question_id INTO created_question_id;

        INSERT INTO public.flashcards (notebook_id, question_id)
        VALUES (p_notebook_id, created_question_id)
        RETURNING flashcard_id INTO created_flashcard_id;

        result := result || jsonb_build_array(
            jsonb_build_object(
                'flashcard_id', created_flashcard_id,
                'question_id', created_question_id,
                'question', question_text,
                'answer', answer_text
            )
        );
    END LOOP;

    INSERT INTO public.user_learning_events (
        user_id,
        notebook_id,
        activity_type,
        quantity,
        duration_seconds,
        metadata,
        idempotency_key
    )
    VALUES (
        p_actor_id,
        p_notebook_id,
        'resource_generated',
        jsonb_array_length(p_items),
        0,
        jsonb_build_object('resource_type', 'flashcards'),
        'server:flashcards:' || created_flashcard_id::TEXT
    );

    RETURN result;
END;
$$;

CREATE OR REPLACE FUNCTION public.list_notebook_flashcards(
    p_actor_id UUID,
    p_notebook_id UUID,
    p_limit INTEGER,
    p_offset INTEGER
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    result JSONB;
BEGIN
    IF p_actor_id IS NULL
       OR p_notebook_id IS NULL
       OR p_limit NOT BETWEEN 1 AND 100
       OR p_offset < 0
       OR NOT EXISTS (
           SELECT 1
           FROM public.users u
           WHERE u.user_id = p_actor_id
             AND u.status = 'active'
       )
       OR NOT (
           EXISTS (
               SELECT 1
               FROM public.personal_notebooks pn
               WHERE pn.user_id = p_actor_id
                 AND pn.notebook_id = p_notebook_id
           )
           OR EXISTS (
               SELECT 1
               FROM public.room_notebooks rn
               JOIN public.members_rooms mr ON mr.room_id = rn.room_id
               JOIN public.study_members sm ON sm.member_id = mr.member_id
               WHERE rn.notebook_id = p_notebook_id
                 AND sm.user_id = p_actor_id
           )
       ) THEN
        RAISE EXCEPTION 'resource not found' USING ERRCODE = 'P0002';
    END IF;

    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'flashcard_id', item.flashcard_id,
                'question_id', item.question_id,
                'notebook_id', item.notebook_id,
                'question', item.statement,
                'answer', item.expected_answer,
                'spent_time', item.spent_time,
                'created_at', item.created_at
            )
            ORDER BY item.created_at DESC
        ),
        '[]'::JSONB
    )
    INTO result
    FROM (
        SELECT
            f.flashcard_id,
            f.question_id,
            f.notebook_id,
            f.spent_time,
            f.created_at,
            q.statement,
            q.expected_answer
        FROM public.flashcards f
        JOIN public.questions q ON q.question_id = f.question_id
        WHERE f.notebook_id = p_notebook_id
        ORDER BY f.created_at DESC
        LIMIT p_limit
        OFFSET p_offset
    ) AS item;

    RETURN result;
END;
$$;

CREATE OR REPLACE FUNCTION public.append_conversation_message(
    p_actor_id UUID,
    p_conversation_id UUID,
    p_role TEXT,
    p_content TEXT
)
RETURNS public.messages
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    next_order INTEGER;
    created_message public.messages%ROWTYPE;
BEGIN
    IF p_actor_id IS NULL
       OR NOT EXISTS (
           SELECT 1
           FROM public.users u
           WHERE u.user_id = p_actor_id
             AND u.status = 'active'
       )
       OR p_role NOT IN ('user', 'assistant')
       OR COALESCE(LENGTH(BTRIM(p_content)), 0) NOT BETWEEN 1 AND 8000
       OR NOT EXISTS (
           SELECT 1
           FROM public.ai_conversations c
           WHERE c.conversation_id = p_conversation_id
             AND (
                 EXISTS (
                     SELECT 1 FROM public.personal_notebooks pn
                     WHERE pn.user_id = p_actor_id
                       AND pn.notebook_id = c.notebook_id
                 )
                 OR EXISTS (
                     SELECT 1
                     FROM public.room_notebooks rn
                     JOIN public.members_rooms mr ON mr.room_id = rn.room_id
                     JOIN public.study_members sm ON sm.member_id = mr.member_id
                     WHERE rn.notebook_id = c.notebook_id
                       AND sm.user_id = p_actor_id
                 )
             )
       ) THEN
        RAISE EXCEPTION 'resource not found' USING ERRCODE = 'P0002';
    END IF;

    PERFORM pg_advisory_xact_lock(
        hashtextextended(p_conversation_id::TEXT, 0)
    );
    SELECT COALESCE(MAX(m.order_message), 0) + 1
    INTO next_order
    FROM public.messages m
    WHERE m.conversation_id = p_conversation_id;

    INSERT INTO public.messages (
        conversation_id, role, content, sent_by_user_id, order_message
    )
    VALUES (
        p_conversation_id,
        p_role,
        p_content,
        CASE WHEN p_role = 'user' THEN p_actor_id ELSE NULL END,
        next_order
    )
    RETURNING * INTO created_message;

    UPDATE public.ai_conversations
    SET updated_at = NOW()
    WHERE conversation_id = p_conversation_id;

    RETURN created_message;
END;
$$;

CREATE OR REPLACE FUNCTION public.persist_generated_exam(
    p_actor_id UUID,
    p_notebook_id UUID,
    p_name TEXT,
    p_description TEXT,
    p_questions JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    question_item JSONB;
    option_item JSONB;
    question_type TEXT;
    statement_text TEXT;
    expected_text TEXT;
    created_exam public.exams%ROWTYPE;
    created_question_id UUID;
    created_option_id UUID;
    question_order INTEGER := 0;
    option_count INTEGER;
    correct_count INTEGER;
    safe_options JSONB;
    safe_questions JSONB := '[]'::JSONB;
BEGIN
    IF p_actor_id IS NULL
       OR p_notebook_id IS NULL
       OR NOT EXISTS (
           SELECT 1
           FROM public.users u
           WHERE u.user_id = p_actor_id
             AND u.status = 'active'
       ) THEN
        RAISE EXCEPTION 'resource not found' USING ERRCODE = 'P0002';
    END IF;
    IF NOT (
        EXISTS (
            SELECT 1 FROM public.personal_notebooks pn
            WHERE pn.user_id = p_actor_id
              AND pn.notebook_id = p_notebook_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.room_notebooks rn
            JOIN public.members_rooms mr ON mr.room_id = rn.room_id
            JOIN public.study_members sm ON sm.member_id = mr.member_id
            WHERE rn.notebook_id = p_notebook_id
              AND sm.user_id = p_actor_id
              AND mr.role = 'admin'
        )
    ) THEN
        RAISE EXCEPTION 'resource not found' USING ERRCODE = 'P0002';
    END IF;
    IF COALESCE(LENGTH(BTRIM(p_name)), 0) NOT BETWEEN 1 AND 160
       OR COALESCE(LENGTH(p_description), 0) > 1000
       OR p_questions IS NULL
       OR jsonb_typeof(p_questions) <> 'array'
       OR jsonb_array_length(p_questions) NOT BETWEEN 1 AND 20 THEN
        RAISE EXCEPTION 'invalid generated exam' USING ERRCODE = '22023';
    END IF;

    INSERT INTO public.exams (notebook_id, name, description)
    VALUES (p_notebook_id, BTRIM(p_name), p_description)
    RETURNING * INTO created_exam;

    FOR question_item IN SELECT value FROM jsonb_array_elements(p_questions)
    LOOP
        question_order := question_order + 1;
        question_type := question_item->>'type';
        statement_text := BTRIM(question_item->>'statement');
        expected_text := NULLIF(BTRIM(question_item->>'expected_answer'), '');

        IF question_type NOT IN ('multiple_choice', 'true_false', 'open')
           OR COALESCE(LENGTH(statement_text), 0) NOT BETWEEN 1 AND 2000
           OR (question_type = 'open' AND (
               expected_text IS NULL OR LENGTH(expected_text) > 4000
           ))
           OR (question_type <> 'open' AND expected_text IS NOT NULL) THEN
            RAISE EXCEPTION 'invalid generated question' USING ERRCODE = '22023';
        END IF;

        option_count := COALESCE(jsonb_array_length(question_item->'options'), 0);
        SELECT COUNT(*)
        INTO correct_count
        FROM jsonb_array_elements(COALESCE(question_item->'options', '[]'::JSONB)) opt
        WHERE (opt->>'is_correct')::BOOLEAN IS TRUE;

        IF (question_type = 'open' AND option_count <> 0)
           OR (question_type = 'true_false' AND (
               option_count <> 2 OR correct_count <> 1
           ))
           OR (question_type = 'multiple_choice' AND (
               option_count NOT BETWEEN 2 AND 6 OR correct_count <> 1
           )) THEN
            RAISE EXCEPTION 'invalid generated options' USING ERRCODE = '22023';
        END IF;

        INSERT INTO public.questions (type, statement, expected_answer)
        VALUES (question_type, statement_text, expected_text)
        RETURNING question_id INTO created_question_id;

        INSERT INTO public.exam_questions (
            exam_id, question_id, question_order, points
        )
        VALUES (created_exam.exam_id, created_question_id, question_order, 1);

        safe_options := '[]'::JSONB;
        FOR option_item IN
            SELECT value
            FROM jsonb_array_elements(
                COALESCE(question_item->'options', '[]'::JSONB)
            )
            ORDER BY (value->>'option_order')::INTEGER
        LOOP
            IF COALESCE(LENGTH(BTRIM(option_item->>'option_text')), 0)
                   NOT BETWEEN 1 AND 1000
               OR COALESCE((option_item->>'option_order')::INTEGER, 0)
                   NOT BETWEEN 1 AND 6 THEN
                RAISE EXCEPTION 'invalid generated option' USING ERRCODE = '22023';
            END IF;

            INSERT INTO public.questions_options (
                question_id, option_text, is_correct, option_order
            )
            VALUES (
                created_question_id,
                BTRIM(option_item->>'option_text'),
                (option_item->>'is_correct')::BOOLEAN,
                (option_item->>'option_order')::INTEGER
            )
            RETURNING option_id INTO created_option_id;

            safe_options := safe_options || jsonb_build_array(
                jsonb_build_object(
                    'option_id', created_option_id,
                    'option_text', BTRIM(option_item->>'option_text'),
                    'option_order', (option_item->>'option_order')::INTEGER
                )
            );
        END LOOP;

        safe_questions := safe_questions || jsonb_build_array(
            jsonb_build_object(
                'question_id', created_question_id,
                'type', question_type,
                'statement', statement_text,
                'question_order', question_order,
                'options', safe_options
            )
        );
    END LOOP;

    INSERT INTO public.user_learning_events (
        user_id,
        notebook_id,
        activity_type,
        quantity,
        duration_seconds,
        metadata,
        idempotency_key
    )
    VALUES (
        p_actor_id,
        p_notebook_id,
        'resource_generated',
        1,
        0,
        jsonb_build_object('resource_type', 'exam'),
        'server:exam:' || created_exam.exam_id::TEXT
    );

    RETURN jsonb_build_object(
        'exam_id', created_exam.exam_id,
        'notebook_id', created_exam.notebook_id,
        'name', created_exam.name,
        'description', created_exam.description,
        'status', created_exam.status,
        'questions', safe_questions
    );
END;
$$;

REVOKE ALL ON FUNCTION public.persist_generated_flashcards(UUID, UUID, JSONB)
FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.list_notebook_flashcards(UUID, UUID, INTEGER, INTEGER)
FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.persist_generated_exam(
    UUID, UUID, TEXT, TEXT, JSONB
) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.append_conversation_message(UUID, UUID, TEXT, TEXT)
FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.persist_generated_flashcards(UUID, UUID, JSONB)
TO service_role;
GRANT EXECUTE ON FUNCTION public.list_notebook_flashcards(UUID, UUID, INTEGER, INTEGER)
TO service_role;
GRANT EXECUTE ON FUNCTION public.persist_generated_exam(
    UUID, UUID, TEXT, TEXT, JSONB
) TO service_role;
GRANT EXECUTE ON FUNCTION public.append_conversation_message(UUID, UUID, TEXT, TEXT)
TO service_role;

COMMIT;
