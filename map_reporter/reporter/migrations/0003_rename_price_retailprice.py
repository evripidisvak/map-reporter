# Generated by Django 4.0.4 on 2022-06-01 13:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0002_shop_alter_category_options_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Price',
            new_name='RetailPrice',
        ),
    ]
