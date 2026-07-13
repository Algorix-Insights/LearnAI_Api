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
