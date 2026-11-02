from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context['response'].status_code
        success = status_code < 400

        if status_code in (204, 205, 304):
            return b""

        response = {
            "success": success,
            "data": data if success else None,
            "errors": None if success else data,
            "status_code": status_code,
        }
        return super(CustomJSONRenderer, self).render(response, accepted_media_type, renderer_context)
