from rest_framework.routers import DefaultRouter

from sessions.views import SessionViewSet

router = DefaultRouter()
router.register('sessions', SessionViewSet, basename='sessions')

urlpatterns = router.urls
