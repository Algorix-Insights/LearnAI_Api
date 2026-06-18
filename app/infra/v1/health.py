from fastapi import APIRouter, Depends

from app.dependencies import DependencyService
from app.interfaces.health import HealthDTO
from app.services.health import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthDTO)
def health_check(
    health_service: HealthService = Depends(DependencyService.get_health_service),
) -> HealthDTO:
    return health_service.get_status()
