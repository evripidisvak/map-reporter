# Generated by Django 4.0.4 on 2022-06-16 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0039_product_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(default='placeholder_img.png', upload_to='product_images'),
        ),
    ]