from django.utils import timezone
from rest_framework_json_api.django_filters import DjangoFilterBackend
from rest_framework import viewsets
from core.mixins import DeleteResponseMixin
from core.pagination import JSONAPIPagination
from rest_framework_json_api.filters import QueryParameterValidationFilter, OrderingFilter, IncludedResourcesFilter

from products.filters import ProductFilter
from products.models import Product
from products.serializers import ProductSerializer
from users.permissions import IsAdminOrReadOnly


class ProductPagination(JSONAPIPagination):
    page_size = 10
    ordering = '-id'


class ProductViewSet(DeleteResponseMixin, viewsets.ModelViewSet):
    """Reads are public. Creating, updating and deleting products requires an administrator."""
    queryset = Product.objects.filter(deleted_at__isnull=True).select_related("category").order_by("-id")
    serializer_class = ProductSerializer
    filter_backends = [QueryParameterValidationFilter, OrderingFilter, IncludedResourcesFilter, DjangoFilterBackend]
    filterset_class = ProductFilter
    pagination_class = ProductPagination
    permission_classes = [IsAdminOrReadOnly]

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])
