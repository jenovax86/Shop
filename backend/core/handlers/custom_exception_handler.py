import logging

from django.db import IntegrityError
from rest_framework.exceptions import APIException
from rest_framework.views import set_rollback
from rest_framework_json_api.exceptions import Conflict, exception_handler

from core.exceptions import AbstractException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    if isinstance(exc, AbstractException):
        converted = APIException(detail=exc.message, code=exc.error_code)
        converted.status_code = exc.status_code
        exc = converted
    elif isinstance(exc, IntegrityError):
        exc = Conflict("Request conflicts with the current resource state.")

    response = exception_handler(exc, context)
    if response is not None:
        return response

    logger.error("Unhandled API exception", exc_info=(type(exc), exc, exc.__traceback__))
    set_rollback()
    return exception_handler(APIException("Internal server error."), context)
