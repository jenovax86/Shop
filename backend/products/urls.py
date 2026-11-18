from rest_framework.routers import DefaultRouter

from products.views import ProductViewSet, ProductMediaViewSet

router = DefaultRouter()
router.register('products', ProductViewSet)
router.register("product-media", ProductMediaViewSet, basename="product-media")

urlpatterns = router.urls
