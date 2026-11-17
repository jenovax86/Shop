import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("male", "Male"),
                            ("female", "Female"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=50),
                ),
                (
                    "size",
                    models.CharField(
                        choices=[
                            ("small", "Small"),
                            ("medium", "Medium"),
                            ("large", "Large"),
                            ("XL", "XL"),
                            ("XXL", "XXL"),
                            ("XXXL", "XXXL"),
                            ("XXXXL", "XXXXL"),
                        ],
                        max_length=15,
                    ),
                ),
                (
                    "price",
                    models.FloatField(),
                ),
                (
                    "color",
                    models.CharField(
                        choices=[
                            ("red", "Red"),
                            ("green", "Green"),
                            ("blue", "Blue"),
                            ("yellow", "Yellow"),
                            ("white", "White"),
                            ("black", "Black"),
                            ("gray", "Gray"),
                            ("brown", "Brown"),
                            ("purple", "Purple"),
                            ("orange", "Orange"),
                            ("pink", "Pink"),
                            ("beige", "Beige"),
                            ("navy", "Navy"),
                            ("olive", "Olive"),
                        ],
                        max_length=15,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                    ),
                ),
            ],
            options={
                "db_table": "products",
            },
        ),
    ]