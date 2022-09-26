from itertools import product
from urllib import response
from django.test import TestCase, SimpleTestCase, Client
from django.contrib.auth.models import AnonymousUser
from dashboard.urls import *
from django.urls import reverse
from django.contrib.auth.models import User
from model_bakery import baker
from reporter.models import *
from mptt.models import MPTTModel, TreeForeignKey

# import reverse


def login_dummy_user():
    client = Client()
    user = User.objects.create(username="testuser")
    user.set_password("12345")
    user.save()
    client.login(username="testuser", password="12345")
    return client


class TestLoginView(TestCase, SimpleTestCase):
    def setup(self):
        pass

    def test_login_redirect(self):
        login_redirect_path = reverse("login") + "?next=" + reverse("index")
        client = Client()
        response = client.get("/")
        self.assertURLEqual(response.url, login_redirect_path)
        self.assertRedirects(response, login_redirect_path)

    def test_login_success_and_fail(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        logged_out = client.login(username="WRONGuser", password="WRONGpasswd")
        logged_in = client.login(username="testuser", password="12345")
        self.assertFalse(logged_out)
        self.assertTrue(logged_in)


class TestIndexView(TestCase, SimpleTestCase):
    def test_index_has_data(self):
        client = login_dummy_user()
        response = client.get(reverse("index"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestAllProductsView(TestCase, SimpleTestCase):
    def test_all_prods_view(self):
        client = login_dummy_user()
        response = client.get(reverse("all_products"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestShopsPageView(TestCase, SimpleTestCase):
    def test_shops_page_view(self):
        client = login_dummy_user()
        response = client.get(reverse("shops_page"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


# TODO create shop
class TestShopInfoView(TestCase, SimpleTestCase):
    def test_shop_info_view(self):
        client = login_dummy_user()
        shop = baker.make("reporter.Shop")
        response = client.get(reverse("shop_info", kwargs={"pk": shop.id}))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


# TODO create categories
class TestCategoriesPageView(TestCase, SimpleTestCase):
    def test_categories_page_view(self):
        client = login_dummy_user()
        response = client.get(reverse("categories_page"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


# TODO create a dummy caregory
class TestCategoryInfoView(TestCase, SimpleTestCase):
    def test_category_info_view(self):
        client = login_dummy_user()
        category = baker.make("reporter.Category")
        response = client.get(reverse("category_info", kwargs={"pk": category.id}))
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestManufacturersPageView(TestCase, SimpleTestCase):
    def test_manufacturers_page_view(self):
        client = login_dummy_user()
        response = client.get(reverse("manufacturer_page"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestManufacturerInfoView(TestCase, SimpleTestCase):
    def test_manufacturer_info_view(self):
        client = login_dummy_user()
        manufacturer = baker.make("reporter.Manufacturer")
        response = client.get(
            reverse("manufacturer_info", kwargs={"pk": manufacturer.id})
        )
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestShopProductInfoView(TestCase, SimpleTestCase):
    def test_shop_product_info_view(self):
        client = login_dummy_user()
        product = baker.make("reporter.Product")
        shop = baker.make("reporter.Shop")
        response = client.get(
            reverse(
                "shop_product_info",
                kwargs={"pk_shop": shop.id, "pk_product": product.id},
            )
        )
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestProductInfoView(TestCase, SimpleTestCase):
    def test_product_info_view(self):
        client = login_dummy_user()
        product = baker.make("reporter.Product")
        response = client.get(reverse("product_info", kwargs={"pk": product.id}))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


def populate_db():
    product = baker.make("reporter.Product", _quantity=5, _fill_optional=True)
    category = baker.make("reporter.Category")
    manufacturer = baker.make("reporter.Manufacturer")
    source = baker.make("reporter.Source")
    shop = baker.make("reporter.Shop", key_account=True)
    shop = baker.make("reporter.Shop", key_account=False)
    page = baker.make("reporter.Page", product=product, source=source)
    map_price = baker.make("reporter.MapPrice", product=product)
    retail_price_off_reseller = baker.make(
        "reporter.RetailPrice",
        product=product,
        shop=shop,
        source=source,
        official_reseller=True,
    )
    retail_price = baker.make(
        "reporter.RetailPrice",
        product=product,
        shop=shop,
        source=source,
        official_reseller=False,
    )
