import django_tables2 as tables
from reporter.models import *
# from .models import Person

class ProductTable(tables.Table):
    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap.html"
        fields = ("model", )