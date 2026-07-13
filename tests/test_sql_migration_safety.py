from __future__ import annotations

import re
from pathlib import Path


MIGRATIONS = Path(__file__).parents[1] / "supabase" / "migrations"


def _sql(name: str) -> str:
    return (MIGRATIONS / name).read_text(encoding="utf-8")


def test_membership_role_constraint_is_dropped_before_data_rewrite() -> None:
    migration = _sql("20260713000400_rag_storage_multitenant.sql")

    constraint_drop = migration.index("END $$;")
    data_rewrite = migration.index("UPDATE members_rooms")
    replacement_check = migration.index("ADD CONSTRAINT members_rooms_role_check")

    assert constraint_drop < data_rewrite < replacement_check


def test_public_tables_are_fail_closed_in_their_creation_migrations() -> None:
    initial = _sql("20260713000100_initial_schema.sql")
    tags = _sql("20260713000200_add_tags_to_notebooks.sql")
    rag = _sql("20260713000400_rag_storage_multitenant.sql")

    for table in (
        "health",
        "users",
        "notebooks",
        "rooms",
        "study_members",
        "members_rooms",
        "personal_notebooks",
        "room_notebooks",
        "exams",
        "questions",
        "exam_questions",
        "questions_options",
        "attempts",
        "user_answers",
        "flashcards",
        "documents",
        "document_chunks",
        "ai_conversations",
        "messages",
    ):
        assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;" in initial
    for table in ("tags", "notebook_tags"):
        assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;" in tags
    assert (
        "REVOKE ALL ON FUNCTION public.match_document_chunks(VECTOR, UUID, INT)"
        in rag
    )


def test_atomic_generation_rejects_null_collections() -> None:
    migration = _sql("20260713001000_atomic_rag_generation.sql")

    assert "IF p_items IS NULL" in migration
    assert "OR p_questions IS NULL" in migration


def test_flashcard_listing_never_exposes_exam_answer_keys() -> None:
    migration = _sql("20260713001000_atomic_rag_generation.sql")
    listing = migration[
        migration.index("CREATE OR REPLACE FUNCTION public.list_notebook_flashcards(") :
        migration.index("CREATE OR REPLACE FUNCTION public.append_conversation_message(")
    ]

    assert "AND NOT EXISTS (" in listing
    assert "FROM public.exam_questions eq" in listing
    assert "WHERE eq.question_id = f.question_id" in listing


def test_authenticated_grants_hide_internal_document_fields() -> None:
    migration = _sql("20260713000500_security_rls.sql")

    document_grant = migration[
        migration.index("GRANT SELECT (\n    document_id,") : migration.index(
            ") ON TABLE public.documents TO authenticated;"
        )
    ]
    assert "storage_path" not in document_grant
    assert "content_text" not in document_grant
    assert "content_hash" not in document_grant

    chunk_start = migration.index("GRANT SELECT (\n    chunk_id,")
    chunk_grant = migration[
        chunk_start : migration.index(
            ") ON TABLE public.document_chunks TO authenticated;", chunk_start
        )
    ]
    assert "embedding" not in chunk_grant


def test_authenticated_mutations_use_column_level_grants() -> None:
    migration = _sql("20260713000500_security_rls.sql")

    assert "GRANT SELECT, UPDATE, DELETE ON TABLE public.notebooks" not in migration
    assert "GRANT SELECT, UPDATE, DELETE ON TABLE public.rooms" not in migration
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.study_members" not in migration
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.members_rooms" not in migration
    assert "GRANT SELECT, UPDATE, DELETE ON TABLE public.exams" not in migration
    assert "GRANT UPDATE (role) ON TABLE public.members_rooms" in migration


def test_inactive_accounts_are_blocked_by_rls_rpcs_and_storage() -> None:
    security = _sql("20260713000500_security_rls.sql")
    statistics = _sql("20260713000700_user_learning_statistics.sql")
    owned = _sql("20260713000800_owned_resource_workflows.sql")
    events = _sql("20260713000900_learning_event_hardening.sql")

    assert "CREATE OR REPLACE FUNCTION public.current_user_is_active()" in security
    assert "AS RESTRICTIVE FOR ALL TO authenticated" in security
    assert "public.current_user_is_active()" in security[
        security.index("learnia_storage_documents_select") :
    ]
    assert "profile-[0-9a-f]{8}" in security
    assert "AS RESTRICTIVE" in statistics
    assert owned.count("IF NOT public.current_user_is_active()") == 3
    assert "IF NOT public.current_user_is_active()" in events


def test_attempt_start_is_atomic_limited_and_recoverable() -> None:
    migration = _sql("20260713000600_exam_attempt_workflow.sql")

    assert "ADD COLUMN IF NOT EXISTS attempt_number INTEGER" in migration
    assert "CREATE OR REPLACE FUNCTION public.start_exam_attempt(" in migration
    assert "pg_catalog.pg_advisory_xact_lock" in migration
    assert "attempt.status = 'in_progress'" in migration
    assert "RETURN NEXT v_existing" in migration
    assert "attempt_limit_reached" in migration
    assert "TO service_role" in migration


def test_preflight_detects_duplicate_active_attempts_before_unique_index() -> None:
    preflight = (
        Path(__file__).parents[1] / "scripts" / "security_preflight.sql"
    ).read_text(encoding="utf-8")

    assert "WHERE attempt.status = 'in_progress'" in preflight
    assert "GROUP BY attempt.exam_id, attempt.user_id" in preflight
    assert "HAVING COUNT(*) > 1" in preflight


def test_attempt_finalization_verifies_the_graded_answer_snapshot() -> None:
    migration = _sql("20260713000600_exam_attempt_workflow.sql")

    assert "attempt_answers_changed" in migration
    assert "v_grade ? 'selected_option_id'" in migration
    assert "v_grade ? 'answer_text'" in migration
    assert "answer.question_id = v_question_id" in migration
    assert "answer.selected_option_id IS NOT DISTINCT FROM v_selected_option_id" in migration
    assert "answer.answer_text IS NOT DISTINCT FROM v_answer_text" in migration


def test_concurrent_room_creation_reuses_study_member_identity() -> None:
    migration = _sql("20260713000800_owned_resource_workflows.sql")

    assert "ON CONFLICT (user_id) DO NOTHING" in migration
    assert migration.count("WHERE sm.user_id = actor_id;") >= 2


def test_every_security_definer_has_fixed_search_path_and_public_revoke() -> None:
    for migration_path in sorted(MIGRATIONS.glob("*.sql")):
        migration = migration_path.read_text(encoding="utf-8")
        headers = re.finditer(
            r"CREATE OR REPLACE FUNCTION\s+(public\.[a-z0-9_]+)\s*\(.*?\)"
            r"\s*RETURNS\b.*?\bAS\s+\$\$",
            migration,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for match in headers:
            header = match.group(0)
            if "SECURITY DEFINER" not in header.upper():
                continue
            function_name = match.group(1)
            assert "SET search_path = ''" in header, (
                f"{migration_path.name}: {function_name} needs a fixed search_path"
            )
            assert f"REVOKE ALL ON FUNCTION {function_name}(" in migration, (
                f"{migration_path.name}: {function_name} keeps PUBLIC execute"
            )
