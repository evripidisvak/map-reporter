from django.db import models
from decimal import Decimal
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self', models.SET_NULL, blank=True, null=True, related_query_name='children')

    def get_categories(self):
        if self.parent is None:
            return self.name
        else:
            return self.parent.get_categories() + ' > ' + self.name

    def __str__(self):
        return self.get_categories()

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class Product(models.Model):
    product_name = models.CharField(max_length=100)
    sku = models.CharField(max_length=20)
    active = models.BooleanField(default=True)
    map_price = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'), null=False, blank=False)
    key_acc_price = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'), null=False, blank=False)
    main_category = models.ForeignKey(
        Category, models.SET_NULL, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_map_price = self.map_price
        self.__original_key_acc_price = self.key_acc_price

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        old_map_price = self.__original_map_price
        new_map_price = self.map_price

        old_key_acc_price = self.__original_key_acc_price
        new_key_acc_price = self.key_acc_price
        super().save(force_insert, force_update, *args, **kwargs)

        if new_map_price != old_map_price:
            MapPrice.objects.create(
                price=new_map_price, timestamp=timezone.now(), product=self)

        if new_key_acc_price != old_key_acc_price:
            KeyAccPrice.objects.create(
                price=new_key_acc_price, timestamp=timezone.now(), product=self)

    def __str__(self):
        return self.product_name


class Source(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Shop(models.Model):
    name = models.CharField(max_length=100)
    key_account = models.BooleanField(default=False)
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, default=None, blank=False, null=False)
        # TODO Add Seller user

    def __str__(self):
        return self.name


class Page(models.Model):
    url = models.URLField(max_length=9999)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, default=None)
    # shop = models.ForeignKey(Shop, on_delete=models.CASCADE, default=None)
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, default=None, blank=False, null=False)

    def __str__(self):
        return self.url


class RetailPrice(models.Model):
    price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(
        '0.00'), null=False, blank=False)
    timestamp = models.DateTimeField()
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, default=None)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, default=None)
    official_reseller = models.BooleanField(default=False)


class MapPrice(models.Model):
    price = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(
        '0.00'), null=False, blank=False)
    timestamp = models.DateTimeField()
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=False, null=False, default=None)

    def __str__(self):
        return self.price


class KeyAccPrice(models.Model):
    price = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(
        '0.00'), null=False, blank=False)
    timestamp = models.DateTimeField()
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=False, null=False, default=None)

    def __str__(self):
        return self.price
