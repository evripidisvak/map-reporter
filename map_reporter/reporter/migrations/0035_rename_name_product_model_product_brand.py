# Generated by Django 4.0.4 on 2022-06-16 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0034_rename_product_name_product_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='name',
            new_name='model',
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
    ]