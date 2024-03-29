# Generated by Django 4.1 on 2022-09-21 08:58

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("reporter", "0071_alter_retailprice_source"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mapprice",
            name="price",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0.00"), max_digits=5
            ),
        ),
        migrations.AlterField(
            model_name="mapprice",
            name="product",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="reporter.product",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="product",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="reporter.product",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="source",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="reporter.source",
            ),
        ),
        migrations.AlterField(
            model_name="retailprice",
            name="product",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="reporter.product",
            ),
        ),
        migrations.AlterField(
            model_name="retailprice",
            name="shop",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="reporter.shop",
            ),
        ),
        migrations.AlterField(
            model_name="retailprice",
            name="source",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="reporter.source",
            ),
        ),
    ]
