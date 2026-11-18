from rest_framework_json_api import serializers

from products.models import Product, ProductMedia


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


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ["id", "product", "image", ]

    class JSONAPIMeta:
        resource_name = "product-media"

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    def validate_product(self, product):
        if ProductMedia.objects.filter(product=product).count() >= 10:
            raise serializers.ValidationError(
                "A product cannot have more than 10 images."
            )

        return product
