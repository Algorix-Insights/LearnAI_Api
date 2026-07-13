import asyncio
from pathlib import Path

from app.domain.schemas.resources.question_options import (
    QuestionOptionRepositoryListRequest,
)
from app.domain.schemas.resources.questions import QuestionRepositoryListRequest
from app.domain.schemas.resources.user_answers import UserAnswerRepositoryListRequest
from app.domain.schemas.resources.users import UserRepositoryListRequest
from app.infra.repositories.question_options import QuestionOptionRepository
from app.infra.repositories.questions import QuestionRepository
from app.infra.repositories.user_answers import UserAnswerRepository
from app.infra.repositories.users import UserRepository


class RecordingQuery:
    def __init__(self) -> None:
        self.selected: list[str] = []

    def select(self, columns: str) -> "RecordingQuery":
        self.selected.append(columns)
        return self

    def range(self, _start: int, _end: int) -> "RecordingQuery":
        return self

    def execute(self) -> object:
        return type("Response", (), {"data": []})()


class RecordingClient:
    def __init__(self) -> None:
        self.query = RecordingQuery()

    def table(self, _table_name: str) -> RecordingQuery:
        return self.query


def test_student_repositories_never_select_grading_columns() -> None:
    cases: list[tuple[object, object, set[str]]] = [
        (
            UserRepository(RecordingClient()),
            UserRepositoryListRequest(),
            {"hash_password"},
        ),
        (
            QuestionRepository(RecordingClient()),
            QuestionRepositoryListRequest(),
            {"expected_answer"},
        ),
        (
            QuestionOptionRepository(RecordingClient()),
            QuestionOptionRepositoryListRequest(),
            {"is_correct"},
        ),
        (
            UserAnswerRepository(RecordingClient()),
            UserAnswerRepositoryListRequest(),
            {"is_correct", "points_awarded"},
        ),
    ]

    for repository, request, forbidden_columns in cases:
        asyncio.run(repository.list(request))
        selected = set(repository.client.query.selected[-1].split(","))
        assert "*" not in selected
        assert selected.isdisjoint(forbidden_columns)


def test_rls_migration_revokes_table_wide_grading_select() -> None:
    migration = (Path(__file__).parents[1] / "supabase" / "migrations" / "20260713000500_security_rls.sql").read_text(
        encoding="utf-8"
    )

    assert "REVOKE INSERT, UPDATE, DELETE ON TABLE public.users" in migration
    for table in ("users", "questions", "questions_options", "user_answers"):
        assert f"REVOKE SELECT ON TABLE public.{table}" in migration
    assert "hash_password" not in _authenticated_grant(migration, "users")
    assert "expected_answer" not in _authenticated_grant(migration, "questions")
    assert "is_correct" not in _authenticated_grant(migration, "questions_options")
    assert "is_correct" not in _authenticated_grant(migration, "user_answers")
    assert "points_awarded" not in _authenticated_grant(migration, "user_answers")


def test_rls_migration_blocks_ownership_escalation_and_storage_ddl() -> None:
    migration = (Path(__file__).parents[1] / "supabase" / "migrations" / "20260713000500_security_rls.sql").read_text(
        encoding="utf-8"
    )

    # Supabase owns storage.objects and already enables RLS on it. Trying to alter
    # the table from an application migration can roll back the whole transaction.
    assert "ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY" not in migration

    policy_start = migration.index("DROP POLICY IF EXISTS learnia_personal_notebooks_self_insert")
    policy_end = migration.index(
        "DROP POLICY IF EXISTS learnia_personal_notebooks_self_delete",
        policy_start,
    )
    assert "CREATE POLICY" not in migration[policy_start:policy_end]

    room_link_policy = migration[
        migration.index("CREATE POLICY learnia_room_notebooks_admin_insert") : migration.index(
            "DROP POLICY IF EXISTS learnia_room_notebooks_admin_delete"
        )
    ]
    assert "current_user_can_manage_notebook(notebook_id)" in room_link_policy
    assert "sm.user_id = (SELECT auth.uid())" in room_link_policy

    user_insert_start = migration.index("DROP POLICY IF EXISTS learnia_users_self_insert")
    user_insert_end = migration.index(
        "DROP POLICY IF EXISTS learnia_users_self_update",
        user_insert_start,
    )
    assert "CREATE POLICY" not in migration[user_insert_start:user_insert_end]

    user_update_grant = migration[
        migration.index("GRANT UPDATE (", migration.index("public.users")) : migration.index(
            ") ON TABLE public.users TO authenticated;",
            migration.index("GRANT UPDATE (", migration.index("public.users")),
        )
    ]
    assert "email" not in user_update_grant
    assert "streak" not in user_update_grant
    assert "status" not in user_update_grant

    assert "REVOKE ALL PRIVILEGES ON TABLE" in migration
    assert "GRANT SELECT ON TABLE public.attempts TO authenticated" in migration

    flashcard_update = migration[
        migration.index("CREATE POLICY learnia_flashcards_manager_update") : migration.index(
            "DROP POLICY IF EXISTS learnia_flashcards_manager_delete"
        )
    ]
    assert "current_user_can_manage_question(question_id)" in flashcard_update


def test_rls_migration_keeps_pipeline_writes_service_only() -> None:
    migration = (Path(__file__).parents[1] / "supabase" / "migrations" / "20260713000500_security_rls.sql").read_text(
        encoding="utf-8"
    )

    policy_pairs = (
        (
            "learnia_document_chunks_manager_insert",
            "learnia_conversations_member_select",
        ),
        (
            "learnia_conversations_member_insert",
            "learnia_messages_member_select",
        ),
        ("learnia_messages_member_insert", "learnia_storage_documents_select"),
        ("learnia_storage_documents_insert", "learnia_storage_documents_update"),
        ("learnia_storage_documents_update", "learnia_storage_documents_delete"),
        ("learnia_storage_documents_delete", "learnia_storage_profile_select"),
    )
    for dropped_policy, next_policy in policy_pairs:
        section = migration[
            migration.index(f"DROP POLICY IF EXISTS {dropped_policy}") : migration.index(
                f"DROP POLICY IF EXISTS {next_policy}"
            )
        ]
        assert "CREATE POLICY" not in section

    assert "LIMIT LEAST(GREATEST(COALESCE(match_count, 6), 1), 50)" in migration
    assert "REVOKE ALL ON FUNCTION public.match_document_chunks(VECTOR, UUID, INT)" in migration


def _authenticated_grant(migration: str, table: str) -> str:
    revoke = migration.index(f"REVOKE SELECT ON TABLE public.{table}")
    grant_end = migration.index("TO authenticated;", revoke)
    return migration[revoke:grant_end]
