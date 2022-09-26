from distutils.command.clean import clean
from enum import unique
import re
from typing import List
from django.db import models
from decimal import Decimal
from django.forms import ValidationError
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe
import os, urllib, sys
from urllib.parse import urlparse
from urllib.request import urlretrieve
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import User, Group
from . import wc_api


class Category(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


def get_default_category():
    # Return a category to use as a default value
    return Category.objects.get_or_create(name="No Category")[0].id


class Manufacturer(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


def get_default_manufacturer():
    # Return a manufaturer to use as a default value
    return Manufacturer.objects.get_or_create(name="No Manufacturer")[0].id


class Product(models.Model):
    manufacturer = models.ForeignKey(
        Manufacturer,
        models.SET_DEFAULT,
        blank=False,
        null=False,
        default=get_default_manufacturer,
    )
    model = models.CharField(max_length=100)
    sku = models.CharField(max_length=20)
    active = models.BooleanField(default=True)
    map_price = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), null=False, blank=False
    )
    main_category = models.ForeignKey(
        Category,
        models.SET_DEFAULT,
        blank=False,
        null=False,
        default=get_default_category,
    )
    upload_path = "product_images"
    image = models.ImageField(
        upload_to="product_images", default="product_images/placeholder_img.png"
    )
    image_url = models.URLField(null=True, blank=True)
    # name = models.CharField(blank=True, max_length=200)

    is_cleaned = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_map_price = self.map_price
        # self.name = self.manufacturer.name + " " + self.model
        # self.__original_key_acc_price = self.key_acc_price

    def clean(self):
        new_map_price = self.map_price
        wc_api.update_woocommerce(self, new_map_price)
        super(Product, self).clean()

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if not self.is_cleaned:
            self.full_clean()

        # Create new MapPrice objects when these prices change
        old_map_price = self.__original_map_price
        new_map_price = self.map_price
        super().save(force_insert, force_update, *args, **kwargs)

        # TODO What happens if the product does not exist?
        if new_map_price != old_map_price:
            MapPrice.objects.create(
                price=new_map_price, timestamp=timezone.now(), product=self
            )

        # Save the image from the image_url field
        if self.image_url:
            upload_path = "uploads/product_images"
            filename = urlparse(self.image_url).path.split("/")[-1]
            urllib.request.urlretrieve(
                self.image_url, os.path.join(upload_path, filename)
            )
            file_save_dir = "product_images"
            self.image = os.path.join(file_save_dir, filename)
            self.image_url = ""

        # Optimize uploaded image
        if self.image:
            output = BytesIO()
            img = Image.open(self.image)
            output = BytesIO()
            if img.mode != "RGB":
                img = img.convert("RGB")
            if img.width > 800 or img.height > 800:
                img.resize((800, 800))
            img.save(output, format="jpeg", quality=80)
            output.seek(0)
            self.image = InMemoryUploadedFile(
                output,
                "ImageField",
                "%s.jpg" % self.image.name.split(".")[0],
                "image/jpeg",
                sys.getsizeof(output),
                None,
            )

        super(Product, self).save()

    def is_active(self):
        if self.active:
            return "Ναι"
        else:
            return "Όχι"

    def name(self):
        return str(self.model)
        # return str(self.manufacturer.name + " " + self.model)

    def __str__(self):
        # return str(self.manufacturer.name + " " + self.model)
        return self.model

    @property
    def image_preview(self):
        if self.image:
            return mark_safe(
                '<img src="{}" width="200" height="200" />'.format(self.image.url)
            )
        return ""


class Source(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Shop(models.Model):
    name = models.CharField(max_length=100)
    key_account = models.BooleanField(default=False)
    seller = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        default=None,
        blank=True,
        null=True,
        limit_choices_to={"groups__name__in": ["Sales_Dep", "Seller"]},
    )
    # source = models.ForeignKey(
    #     Source, on_delete=models.CASCADE, default=None, blank=False, null=False
    # )
    products = models.ManyToManyField(
        Product,
        through="RetailPrice",
    )
    phone_regex = RegexValidator(
        regex=r"\d{9,10}$",
        message="Επιτρέπονται μόνο αριθμοί (0-9). Μέχρι 10 χαρακτήρες. π.χ. 2310123456",
    )
    # phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], blank=True, max_length=10)
    address = models.CharField(max_length=100, default=None, blank=True, null=True)
    website = models.CharField(blank=True, max_length=100)

    def __str__(self):
        return self.name

    def is_key_account(self):
        if self.key_account == True:
            return "Ναι"
        else:
            return "Όχι"


class Page(models.Model):
    url = models.URLField(max_length=9999)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, default=None)
    # shop = models.ForeignKey(Shop, on_delete=models.CASCADE, default=None)
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, default=None, blank=False, null=False
    )
    valid = models.BooleanField(default=True)

    def __str__(self):
        return self.url


class MapPrice(models.Model):
    price = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), null=False, blank=False
    )
    timestamp = models.DateTimeField()
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=False, null=False, default=None
    )

    def __str__(self):
        return str(self.price)


class RetailPrice(models.Model):
    price = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0.00"), null=False, blank=False
    )
    original_price = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0.00"), null=True, blank=True
    )
    timestamp = models.DateTimeField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, default=None)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, default=None)
    official_reseller = models.BooleanField(default=False)
    curr_target_price = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0.00"), null=False, blank=False
    )
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, default=None, blank=False, null=False
    )

    def __str__(self):
        return str(self.price)

    def get_shop_products(shop_id):
        retailprices = RetailPrice.objects.filter(shop=shop_id)
        productList = []

        for price in retailprices:
            if not price.product in productList:
                productList.append(price.product)
        return productList

    def get_valid_product_shops(product_id, user=None):
        if user:
            retailprices = RetailPrice.objects.filter(
                product=product_id, shop__seller=user
            )
        else:
            retailprices = RetailPrice.objects.filter(product=product_id)
        shopList = []

        for price in retailprices:
            if not price.shop in shopList:
                shopList.append(price.shop)
        return shopList

    def is_shop_official_reseller(self):
        if self.official_reseller == True:
            return "Ναι"
        else:
            return "Όχι"
