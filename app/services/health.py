from dataclasses import dataclass

from app.interfaces.health import HealthDTO


@dataclass(frozen=True)
class HealthService:
    app_name: str
    environment: str

    def get_status(self) -> HealthDTO:
        return HealthDTO(
            status="ok",
            service=self.app_name,
            environment=self.environment,
        )
