# Generated by Django 4.0.4 on 2022-06-08 10:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0017_product_map_price_1'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='map_price',
        ),
    ]
