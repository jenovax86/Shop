from django.db import models
from django.db.models.functions import Now

from users.models import User


class Session(models.Model):
    class Meta:
        db_table = 'sessions'

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(db_default=Now())
    revoked_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    user_agent = models.CharField(max_length=255)
