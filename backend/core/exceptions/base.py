from rest_framework import status


class AbstractException(Exception):
    status_code = 500
    error_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message):
        self.message = message

        super().__init__(self.message)


class NotFoundException(AbstractException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"

