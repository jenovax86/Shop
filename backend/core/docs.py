from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView
from rest_framework.negotiation import DefaultContentNegotiation


class OpenAPISchemaView(SpectacularJSONAPIView):
    content_negotiation_class = DefaultContentNegotiation


class SwaggerUIView(SpectacularSwaggerView):
    content_negotiation_class = DefaultContentNegotiation
