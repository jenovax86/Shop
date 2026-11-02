from rest_framework import status

from core.exceptions import AbstractException


class TokenExpired(AbstractException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "Token expired"

class InvalidToken(AbstractException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "Token invalid"

class AuthenticationFailed(AbstractException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "Authentication failed"

