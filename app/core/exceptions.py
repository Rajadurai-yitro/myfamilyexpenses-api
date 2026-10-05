from typing import Any, Optional


class AppException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class EntityNotFoundException(AppException):
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' not found",
            code=f"{entity_name.upper()}_NOT_FOUND",
            status_code=404,
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Invalid credentials or session expired"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access forbidden to requested resource"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
        )


class ConflictException(AppException):
    def __init__(self, message: str, code: str = "RESOURCE_CONFLICT"):
        super().__init__(
            message=message,
            code=code,
            status_code=409,
        )


class ValidationException(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )
