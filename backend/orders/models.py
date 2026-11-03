from django.db import models
from django.db.models.functions import Now

from addresses.models import Address
from products.models import Product
from users.models import User


class Order(models.Model):
    class Meta:
        db_table = "order"

    class State(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    state = models.CharField(max_length=10, choices=State.choices)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(null=True, blank=True)


class OrderProduct(models.Model):
    class Meta:
        db_table = "orders_products"

    pk = models.CompositePrimaryKey('order_id', 'product_id')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(
        max_length=15,
        choices=Product.Sizes.choices
    )
    color = models.CharField(
        max_length=15,
        choices=Product.Colors.choices
    )
