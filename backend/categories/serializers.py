from rest_framework_json_api import serializers

from categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="category-detail")

    class Meta:
        model = Category
        fields = ["id", "url", "name"]
