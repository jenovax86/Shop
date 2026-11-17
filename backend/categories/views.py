from django.utils import timezone
from rest_framework import viewsets
from core.mixins import DeleteResponseMixin

from categories.models import Category
from categories.serializers import CategorySerializer
from users.permissions import IsAdminOrReadOnly


class CategoryViewSet(DeleteResponseMixin, viewsets.ModelViewSet):
    queryset = Category.objects.filter(deleted_at__isnull=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])
