"""Единый формат ошибок API: `{"error": {"code", "message"}}`."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import AppError

log = logging.getLogger(__name__)

FIELD_LABELS = {"name": "Название", "geo": "Гео", "offer_id": "Оффер"}
"""Подписи полей запроса для сообщений об ошибках."""


def _body(code: str, message: str) -> dict:
    """Тело ответа с ошибкой."""
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    """Подключает обработчики доменных, валидационных и непредвиденных ошибок."""

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            log.error("%s: %s", exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        parts = []
        for err in exc.errors():
            field = str(err["loc"][-1])
            parts.append(f"{FIELD_LABELS.get(field, field)}: {err['msg']}")
        return JSONResponse(status_code=422, content=_body("validation_error", "; ".join(parts)))

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        log.exception("Необработанная ошибка")
        return JSONResponse(
            status_code=500, content=_body("internal_error", "Внутренняя ошибка сервера")
        )
