# Generated by Django 4.1 on 2022-09-19 10:03

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reporter", "0064_page_valid"),
    ]

    operations = [
        migrations.AddField(
            model_name="retailprice",
            name="original_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=6,
                null=True,
            ),
        ),
    ]
