from django.utils.http import parse_header_parameters
from rest_framework.exceptions import NotAcceptable, UnsupportedMediaType
from rest_framework.negotiation import DefaultContentNegotiation


class JSONAPIContentNegotiation(DefaultContentNegotiation):
    @staticmethod
    def supported_media_type(value, accept=False):
        media_type, params = parse_header_parameters(value)
        if media_type != "application/vnd.api+json":
            return True
        allowed = {"profile", "q"} if accept else {"profile"}
        return not (params.keys() - allowed)

    def select_parser(self, request, parsers):
        if not self.supported_media_type(request.content_type):
            raise UnsupportedMediaType(request.content_type)
        return super().select_parser(request, parsers)

    def get_accept_list(self, request):
        media_types = [value for value in super().get_accept_list(request) if
                       self.supported_media_type(value, accept=True)]
        if not media_types:
            raise NotAcceptable()
        return media_types
