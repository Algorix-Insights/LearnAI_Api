from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies import bearer_scheme, get_current_user
from app.api.v1.health import router as health_router
from app.api.v1.resources import PROTECTED_RESOURCE_ROUTERS, PUBLIC_RESOURCE_ROUTERS
from app.core.exceptions import UnauthorizedError


def require_bearer_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    if not credentials or not credentials.credentials:
        raise UnauthorizedError(
            "No autorizado. Se requiere header Authorization: Bearer <token>."
        )
    return credentials.credentials

api_router = APIRouter()
api_router.include_router(health_router)
for resource_router in PUBLIC_RESOURCE_ROUTERS:
    api_router.include_router(resource_router)
for resource_router in PROTECTED_RESOURCE_ROUTERS:
    api_router.include_router(
        resource_router,
        dependencies=[Depends(require_bearer_token), Depends(get_current_user)],
    )
