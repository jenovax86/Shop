from rest_framework import status

from core.exceptions import AbstractException


class SessionNotFound(AbstractException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "Not found"


class SessionRevoked(AbstractException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "Session revoked"


class AccountNotFound(AbstractException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "Account not found"


class SessionExpired(AbstractException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "Session expired"
