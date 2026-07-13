-- Read-only deployment preflight. Run this against staging/production before
-- supabase/migrations/20260713000500_security_rls.sql. Any returned unexpected policy must be
-- reviewed: permissive PostgreSQL policies combine with OR.

WITH scoped_tables(table_name) AS (
    VALUES
        ('health'),
        ('users'),
        ('notebooks'),
        ('rooms'),
        ('study_members'),
        ('members_rooms'),
        ('personal_notebooks'),
        ('room_notebooks'),
        ('exams'),
        ('questions'),
        ('exam_questions'),
        ('questions_options'),
        ('attempts'),
        ('user_answers'),
        ('flashcards'),
        ('documents'),
        ('document_chunks'),
        ('ai_conversations'),
        ('messages'),
        ('tags'),
        ('notebook_tags')
)
SELECT
    policy.schemaname,
    policy.tablename,
    policy.policyname,
    policy.permissive,
    policy.roles,
    policy.cmd,
    policy.qual,
    policy.with_check
FROM pg_catalog.pg_policies AS policy
JOIN scoped_tables AS scoped ON scoped.table_name = policy.tablename
WHERE policy.schemaname = 'public'
  AND policy.policyname NOT LIKE 'learnia\_%' ESCAPE '\'
ORDER BY policy.tablename, policy.policyname;

-- Storage is shared infrastructure. Review every policy manually; do not drop
-- policies for unrelated buckets merely because LearnIA does not recognize them.
SELECT
    policy.schemaname,
    policy.tablename,
    policy.policyname,
    policy.permissive,
    policy.roles,
    policy.cmd,
    policy.qual,
    policy.with_check
FROM pg_catalog.pg_policies AS policy
WHERE policy.schemaname = 'storage'
  AND policy.tablename = 'objects'
ORDER BY policy.policyname;

WITH scoped_tables(table_name) AS (
    VALUES
        ('health'),
        ('users'),
        ('notebooks'),
        ('rooms'),
        ('study_members'),
        ('members_rooms'),
        ('personal_notebooks'),
        ('room_notebooks'),
        ('exams'),
        ('questions'),
        ('exam_questions'),
        ('questions_options'),
        ('attempts'),
        ('user_answers'),
        ('flashcards'),
        ('documents'),
        ('document_chunks'),
        ('ai_conversations'),
        ('messages'),
        ('tags'),
        ('notebook_tags')
)
SELECT
    namespace.nspname AS schemaname,
    relation.relname AS tablename,
    relation.relrowsecurity AS rls_enabled,
    relation.relforcerowsecurity AS rls_forced
FROM pg_catalog.pg_class AS relation
JOIN pg_catalog.pg_namespace AS namespace
  ON namespace.oid = relation.relnamespace
JOIN scoped_tables AS scoped ON scoped.table_name = relation.relname
WHERE namespace.nspname = 'public'
  AND relation.relkind = 'r'
ORDER BY relation.relname;

SELECT
    grant_info.table_schema,
    grant_info.table_name,
    grant_info.grantee,
    grant_info.privilege_type
FROM information_schema.role_table_grants AS grant_info
WHERE grant_info.table_schema IN ('public', 'storage')
  AND grant_info.grantee IN ('anon', 'authenticated', 'service_role')
ORDER BY
    grant_info.table_schema,
    grant_info.table_name,
    grant_info.grantee,
    grant_info.privilege_type;

-- Migration filenames are timestamped and unique. Compare the local list with
-- the target history before every push; never repair versions by guesswork.

-- Migration 006 creates a unique partial index for active attempts. Any row
-- returned here must be reconciled in staging before the push, otherwise that
-- migration will stop without applying its transaction.
SELECT
    attempt.exam_id,
    attempt.user_id,
    COUNT(*) AS active_attempts
FROM public.attempts AS attempt
WHERE attempt.status = 'in_progress'
GROUP BY attempt.exam_id, attempt.user_id
HAVING COUNT(*) > 1
ORDER BY active_attempts DESC, attempt.exam_id, attempt.user_id;
