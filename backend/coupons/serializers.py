from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework_json_api import serializers

from coupons.models import Coupon
from users.models import User


class CouponSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="coupon-detail")

    class Meta:
        model = Coupon
        fields = ["id", "url", "user", "code", "percentage", "duration_days", "expires_at", ]
        read_only_fields = [
            "id",
            "expires_at",
            "code",
        ]

    user = serializers.ResourceRelatedField(
        queryset=User.objects.all()
    )
    duration_days = serializers.IntegerField(write_only=True, min_value=1, required=False)

    def create(self, validated_data):
        days = validated_data.pop("duration_days")
        validated_data["expires_at"] = (
                timezone.now() + timedelta(days=days)
        )
        return super(CouponSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        days = validated_data.pop("duration_days", None)
        if days is not None:
            validated_data["expires_at"] = (
                    timezone.now() + timedelta(days=days)
            )
        return super().update(instance, validated_data)
