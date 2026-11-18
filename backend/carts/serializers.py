from rest_framework_json_api import serializers

from carts.models import Carts, CartItems
from products.models import Product
from users.mixins import OwnerFieldsMixin
from users.models import User


class CartsSerializer(OwnerFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Carts
        fields = ["id", "url", "user", ]
        read_only_fields = ["id", "user", ]
        extra_kwargs = {"size": {"required": False}, "color": {"required": False}}

    url = serializers.HyperlinkedIdentityField(view_name="carts-detail")
    user = serializers.ResourceRelatedField(queryset=User.objects.all(), required=False)


class CartItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItems
        fields = ["id", "cart", "url", "product", "quantity", "size", "color", "deleted_at"]
        read_only_fields = ["id", "deleted_at"]

    url = serializers.HyperlinkedIdentityField(view_name="cart-items-detail")
    cart = serializers.ResourceRelatedField(queryset=Carts.objects.none())
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)
    product = serializers.ResourceRelatedField(queryset=Product.objects.filter(deleted_at__isnull=True))
    included_serializers = {"product": "products.serializers.ProductSerializer"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            self.fields["cart"].queryset = Carts.objects.filter(
                user=request.user
            )

    def validate(self, attrs):
        errors = {}
        product = attrs.get("product", getattr(self.instance, "product", None))
        color = attrs.get("color", getattr(self.instance, "color", None))
        size = attrs.get("size", getattr(self.instance, "size", None))

        if product is None:
            return attrs

        if color is not None and product.color != color:
            errors["color"] = "This product is not available in this color."

        if size is not None and size != product.size:
            errors["size"] = "This product is not available in this size."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs
