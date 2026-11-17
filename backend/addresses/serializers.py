from rest_framework_json_api import serializers

from addresses.models import Address
from users.mixins import OwnerFieldsMixin
from users.models import User


class AddressSerializer(OwnerFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="address-detail")
    user = serializers.ResourceRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Address
        fields = ["id", "url", "country", "user", "zip_code", "city", "province", "deleted_at"]
        read_only_fields = ["id"]
