from app.main import app


def test_sensitive_creation_is_only_exposed_through_owned_workflows() -> None:
    paths = app.openapi()["paths"]

    assert "post" in paths["/api/v1/notebooks"]
    assert "post" in paths["/api/v1/rooms"]
    assert "post" in paths["/api/v1/notebooks/{notebook_id}/flashcards/generate"]
    assert "get" in paths["/api/v1/notebooks/{notebook_id}/flashcards"]
    assert "post" in paths["/api/v1/notebooks/{notebook_id}/exams/generate"]
    assert "post" in paths["/api/v1/tags"]

    for path in (
        "/api/v1/questions",
        "/api/v1/question-options",
        "/api/v1/documents",
        "/api/v1/document-chunks",
        "/api/v1/flashcards",
        "/api/v1/exams",
    ):
        assert "post" not in paths[path]

    assert "/api/v1/users/me/notebooks/{notebook_id}" not in paths
    assert "/api/v1/exams/{exam_id}/questions" not in paths


def test_requested_profile_attempt_and_statistics_routes_are_present() -> None:
    paths = app.openapi()["paths"]

    assert set(paths["/api/v1/users/me/profile-photo"]) >= {
        "get",
        "post",
        "delete",
    }
    assert "get" in paths["/api/v1/users/me/statistics"]
    assert "post" in paths["/api/v1/exams/{exam_id}/attempts"]
    assert "put" in paths[
        "/api/v1/attempts/{attempt_id}/answers/{question_id}"
    ]
    assert "post" in paths["/api/v1/attempts/{attempt_id}/finish"]
