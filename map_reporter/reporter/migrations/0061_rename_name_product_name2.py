# Generated by Django 4.1 on 2022-08-18 13:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0060_alter_product_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='name',
            new_name='name2',
        ),
    ]
