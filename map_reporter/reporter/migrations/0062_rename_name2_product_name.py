# Generated by Django 4.1 on 2022-08-18 13:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0061_rename_name_product_name2'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='name2',
            new_name='name',
        ),
    ]
