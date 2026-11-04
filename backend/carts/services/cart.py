from decimal import Decimal

from carts.models import Carts


def calculate_cart_price(user):
    total_price = Decimal("0.00")
    cart_items = Carts.objects.filter(user=user).select_related('product')
    for cart_item in cart_items:
        total_price += cart_item.product.price * cart_item.quantity
    return total_price
