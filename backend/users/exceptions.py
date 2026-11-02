from core.exceptions import AbstractException
from rest_framework import status


class UserNotFound(AbstractException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "Not found"


