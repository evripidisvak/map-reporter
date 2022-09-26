from django.test import TestCase

from reporter.models import *
from model_bakery import baker
from mptt.models import MPTTModel, TreeForeignKey


class CategoryTestModel(TestCase):
    """
    Class to test the model Category
    """

    def set_up(self):
        category = baker.make("reporter.Category")
        return category

    def test_category_model_name(self):
        category = self.set_up()
        self.assertTrue(isinstance(category, Category))
        self.assertEqual(str(category), category.name)


class ManufacturerTestModel(TestCase):
    """
    Class to test the model Manufacturer
    """

    def set_up(self):
        manufacturer = baker.make("reporter.Manufacturer")
        return manufacturer

    def test_manufacturer_model_name(self):
        manufacturer = self.set_up()
        self.assertTrue(isinstance(manufacturer, Manufacturer))
        self.assertEqual(str(manufacturer), manufacturer.name)


class ProductTestModel(TestCase):
    """
    Class to test the model Product
    """

    def set_up(self, type):
        if type == "normal":
            product = baker.make("reporter.Product")
            return product
        elif type == "active":
            product = baker.make("reporter.Product", active=True)
            return product
        elif type == "inactive":
            product = baker.make("reporter.Product", active=False)
            return product

    def test_product_model_name(self):
        product = self.set_up("normal")
        self.assertTrue(isinstance(product, Product))
        self.assertEqual(str(product), product.model)
        self.assertEqual(product.name(), product.model)

    def test_is_active(self):
        product = self.set_up("active")
        self.assertEqual(product.is_active(), "Ναι")
        product = self.set_up("inactive")
        self.assertEqual(product.is_active(), "Όχι")


class SourceTestModel(TestCase):
    """
    Class to test the model Source
    """

    def set_up(self):
        source = baker.make("reporter.Source")
        return source

    def test_source_model_name(self):
        source = self.set_up()
        self.assertTrue(isinstance(source, Source))
        self.assertEqual(str(source), source.name)


class ShopTestModel(TestCase):
    """
    Class to test the model Shop
    """

    def set_up(self, type):
        if type == "normal":
            shop = baker.make("reporter.Shop")
            return shop
        if type == "key":
            shop = baker.make("reporter.Shop", key_account=True)
            return shop
        if type == "non_key":
            shop = baker.make("reporter.Shop", key_account=False)
            return shop

    def test_shop_model_name(self):
        shop = self.set_up("normal")
        self.assertTrue(isinstance(shop, Shop))
        self.assertEqual(str(shop), shop.name)

    def test_is_key_account(self):
        shop = self.set_up("key")
        self.assertEqual(shop.is_key_account(), "Ναι")
        shop = self.set_up("non_key")
        self.assertEqual(shop.is_key_account(), "Όχι")


class PageTestModel(TestCase):
    """
    Class to test the model Page
    """

    def set_up(self):
        product = baker.make("reporter.Product")
        source = baker.make("reporter.Source")
        page = baker.make("reporter.Page", product=product, source=source)
        return page

    def test_page_model_url(self):
        page = self.set_up()
        self.assertTrue(isinstance(page, Page))
        self.assertEqual(str(page), page.url)


class MapPriceTestModel(TestCase):
    """
    Class to test the model MapPrice
    """

    def set_up(self):
        product = baker.make("reporter.Product")
        map_price = baker.make("reporter.MapPrice", product=product)
        return map_price

    def test_map_price_model_price(self):
        map_price = self.set_up()
        self.assertTrue(isinstance(map_price, MapPrice))
        self.assertEqual(str(map_price), str(map_price.price))


class RetailPriceTestModel(TestCase):
    """
    Class to test the model RetailPrice
    """

    def set_up(self, type):
        product = baker.make("reporter.Product")
        shop = baker.make("reporter.Shop")
        source = baker.make("reporter.Source")
        if type == "normal":
            retail_price = baker.make(
                "reporter.RetailPrice", product=product, shop=shop, source=source
            )
            return retail_price
        elif type == "official_reseller":
            retail_price = baker.make(
                "reporter.RetailPrice",
                product=product,
                shop=shop,
                source=source,
                official_reseller=True,
            )
            return retail_price
        elif type == "non_official_reseller":
            retail_price = baker.make(
                "reporter.RetailPrice",
                product=product,
                shop=shop,
                source=source,
                official_reseller=False,
            )
            return retail_price

    def test_retail_price_model_price(self):
        retail_price = self.set_up("normal")
        self.assertTrue(isinstance(retail_price, RetailPrice))
        self.assertEqual(str(retail_price), str(retail_price.price))

    def test_is_shop_official_reseller(self):
        retail_price = self.set_up("official_reseller")
        self.assertEqual(retail_price.is_shop_official_reseller(), "Ναι")
        retail_price = self.set_up("non_official_reseller")
        self.assertEqual(retail_price.is_shop_official_reseller(), "Όχι")

    # def test_get_shop_products(self):
    #     quantity = 5
    #     products = baker.make("reporter.Product", _quantity=quantity)
    #     shop = baker.make("reporter.Shop", _quantity=quantity)
    #     source = baker.make("reporter.Source", _quantity=quantity)
    #     for product in products:
    #         retail_price = baker.make(
    #                 "reporter.RetailPrice",
    #                 product=product,
    #                 shop=shop,
    #                 source=source,
    #             )
