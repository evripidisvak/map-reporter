# Generated by Django 4.0.4 on 2022-06-16 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0035_rename_name_product_model_product_brand'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='brand',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
    ]
