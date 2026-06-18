from pydantic import BaseModel, ConfigDict


class HealthDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    service: str
    environment: str
