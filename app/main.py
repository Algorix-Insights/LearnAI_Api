from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import ApiError
from app.core.middlewares import ApiQueryMiddleware
from fastapi.middleware.cors import CORSMiddleware


async def api_error_handler(_: object, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def request_validation_error_handler(
    _: object, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": "La solicitud no es valida.",
            "errors": [
                {"field": ".".join(str(part) for part in error["loc"]), "type": error["type"]}
                for error in exc.errors()
            ],
        },
    )


async def validation_error_handler(_: object, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": "La solicitud no es valida.",
            "errors": [
                {"field": ".".join(str(part) for part in error["loc"]), "type": error["type"]}
                for error in exc.errors()
            ],
        },
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
    )
    
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    
    app.add_middleware(ApiQueryMiddleware, api_prefix=app_settings.api_v1_prefix)
    
    app.include_router(health_router)
    app.include_router(api_router, prefix=app_settings.api_v1_prefix)

    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


app = create_app()
