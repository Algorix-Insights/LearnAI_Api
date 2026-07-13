from fastapi.routing import APIRoute

from app.api.dependencies import get_current_user
from app.api.v1.resources.rag import router


def test_every_rag_route_requires_current_user() -> None:
    routes = [route for route in router.routes if isinstance(route, APIRoute)]

    assert routes
    assert all(
        get_current_user in {dependency.call for dependency in route.dependant.dependencies}
        for route in routes
    )
    assert all("profile-photo" not in route.path for route in routes)
