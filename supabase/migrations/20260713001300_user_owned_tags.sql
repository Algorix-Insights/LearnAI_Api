ALTER TABLE public.tags
ADD COLUMN IF NOT EXISTS created_by_user_id UUID
REFERENCES public.users(user_id)
ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS tags_created_by_user_id_idx
ON public.tags (created_by_user_id);

CREATE UNIQUE INDEX IF NOT EXISTS tags_owner_normalized_name_key
ON public.tags (created_by_user_id, LOWER(BTRIM(name)))
WHERE created_by_user_id IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'tags_name_not_blank_check'
          AND conrelid = 'public.tags'::regclass
    ) THEN
        -- Keep legacy rows deployable while rejecting blank names for every new
        -- insert/update, including writes made directly through PostgREST.
        ALTER TABLE public.tags
        ADD CONSTRAINT tags_name_not_blank_check
        CHECK (name = BTRIM(name) AND name <> '') NOT VALID;
    END IF;
END $$;

ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;

-- Rows created before tags had ownership remain global/read-only. Authenticated
-- users can list those legacy tags plus their own, but never another user's tags.
DROP POLICY IF EXISTS learnia_tags_authenticated_select ON public.tags;
DROP POLICY IF EXISTS learnia_tags_available_select ON public.tags;
CREATE POLICY learnia_tags_available_select ON public.tags
FOR SELECT TO authenticated
USING (
    status = 'active'
    AND (
        created_by_user_id IS NULL
        OR created_by_user_id = (SELECT auth.uid())
    )
);

DROP POLICY IF EXISTS learnia_tags_owner_insert ON public.tags;
CREATE POLICY learnia_tags_owner_insert ON public.tags
FOR INSERT TO authenticated
WITH CHECK (
    created_by_user_id = (SELECT auth.uid())
    AND status = 'active'
);

-- A notebook manager can only attach a global tag or one they created. This
-- closes the guessed-UUID path for linking another user's private tag.
DROP POLICY IF EXISTS learnia_notebook_tags_manager_insert ON public.notebook_tags;
CREATE POLICY learnia_notebook_tags_manager_insert ON public.notebook_tags
FOR INSERT TO authenticated
WITH CHECK (
    public.current_user_can_manage_notebook(notebook_id)
    AND EXISTS (
        SELECT 1
        FROM public.tags AS available_tag
        WHERE available_tag.id = notebook_tags.tag_id
          AND (
              available_tag.created_by_user_id IS NULL
              OR available_tag.created_by_user_id = (SELECT auth.uid())
          )
    )
);

REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE public.tags FROM authenticated;
GRANT SELECT (
    id,
    name,
    status,
    created_by_user_id
) ON TABLE public.tags TO authenticated;
GRANT INSERT (
    name,
    created_by_user_id
) ON TABLE public.tags TO authenticated;
