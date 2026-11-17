from django.utils import timezone
from rest_framework import viewsets
from core.mixins import DeleteResponseMixin

from users.models import User
from users.permissions import IsAdminOrSelf, is_admin
from users.serializers import AdminUserSerializer, UserSerializer


class UserViewSet(DeleteResponseMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAdminOrSelf]

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if is_admin(self.request.user):
            return queryset
        return queryset.filter(pk=self.request.user.pk, deleted_at__isnull=True)

    def get_serializer_class(self):
        if getattr(self, "swagger_fake_view", False) or is_admin(self.request.user):
            return AdminUserSerializer
        return UserSerializer

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.is_active = False
        instance.save(update_fields=["deleted_at", "is_active"])
