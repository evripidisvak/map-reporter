# Generated by Django 4.0.4 on 2022-06-16 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0032_alter_category_options_shop_phone_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='address',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
    ]
