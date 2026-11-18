from rest_framework.routers import DefaultRouter

from carts.views import CartsViewSet, CartItemsViewSet

router = DefaultRouter()
router.register('carts', CartsViewSet, basename='carts')
router.register('cart-items', CartItemsViewSet, basename='cart-items')

urlpatterns = router.urls
