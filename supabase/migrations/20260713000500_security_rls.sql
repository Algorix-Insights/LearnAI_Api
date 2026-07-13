BEGIN;

-- Security-definer helpers avoid recursive RLS evaluation across membership tables.
-- They only answer questions about auth.uid(); callers cannot inspect another user.
CREATE OR REPLACE FUNCTION public.current_user_is_active()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.users u
        WHERE u.user_id = (SELECT auth.uid())
          AND u.status = 'active'
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_is_room_member(target_room_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT public.current_user_is_active() AND EXISTS (
        SELECT 1
        FROM public.study_members sm
        JOIN public.members_rooms mr ON mr.member_id = sm.member_id
        WHERE sm.user_id = (SELECT auth.uid())
          AND mr.room_id = target_room_id
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_is_room_admin(target_room_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT public.current_user_is_active() AND EXISTS (
        SELECT 1
        FROM public.study_members sm
        JOIN public.members_rooms mr ON mr.member_id = sm.member_id
        WHERE sm.user_id = (SELECT auth.uid())
          AND mr.room_id = target_room_id
          AND mr.role = 'admin'
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_is_notebook_member(target_notebook_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT public.current_user_is_active() AND (
        EXISTS (
            SELECT 1
            FROM public.personal_notebooks pn
            WHERE pn.user_id = (SELECT auth.uid())
              AND pn.notebook_id = target_notebook_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.room_notebooks rn
            JOIN public.members_rooms mr ON mr.room_id = rn.room_id
            JOIN public.study_members sm ON sm.member_id = mr.member_id
            WHERE sm.user_id = (SELECT auth.uid())
              AND rn.notebook_id = target_notebook_id
        )
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_manage_notebook(target_notebook_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT public.current_user_is_active() AND (
        EXISTS (
            SELECT 1
            FROM public.personal_notebooks pn
            WHERE pn.user_id = (SELECT auth.uid())
              AND pn.notebook_id = target_notebook_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.room_notebooks rn
            JOIN public.members_rooms mr ON mr.room_id = rn.room_id
            JOIN public.study_members sm ON sm.member_id = mr.member_id
            WHERE sm.user_id = (SELECT auth.uid())
              AND rn.notebook_id = target_notebook_id
              AND mr.role = 'admin'
        )
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_access_exam(target_exam_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT public.current_user_is_active() AND EXISTS (
        SELECT 1
        FROM public.exams e
        WHERE e.exam_id = target_exam_id
          AND public.current_user_is_notebook_member(e.notebook_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_manage_exam(target_exam_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.exams e
        WHERE e.exam_id = target_exam_id
          AND public.current_user_can_manage_notebook(e.notebook_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_access_question(target_question_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT
        EXISTS (
            SELECT 1
            FROM public.exam_questions eq
            JOIN public.exams e ON e.exam_id = eq.exam_id
            WHERE eq.question_id = target_question_id
              AND public.current_user_is_notebook_member(e.notebook_id)
        )
        OR EXISTS (
            SELECT 1
            FROM public.flashcards f
            WHERE f.question_id = target_question_id
              AND public.current_user_is_notebook_member(f.notebook_id)
        );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_manage_question(target_question_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT
        (
            EXISTS (
                SELECT 1
                FROM public.exam_questions eq
                WHERE eq.question_id = target_question_id
            )
            OR EXISTS (
                SELECT 1
                FROM public.flashcards f
                WHERE f.question_id = target_question_id
            )
        )
        AND NOT EXISTS (
            SELECT 1
            FROM public.exam_questions eq
            JOIN public.exams e ON e.exam_id = eq.exam_id
            WHERE eq.question_id = target_question_id
              AND NOT public.current_user_can_manage_notebook(e.notebook_id)
        )
        AND NOT EXISTS (
            SELECT 1
            FROM public.flashcards f
            WHERE f.question_id = target_question_id
              AND NOT public.current_user_can_manage_notebook(f.notebook_id)
        );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_access_document(target_document_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.documents d
        WHERE d.document_id = target_document_id
          AND public.current_user_is_notebook_member(d.notebook_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_access_conversation(target_conversation_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.ai_conversations c
        WHERE c.conversation_id = target_conversation_id
          AND public.current_user_is_notebook_member(c.notebook_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_owns_attempt(target_attempt_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT public.current_user_is_active() AND EXISTS (
        SELECT 1
        FROM public.attempts a
        WHERE a.attempt_id = target_attempt_id
          AND a.user_id = (SELECT auth.uid())
    );
$$;

CREATE OR REPLACE FUNCTION public.storage_path_first_uuid(object_name TEXT)
RETURNS UUID
LANGUAGE plpgsql
IMMUTABLE
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    first_segment TEXT;
BEGIN
    first_segment := (storage.foldername(object_name))[1];
    RETURN first_segment::UUID;
EXCEPTION
    WHEN invalid_text_representation OR array_subscript_error THEN
        RETURN NULL;
END;
$$;

-- Replace the legacy RPC with a bounded service-only version. Without an
-- explicit revoke, PostgreSQL grants function execution to PUBLIC by default.
CREATE OR REPLACE FUNCTION public.match_document_chunks(
    query_embedding VECTOR(1536),
    match_notebook_id UUID,
    match_count INT DEFAULT 6
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    notebook_id UUID,
    content TEXT,
    model TEXT,
    token_count INT,
    document_name TEXT,
    storage_path TEXT,
    similarity DOUBLE PRECISION
)
LANGUAGE sql
STABLE
SECURITY INVOKER
AS $$
    SELECT
        dc.chunk_id,
        dc.document_id,
        d.notebook_id,
        dc.content,
        dc.model,
        dc.token_count,
        d.name AS document_name,
        d.storage_path,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM public.document_chunks dc
    JOIN public.documents d ON d.document_id = dc.document_id
    WHERE d.notebook_id = match_notebook_id
      AND d.status = 'active'
      AND d.processing_status = 'completed'
    ORDER BY dc.embedding <=> query_embedding
    LIMIT LEAST(GREATEST(COALESCE(match_count, 6), 1), 50);
$$;

REVOKE ALL ON FUNCTION public.current_user_is_active() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_is_room_member(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_is_room_admin(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_is_notebook_member(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_can_manage_notebook(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_can_access_exam(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_can_manage_exam(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_can_access_question(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_can_manage_question(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_can_access_document(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_can_access_conversation(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.current_user_owns_attempt(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.storage_path_first_uuid(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.match_document_chunks(VECTOR, UUID, INT)
FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.current_user_is_active() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_is_room_member(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_is_room_admin(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_is_notebook_member(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_can_manage_notebook(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_can_access_exam(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_can_manage_exam(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_can_access_question(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_can_manage_question(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_can_access_document(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_can_access_conversation(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_owns_attempt(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.storage_path_first_uuid(TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.match_document_chunks(VECTOR, UUID, INT)
TO service_role;

ALTER TABLE public.health ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notebooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.study_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.members_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.personal_notebooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.room_notebooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exam_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flashcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notebook_tags ENABLE ROW LEVEL SECURITY;

-- Account status is an independent, restrictive gate. It is combined with every
-- resource policy below, so a suspended/inactive JWT cannot bypass the API by
-- calling PostgREST directly. Health stays public by design.
DO $$
DECLARE
    guarded_table TEXT;
BEGIN
    FOREACH guarded_table IN ARRAY ARRAY[
        'users',
        'notebooks',
        'rooms',
        'study_members',
        'members_rooms',
        'personal_notebooks',
        'room_notebooks',
        'exams',
        'questions',
        'exam_questions',
        'questions_options',
        'attempts',
        'user_answers',
        'flashcards',
        'documents',
        'document_chunks',
        'ai_conversations',
        'messages',
        'tags',
        'notebook_tags'
    ]
    LOOP
        EXECUTE format(
            'DROP POLICY IF EXISTS learnia_active_user_guard ON public.%I',
            guarded_table
        );
        EXECUTE format(
            'CREATE POLICY learnia_active_user_guard ON public.%I '
            'AS RESTRICTIVE FOR ALL TO authenticated '
            'USING (public.current_user_is_active()) '
            'WITH CHECK (public.current_user_is_active())',
            guarded_table
        );
    END LOOP;
END $$;

-- Enforce the same upload envelope at Storage itself. The publishable key is
-- intentionally public, so API-only validation is not a security boundary.
UPDATE storage.buckets
SET public = FALSE,
    file_size_limit = 10485760,
    allowed_mime_types = ARRAY[
        'application/pdf',
        'text/plain',
        'text/markdown'
    ]
WHERE id = 'documents';

UPDATE storage.buckets
SET public = FALSE,
    file_size_limit = 5242880,
    allowed_mime_types = ARRAY[
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/gif'
    ]
WHERE id = 'profile';

-- Do not depend on Supabase project defaults. RLS decides which rows are
-- visible; table grants below decide which operations can reach those policies.
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

REVOKE ALL PRIVILEGES ON TABLE
    public.health,
    public.users,
    public.notebooks,
    public.rooms,
    public.study_members,
    public.members_rooms,
    public.personal_notebooks,
    public.room_notebooks,
    public.exams,
    public.questions,
    public.exam_questions,
    public.questions_options,
    public.attempts,
    public.user_answers,
    public.flashcards,
    public.documents,
    public.document_chunks,
    public.ai_conversations,
    public.messages,
    public.tags,
    public.notebook_tags
FROM PUBLIC, anon, authenticated;

GRANT ALL PRIVILEGES ON TABLE
    public.health,
    public.users,
    public.notebooks,
    public.rooms,
    public.study_members,
    public.members_rooms,
    public.personal_notebooks,
    public.room_notebooks,
    public.exams,
    public.questions,
    public.exam_questions,
    public.questions_options,
    public.attempts,
    public.user_answers,
    public.flashcards,
    public.documents,
    public.document_chunks,
    public.ai_conversations,
    public.messages,
    public.tags,
    public.notebook_tags
TO service_role;

GRANT SELECT ON TABLE public.health TO anon, authenticated;
GRANT SELECT, DELETE ON TABLE public.notebooks TO authenticated;
GRANT UPDATE (
    name,
    description,
    summary,
    is_favorite,
    status,
    due_date,
    updated_at
) ON TABLE public.notebooks TO authenticated;
GRANT SELECT, DELETE ON TABLE public.rooms TO authenticated;
GRANT UPDATE (
    name,
    description,
    updated_at
) ON TABLE public.rooms TO authenticated;
GRANT SELECT, DELETE ON TABLE public.study_members TO authenticated;
GRANT INSERT (
    user_id,
    nickname
) ON TABLE public.study_members TO authenticated;
GRANT UPDATE (
    nickname,
    updated_at
) ON TABLE public.study_members TO authenticated;
GRANT SELECT, DELETE ON TABLE public.members_rooms TO authenticated;
GRANT INSERT (
    member_id,
    room_id,
    role
) ON TABLE public.members_rooms TO authenticated;
GRANT UPDATE (role) ON TABLE public.members_rooms TO authenticated;
GRANT SELECT, DELETE ON TABLE public.personal_notebooks TO authenticated;
GRANT SELECT, DELETE ON TABLE public.room_notebooks TO authenticated;
GRANT SELECT, DELETE ON TABLE public.exams TO authenticated;
GRANT UPDATE (
    name,
    description,
    status,
    updated_at
) ON TABLE public.exams TO authenticated;
GRANT DELETE ON TABLE public.questions TO authenticated;
GRANT SELECT, DELETE ON TABLE public.exam_questions TO authenticated;
GRANT DELETE ON TABLE public.questions_options TO authenticated;
GRANT SELECT ON TABLE public.attempts TO authenticated;
GRANT SELECT, DELETE ON TABLE public.flashcards TO authenticated;
GRANT SELECT (
    document_id,
    notebook_id,
    name,
    description,
    source_type,
    status,
    processing_status,
    mime_type,
    size_bytes,
    created_at,
    updated_at
) ON TABLE public.documents TO authenticated;
GRANT SELECT (
    chunk_id,
    document_id,
    chunk_index,
    content,
    model,
    token_count,
    created_at
) ON TABLE public.document_chunks TO authenticated;
GRANT SELECT ON TABLE public.ai_conversations TO authenticated;
GRANT SELECT ON TABLE public.messages TO authenticated;
GRANT SELECT ON TABLE public.tags TO authenticated;
GRANT SELECT, DELETE ON TABLE public.notebook_tags TO authenticated;
GRANT INSERT (
    notebook_id,
    tag_id
) ON TABLE public.notebook_tags TO authenticated;

-- Row policies cannot hide individual columns. Keep credentials,
-- server-controlled attributes and grading material unavailable even when a
-- client calls PostgREST directly with the public project key.
REVOKE SELECT ON TABLE public.users
FROM PUBLIC, anon, authenticated;
REVOKE INSERT, UPDATE, DELETE ON TABLE public.users
FROM PUBLIC, anon, authenticated;
GRANT SELECT (
    user_id,
    name,
    last_name,
    email,
    streak,
    status,
    profile_image_path,
    profile_image_mime_type,
    profile_image_size_bytes,
    created_at,
    updated_at,
    last_login
) ON TABLE public.users TO authenticated;
GRANT UPDATE (
    name,
    last_name,
    profile_image_path,
    profile_image_mime_type,
    profile_image_size_bytes,
    updated_at
) ON TABLE public.users TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.users TO service_role;

REVOKE SELECT ON TABLE public.questions
FROM PUBLIC, anon, authenticated;
GRANT SELECT (
    question_id,
    type,
    statement,
    created_at
) ON TABLE public.questions TO authenticated;
GRANT SELECT ON TABLE public.questions TO service_role;
GRANT UPDATE (
    type,
    statement,
    expected_answer
) ON TABLE public.questions TO authenticated;

REVOKE SELECT ON TABLE public.questions_options
FROM PUBLIC, anon, authenticated;
GRANT SELECT (
    option_id,
    question_id,
    option_text,
    option_order,
    created_at
) ON TABLE public.questions_options TO authenticated;
GRANT SELECT ON TABLE public.questions_options TO service_role;
GRANT UPDATE (
    option_text,
    is_correct,
    option_order
) ON TABLE public.questions_options TO authenticated;

REVOKE SELECT ON TABLE public.user_answers
FROM PUBLIC, anon, authenticated;
GRANT SELECT (
    answer_id,
    attempt_id,
    question_id,
    selected_option_id,
    answer_text,
    created_at
) ON TABLE public.user_answers TO authenticated;
GRANT SELECT ON TABLE public.user_answers TO service_role;

DROP POLICY IF EXISTS learnia_health_read ON public.health;
CREATE POLICY learnia_health_read ON public.health
FOR SELECT TO anon, authenticated USING (TRUE);

DROP POLICY IF EXISTS learnia_users_self_select ON public.users;
CREATE POLICY learnia_users_self_select ON public.users
FOR SELECT TO authenticated USING (user_id = (SELECT auth.uid()));
DROP POLICY IF EXISTS learnia_users_self_insert ON public.users;
-- Supabase Auth profile synchronization uses the service client. Direct INSERT
-- would let a user pre-create an inconsistent email/status profile.
DROP POLICY IF EXISTS learnia_users_self_update ON public.users;
CREATE POLICY learnia_users_self_update ON public.users
FOR UPDATE TO authenticated
USING (user_id = (SELECT auth.uid()))
WITH CHECK (user_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS learnia_notebooks_member_select ON public.notebooks;
CREATE POLICY learnia_notebooks_member_select ON public.notebooks
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));
DROP POLICY IF EXISTS learnia_notebooks_manager_update ON public.notebooks;
CREATE POLICY learnia_notebooks_manager_update ON public.notebooks
FOR UPDATE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id))
WITH CHECK (public.current_user_can_manage_notebook(notebook_id));
DROP POLICY IF EXISTS learnia_notebooks_manager_delete ON public.notebooks;
CREATE POLICY learnia_notebooks_manager_delete ON public.notebooks
FOR DELETE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id));

DROP POLICY IF EXISTS learnia_rooms_member_select ON public.rooms;
CREATE POLICY learnia_rooms_member_select ON public.rooms
FOR SELECT TO authenticated USING (public.current_user_is_room_member(room_id));
DROP POLICY IF EXISTS learnia_rooms_admin_update ON public.rooms;
CREATE POLICY learnia_rooms_admin_update ON public.rooms
FOR UPDATE TO authenticated
USING (public.current_user_is_room_admin(room_id))
WITH CHECK (public.current_user_is_room_admin(room_id));
DROP POLICY IF EXISTS learnia_rooms_admin_delete ON public.rooms;
CREATE POLICY learnia_rooms_admin_delete ON public.rooms
FOR DELETE TO authenticated USING (public.current_user_is_room_admin(room_id));

DROP POLICY IF EXISTS learnia_study_members_self_select ON public.study_members;
CREATE POLICY learnia_study_members_self_select ON public.study_members
FOR SELECT TO authenticated USING (user_id = (SELECT auth.uid()));
DROP POLICY IF EXISTS learnia_study_members_self_insert ON public.study_members;
CREATE POLICY learnia_study_members_self_insert ON public.study_members
FOR INSERT TO authenticated WITH CHECK (user_id = (SELECT auth.uid()));
DROP POLICY IF EXISTS learnia_study_members_self_update ON public.study_members;
CREATE POLICY learnia_study_members_self_update ON public.study_members
FOR UPDATE TO authenticated
USING (user_id = (SELECT auth.uid()))
WITH CHECK (user_id = (SELECT auth.uid()));
DROP POLICY IF EXISTS learnia_study_members_self_delete ON public.study_members;
CREATE POLICY learnia_study_members_self_delete ON public.study_members
FOR DELETE TO authenticated USING (user_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS learnia_members_rooms_member_select ON public.members_rooms;
CREATE POLICY learnia_members_rooms_member_select ON public.members_rooms
FOR SELECT TO authenticated USING (public.current_user_is_room_member(room_id));
DROP POLICY IF EXISTS learnia_members_rooms_admin_insert ON public.members_rooms;
CREATE POLICY learnia_members_rooms_admin_insert ON public.members_rooms
FOR INSERT TO authenticated WITH CHECK (public.current_user_is_room_admin(room_id));
DROP POLICY IF EXISTS learnia_members_rooms_admin_update ON public.members_rooms;
CREATE POLICY learnia_members_rooms_admin_update ON public.members_rooms
FOR UPDATE TO authenticated
USING (public.current_user_is_room_admin(room_id))
WITH CHECK (public.current_user_is_room_admin(room_id));
DROP POLICY IF EXISTS learnia_members_rooms_admin_delete ON public.members_rooms;
CREATE POLICY learnia_members_rooms_admin_delete ON public.members_rooms
FOR DELETE TO authenticated USING (public.current_user_is_room_admin(room_id));

DROP POLICY IF EXISTS learnia_personal_notebooks_self_select ON public.personal_notebooks;
CREATE POLICY learnia_personal_notebooks_self_select ON public.personal_notebooks
FOR SELECT TO authenticated USING (user_id = (SELECT auth.uid()));
DROP POLICY IF EXISTS learnia_personal_notebooks_self_insert ON public.personal_notebooks;
-- No direct INSERT policy: allowing a user to attach an arbitrary existing
-- notebook here would turn room membership into ownership. Notebook creation and
-- ownership linking must be one trusted, atomic server-side operation.
DROP POLICY IF EXISTS learnia_personal_notebooks_self_delete ON public.personal_notebooks;
CREATE POLICY learnia_personal_notebooks_self_delete ON public.personal_notebooks
FOR DELETE TO authenticated USING (user_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS learnia_room_notebooks_member_select ON public.room_notebooks;
CREATE POLICY learnia_room_notebooks_member_select ON public.room_notebooks
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));
DROP POLICY IF EXISTS learnia_room_notebooks_admin_insert ON public.room_notebooks;
CREATE POLICY learnia_room_notebooks_admin_insert ON public.room_notebooks
FOR INSERT TO authenticated
WITH CHECK (
    public.current_user_is_room_admin(room_id)
    AND public.current_user_can_manage_notebook(notebook_id)
    AND EXISTS (
        SELECT 1
        FROM public.study_members sm
        WHERE sm.member_id = created_by
          AND sm.user_id = (SELECT auth.uid())
    )
);
DROP POLICY IF EXISTS learnia_room_notebooks_admin_delete ON public.room_notebooks;
CREATE POLICY learnia_room_notebooks_admin_delete ON public.room_notebooks
FOR DELETE TO authenticated USING (public.current_user_is_room_admin(room_id));

DROP POLICY IF EXISTS learnia_tags_authenticated_select ON public.tags;
CREATE POLICY learnia_tags_authenticated_select ON public.tags
FOR SELECT TO authenticated USING (TRUE);
DROP POLICY IF EXISTS learnia_notebook_tags_member_select ON public.notebook_tags;
CREATE POLICY learnia_notebook_tags_member_select ON public.notebook_tags
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));
DROP POLICY IF EXISTS learnia_notebook_tags_manager_insert ON public.notebook_tags;
CREATE POLICY learnia_notebook_tags_manager_insert ON public.notebook_tags
FOR INSERT TO authenticated
WITH CHECK (public.current_user_can_manage_notebook(notebook_id));
DROP POLICY IF EXISTS learnia_notebook_tags_manager_delete ON public.notebook_tags;
CREATE POLICY learnia_notebook_tags_manager_delete ON public.notebook_tags
FOR DELETE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id));

DROP POLICY IF EXISTS learnia_exams_member_select ON public.exams;
CREATE POLICY learnia_exams_member_select ON public.exams
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));
DROP POLICY IF EXISTS learnia_exams_manager_insert ON public.exams;
CREATE POLICY learnia_exams_manager_insert ON public.exams
FOR INSERT TO authenticated
WITH CHECK (public.current_user_can_manage_notebook(notebook_id));
DROP POLICY IF EXISTS learnia_exams_manager_update ON public.exams;
CREATE POLICY learnia_exams_manager_update ON public.exams
FOR UPDATE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id))
WITH CHECK (public.current_user_can_manage_notebook(notebook_id));
DROP POLICY IF EXISTS learnia_exams_manager_delete ON public.exams;
CREATE POLICY learnia_exams_manager_delete ON public.exams
FOR DELETE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id));

DROP POLICY IF EXISTS learnia_questions_member_select ON public.questions;
CREATE POLICY learnia_questions_member_select ON public.questions
FOR SELECT TO authenticated
USING (public.current_user_can_access_question(question_id));
DROP POLICY IF EXISTS learnia_questions_manager_update ON public.questions;
CREATE POLICY learnia_questions_manager_update ON public.questions
FOR UPDATE TO authenticated
USING (public.current_user_can_manage_question(question_id))
WITH CHECK (public.current_user_can_manage_question(question_id));
DROP POLICY IF EXISTS learnia_questions_manager_delete ON public.questions;
CREATE POLICY learnia_questions_manager_delete ON public.questions
FOR DELETE TO authenticated
USING (public.current_user_can_manage_question(question_id));

DROP POLICY IF EXISTS learnia_exam_questions_member_select ON public.exam_questions;
CREATE POLICY learnia_exam_questions_member_select ON public.exam_questions
FOR SELECT TO authenticated
USING (public.current_user_can_access_exam(exam_id));
DROP POLICY IF EXISTS learnia_exam_questions_manager_insert ON public.exam_questions;
CREATE POLICY learnia_exam_questions_manager_insert ON public.exam_questions
FOR INSERT TO authenticated
WITH CHECK (
    public.current_user_can_manage_exam(exam_id)
    AND public.current_user_can_manage_question(question_id)
);
DROP POLICY IF EXISTS learnia_exam_questions_manager_delete ON public.exam_questions;
CREATE POLICY learnia_exam_questions_manager_delete ON public.exam_questions
FOR DELETE TO authenticated
USING (public.current_user_can_manage_exam(exam_id));

DROP POLICY IF EXISTS learnia_question_options_member_select ON public.questions_options;
CREATE POLICY learnia_question_options_member_select ON public.questions_options
FOR SELECT TO authenticated
USING (public.current_user_can_access_question(question_id));
DROP POLICY IF EXISTS learnia_question_options_manager_update ON public.questions_options;
CREATE POLICY learnia_question_options_manager_update ON public.questions_options
FOR UPDATE TO authenticated
USING (public.current_user_can_manage_question(question_id))
WITH CHECK (public.current_user_can_manage_question(question_id));
DROP POLICY IF EXISTS learnia_question_options_manager_delete ON public.questions_options;
CREATE POLICY learnia_question_options_manager_delete ON public.questions_options
FOR DELETE TO authenticated
USING (public.current_user_can_manage_question(question_id));

DROP POLICY IF EXISTS learnia_attempts_owner_select ON public.attempts;
CREATE POLICY learnia_attempts_owner_select ON public.attempts
FOR SELECT TO authenticated USING (user_id = (SELECT auth.uid()));
DROP POLICY IF EXISTS learnia_user_answers_owner_select ON public.user_answers;
CREATE POLICY learnia_user_answers_owner_select ON public.user_answers
FOR SELECT TO authenticated
USING (public.current_user_owns_attempt(attempt_id));

DROP POLICY IF EXISTS learnia_flashcards_member_select ON public.flashcards;
CREATE POLICY learnia_flashcards_member_select ON public.flashcards
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));
DROP POLICY IF EXISTS learnia_flashcards_manager_insert ON public.flashcards;
CREATE POLICY learnia_flashcards_manager_insert ON public.flashcards
FOR INSERT TO authenticated
WITH CHECK (
    public.current_user_can_manage_notebook(notebook_id)
    AND public.current_user_can_manage_question(question_id)
);
DROP POLICY IF EXISTS learnia_flashcards_manager_update ON public.flashcards;
CREATE POLICY learnia_flashcards_manager_update ON public.flashcards
FOR UPDATE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id))
WITH CHECK (
    public.current_user_can_manage_notebook(notebook_id)
    AND public.current_user_can_manage_question(question_id)
);
DROP POLICY IF EXISTS learnia_flashcards_manager_delete ON public.flashcards;
CREATE POLICY learnia_flashcards_manager_delete ON public.flashcards
FOR DELETE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id));

DROP POLICY IF EXISTS learnia_documents_member_select ON public.documents;
CREATE POLICY learnia_documents_member_select ON public.documents
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));
DROP POLICY IF EXISTS learnia_documents_manager_insert ON public.documents;
CREATE POLICY learnia_documents_manager_insert ON public.documents
FOR INSERT TO authenticated
WITH CHECK (public.current_user_can_manage_notebook(notebook_id));
DROP POLICY IF EXISTS learnia_documents_manager_update ON public.documents;
CREATE POLICY learnia_documents_manager_update ON public.documents
FOR UPDATE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id))
WITH CHECK (public.current_user_can_manage_notebook(notebook_id));
DROP POLICY IF EXISTS learnia_documents_manager_delete ON public.documents;
CREATE POLICY learnia_documents_manager_delete ON public.documents
FOR DELETE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id));

DROP POLICY IF EXISTS learnia_document_chunks_member_select ON public.document_chunks;
CREATE POLICY learnia_document_chunks_member_select ON public.document_chunks
FOR SELECT TO authenticated
USING (public.current_user_can_access_document(document_id));
DROP POLICY IF EXISTS learnia_document_chunks_manager_insert ON public.document_chunks;
-- Embeddings are generated by the trusted RAG pipeline. Direct client writes
-- would let a notebook member poison retrieval results.

DROP POLICY IF EXISTS learnia_conversations_member_select ON public.ai_conversations;
CREATE POLICY learnia_conversations_member_select ON public.ai_conversations
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));
DROP POLICY IF EXISTS learnia_conversations_member_insert ON public.ai_conversations;
-- Conversation/message writes go through the API so it can derive the actor,
-- enforce ordering and apply model/input limits.

DROP POLICY IF EXISTS learnia_messages_member_select ON public.messages;
CREATE POLICY learnia_messages_member_select ON public.messages
FOR SELECT TO authenticated
USING (public.current_user_can_access_conversation(conversation_id));
DROP POLICY IF EXISTS learnia_messages_member_insert ON public.messages;

DROP POLICY IF EXISTS learnia_storage_documents_select ON storage.objects;
CREATE POLICY learnia_storage_documents_select ON storage.objects
FOR SELECT TO authenticated
USING (
    bucket_id = 'documents'
    AND public.current_user_is_active()
    AND public.current_user_is_notebook_member(
        public.storage_path_first_uuid(name)
    )
);
DROP POLICY IF EXISTS learnia_storage_documents_insert ON storage.objects;
DROP POLICY IF EXISTS learnia_storage_documents_update ON storage.objects;
DROP POLICY IF EXISTS learnia_storage_documents_delete ON storage.objects;
-- The document pipeline uses a service client after application-level access,
-- MIME and size checks. Authenticated clients only receive read access here.

DROP POLICY IF EXISTS learnia_storage_profile_select ON storage.objects;
CREATE POLICY learnia_storage_profile_select ON storage.objects
FOR SELECT TO authenticated
USING (
    bucket_id = 'profile'
    AND public.current_user_is_active()
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
    AND (
        name = ANY (ARRAY[
            (SELECT auth.uid())::TEXT || '/profile.jpg',
            (SELECT auth.uid())::TEXT || '/profile.png',
            (SELECT auth.uid())::TEXT || '/profile.webp',
            (SELECT auth.uid())::TEXT || '/profile.gif'
        ])
        OR name ~ (
            '^' || (SELECT auth.uid())::TEXT
            || '/profile-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
            || '[0-9a-f]{4}-[0-9a-f]{12}[.](jpg|png|webp|gif)$'
        )
    )
);
DROP POLICY IF EXISTS learnia_storage_profile_insert ON storage.objects;
CREATE POLICY learnia_storage_profile_insert ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'profile'
    AND public.current_user_is_active()
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
    AND (
        name = ANY (ARRAY[
            (SELECT auth.uid())::TEXT || '/profile.jpg',
            (SELECT auth.uid())::TEXT || '/profile.png',
            (SELECT auth.uid())::TEXT || '/profile.webp',
            (SELECT auth.uid())::TEXT || '/profile.gif'
        ])
        OR name ~ (
            '^' || (SELECT auth.uid())::TEXT
            || '/profile-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
            || '[0-9a-f]{4}-[0-9a-f]{12}[.](jpg|png|webp|gif)$'
        )
    )
);
DROP POLICY IF EXISTS learnia_storage_profile_update ON storage.objects;
CREATE POLICY learnia_storage_profile_update ON storage.objects
FOR UPDATE TO authenticated
USING (
    bucket_id = 'profile'
    AND public.current_user_is_active()
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
    AND (
        name = ANY (ARRAY[
            (SELECT auth.uid())::TEXT || '/profile.jpg',
            (SELECT auth.uid())::TEXT || '/profile.png',
            (SELECT auth.uid())::TEXT || '/profile.webp',
            (SELECT auth.uid())::TEXT || '/profile.gif'
        ])
        OR name ~ (
            '^' || (SELECT auth.uid())::TEXT
            || '/profile-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
            || '[0-9a-f]{4}-[0-9a-f]{12}[.](jpg|png|webp|gif)$'
        )
    )
)
WITH CHECK (
    bucket_id = 'profile'
    AND public.current_user_is_active()
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
    AND (
        name = ANY (ARRAY[
            (SELECT auth.uid())::TEXT || '/profile.jpg',
            (SELECT auth.uid())::TEXT || '/profile.png',
            (SELECT auth.uid())::TEXT || '/profile.webp',
            (SELECT auth.uid())::TEXT || '/profile.gif'
        ])
        OR name ~ (
            '^' || (SELECT auth.uid())::TEXT
            || '/profile-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
            || '[0-9a-f]{4}-[0-9a-f]{12}[.](jpg|png|webp|gif)$'
        )
    )
);
DROP POLICY IF EXISTS learnia_storage_profile_delete ON storage.objects;
CREATE POLICY learnia_storage_profile_delete ON storage.objects
FOR DELETE TO authenticated
USING (
    bucket_id = 'profile'
    AND public.current_user_is_active()
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
    AND (
        name = ANY (ARRAY[
            (SELECT auth.uid())::TEXT || '/profile.jpg',
            (SELECT auth.uid())::TEXT || '/profile.png',
            (SELECT auth.uid())::TEXT || '/profile.webp',
            (SELECT auth.uid())::TEXT || '/profile.gif'
        ])
        OR name ~ (
            '^' || (SELECT auth.uid())::TEXT
            || '/profile-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
            || '[0-9a-f]{4}-[0-9a-f]{12}[.](jpg|png|webp|gif)$'
        )
    )
);

COMMIT;
