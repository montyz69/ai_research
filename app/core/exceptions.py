from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class AuthenticationError(BaseAPIException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(BaseAPIException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class ResourceNotFoundError(BaseAPIException):
    def __init__(self, resource: str, identifier: str = None):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} with identifier '{identifier}' not found"
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ResourceAlreadyExistsError(BaseAPIException):
    def __init__(self, resource: str, identifier: str = None):
        detail = f"{resource} already exists"
        if identifier:
            detail = f"{resource} with identifier '{identifier}' already exists"
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class ValidationError(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class DatabaseError(BaseAPIException):
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExternalServiceError(BaseAPIException):
    def __init__(self, service: str, detail: str = None):
        message = f"{service} service error"
        if detail:
            message = f"{service} service error: {detail}"
        super().__init__(detail=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class StorageError(BaseAPIException):
    def __init__(self, detail: str = "Storage operation failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvalidTokenError(AuthenticationError):
    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(detail=detail)


class InvalidCredentialsError(AuthenticationError):
    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(detail=detail)