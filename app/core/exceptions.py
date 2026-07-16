from fastapi import status


class AppException(Exception):
    """
    Base application exception.

    Use this for expected application-level errors where we want
    clean API responses instead of raw Python tracebacks.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "APP_ERROR"
    message: str = "An unexpected application error occurred."

    def __init__(
        self,
        message: str | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message or self.message
        self.status_code = status_code or self.status_code
        self.error_code = error_code or self.error_code
        super().__init__(self.message)


class BadRequestException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BAD_REQUEST"
    message = "The request is invalid."


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"
    message = "The requested resource was not found."


class ServiceException(AppException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "SERVICE_ERROR"
    message = "A backend service error occurred."


class ConfigurationException(AppException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "CONFIGURATION_ERROR"
    message = "The application is not configured correctly."


class DatabaseUnavailableException(AppException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "DATABASE_UNAVAILABLE"
    message = "Document metadata is temporarily unavailable."
