from rest_framework.views import exception_handler
from rest_framework.response import Response

from core.exceptions import AbstractException


def custom_exception_handler(exception, context):
    if isinstance(exception, AbstractException):
        return Response({
            "error_code": exception.error_code,
            "message": exception.message,
        }, status=exception.status_code)

    response = exception_handler(exception, context)

    if response is not None:
        response.data = {
            "success": False,
            "message": response.data,
        }
        return response

    return Response(
        {
            "error_code": 500,
            "message": "Internal server error",
        },
        status=500,
    )
