from rest_framework_json_api import serializers

from addresses.models import Address
from carts.models import Carts
from coupons.models import Coupon
from orders.models import Order, OrderProduct
from users.models import User
from users.permissions import is_admin


class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ["id", "order", "product", "quantity", "price", "size", "color"]
        read_only_fields = fields

    included_serializers = {"product": "products.serializers.ProductSerializer"}


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "url", "cart", "price", "discounted_price", "state", "user", "coupon", "address", "items",
                  "deleted_at"]
        read_only_fields = ["id", "url", "price", "discounted_price", "user", "state", "items", "deleted_at"]

    url = serializers.HyperlinkedIdentityField(view_name="order-detail")
    included_serializers = {"items": "orders.serializers.OrderProductSerializer"}
    cart = serializers.ResourceRelatedField(queryset=Carts.objects.none(), required=True, write_only=True)
    items = serializers.ResourceRelatedField(source="order_product_set", many=True, read_only=True, model=OrderProduct)
    coupon = serializers.ResourceRelatedField(
        queryset=Coupon.objects.all(), required=False, allow_null=True,
    )
    address = serializers.ResourceRelatedField(queryset=Address.objects.filter(deleted_at__isnull=True))

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and not is_admin(request.user):
            fields["cart"].queryset = Carts.objects.filter(user=request.user)
            fields["address"].queryset = fields["address"].queryset.filter(user=request.user)
            fields["coupon"].queryset = fields["coupon"].queryset.filter(user=request.user)
            if self.instance is not None:
                fields["coupon"].read_only = True
        return fields


class AdminOrderSerializer(OrderSerializer):
    class Meta(OrderSerializer.Meta):
        read_only_fields = ["id", "items"]

    user = serializers.ResourceRelatedField(queryset=User.objects.all(), required=False)
