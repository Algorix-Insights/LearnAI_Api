-- A tag belongs to the application profile in public.users, not directly to
-- auth.users. Running this trigger after the profile insert guarantees that
-- the owner row required by tags.created_by_user_id already exists.
CREATE OR REPLACE FUNCTION public.ensure_user_general_tag()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.tags (
        name,
        status,
        created_by_user_id
    )
    VALUES (
        'general',
        'active',
        NEW.user_id
    )
    ON CONFLICT (created_by_user_id, (LOWER(BTRIM(name))))
    WHERE created_by_user_id IS NOT NULL
    DO UPDATE SET
        name = EXCLUDED.name,
        status = EXCLUDED.status;

    RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.ensure_user_general_tag()
FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS trg_users_ensure_general_tag ON public.users;
CREATE TRIGGER trg_users_ensure_general_tag
AFTER INSERT ON public.users
FOR EACH ROW
EXECUTE FUNCTION public.ensure_user_general_tag();

-- Cover profiles created before the trigger. The same normalized-name conflict
-- target makes the backfill safe to rerun and reactivates an existing default.
INSERT INTO public.tags (
    name,
    status,
    created_by_user_id
)
SELECT
    'general',
    'active',
    app_user.user_id
FROM public.users AS app_user
WHERE TRUE
ON CONFLICT (created_by_user_id, (LOWER(BTRIM(name))))
WHERE created_by_user_id IS NOT NULL
DO UPDATE SET
    name = EXCLUDED.name,
    status = EXCLUDED.status;
