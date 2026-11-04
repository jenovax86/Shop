from datetime import timedelta

from django.db import models
from django.db.models.functions import Now
from django.utils import timezone

from coupons.utils import generate_discount_code
from users.models import User


class Coupon(models.Model):
    class Meta:
        db_table = 'coupons'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=40, unique=True, default=generate_discount_code)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    expires_at = models.DateTimeField(editable=False)
    is_active = models.BooleanField(default=True)
    duration = models.DurationField(default=timedelta(days=3))
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(db_default=Now())

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.expires_at = timezone.now() + self.duration
        super(Coupon, self).save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_valid(self):
        return self.is_active and not self.is_expired and self.used_at is None
