from itertools import product
from urllib import response
from django.test import TestCase, SimpleTestCase, Client
from django.contrib.auth.models import AnonymousUser
from .urls import *
from django.urls import reverse
from django.contrib.auth.models import User
from model_bakery import baker

# import reverse


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
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("index"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestAllProductsView(TestCase, SimpleTestCase):
    def test_all_prods_view(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("all_products"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestShopsPageView(TestCase, SimpleTestCase):
    def test_shops_page_view(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("shops_page"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


# TODO create shop
class TestShopInfoView(TestCase, SimpleTestCase):
    def test_shops_page_view(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("shop_info"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


# TODO create categories
class TestCategoriesPageView(TestCase, SimpleTestCase):
    def test_shops_page_view(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("categories_page"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


# TODO create a dummy caregory
class TestCategoryInfoView(TestCase, SimpleTestCase):
    def test_shops_page_view(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("category_info"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestManufacturersPageView(TestCase, SimpleTestCase):
    def test_shops_page_view(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("manufacturer_page"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestManufacturerInfoView(TestCase, SimpleTestCase):
    def test_shops_page_view(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("manufacturer_info"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestShopProductInfoView(TestCase, SimpleTestCase):
    def test_shops_page_view(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("shop_product_info"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


class TestProductInfoView(TestCase, SimpleTestCase):
    def test_shops_page_view(self):
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        client = Client()
        client.login(username="testuser", password="12345")
        response = client.get(reverse("product_info"))
        # print(response.content)
        self.assertTrue(response.status_code, 200)
        # self.assertTrue(response.context[0]["data_exists"])


# def populate_db():
#     product = baker.make("reporter.Product", _quantity=5, _fill_optional=True)
