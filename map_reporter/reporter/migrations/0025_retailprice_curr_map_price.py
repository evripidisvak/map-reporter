# Generated by Django 4.0.4 on 2022-06-10 09:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0024_keyaccprice'),
    ]

    operations = [
        migrations.AddField(
            model_name='retailprice',
            name='curr_map_price',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='reporter.mapprice'),
        ),
    ]
