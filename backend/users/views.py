from django.http import Http404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from users.exceptions import UserNotFound
from users.serializers import UserSerializer
from users.models import User


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(deleted_at__isnull=True)
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        try:
            return super(UserViewSet, self).get_object()
        except Http404:
            raise UserNotFound("User not found exception.")

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])
