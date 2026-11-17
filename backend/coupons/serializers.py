from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework_json_api import serializers

from coupons.models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="coupon-detail")

    class Meta:
        model = Coupon
        fields = ["id", "url", "user", "code", "percentage", "duration", "duration_days", "expires_at", "is_active",
                  "used_at",
                  "created_at", ]
        read_only_fields = [
            "id",
            "created_at",
            "expires_at",
            "code",
            "duration"
        ]

    duration_days = serializers.IntegerField(write_only=True, min_value=1, required=False)
    duration = serializers.DurationField(read_only=True)

    def create(self, value):
        days = value.pop("duration_days", 3)
        value["duration"] = timedelta(days=days)
        return super(CouponSerializer, self).create(value)

    def update(self, instance, validated_data):
        days = validated_data.pop("duration_days", None)
        if days is not None:
            validated_data["duration"] = timedelta(days=days)
            validated_data["expires_at"] = timezone.now() + timedelta(days=days)
        return super().update(instance, validated_data)

    def validate_percentage(self, value):
        if not Decimal("0") < value <= Decimal("100"):
            raise serializers.ValidationError(
                "Percentage must be between 0 and 100."
            )

        return value
