from enum import unique
import re
from django.db import models
from decimal import Decimal
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def get_recursive_product_count(self):
        return Product.objects.filter(main_category__in=self.get_descendants(include_self=True)).count()



class Product(models.Model):
    # TODO add manufacturer
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

    def get_active(self):
        return self.active


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
    products = models.ManyToManyField(
        Product,
        through='RetailPrice',
        )
    # TODO Add Seller user

    def __str__(self):
        return self.name

    def is_key_account(self):
        if self.key_account == True:
            return 'Ναι'
        else:
            return 'Όχι'


class Page(models.Model):
    url = models.URLField(max_length=9999)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, default=None)
    # shop = models.ForeignKey(Shop, on_delete=models.CASCADE, default=None)
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, default=None, blank=False, null=False)

    def __str__(self):
        return self.url

class MapPrice(models.Model):
    price = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(
        '0.00'), null=False, blank=False)
    timestamp = models.DateTimeField()
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=False, null=False, default=None)

    def __str__(self):
        return str(self.price)


class RetailPrice(models.Model):
    price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(
        '0.00'), null=False, blank=False)
    timestamp = models.DateTimeField()
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, default=None)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, default=None)
    official_reseller = models.BooleanField(default=False)
    curr_target_price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(
        '0.00'), null=False, blank=False)

    def get_shop_products(shop_id):
        retailprices = RetailPrice.objects.filter(shop=shop_id)
        productList = []

        for price in retailprices:
            if not price.product in productList:
                productList.append(price.product)
        return productList


class KeyAccPrice(models.Model):
    price = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(
        '0.00'), null=False, blank=False)
    timestamp = models.DateTimeField()
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=False, null=False, default=None)

    def __str__(self):
        return self.price
