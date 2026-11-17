from rest_framework.renderers import JSONRenderer as DRFJSONRenderer
from rest_framework_json_api.renderers import JSONRenderer


class JSONAPIRenderer(JSONRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
        context = renderer_context or {}
        response = context.get("response")
        view = context.get("view")
        request = context.get("request")
        if response is not None and response.status_code >= 400:
            return super().render(data, accepted_media_type, context)
        if response is not None and response.status_code in (204, 205, 304):
            return b""
        if request is not None and request.method == "OPTIONS":
            return DRFJSONRenderer.render(self, {"meta": data}, accepted_media_type, context)
        if view is not None and view.__class__.__name__ == "APIRootView":
            return DRFJSONRenderer.render(self, {"data": None, "links": data}, accepted_media_type, context)
        if isinstance(data, dict) and not hasattr(data, "serializer") and set(data) <= {"data", "meta", "links",
                                                                                        "jsonapi", "included"}:
            return DRFJSONRenderer.render(self, data, accepted_media_type, context)
        return super().render(data, accepted_media_type, context)
