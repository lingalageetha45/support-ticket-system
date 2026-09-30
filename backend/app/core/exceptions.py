from fastapi import HTTPException, status


class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(code=code, message=message, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", code: str = "UNAUTHORIZED"):
        super().__init__(code=code, message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", code: str = "FORBIDDEN"):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", code: str = "CONFLICT"):
        super().__init__(code=code, message=message, status_code=status.HTTP_409_CONFLICT)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", code: str = "VALIDATION_ERROR"):
        super().__init__(code=code, message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class InvalidStatusTransition(AppException):
    def __init__(self, message: str = "Invalid status transition"):
        super().__init__(code="INVALID_STATUS_TRANSITION", message=message, status_code=status.HTTP_400_BAD_REQUEST)
