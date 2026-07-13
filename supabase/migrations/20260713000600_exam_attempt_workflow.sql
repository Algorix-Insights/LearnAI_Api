BEGIN;

-- One active attempt per student and exam, including concurrent starts.
CREATE UNIQUE INDEX IF NOT EXISTS attempts_one_active_per_user_exam
ON public.attempts (exam_id, user_id)
WHERE status = 'in_progress';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'attempts_score_percentage_check'
          AND conrelid = 'public.attempts'::regclass
    ) THEN
        ALTER TABLE public.attempts
        ADD CONSTRAINT attempts_score_percentage_check
        CHECK (score <= 100) NOT VALID;
    END IF;
END $$;

-- Clients cannot bypass the server-owned workflow or grading through Data API.
REVOKE INSERT, UPDATE, DELETE ON public.attempts FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.user_answers FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.attempts TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_answers TO service_role;

CREATE OR REPLACE FUNCTION public.submit_exam_attempt_answer(
    p_attempt_id UUID,
    p_user_id UUID,
    p_question_id UUID,
    p_selected_option_id UUID,
    p_answer_text TEXT
)
RETURNS SETOF public.user_answers
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_exam_id UUID;
    v_question_type TEXT;
BEGIN
    SELECT attempt.exam_id
    INTO v_exam_id
    FROM public.attempts AS attempt
    WHERE attempt.attempt_id = p_attempt_id
      AND attempt.user_id = p_user_id
      AND attempt.status = 'in_progress'
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    SELECT question.type
    INTO v_question_type
    FROM public.exam_questions AS exam_question
    JOIN public.questions AS question
      ON question.question_id = exam_question.question_id
    WHERE exam_question.exam_id = v_exam_id
      AND exam_question.question_id = p_question_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'question_not_in_attempt'
            USING ERRCODE = '22023';
    END IF;

    IF (p_selected_option_id IS NULL) = (p_answer_text IS NULL) THEN
        RAISE EXCEPTION 'invalid_answer_value'
            USING ERRCODE = '22023';
    END IF;

    IF v_question_type = 'open' THEN
        IF p_selected_option_id IS NOT NULL OR NULLIF(BTRIM(p_answer_text), '') IS NULL THEN
            RAISE EXCEPTION 'open_question_requires_text'
                USING ERRCODE = '22023';
        END IF;
    ELSE
        IF p_selected_option_id IS NULL OR p_answer_text IS NOT NULL THEN
            RAISE EXCEPTION 'closed_question_requires_option'
                USING ERRCODE = '22023';
        END IF;
        IF NOT EXISTS (
            SELECT 1
            FROM public.questions_options AS question_option
            WHERE question_option.option_id = p_selected_option_id
              AND question_option.question_id = p_question_id
        ) THEN
            RAISE EXCEPTION 'option_not_in_question'
                USING ERRCODE = '22023';
        END IF;
    END IF;

    RETURN QUERY
    INSERT INTO public.user_answers AS answer (
        attempt_id,
        question_id,
        selected_option_id,
        answer_text,
        is_correct,
        points_awarded
    )
    VALUES (
        p_attempt_id,
        p_question_id,
        p_selected_option_id,
        p_answer_text,
        NULL,
        0
    )
    ON CONFLICT (attempt_id, question_id)
    DO UPDATE SET
        selected_option_id = EXCLUDED.selected_option_id,
        answer_text = EXCLUDED.answer_text,
        is_correct = NULL,
        points_awarded = 0
    RETURNING answer.*;
END;
$$;

REVOKE ALL ON FUNCTION public.submit_exam_attempt_answer(UUID, UUID, UUID, UUID, TEXT)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.submit_exam_attempt_answer(UUID, UUID, UUID, UUID, TEXT)
TO service_role;

CREATE OR REPLACE FUNCTION public.finalize_exam_attempt(
    p_attempt_id UUID,
    p_user_id UUID,
    p_completed_at TIMESTAMPTZ,
    p_spent_time INTEGER,
    p_grades JSONB
)
RETURNS SETOF public.attempts
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_exam_id UUID;
    v_status TEXT;
    v_grade JSONB;
    v_answer_id UUID;
    v_question_id UUID;
    v_selected_option_id UUID;
    v_answer_text TEXT;
    v_is_correct BOOLEAN;
    v_points_awarded NUMERIC(7,2);
    v_grade_count INTEGER;
    v_unique_grade_count INTEGER;
    v_current_answer_count INTEGER;
    v_earned_points NUMERIC;
    v_total_points NUMERIC;
    v_score NUMERIC(7,2);
