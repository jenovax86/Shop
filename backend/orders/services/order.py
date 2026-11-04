from django.utils import timezone
from rest_framework.exceptions import ValidationError

from carts.models import Carts
from carts.services.cart import calculate_cart_price
from coupons.models import Coupon
from orders.models import Order, OrderProduct
from orders.services.price import calculate_discounted_price


def create_order(user, serializer):
    cart_items = list(
        Carts.objects.filter(
            user=user,
            deleted_at__isnull=True,
        ).select_related("product")
    )
    price = calculate_cart_price(user)
    coupon = serializer.validated_data.get('coupon')

    if coupon is not None:
        coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)
        if coupon.user.id != user.id or not coupon.is_valid:
            raise ValidationError("Invalid coupon or coupon is used. ")

        discounted_price = calculate_discounted_price(price, coupon.percentage)

        order = serializer.save(user=user, price=price, discounted_price=discounted_price,
                                coupon=serializer.validated_data.get("coupon"),
                                state=Order.State.PENDING, )
        OrderProduct.objects.bulk_create([
            OrderProduct(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                size=item.product.size,
                color=item.product.color,
            )
            for item in cart_items
        ])
        coupon.used_at = timezone.now()
        coupon.save(update_fields=["used_at"])
