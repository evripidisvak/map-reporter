# Generated by Django 4.0.4 on 2022-06-06 08:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0012_page_source'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='shop',
        ),
    ]