BEGIN
    IF p_spent_time < 0 OR jsonb_typeof(COALESCE(p_grades, '[]'::jsonb)) <> 'array' THEN
        RAISE EXCEPTION 'invalid_grading_payload'
            USING ERRCODE = '22023';
    END IF;

    SELECT attempt.exam_id, attempt.status
    INTO v_exam_id, v_status
    FROM public.attempts AS attempt
    WHERE attempt.attempt_id = p_attempt_id
      AND attempt.user_id = p_user_id
    FOR UPDATE;

    IF NOT FOUND OR v_status <> 'in_progress' THEN
        RETURN;
    END IF;

    -- The application grades a snapshot outside this transaction (open answers
    -- may require an LLM). Locking the attempt stops future writes, while this
    -- cardinality check plus the value predicates below reject any answer that
    -- changed between snapshot and finalization.
    SELECT
        COUNT(*)::INTEGER,
        COUNT(DISTINCT (grade ->> 'answer_id')::UUID)::INTEGER
    INTO v_grade_count, v_unique_grade_count
    FROM jsonb_array_elements(COALESCE(p_grades, '[]'::JSONB)) AS grade;

    SELECT COUNT(*)::INTEGER
    INTO v_current_answer_count
    FROM public.user_answers AS answer
    WHERE answer.attempt_id = p_attempt_id;

    IF v_grade_count <> v_current_answer_count
       OR v_unique_grade_count <> v_grade_count THEN
        RAISE EXCEPTION 'attempt_answers_changed'
            USING ERRCODE = '40001';
    END IF;

    FOR v_grade IN
        SELECT value FROM jsonb_array_elements(COALESCE(p_grades, '[]'::jsonb))
    LOOP
        IF NOT (
            v_grade ? 'answer_id'
            AND v_grade ? 'question_id'
            AND v_grade ? 'selected_option_id'
            AND v_grade ? 'answer_text'
            AND v_grade ? 'is_correct'
            AND v_grade ? 'points_awarded'
        ) THEN
            RAISE EXCEPTION 'invalid_answer_grade'
                USING ERRCODE = '22023';
        END IF;

        v_answer_id := (v_grade ->> 'answer_id')::UUID;
        v_question_id := (v_grade ->> 'question_id')::UUID;
        v_selected_option_id := (v_grade ->> 'selected_option_id')::UUID;
        v_answer_text := v_grade ->> 'answer_text';
        v_is_correct := (v_grade ->> 'is_correct')::BOOLEAN;
        v_points_awarded := (v_grade ->> 'points_awarded')::NUMERIC(7,2);

        IF v_answer_id IS NULL
           OR v_question_id IS NULL
           OR v_is_correct IS NULL
           OR v_points_awarded < 0 THEN
            RAISE EXCEPTION 'invalid_answer_grade'
                USING ERRCODE = '22023';
        END IF;

        UPDATE public.user_answers AS answer
        SET is_correct = v_is_correct,
            points_awarded = v_points_awarded
        WHERE answer.answer_id = v_answer_id
          AND answer.attempt_id = p_attempt_id
          AND answer.question_id = v_question_id
          AND answer.selected_option_id IS NOT DISTINCT FROM v_selected_option_id
          AND answer.answer_text IS NOT DISTINCT FROM v_answer_text
          AND EXISTS (
              SELECT 1
              FROM public.exam_questions AS exam_question
              WHERE exam_question.exam_id = v_exam_id
                AND exam_question.question_id = answer.question_id
                AND v_points_awarded = CASE
                    WHEN v_is_correct THEN exam_question.points
                    ELSE 0
                END
          );

        IF NOT FOUND THEN
            RAISE EXCEPTION 'answer_grade_not_in_attempt'
                USING ERRCODE = '22023';
        END IF;
    END LOOP;

    SELECT
        COALESCE(SUM(answer.points_awarded), 0),
        COALESCE(SUM(exam_question.points), 0)
    INTO v_earned_points, v_total_points
    FROM public.exam_questions AS exam_question
    LEFT JOIN public.user_answers AS answer
      ON answer.question_id = exam_question.question_id
     AND answer.attempt_id = p_attempt_id
    WHERE exam_question.exam_id = v_exam_id;

    v_score := CASE
        WHEN v_total_points > 0
            THEN ROUND(v_earned_points / v_total_points * 100, 2)
        ELSE 0
    END;

    RETURN QUERY
    UPDATE public.attempts AS attempt
    SET score = v_score,
        status = 'completed',
        completed_at = p_completed_at,
        spent_time = p_spent_time
    WHERE attempt.attempt_id = p_attempt_id
      AND attempt.user_id = p_user_id
      AND attempt.status = 'in_progress'
    RETURNING attempt.*;
END;
$$;

REVOKE ALL ON FUNCTION public.finalize_exam_attempt(UUID, UUID, TIMESTAMPTZ, INTEGER, JSONB)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.finalize_exam_attempt(UUID, UUID, TIMESTAMPTZ, INTEGER, JSONB)
TO service_role;

COMMIT;
