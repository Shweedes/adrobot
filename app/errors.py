"""Доменные ошибки; в HTTP-ответы их превращает `app.api.error_handlers`."""


class AppError(Exception):
    """Базовая ошибка приложения: HTTP-статус и код для клиента."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationFailed(AppError):
    """Входные данные не прошли проверку."""

    status_code = 422
    code = "validation_error"


class NotFoundError(AppError):
    """Объект не найден."""

    status_code = 404
    code = "not_found"


class ForbiddenError(AppError):
    """Действие запрещено правилами приложения."""

    status_code = 403
    code = "forbidden"


class ConflictError(AppError):
    """Состояние объекта не позволяет выполнить действие."""

    status_code = 409
    code = "conflict"


class UpstreamError(AppError):
    """Keitaro недоступен или вернул ошибку."""

    status_code = 502
    code = "keitaro_error"


class ConfigurationError(AppError):
    """Настройки приложения не соответствуют данным в Keitaro."""

    status_code = 500
    code = "configuration_error"
