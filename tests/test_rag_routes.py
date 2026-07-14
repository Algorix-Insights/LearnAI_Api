from uuid import UUID

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user, get_rag_use_case
from app.api.v1.resources.rag import router
from app.domain.schemas.resources.rag import ExamGenerationResponse
from app.domain.schemas.resources.users import UserRead


NOTEBOOK_ID = UUID("00000000-0000-0000-0000-000000000010")
USER_ID = UUID("00000000-0000-0000-0000-000000000020")
EXAM_ID = UUID("00000000-0000-0000-0000-000000000030")


def test_every_rag_route_requires_current_user() -> None:
    routes = [route for route in router.routes if isinstance(route, APIRoute)]

    assert routes
    assert all(
        get_current_user in {dependency.call for dependency in route.dependant.dependencies}
        for route in routes
    )
    assert all("profile-photo" not in route.path for route in routes)


class FakeExamGenerationUseCase:
    def __init__(self) -> None:
        self.calls = []

    async def generate_exam(self, *, notebook_id, user_id, request):
        self.calls.append(
            {
                "notebook_id": notebook_id,
                "user_id": user_id,
                "request": request,
            }
        )
        return ExamGenerationResponse.model_validate(
            {
                "data": {
                    "exam_id": EXAM_ID,
                    "notebook_id": notebook_id,
                    "name": "Examen persistido",
                    "description": None,
                    "status": "active",
                    "questions": [
                        {
                            "question_id": "00000000-0000-0000-0000-000000000040",
                            "type": "true_false",
                            "statement": "La fotosíntesis usa luz.",
                            "question_order": 1,
                            "options": [
                                {
                                    "option_id": "00000000-0000-0000-0000-000000000050",
                                    "option_text": "Verdadero",
                                    "option_order": 1,
                                },
                                {
                                    "option_id": "00000000-0000-0000-0000-000000000051",
                                    "option_text": "Falso",
                                    "option_order": 2,
                                },
                            ],
                        }
                    ],
                },
                "sources": [],
            }
        )


def test_generate_exam_endpoint_returns_persisted_database_ids() -> None:
    use_case = FakeExamGenerationUseCase()
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: UserRead(user_id=USER_ID)
    app.dependency_overrides[get_rag_use_case] = lambda: use_case

    with TestClient(app, headers={"Authorization": "Bearer test-token"}) as client:
        response = client.post(
            f"/api/v1/notebooks/{NOTEBOOK_ID}/exams/generate",
            json={
                "true_false_count": 1,
                "multiple_choice_count": 0,
                "open_count": 0,
            },
        )

    assert response.status_code == 201
    assert response.json()["data"]["exam_id"] == str(EXAM_ID)
    assert response.json()["data"]["questions"][0]["question_id"]
    assert len(response.json()["data"]["questions"][0]["options"]) == 2
    assert use_case.calls[0]["notebook_id"] == NOTEBOOK_ID
    assert use_case.calls[0]["user_id"] == USER_ID
