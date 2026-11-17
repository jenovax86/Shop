from rest_framework_json_api import serializers

from carts.models import Carts
from products.models import Product
from users.mixins import OwnerFieldsMixin
from users.models import User


class CartsSerializer(OwnerFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="carts-detail")
    included_serializers = {"product": "products.serializers.ProductSerializer"}

    quantity = serializers.IntegerField(min_value=1)
    user = serializers.ResourceRelatedField(queryset=User.objects.all(), required=False)
    product = serializers.ResourceRelatedField(queryset=Product.objects.filter(deleted_at__isnull=True))

    class Meta:
        model = Carts
        fields = ["id", "url", "user", "product", "quantity", "size", "color", "deleted_at"]
        read_only_fields = ["id"]
        extra_kwargs = {"size": {"required": False}, "color": {"required": False}}
