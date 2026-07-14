class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.headers = headers or {}
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


class UnauthorizedError(ApiError):
    def __init__(self, message: str = "No autorizado. Token inválido o ausente.") -> None:
        super().__init__(401, message)


class InvalidCredentialsError(ApiError):
    def __init__(self, message: str = "Credenciales incorrectas.") -> None:
        super().__init__(401, message)


class AuthError(ApiError):
    def __init__(self, message: str = "Error en autenticación de Supabase.") -> None:
        super().__init__(400, message)


class AuthRateLimitError(ApiError):
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            429,
            "Demasiadas solicitudes de autenticación. Intenta de nuevo más tarde.",
            headers={"Retry-After": str(max(1, retry_after))},
        )


class AuthUnavailableError(ApiError):
    def __init__(self) -> None:
        super().__init__(503, "Servicio de autenticación no disponible temporalmente.", ApiError)


class AiServiceUnavailableError(ApiError):
    def __init__(
        self,
        message: str = "Servicio de IA no disponible temporalmente.",
    ) -> None:
        super().__init__(503, message, ApiError)
