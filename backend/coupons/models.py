from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.functions import Now

from coupons.utils import generate_discount_code
from users.models import User


class Coupon(models.Model):
    class Meta:
        db_table = 'coupons'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=40, unique=True, default=generate_discount_code)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(db_default=Now())
