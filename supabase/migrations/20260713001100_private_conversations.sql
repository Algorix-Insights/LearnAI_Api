BEGIN;

ALTER TABLE public.ai_conversations
ADD COLUMN IF NOT EXISTS created_by_user_id UUID
REFERENCES public.users(user_id)
ON DELETE CASCADE;

-- Personal-notebook conversations have an unambiguous historical owner. Legacy
-- room conversations cannot be attributed safely and remain inaccessible until
-- explicitly repaired by an administrator.
UPDATE public.ai_conversations AS conversation
SET created_by_user_id = personal.user_id
FROM public.personal_notebooks AS personal
WHERE personal.notebook_id = conversation.notebook_id
  AND conversation.created_by_user_id IS NULL;

CREATE INDEX IF NOT EXISTS ai_conversations_owner_updated_idx
ON public.ai_conversations (created_by_user_id, updated_at DESC);

CREATE OR REPLACE FUNCTION public.current_user_can_access_conversation(
    target_conversation_id UUID
)
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
          AND c.created_by_user_id = (SELECT auth.uid())
          AND public.current_user_is_notebook_member(c.notebook_id)
    );
$$;

REVOKE ALL ON FUNCTION public.current_user_can_access_conversation(UUID)
FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.current_user_can_access_conversation(UUID)
TO authenticated, service_role;

DROP POLICY IF EXISTS learnia_conversations_member_select
ON public.ai_conversations;
DROP POLICY IF EXISTS learnia_conversations_owner_select
ON public.ai_conversations;
CREATE POLICY learnia_conversations_owner_select
ON public.ai_conversations
FOR SELECT TO authenticated
USING (
    created_by_user_id = (SELECT auth.uid())
    AND public.current_user_is_notebook_member(notebook_id)
);

DROP POLICY IF EXISTS learnia_messages_member_select ON public.messages;
DROP POLICY IF EXISTS learnia_messages_owner_select ON public.messages;
CREATE POLICY learnia_messages_owner_select
ON public.messages
FOR SELECT TO authenticated
USING (public.current_user_can_access_conversation(conversation_id));

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
             AND c.created_by_user_id = p_actor_id
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

REVOKE ALL ON FUNCTION public.append_conversation_message(UUID, UUID, TEXT, TEXT)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.append_conversation_message(UUID, UUID, TEXT, TEXT)
TO service_role;

COMMIT;
