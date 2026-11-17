from django.db import models
from django.db.models.functions import Now

from users.models import User


class Address(models.Model):
    class Meta:
        db_table = "addresses"

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    country = models.CharField(max_length=20)
    zip_code = models.CharField(max_length=20)
    city = models.CharField(max_length=10)
    province = models.CharField(max_length=20)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(null=True, blank=True)
