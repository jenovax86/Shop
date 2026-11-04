from rest_framework import serializers

from coupons.models import Coupon
from orders.models import Order, OrderProduct


class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ["id", "order_id", "product_id", "quantity", "price", "size", "color"]
        read_only_fields = ["id", "order_id", "product_id", "quantity", "size", "color"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderProductSerializer(many=True, read_only=True)
    coupon = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Coupon.objects.all(),
        required=False,
        allow_null=True,
    )
    class Meta:
        model = Order
        fields = ['price', 'discounted_price', 'state', 'user', "coupon", 'address', 'items',]
        read_only_fields = ['price', 'discounted_price', 'user', 'state', 'items',]
