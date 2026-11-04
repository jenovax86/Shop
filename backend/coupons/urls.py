from rest_framework.routers import DefaultRouter

from coupons.views import CouponsViewSet

router = DefaultRouter()
router.register("coupons", CouponsViewSet)

urlpatterns = router.urls