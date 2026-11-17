from decimal import Decimal

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from carts.models import Carts
from coupons.models import Coupon
from orders.models import Order, OrderProduct
from orders.services.price import calculate_discounted_price


def create_order(user, serializer):
    cart_items = list(Carts.objects.filter(user=user, deleted_at__isnull=True).select_related("product"))
    if not cart_items:
        raise ValidationError("Your cart is empty.")
    price = sum((item.product.price * item.quantity for item in cart_items), Decimal("0.00"))
    coupon = serializer.validated_data.get("coupon")
    discounted_price = price
    if coupon is not None:
        coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)
        if coupon.user_id != user.pk or not coupon.is_valid:
            raise ValidationError("Invalid coupon or coupon is used.")
        discounted_price = calculate_discounted_price(price, coupon.percentage)

    order = serializer.save(
        user=user, price=price, discounted_price=discounted_price,
        coupon=coupon, state=Order.State.PENDING,
    )
    OrderProduct.objects.bulk_create([
        OrderProduct(
            order=order, product=item.product, quantity=item.quantity,
            price=item.product.price, size=item.size or item.product.size,
            color=item.color or item.product.color,
        )
        for item in cart_items
    ])
    if coupon is not None:
        coupon.used_at = timezone.now()
        coupon.save(update_fields=["used_at"])
