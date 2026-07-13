from pathlib import Path


def test_supabase_migrations_use_unique_timestamp_versions() -> None:
    migration_dir = Path(__file__).parents[1] / "supabase" / "migrations"
    files = sorted(migration_dir.glob("*.sql"))
    versions = [file.name.split("_", 1)[0] for file in files]

    assert len(files) == 12
    assert len(versions) == len(set(versions))
    assert versions == sorted(versions)
    assert all(len(version) == 14 and version.isdigit() for version in versions)


def test_rag_persistence_and_conversation_privacy_are_database_enforced() -> None:
    migration_dir = Path(__file__).parents[1] / "supabase" / "migrations"
    atomic = (migration_dir / "20260713001000_atomic_rag_generation.sql").read_text()
    privacy = (migration_dir / "20260713001100_private_conversations.sql").read_text()

    assert "persist_generated_flashcards" in atomic
    assert "persist_generated_exam" in atomic
    assert "pg_advisory_xact_lock" in atomic
    assert "TO service_role" in atomic
    assert "created_by_user_id = (SELECT auth.uid())" in privacy
    assert "created_by_user_id = p_actor_id" in privacy

    quotas = (migration_dir / "20260713001200_ai_usage_quotas.sql").read_text()
    assert "pg_advisory_xact_lock" in quotas
    assert "ai_usage_rate_limit" in quotas
    assert "TO service_role" in quotas
