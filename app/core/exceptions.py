class ApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class ResourceNotFoundError(ApiError):
    def __init__(self) -> None:
        super().__init__(404, "Recurso no encontrado.")


class UnknownResourceError(ApiError):
    def __init__(self) -> None:
        super().__init__(404, "El recurso solicitado no existe.")


class EmptyPayloadError(ApiError):
    def __init__(self) -> None:
        super().__init__(400, "Debe enviar al menos un campo para actualizar.")


class BadRequestError(ApiError):
    def __init__(self, message: str = "Solicitud invalida.") -> None:
        super().__init__(400, message)


class ForbiddenError(ApiError):
    def __init__(self) -> None:
        super().__init__(403, "No tienes permisos para acceder a este recurso.")


class RepositoryError(ApiError):
    def __init__(self, action: str) -> None:
        super().__init__(500, f"No se pudo {action} el registro.")
