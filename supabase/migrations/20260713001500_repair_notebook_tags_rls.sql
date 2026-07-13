BEGIN;

-- Some environments were bootstrapped before the complete security migration
-- history was registered. Recreate only the helpers needed by notebook_tags so
-- this repair remains safe and idempotent on both old and current databases.
CREATE OR REPLACE FUNCTION public.current_user_is_active()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.users AS app_user
        WHERE app_user.user_id = (SELECT auth.uid())
          AND app_user.status = 'active'
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_is_notebook_member(
    target_notebook_id UUID
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT public.current_user_is_active() AND (
        EXISTS (
            SELECT 1
            FROM public.personal_notebooks AS personal
            WHERE personal.user_id = (SELECT auth.uid())
              AND personal.notebook_id = target_notebook_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.room_notebooks AS room_notebook
            JOIN public.members_rooms AS room_member
              ON room_member.room_id = room_notebook.room_id
            JOIN public.study_members AS study_member
              ON study_member.member_id = room_member.member_id
            WHERE study_member.user_id = (SELECT auth.uid())
              AND room_notebook.notebook_id = target_notebook_id
        )
    );
$$;

CREATE OR REPLACE FUNCTION public.current_user_can_manage_notebook(
    target_notebook_id UUID
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT public.current_user_is_active() AND (
        EXISTS (
            SELECT 1
            FROM public.personal_notebooks AS personal
            WHERE personal.user_id = (SELECT auth.uid())
              AND personal.notebook_id = target_notebook_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.room_notebooks AS room_notebook
            JOIN public.members_rooms AS room_member
              ON room_member.room_id = room_notebook.room_id
            JOIN public.study_members AS study_member
              ON study_member.member_id = room_member.member_id
            WHERE study_member.user_id = (SELECT auth.uid())
              AND room_notebook.notebook_id = target_notebook_id
              AND room_member.role = 'admin'
        )
    );
$$;

REVOKE ALL ON FUNCTION public.current_user_is_active()
FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.current_user_is_notebook_member(UUID)
FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.current_user_can_manage_notebook(UUID)
FROM PUBLIC, anon;

GRANT EXECUTE ON FUNCTION public.current_user_is_active()
TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_is_notebook_member(UUID)
TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.current_user_can_manage_notebook(UUID)
TO authenticated, service_role;

ALTER TABLE public.notebook_tags ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS learnia_notebook_tags_member_select
ON public.notebook_tags;
CREATE POLICY learnia_notebook_tags_member_select
ON public.notebook_tags
FOR SELECT TO authenticated
USING (public.current_user_is_notebook_member(notebook_id));

DROP POLICY IF EXISTS learnia_notebook_tags_manager_insert
ON public.notebook_tags;
CREATE POLICY learnia_notebook_tags_manager_insert
ON public.notebook_tags
FOR INSERT TO authenticated
WITH CHECK (
    public.current_user_can_manage_notebook(notebook_id)
    AND EXISTS (
        SELECT 1
        FROM public.tags AS available_tag
        WHERE available_tag.id = notebook_tags.tag_id
          AND available_tag.status = 'active'
          AND (
              available_tag.created_by_user_id IS NULL
              OR available_tag.created_by_user_id = (SELECT auth.uid())
          )
    )
);

DROP POLICY IF EXISTS learnia_notebook_tags_manager_delete
ON public.notebook_tags;
CREATE POLICY learnia_notebook_tags_manager_delete
ON public.notebook_tags
FOR DELETE TO authenticated
USING (public.current_user_can_manage_notebook(notebook_id));

REVOKE ALL PRIVILEGES ON TABLE public.notebook_tags
FROM PUBLIC, anon, authenticated;
GRANT SELECT, DELETE ON TABLE public.notebook_tags TO authenticated;
GRANT INSERT (notebook_id, tag_id)
ON TABLE public.notebook_tags TO authenticated;
GRANT ALL PRIVILEGES ON TABLE public.notebook_tags TO service_role;

COMMIT;
