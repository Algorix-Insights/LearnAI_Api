BEGIN;

-- Create the notebook and its ownership link atomically. The owner comes only
-- from the authenticated PostgreSQL session, never from request JSON.
CREATE OR REPLACE FUNCTION public.create_personal_notebook(
    p_name TEXT,
    p_description TEXT DEFAULT NULL,
    p_summary TEXT DEFAULT NULL,
    p_is_favorite BOOLEAN DEFAULT FALSE,
    p_due_date TIMESTAMPTZ DEFAULT NULL
)
RETURNS public.notebooks
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    actor_id UUID := auth.uid();
    created_notebook public.notebooks%ROWTYPE;
BEGIN
    IF actor_id IS NULL THEN
        RAISE EXCEPTION 'authentication required' USING ERRCODE = '28000';
    END IF;
    IF NOT public.current_user_is_active() THEN
        RAISE EXCEPTION 'inactive user' USING ERRCODE = '42501';
    END IF;

    IF COALESCE(LENGTH(BTRIM(p_name)), 0) NOT BETWEEN 1 AND 200
       OR COALESCE(LENGTH(p_description), 0) > 4000
       OR COALESCE(LENGTH(p_summary), 0) > 10000 THEN
        RAISE EXCEPTION 'invalid notebook payload' USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.users AS u WHERE u.user_id = actor_id
    ) THEN
        RAISE EXCEPTION 'user profile missing' USING ERRCODE = '23503';
    END IF;

    INSERT INTO public.notebooks (
        name, description, summary, is_favorite, due_date
    )
    VALUES (
        BTRIM(p_name), p_description, p_summary, p_is_favorite, p_due_date
    )
    RETURNING * INTO created_notebook;

    INSERT INTO public.personal_notebooks (notebook_id, user_id)
    VALUES (created_notebook.notebook_id, actor_id);

    RETURN created_notebook;
END;
$$;

-- Create a room and make the caller its initial administrator in the same
-- transaction. A study-member identity is created once per authenticated user.
CREATE OR REPLACE FUNCTION public.create_study_room(
    p_name TEXT,
    p_description TEXT DEFAULT NULL,
    p_nickname TEXT DEFAULT NULL
)
RETURNS public.rooms
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    actor_id UUID := auth.uid();
    actor_member_id UUID;
    actor_nickname TEXT;
    created_room public.rooms%ROWTYPE;
BEGIN
    IF actor_id IS NULL THEN
        RAISE EXCEPTION 'authentication required' USING ERRCODE = '28000';
    END IF;
    IF NOT public.current_user_is_active() THEN
        RAISE EXCEPTION 'inactive user' USING ERRCODE = '42501';
    END IF;

    IF COALESCE(LENGTH(BTRIM(p_name)), 0) NOT BETWEEN 1 AND 200
       OR COALESCE(LENGTH(p_description), 0) > 4000
       OR COALESCE(LENGTH(BTRIM(p_nickname)), 0) > 100 THEN
        RAISE EXCEPTION 'invalid room payload' USING ERRCODE = '22023';
    END IF;

    SELECT sm.member_id
    INTO actor_member_id
    FROM public.study_members AS sm
    WHERE sm.user_id = actor_id;

    IF actor_member_id IS NULL THEN
        SELECT COALESCE(
            NULLIF(BTRIM(p_nickname), ''),
            NULLIF(BTRIM(CONCAT_WS(' ', u.name, u.last_name)), ''),
            'Usuario'
        )
        INTO actor_nickname
        FROM public.users AS u
        WHERE u.user_id = actor_id;

        IF actor_nickname IS NULL THEN
            RAISE EXCEPTION 'user profile missing' USING ERRCODE = '23503';
        END IF;

        INSERT INTO public.study_members (user_id, nickname)
        VALUES (actor_id, LEFT(actor_nickname, 100))
        ON CONFLICT (user_id) DO NOTHING
        RETURNING member_id INTO actor_member_id;

        -- A concurrent room creation can win the unique user_id insert while this
        -- transaction waits. Read the winner instead of failing the whole RPC.
        IF actor_member_id IS NULL THEN
            SELECT sm.member_id
            INTO actor_member_id
            FROM public.study_members AS sm
            WHERE sm.user_id = actor_id;
        END IF;
    END IF;

    INSERT INTO public.rooms (name, description)
    VALUES (BTRIM(p_name), p_description)
    RETURNING * INTO created_room;

    INSERT INTO public.members_rooms (member_id, room_id, role)
    VALUES (actor_member_id, created_room.room_id, 'admin');

    RETURN created_room;
