from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_extensions.bulk_operations.mixins import ListUpdateModelMixin, ListDestroyModelMixin
from rest_framework import viewsets
from rest_framework.pagination import CursorPagination

from products.filters import ProductFilter
from products.models import Product
from products.serializers import ProductSerializer


class ProductCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    ordering = '-id'


class ProductViewSet(ListUpdateModelMixin, ListDestroyModelMixin, viewsets.ModelViewSet):
    queryset = Product.objects.filter(deleted_at__isnull=True)
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    pagination_class = ProductCursorPagination

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])
