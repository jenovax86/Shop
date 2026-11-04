from datetime import timedelta
from decimal import Decimal

from rest_framework import serializers

from coupons.models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ["id", "user", "code", "percentage", "duration", "duration_days", "expires_at", "is_active", "used_at",
                  "created_at", ]
        read_only_fields = [
            "id",
            "used_at",
            "created_at",
            "expires_at",
            "code",
            "is_active",
            "duration"
        ]

    duration_days = serializers.IntegerField(write_only=True, min_value=1)
    duration = serializers.DurationField(read_only=True)

    def create(self, value):
        days = value.pop("duration_days")
        value["duration"] = timedelta(days=days)
        return super(CouponSerializer, self).create(value)

    def validate_percentage(self, value):
        if not Decimal("0") < value <= Decimal("100"):
            raise serializers.ValidationError(
                "Percentage must be between 0 and 100."
            )

        return value
