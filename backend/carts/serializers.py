from rest_framework import serializers

from carts.models import Carts


class CartsSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = Carts
        fields = ["user", "product", "quantity", ]
        read_only_fields = ["user", ]

