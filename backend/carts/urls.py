from rest_framework.routers import DefaultRouter

from carts.views import CartsViewSet

router = DefaultRouter()
router.register('carts', CartsViewSet, basename='carts' )

urlpatterns = router.urls
