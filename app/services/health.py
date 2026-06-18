from app.interfaces.health import HealthDTO


class HealthService:
    def __init__(self, app_name: str, environment: str) -> None:
        self.app_name = app_name
        self.environment = environment

    def get_status(self) -> HealthDTO:
        return HealthDTO(
            status="ok",
            service=self.app_name,
            environment=self.environment,
        )
