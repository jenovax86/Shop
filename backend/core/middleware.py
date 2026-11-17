from http import HTTPStatus

from django.http import JsonResponse
from django.urls import is_valid_path
from rest_framework.exceptions import NotFound


class JSONAPIErrorsMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path_info.startswith("/api/") and response.status_code >= 400 and \
                response.get("Content-Type", "").split(";", 1)[0] != "application/vnd.api+json":
            status = response.status_code
            try:
                http_status = HTTPStatus(status)
                detail = http_status.phrase + "."
                code = http_status.name.lower()
            except ValueError:
                detail = "Request failed."
                code = "error"
            if status == 404:
                detail = str(NotFound.default_detail)
                code = NotFound.default_code
            replacement = JsonResponse(
                {"errors": [{"status": str(status), "detail": detail, "code": code}]},
                status=status, content_type="application/vnd.api+json",
            )
            for name in ("WWW-Authenticate", "Retry-After", "Allow"):
                if name in response:
                    replacement[name] = response[name]
            return replacement
        return response


class OptionalTrailingSlashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        urlconf = getattr(request, "urlconf", None)

        if path != "/" and not is_valid_path(path, urlconf):
            alternate = path[:-1] if path.endswith("/") else path + "/"

            if is_valid_path(alternate, urlconf):
                request.path_info = alternate
                request.META["PATH_INFO"] = alternate

        return self.get_response(request)
