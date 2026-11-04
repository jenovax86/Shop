from rest_framework import serializers

from addresses.models import Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["country", "user_id", "zip_code", 'city', 'province',]
        read_only_fields= ['user_id',]