END;
$$;

-- Attach an existing notebook without trusting a client-supplied creator. The
-- caller must administer the room and already manage the notebook.
CREATE OR REPLACE FUNCTION public.attach_room_notebook(
    p_room_id UUID,
    p_notebook_id UUID
)
RETURNS public.room_notebooks
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    actor_id UUID := auth.uid();
    actor_member_id UUID;
    created_link public.room_notebooks%ROWTYPE;
BEGIN
    IF actor_id IS NULL THEN
        RAISE EXCEPTION 'authentication required' USING ERRCODE = '28000';
    END IF;
    IF NOT public.current_user_is_active() THEN
        RAISE EXCEPTION 'inactive user' USING ERRCODE = '42501';
    END IF;

    SELECT sm.member_id
    INTO actor_member_id
    FROM public.study_members AS sm
    WHERE sm.user_id = actor_id;

    IF actor_member_id IS NULL
       OR NOT public.current_user_is_room_admin(p_room_id)
       OR NOT public.current_user_can_manage_notebook(p_notebook_id) THEN
        RAISE EXCEPTION 'resource not found' USING ERRCODE = 'P0002';
    END IF;

    INSERT INTO public.room_notebooks (notebook_id, room_id, created_by)
    VALUES (p_notebook_id, p_room_id, actor_member_id)
    RETURNING * INTO created_link;

    INSERT INTO public.user_learning_events (
        user_id,
        notebook_id,
        activity_type,
        quantity,
        duration_seconds,
        metadata
    )
    VALUES (
        actor_id,
        p_notebook_id,
        'notebook_shared',
        1,
        0,
        jsonb_build_object('room_id', p_room_id)
    );

    RETURN created_link;
END;
$$;

-- Direct Data API writes must meet the same invariants as the RPC.
DROP POLICY IF EXISTS learnia_room_notebooks_admin_insert
ON public.room_notebooks;
CREATE POLICY learnia_room_notebooks_admin_insert
ON public.room_notebooks
FOR INSERT TO authenticated
WITH CHECK (
    public.current_user_is_room_admin(room_id)
    AND public.current_user_can_manage_notebook(notebook_id)
    AND created_by = (
        SELECT sm.member_id
        FROM public.study_members AS sm
        WHERE sm.user_id = (SELECT auth.uid())
    )
);

-- Linking an arbitrary notebook as "personal" would turn a guessed UUID into
-- ownership. Only create_personal_notebook may create this relationship.
DROP POLICY IF EXISTS learnia_personal_notebooks_self_insert
ON public.personal_notebooks;

REVOKE ALL ON FUNCTION public.create_personal_notebook(
    TEXT, TEXT, TEXT, BOOLEAN, TIMESTAMPTZ
) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.create_study_room(TEXT, TEXT, TEXT)
FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.attach_room_notebook(UUID, UUID)
FROM PUBLIC, anon;

GRANT EXECUTE ON FUNCTION public.create_personal_notebook(
    TEXT, TEXT, TEXT, BOOLEAN, TIMESTAMPTZ
) TO authenticated;
GRANT EXECUTE ON FUNCTION public.create_study_room(TEXT, TEXT, TEXT)
TO authenticated;
GRANT EXECUTE ON FUNCTION public.attach_room_notebook(UUID, UUID)
TO authenticated;

-- Credentials live only in Supabase Auth.
ALTER TABLE public.users DROP COLUMN IF EXISTS hash_password;

COMMIT;
