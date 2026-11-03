from django.db import models
from django.db.models.functions import Now

from categories.models import Category


class Product(models.Model):
    class Meta:
        db_table = "products"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    class Sizes(models.TextChoices):
        SMALL = "small", "Small"
        MEDIUM = "medium", "Medium"
        LARGE = "large", "Large"
        X_LARGE = "XL", "XL"
        XX_LARGE = "XXL", "XXL"
        XXX_LARGE = "XXXL", "XXXL"
        XXXX_LARGE = "XXXXL", "XXXXL"

    class Colors(models.TextChoices):
        RED = "red", "Red"
        GREEN = "green", "Green"
        BLUE = "blue", "Blue"
        YELLOW = "yellow", "Yellow"
        WHITE = "white", "White"
        BLACK = "black", "Black"
        GRAY = "gray", "Gray"
        BROWN = "brown", "Brown"
        PURPLE = "purple", "Purple"
        ORANGE = "orange", "Orange"
        PINK = "pink", "Pink"
        BEIGE = "beige", "Beige"
        NAVY = "navy", "Navy"
        OLIVE = "olive", "Olive"

    id = models.AutoField(primary_key=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    size = models.CharField(max_length=15, choices=Sizes.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=15, choices=Colors.choices)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(null=True, blank=True)
