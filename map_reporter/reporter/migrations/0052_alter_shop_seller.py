# Generated by Django 4.0.5 on 2022-07-04 11:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reporter', '0051_alter_shop_seller'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shop',
            name='seller',
            field=models.ForeignKey(blank=True, default=None, limit_choices_to={'groups__name__in': ['Sales_Dep', 'Seller']}, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
