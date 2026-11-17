from rest_framework_json_api import serializers

from addresses.models import Address
from coupons.models import Coupon
from orders.models import Order, OrderProduct
from users.models import User
from users.permissions import is_admin


class OrderProductSerializer(serializers.ModelSerializer):
    included_serializers = {"product": "products.serializers.ProductSerializer"}

    class Meta:
        model = OrderProduct
        fields = ["id", "order", "product", "quantity", "price", "size", "color"]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="order-detail")
    included_serializers = {"items": "orders.serializers.OrderProductSerializer"}
    items = serializers.ResourceRelatedField(source="orderproduct_set", many=True, read_only=True, model=OrderProduct)
    coupon = serializers.ResourceRelatedField(
        queryset=Coupon.objects.all(), required=False, allow_null=True,
    )
    address = serializers.ResourceRelatedField(queryset=Address.objects.filter(deleted_at__isnull=True))

    class Meta:
        model = Order
        fields = ["id", "url", "price", "discounted_price", "state", "user", "coupon", "address", "items", "deleted_at"]
        read_only_fields = ["id", "url", "price", "discounted_price", "user", "state", "items", "deleted_at"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and not is_admin(request.user):
            fields["address"].queryset = fields["address"].queryset.filter(user=request.user)
            fields["coupon"].queryset = fields["coupon"].queryset.filter(user=request.user)
            if self.instance is not None:
                fields["coupon"].read_only = True
        return fields


class AdminOrderSerializer(OrderSerializer):
    user = serializers.ResourceRelatedField(queryset=User.objects.all(), required=False)

    class Meta(OrderSerializer.Meta):
        read_only_fields = ["id", "items"]
