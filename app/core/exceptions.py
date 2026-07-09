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


class RepositoryError(ApiError):
    def __init__(self, action: str) -> None:
        super().__init__(500, f"No se pudo {action} el registro.")


class UnauthorizedError(ApiError):
    def __init__(self, message: str = "No autorizado. Token inválido o ausente.") -> None:
        super().__init__(401, message)


class InvalidCredentialsError(ApiError):
    def __init__(self, message: str = "Credenciales incorrectas.") -> None:
        super().__init__(401, message)


class AuthError(ApiError):
    def __init__(self, message: str = "Error en autenticación de Supabase.") -> None:
        super().__init__(400, message)

