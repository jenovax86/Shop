from decimal import Decimal


def calculate_discounted_price(price: Decimal, percentage: Decimal) -> Decimal:
    percentage = Decimal(str(percentage))
    discounted_price = price * (Decimal("1") - percentage / Decimal("100"))
    return discounted_price


