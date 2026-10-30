from django.urls import path, include

urlpatterns = [
    path("api/v1/auth/", include("sessions.urls")),
    path("api/v1/auth/", include("auth.urls")),
    path("api/v1/", include('users.urls')),
    path("api/v1/", include("addresses.urls")),
    path("api/v1/", include('categories.urls')),
    path("api/v1/", include('products.urls')),
    path("api/v1/", include("orders.urls")),
    path("api/v1/", include("carts.urls")),
    path("api/v1/", include("products.urls")),

]
