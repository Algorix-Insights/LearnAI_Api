from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.resources import RESOURCE_ROUTERS

api_router = APIRouter()
api_router.include_router(health_router)
for resource_router in RESOURCE_ROUTERS:
    api_router.include_router(resource_router)
