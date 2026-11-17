from rest_framework_json_api import serializers

from products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")
    included_serializers = {"category": "categories.serializers.CategorySerializer"}

    class Meta:
        model = Product
        fields = ["id", "url", "gender", "category", "name", "size", "price", "color"]

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
