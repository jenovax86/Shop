from django.utils import timezone

from core.mixins import DeleteResponseMixin
from users.permissions import is_admin


class OwnerQuerysetMixin(DeleteResponseMixin):
    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if is_admin(self.request.user):
            return queryset
        queryset = queryset.filter(user=self.request.user)
        if hasattr(queryset.model, "deleted_at"):
            queryset = queryset.filter(deleted_at__isnull=True)
        return queryset

    def perform_create(self, serializer):
        user = serializer.validated_data.get("user", self.request.user)
        if not is_admin(self.request.user):
            user = self.request.user
        serializer.save(user=user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])


class OwnerFieldsMixin:
    owner_field = "user"

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        schema_view = self.context.get("view")
        if not getattr(schema_view, "swagger_fake_view", False) and (not request or not is_admin(request.user)):
            fields[self.owner_field].read_only = True
            if "deleted_at" in fields:
                fields["deleted_at"].read_only = True
        return fields
