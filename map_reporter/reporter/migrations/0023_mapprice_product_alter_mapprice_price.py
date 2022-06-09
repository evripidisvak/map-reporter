# Generated by Django 4.0.4 on 2022-06-08 12:04

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0022_remove_product_map_price_1'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapprice',
            name='product',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='reporter.product'),
        ),
        migrations.AlterField(
            model_name='mapprice',
            name='price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5),
        ),
    ]