BEGIN;

-- Security-definer helpers avoid recursive RLS evaluation across membership tables.
-- They only answer questions about auth.uid(); callers cannot inspect another user.
CREATE OR REPLACE FUNCTION public.current_user_is_room_member(target_room_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
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
    SELECT EXISTS (
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
    SELECT
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
        );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_manage_notebook(target_notebook_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT
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
        );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_access_exam(target_exam_id UUID)
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
        EXISTS (
            SELECT 1
            FROM public.exam_questions eq
            JOIN public.exams e ON e.exam_id = eq.exam_id
            WHERE eq.question_id = target_question_id
              AND public.current_user_can_manage_notebook(e.notebook_id)
        )
        OR EXISTS (
            SELECT 1
            FROM public.flashcards f
            WHERE f.question_id = target_question_id
              AND public.current_user_can_manage_notebook(f.notebook_id)
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
    SELECT EXISTS (
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

-- Enforce the same upload envelope at Storage itself. The publishable key is
-- intentionally public, so API-only validation is not a security boundary.
UPDATE storage.buckets
SET public = FALSE,
    file_size_limit = 10485760,
    allowed_mime_types = ARRAY[
        'application/pdf',
        'text/plain',
        'text/markdown'
    ]::TEXT[]
WHERE id = 'documents';

UPDATE storage.buckets
SET public = FALSE,
    file_size_limit = 5242880,
    allowed_mime_types = ARRAY[
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/gif'
    ]::TEXT[]
WHERE id = 'profile';

DROP POLICY IF EXISTS learnia_health_read ON public.health;
CREATE POLICY learnia_health_read ON public.health
FOR SELECT TO anon, authenticated USING (TRUE);

DROP POLICY IF EXISTS learnia_users_self_select ON public.users;
CREATE POLICY learnia_users_self_select ON public.users
FOR SELECT TO authenticated USING (user_id = (SELECT auth.uid()));
DROP POLICY IF EXISTS learnia_users_self_insert ON public.users;
CREATE POLICY learnia_users_self_insert ON public.users
FOR INSERT TO authenticated WITH CHECK (user_id = (SELECT auth.uid()));
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
CREATE POLICY learnia_personal_notebooks_self_insert ON public.personal_notebooks
FOR INSERT TO authenticated WITH CHECK (user_id = (SELECT auth.uid()));
DROP POLICY IF EXISTS learnia_personal_notebooks_self_delete ON public.personal_notebooks;
CREATE POLICY learnia_personal_notebooks_self_delete ON public.personal_notebooks
FOR DELETE TO authenticated USING (user_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS learnia_room_notebooks_member_select ON public.room_notebooks;
CREATE POLICY learnia_room_notebooks_member_select ON public.room_notebooks
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));
DROP POLICY IF EXISTS learnia_room_notebooks_admin_insert ON public.room_notebooks;
CREATE POLICY learnia_room_notebooks_admin_insert ON public.room_notebooks
FOR INSERT TO authenticated WITH CHECK (public.current_user_is_room_admin(room_id));
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
    AND public.current_user_can_access_question(question_id)
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
WITH CHECK (public.current_user_can_manage_notebook(notebook_id));
DROP POLICY IF EXISTS learnia_flashcards_manager_update ON public.flashcards;
CREATE POLICY learnia_flashcards_manager_update ON public.flashcards
FOR UPDATE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id))
WITH CHECK (public.current_user_can_manage_notebook(notebook_id));
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
CREATE POLICY learnia_document_chunks_manager_insert ON public.document_chunks
FOR INSERT TO authenticated
WITH CHECK (public.current_user_can_access_document(document_id));

DROP POLICY IF EXISTS learnia_conversations_member_select ON public.ai_conversations;
CREATE POLICY learnia_conversations_member_select ON public.ai_conversations
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));
DROP POLICY IF EXISTS learnia_conversations_member_insert ON public.ai_conversations;
CREATE POLICY learnia_conversations_member_insert ON public.ai_conversations
FOR INSERT TO authenticated
WITH CHECK (public.current_user_is_notebook_member(notebook_id));

DROP POLICY IF EXISTS learnia_messages_member_select ON public.messages;
CREATE POLICY learnia_messages_member_select ON public.messages
FOR SELECT TO authenticated
USING (public.current_user_can_access_conversation(conversation_id));
DROP POLICY IF EXISTS learnia_messages_member_insert ON public.messages;
CREATE POLICY learnia_messages_member_insert ON public.messages
FOR INSERT TO authenticated
WITH CHECK (
    role = 'user'
    AND sent_by_user_id = (SELECT auth.uid())
    AND public.current_user_can_access_conversation(conversation_id)
);

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS learnia_storage_documents_select ON storage.objects;
CREATE POLICY learnia_storage_documents_select ON storage.objects
FOR SELECT TO authenticated
USING (
    bucket_id = 'documents'
    AND public.current_user_is_notebook_member(
        public.storage_path_first_uuid(name)
    )
);
DROP POLICY IF EXISTS learnia_storage_documents_insert ON storage.objects;
CREATE POLICY learnia_storage_documents_insert ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'documents'
    AND public.current_user_is_notebook_member(
        public.storage_path_first_uuid(name)
    )
);
DROP POLICY IF EXISTS learnia_storage_documents_update ON storage.objects;
CREATE POLICY learnia_storage_documents_update ON storage.objects
FOR UPDATE TO authenticated
USING (
    bucket_id = 'documents'
    AND public.current_user_can_manage_notebook(
        public.storage_path_first_uuid(name)
    )
)
WITH CHECK (
    bucket_id = 'documents'
    AND public.current_user_can_manage_notebook(
        public.storage_path_first_uuid(name)
    )
);
DROP POLICY IF EXISTS learnia_storage_documents_delete ON storage.objects;
CREATE POLICY learnia_storage_documents_delete ON storage.objects
FOR DELETE TO authenticated
USING (
    bucket_id = 'documents'
    AND public.current_user_can_manage_notebook(
        public.storage_path_first_uuid(name)
    )
);

DROP POLICY IF EXISTS learnia_storage_profile_select ON storage.objects;
CREATE POLICY learnia_storage_profile_select ON storage.objects
FOR SELECT TO authenticated
USING (
    bucket_id = 'profile'
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
);
DROP POLICY IF EXISTS learnia_storage_profile_insert ON storage.objects;
CREATE POLICY learnia_storage_profile_insert ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'profile'
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
);
DROP POLICY IF EXISTS learnia_storage_profile_update ON storage.objects;
CREATE POLICY learnia_storage_profile_update ON storage.objects
FOR UPDATE TO authenticated
USING (
    bucket_id = 'profile'
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
)
WITH CHECK (
    bucket_id = 'profile'
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
);
DROP POLICY IF EXISTS learnia_storage_profile_delete ON storage.objects;
CREATE POLICY learnia_storage_profile_delete ON storage.objects
FOR DELETE TO authenticated
USING (
    bucket_id = 'profile'
    AND public.storage_path_first_uuid(name) = (SELECT auth.uid())
);

COMMIT;
