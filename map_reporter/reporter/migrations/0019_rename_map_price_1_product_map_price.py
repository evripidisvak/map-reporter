# Generated by Django 4.0.4 on 2022-06-08 10:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0018_remove_product_map_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='map_price_1',
            new_name='map_price',
        ),
    ]
