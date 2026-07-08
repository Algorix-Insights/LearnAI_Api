from fastapi.responses import JSONResponse

from app.core.query import (
    QueryParamError,
    parse_api_query_params,
    reset_api_query_params,
    set_api_query_params,
)


class ApiQueryMiddleware:
    def __init__(self, app, api_prefix: str = "/api/v1") -> None:
        self.app = app
        self.api_prefix = api_prefix

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        query_string = scope.get("query_string", b"")
        if (
            scope.get("method") != "GET"
            or not scope.get("path", "").startswith(self.api_prefix)
            or not query_string
        ):
            await self.app(scope, receive, send)
            return

        try:
            params = parse_api_query_params(query_string)
        except QueryParamError as exc:
            response = JSONResponse(
                status_code=422,
                content={
                    "detail": "La solicitud no es valida.",
                    "errors": [{"field": "query", "type": str(exc)}],
                },
            )
            await response(scope, receive, send)
            return

        token = set_api_query_params(params)
        next_scope = dict(scope)
        next_scope.setdefault("state", {})["api_query"] = params
        next_scope["query_string"] = params.normalized_query_string()

        try:
            await self.app(next_scope, receive, send)
        finally:
            reset_api_query_params(token)
