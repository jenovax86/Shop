from rest_framework_json_api import serializers

from products.models import Product, ProductMedia


class ProductSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")
    included_serializers = {"category": "categories.serializers.CategorySerializer"}

    class Meta:
        model = Product
        fields = ["id", "url", "gender", "category", "name", "size", "price", "color", "discounted_price", ]

    def validate(self, attrs):
        price = attrs.get("price", getattr(self.instance, "price", None))
        discounted_price = attrs.get("discounted_price", getattr(self.instance, "discounted_price", None))

        if price is None:
            return attrs

        if discounted_price is None:
            return attrs

        if discounted_price > price:
            raise serializers.ValidationError({
                "discount_price": "Discount price cannot exceed the original price."
            })
        return attrs


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
