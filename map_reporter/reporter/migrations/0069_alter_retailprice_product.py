# Generated by Django 4.1 on 2022-09-21 08:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("reporter", "0068_alter_mapprice_price_alter_mapprice_product"),
    ]

    operations = [
        migrations.AlterField(
            model_name="retailprice",
            name="product",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="reporter.product",
            ),
        ),
    ]
