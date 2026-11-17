from django.urls import path, include
from core.docs import OpenAPISchemaView, SwaggerUIView

urlpatterns = [
    path("api/schema/", OpenAPISchemaView.as_view(), name="openapi-schema"),
    path("api/docs/", SwaggerUIView.as_view(url_name="openapi-schema"), name="swagger-ui"),
    path("api/v1/auth/", include("sessions.urls")),
    path("api/v1/auth/", include("auth.urls")),
    path("api/v1/", include('users.urls')),
    path("api/v1/", include("addresses.urls")),
    path("api/v1/", include('categories.urls')),
    path("api/v1/", include('products.urls')),
    path("api/v1/", include("orders.urls")),
    path("api/v1/", include("carts.urls")),
    path("api/v1/", include("coupons.urls")),

]
