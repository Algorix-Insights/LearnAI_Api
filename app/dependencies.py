from app.core.config import get_settings
from app.services.health import HealthService


class DependencyService:
    @staticmethod
    def get_health_service() -> HealthService:
        settings = get_settings()
        return HealthService(
            app_name=settings.app_name,
            environment=settings.environment,
        )
