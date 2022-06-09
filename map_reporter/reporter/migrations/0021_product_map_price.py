# Generated by Django 4.0.4 on 2022-06-08 11:48

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0020_rename_map_price_product_map_price_1'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='map_price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5),
        ),
    ]