import datetime
import json
from base64 import b64encode
from mimetypes import guess_type

import numpy as np
import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import *
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.db.models import *
from django.db.models import F, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from reporter.models import *
from sorl.thumbnail import get_thumbnail
from this import d

from .forms import *

# Pass a custom attribute, time in seconds of last modifications, in case we need to make sure this file gets updated correctly
# import os, sys
# last_mod = os.stat(
#     os.path.join("static/map_reporter/css/custom-styles.css")
# ).st_mtime


def is_seller(user):
    return user.groups.filter(name="Seller").exists()


def is_sales_dep(user):
    return user.groups.filter(name="Sales_Dep").exists()


def datalize(filename, content_type=None):
    """
    This filter will return data URI for given file, for more info go to:
    http://en.wikipedia.org/wiki/Data_URI_scheme
    Sample Usage:
    <img src="{{ 'image.jpg'|datalize }}"/> or
    <img src="{% static 'image.jpg'|datalize %}"/>
    will be filtered into:
    <img src="data:image/png;base64,iVBORw0...">
    """
    if filename:
        # we do this because FUCKIN windows..
        # .replace('/','\\')
        filename = filename.replace("/", "", 1)
        with open(filename, "rb") as f:
            data = f.read()

        encoded = b64encode(data)
        content_type, encoding = guess_type(filename)
        return "data:%s;base64,%s" % (content_type, encoded.decode("utf-8"))
    else:
        return ""


class Index(TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)

        user = self.request.user
        seller_flag = is_seller(user)
        table_image_size = "80x80"

        products = (
            Product.objects.filter(active=True)
            .prefetch_related("manufacturer")
            .prefetch_related("main_category")
        )

        retail_prices = []
        products_below = 0
        this_products_below = 0
        products_equal = 0
        this_products_equal = 0
        products_above = 0
        this_products_above = 0
        shops_below = 0
        shops_ok = 0
        sources = Source.objects.all()

        prefetch = Prefetch("products", queryset=Product.objects.distinct())

        if seller_flag:
            shops = Shop.objects.filter(seller=user).prefetch_related(prefetch)
            retailprices_obj = RetailPrice.objects.filter(
                shop__seller=user,
                source__in=sources,
                product__in=products,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            ).select_related()
        else:
            shops = Shop.objects.all().prefetch_related(prefetch)
            retailprices_obj = RetailPrice.objects.filter(
                source__in=sources,
                product__in=products,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            ).select_related()

        data_exists = False
        if retailprices_obj.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:

            retailpricesdf = pd.DataFrame.from_records(
                retailprices_obj.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                ],
            )

            grouped_retailprices_by_shop = retailpricesdf.loc[
                retailpricesdf.groupby(["shop_id", "product_id"])["timestamp"].idxmax()
            ].reset_index(drop=True)

            conditions = [
                grouped_retailprices_by_shop["price"]
                < grouped_retailprices_by_shop["curr_target_price"],
                grouped_retailprices_by_shop["price"]
                == grouped_retailprices_by_shop["curr_target_price"],
                grouped_retailprices_by_shop["price"]
                > grouped_retailprices_by_shop["curr_target_price"],
            ]
            choices = ["below", "equal", "above"]

            grouped_retailprices_by_shop["comparison"] = np.select(
                conditions, choices, default=np.nan
            )

            for shop in shops:
                this_shop_below = 0
                this_shop_equal = 0
                this_shop_above = 0
                shop_records = grouped_retailprices_by_shop.loc[
                    grouped_retailprices_by_shop["shop_id"] == shop.id
                ].copy()
                if not shop_records.empty:
                    this_shop_below = shop_records["comparison"].tolist().count("below")
                    this_shop_equal = shop_records["comparison"].tolist().count("equal")
                    this_shop_above = shop_records["comparison"].tolist().count("above")

                shop.this_shop_below = this_shop_below
                shop.this_shop_equal = this_shop_equal
                shop.this_shop_above = this_shop_above
                shop.prod_count = this_shop_below + this_shop_equal + this_shop_above

                if shop.this_shop_below >= 1:
                    shops_below += 1
                else:
                    shops_ok += 1

            grouped = retailpricesdf.loc[
                retailpricesdf.groupby(["product_id", "source_id"])[
                    "timestamp"
                ].idxmax()
            ].reset_index(drop=True)
            grouped.sort_values(
                by=["product_id", "price"], inplace=True, ascending=True
            )
            grouped.drop_duplicates(subset=["product_id"], inplace=True)

            conditions = [
                grouped["price"] < grouped["curr_target_price"],
                grouped["price"] == grouped["curr_target_price"],
                grouped["price"] > grouped["curr_target_price"],
            ]
            choices = ["below", "equal", "above"]

            grouped["comparison"] = np.select(conditions, choices, default=np.nan)
            products_below = grouped["comparison"].tolist().count("below")
            products_equal = grouped["comparison"].tolist().count("equal")
            products_above = grouped["comparison"].tolist().count("above")

            filtered_retail_prices = grouped.loc[grouped["comparison"] == "below"]

            latest_timestamp = filtered_retail_prices.sort_values(
                by="timestamp", ascending=False
            )["timestamp"].iloc[0]
            if not latest_timestamp:
                raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")

            retail_prices = (
                retailprices_obj.filter(id__in=filtered_retail_prices["id"])
                .select_related()
                .annotate(
                    product_model=F("product__model"),
                    product_manufacturer_id=F("product__manufacturer"),
                    product_manufacturer=F("product__manufacturer__name"),
                    product_category_id=F("product__main_category"),
                    product_category=F("product__main_category__name"),
                    product_sku=F("product__sku"),
                    source_domain=F("source__domain"),
                )
            )

            for retailprice in retail_prices:
                im = get_thumbnail(retailprice.product.image, table_image_size)
                retailprice.product_image = im.url
            latest_timestamp = latest_timestamp.to_pydatetime()
            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")

            context.update(
                {
                    "retail_prices": retail_prices,
                    "products_below": products_below,
                    "products_equal": products_equal,
                    "products_above": products_above,
                    "shops_below": shops_below,
                    "shops_ok": shops_ok,
                    "table_image_size": table_image_size,
                    "latest_timestamp": latest_timestamp,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        else:
            context.update(
                {
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )

        return context


class AllProducts(TemplateView):
    template_name = "dashboard/all_products.html"

    def get_context_data(self, **kwargs):
        context = super(AllProducts, self).get_context_data(**kwargs)
        date_picker = TimeDatePickerClearable
        user = self.request.user
        seller_flag = is_seller(user)
        table_image_size = "80x80"
        products = (
            Product.objects.all()
            .prefetch_related("manufacturer")
            .prefetch_related("main_category")
        )

        products_below = 0
        products_equal = 0
        products_above = 0
        shops_below = 0

        if seller_flag:
            retailprices_obj = RetailPrice.objects.filter(
                product__in=products,
                shop__seller=user,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            )
        else:
            retailprices_obj = (
                RetailPrice.objects.filter(
                    product__in=products,
                    timestamp__range=(
                        datetime.datetime.now() - datetime.timedelta(days=14),
                        datetime.datetime.now(),
                    ),
                )
                .prefetch_related("shop")
                .annotate(shop_name=F("shop__name"))
            )

        data_exists = False
        if retailprices_obj.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:
            categories = Category.objects.all().order_by("name")

            retailpricesdf = pd.DataFrame.from_records(
                retailprices_obj.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                    "shop_name",
                ],
            )

            grouped_retailprices = retailpricesdf.loc[
                retailpricesdf.groupby(["product_id", "shop_id"])["timestamp"].idxmax()
            ].reset_index(drop=True)

            conditions = [
                grouped_retailprices["price"]
                < grouped_retailprices["curr_target_price"],
                grouped_retailprices["price"]
                == grouped_retailprices["curr_target_price"],
                grouped_retailprices["price"]
                > grouped_retailprices["curr_target_price"],
            ]
            choices = ["below", "equal", "above"]

            grouped_retailprices["comparison"] = np.select(
                conditions, choices, default=np.nan
            )

            products_below = grouped_retailprices["comparison"].tolist().count("below")
            products_equal = grouped_retailprices["comparison"].tolist().count("equal")
            products_above = grouped_retailprices["comparison"].tolist().count("above")

            for product in products:
                shops_below = 0
                shops_equal = 0
                shops_above = 0
                product_records = grouped_retailprices.loc[
                    grouped_retailprices["product_id"] == product.id
                ].copy()
                if not product_records.empty:
                    shops_below = product_records["comparison"].tolist().count("below")
                    shops_equal = product_records["comparison"].tolist().count("equal")
                    shops_above = product_records["comparison"].tolist().count("above")
                product.shops_below = shops_below
                product.shops_equal = shops_equal
                product.shops_above = shops_above
                product.shop_count = shops_below + shops_equal + shops_above

                im = get_thumbnail(product.image, table_image_size)
                product.product_image = im.url

            shops = retailprices_obj.order_by("shop_name").distinct("shop_name")

            latest_timestamp = grouped_retailprices.sort_values(
                by="timestamp", ascending=False
            )["timestamp"].iloc[0]
            if not latest_timestamp:
                raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")

            latest_timestamp = latest_timestamp.to_pydatetime()

            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")

            context.update(
                {
                    "products": products,
                    "products_below": products_below,
                    "products_equal": products_equal,
                    "products_above": products_above,
                    "table_image_size": table_image_size,
                    "latest_timestamp": latest_timestamp,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                    "categories": categories,
                    "shops": shops,
                    "date_picker": date_picker,
                }
            )
        else:
            context.update(
                {
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        return context


def all_products_table_filter(request):
    if request.method == "POST":
        # try:
        table_image_size = "80x80"

        user = request.user
        seller_flag = is_seller(user)

        only_below = request.POST.get("only_below")

        categories = request.POST.get("categories_list").strip()
        categories_request = [data.strip() for data in categories.split(" ")]
        categories_list = Category.objects.filter(
            id__in=categories_request
        ).get_descendants(include_self=True)

        shops = request.POST.get("shops_list").strip()
        shops_request = [data.strip() for data in shops.split(" ")]
        shops_list = Shop.objects.filter(id__in=shops_request)

        date_range = request.POST.get("datetime_range_with_predefined_ranges")

        if date_range:
            date_range_list = [data.strip() for data in date_range.split(" - ")]
            date_from = date_range_list[0]
            date_to = date_range_list[1]
            naive_query_date_from = datetime.datetime.strptime(
                date_from, "%d/%m/%Y, %H:%M"
            )
            naive_query_date_to = datetime.datetime.strptime(date_to, "%d/%m/%Y, %H:%M")

            query_date_from = make_aware(naive_query_date_from).replace(
                second=59, microsecond=999999
            )
            query_date_to = make_aware(naive_query_date_to).replace(
                second=59, microsecond=999999
            )
        else:
            query_date_from = make_aware(
                datetime.datetime.now() - datetime.timedelta(days=14)
            )
            query_date_to = make_aware(datetime.datetime.now())

        retail_prices = (
            RetailPrice.objects.filter(
                shop__in=shops_list,
                product__main_category__in=categories_list,
                product__active=True,
                timestamp__range=(query_date_from, query_date_to),
            )
            .select_related("product")
            .annotate(
                shop_name=F("shop__name"),
                product_category=F("product__main_category__name"),
                product_category_id=F("product__main_category__id"),
                product_manufacturer=F("product__manufacturer__name"),
                product_manufacture_id=F("product__manufacturer__id"),
                product_model=F("product__model"),
                product_sku=F("product__sku"),
                product_image=F("product__image"),
                key_account=F("shop__key_account"),
                seller=F("shop__seller__last_name"),
                source_name=F("source__name"),
            )
        )

        if only_below == "true":
            retail_prices = retail_prices.filter(price__lt=F("curr_target_price"))

        retailpricesdf = pd.DataFrame.from_records(
            retail_prices.values_list(),
            columns=[
                "id",
                "price",
                "original_price",
                "timestamp",
                "product_id",
                "shop_id",
                "official_reseller",
                "curr_target_price",
                "source_id",
                "shop_name",
                "product_category",
                "product_category_id",
                "product_manufacturer",
                "product_manufacturer_id",
                "product_model",
                "product_sku",
                "product_image",
                "key_account",
                "seller",
                "source_name",
            ],
        )

        unique_prod_ids = retailpricesdf["product_id"].unique()
        unique_manufacturer_ids = retailpricesdf["product_manufacturer_id"].unique()
        unique_category_ids = retailpricesdf["product_category_id"].unique()
        unique_shop_ids = retailpricesdf["shop_id"].unique()
        unique_dict_img = {}
        unique_dict_model = {}
        unique_dict_manufacturer = {}
        unique_dict_category = {}
        unique_dict_shop = {}

        for id in unique_prod_ids:
            img = (
                retailpricesdf["product_image"]
                .loc[retailpricesdf["product_id"] == id]
                .values[:1][0]
            )
            thumb = get_thumbnail(img, table_image_size).url
            datalized = datalize(thumb)
            model = (
                retailpricesdf["product_model"]
                .loc[retailpricesdf["product_id"] == id]
                .values[:1][0]
            )
            link = reverse(
                "product_info",
                kwargs={"pk": id},
            )

            unique_dict_img[img] = {
                "image": thumb,
                "product_link": link,
                "model": model,
                "aria_src": datalized,
            }
            unique_dict_model[id] = {
                "name": model,
                "link": link,
            }

        for id in unique_manufacturer_ids:
            name = (
                retailpricesdf["product_manufacturer"]
                .loc[retailpricesdf["product_manufacturer_id"] == id]
                .values[:1][0]
            )
            link = reverse(
                "manufacturer_info",
                kwargs={"pk": id},
            )
            unique_dict_manufacturer[id] = {
                "name": name,
                "link": link,
            }

        for id in unique_category_ids:
            name = (
                retailpricesdf["product_category"]
                .loc[retailpricesdf["product_category_id"] == id]
                .values[:1][0]
            )
            link = reverse(
                "category_info",
                kwargs={"pk": id},
            )
            unique_dict_category[id] = {
                "name": name,
                "link": link,
            }

        for id in unique_shop_ids:
            name = (
                retailpricesdf["shop_name"]
                .loc[retailpricesdf["shop_id"] == id]
                .values[:1][0]
            )
            link = reverse(
                "shop_info",
                kwargs={"pk": id},
            )
            unique_dict_shop[id] = {
                "name": name,
                "link": link,
            }

        retailpricesdf["product_image"] = retailpricesdf["product_image"].map(
            unique_dict_img
        )
        retailpricesdf["model_link"] = retailpricesdf["product_id"].map(
            unique_dict_model
        )
        retailpricesdf["manufacturer_link"] = retailpricesdf[
            "product_manufacturer_id"
        ].map(unique_dict_manufacturer)

        retailpricesdf["category_link"] = retailpricesdf["product_category_id"].map(
            unique_dict_category
        )

        retailpricesdf["shop_link"] = retailpricesdf["shop_id"].map(unique_dict_shop)

        retailpricesdf["official_reseller"] = np.where(
            retailpricesdf["official_reseller"] == True, "Ναι", "Όχι"
        )

        retailpricesdf["key_account"] = np.where(
            retailpricesdf["key_account"] == True, "Ναι", "Όχι"
        )

        if date_range:
            grouped_retailprices = retailpricesdf.groupby(
                ["product_id", "shop_name", "timestamp"]
            ).obj.reset_index(drop=True)
        else:
            grouped_retailprices = retailpricesdf.loc[
                retailpricesdf.groupby(["product_id", "shop_name"])[
                    "timestamp"
                ].idxmax()
            ].reset_index(drop=True)

        conditions = [
            grouped_retailprices["price"] < grouped_retailprices["curr_target_price"],
            grouped_retailprices["price"] == grouped_retailprices["curr_target_price"],
            grouped_retailprices["price"] > grouped_retailprices["curr_target_price"],
        ]
        choices = ["below", "equal", "above"]

        grouped_retailprices["comparison"] = np.select(
            conditions, choices, default=np.nan
        )

        grouped_retailprices["diff"] = (
            grouped_retailprices["price"] - grouped_retailprices["curr_target_price"]
        )

        grouped_retailprices["diff%"] = (
            (grouped_retailprices["price"] - grouped_retailprices["curr_target_price"])
            / grouped_retailprices["price"]
        ).map("{:,.2%}".format)

        rows_below = grouped_retailprices.index[
            grouped_retailprices["comparison"] == "below"
        ].tolist()

        grouped_retailprices["timestamp"] = grouped_retailprices[
            "timestamp"
        ].dt.tz_convert(settings.TIME_ZONE)
        grouped_retailprices["timestamp"] = grouped_retailprices["timestamp"].map(
            "{:%d/%m/%Y, %H:%M}".format
        )

        grouped_retailprices["seller"].fillna("-", inplace=True)

        grouped_retailprices = grouped_retailprices[
            [
                "product_image",
                "model_link",
                "manufacturer_link",
                "category_link",
                "product_sku",
                "shop_link",
                "price",
                "curr_target_price",
                "diff",
                "diff%",
                "source_name",
                "key_account",
                "official_reseller",
                "seller",
                "timestamp",
            ]
        ]

        columns = [
            {"title": "Φωτογραφία"},
            {"title": "Μοντέλο"},
            {"title": "Κατασκευαστής"},
            {"title": "Κατηγορία"},
            {"title": "SKU"},
            {"title": "Κατάστημα"},
            {"title": "Τιμή"},
            {"title": "Τιμή MAP"},
            {"title": "Διαφ."},
            {"title": "Διαφ.%"},
            {"title": "Πηγή"},
            {"title": "Key Account"},
            {"title": "Επ. Μεταπωλ."},
            {"title": "Πωλητής"},
            {"title": "Ημερομηνία"},
        ]

        parsed_df = grouped_retailprices.to_json(orient="values")
        response_data = {}
        response_data["columns"] = columns
        response_data["rows_below"] = rows_below
        response_data["seller_flag"] = seller_flag
        response_data["data_set"] = json.loads(parsed_df)
        return JsonResponse(response_data, safe=False)
    else:
        return HttpResponse("This is not the place you are looking for")


class ShopsPage(TemplateView):
    template_name = "dashboard/shops_page.html"

    def get_context_data(self, **kwargs):
        context = super(ShopsPage, self).get_context_data(**kwargs)
        user = self.request.user
        seller_flag = is_seller(user)
        products = Product.objects.filter(active=True).select_related()

        prefetch = Prefetch("products", queryset=Product.objects.distinct())

        if seller_flag:
            shops = Shop.objects.filter(seller=user).prefetch_related(prefetch)
        else:
            shops = Shop.objects.all().prefetch_related(prefetch)

        this_shop_below = 0
        this_shop_equal = 0
        this_shop_above = 0

        shops_below = 0
        shops_ok = 0

        retailprices = RetailPrice.objects.filter(
            shop__in=shops,
            product__in=products,
            timestamp__range=(
                datetime.datetime.now() - datetime.timedelta(days=14),
                datetime.datetime.now(),
            ),
        ).select_related()

        data_exists = False
        if retailprices.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:

            retailpricesdf = pd.DataFrame.from_records(
                retailprices.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                ],
            )

            groupedretailprices = retailpricesdf.loc[
                retailpricesdf.groupby(["shop_id", "product_id"])["timestamp"].idxmax()
            ].reset_index(drop=True)

            for shop in shops:
                this_shop_below = 0
                this_shop_equal = 0
                this_shop_above = 0
                shop_records = groupedretailprices.loc[
                    groupedretailprices["shop_id"] == shop.id
                ].copy()
                if not shop_records.empty:
                    conditions = [
                        shop_records["price"] < shop_records["curr_target_price"],
                        shop_records["price"] == shop_records["curr_target_price"],
                        shop_records["price"] > shop_records["curr_target_price"],
                    ]
                    choices = ["below", "equal", "above"]

                    shop_records["comparison"] = np.select(
                        conditions, choices, default=np.nan
                    )

                    this_shop_below = shop_records["comparison"].tolist().count("below")
                    this_shop_equal = shop_records["comparison"].tolist().count("equal")
                    this_shop_above = shop_records["comparison"].tolist().count("above")

                shop.this_shop_below = this_shop_below
                shop.this_shop_equal = this_shop_equal
                shop.this_shop_above = this_shop_above
                shop.prod_count = this_shop_below + this_shop_equal + this_shop_above

                if shop.this_shop_below >= 1:
                    shops_below += 1
                else:
                    shops_ok += 1

            latest_timestamp = groupedretailprices.sort_values(
                by="timestamp", ascending=False
            )["timestamp"].iloc[0]
            if not latest_timestamp:
                raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")

            latest_timestamp = latest_timestamp.to_pydatetime()

            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")

            context.update(
                {
                    "shops": shops,
                    "shops_below": shops_below,
                    "shops_ok": shops_ok,
                    "latest_timestamp": latest_timestamp,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        else:
            context.update(
                {
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        return context


class ShopInfo(TemplateView):
    template_name = "dashboard/shop_info.html"

    def get_context_data(self, **kwargs):
        context = super(ShopInfo, self).get_context_data(**kwargs)
        shop = get_object_or_404(Shop, id=kwargs["pk"])
        user = self.request.user
        seller_flag = is_seller(user)
        if seller_flag and not shop.seller == user:
            raise Http404("Δεν έχετε πρόσβαση σε αυτό το κατάστημα.")
        retailprices = RetailPrice.objects.filter(
            shop=kwargs["pk"],
            product__active=True,
            timestamp__range=(
                datetime.datetime.now() - datetime.timedelta(days=14),
                datetime.datetime.now(),
            ),
        )

        data_exists = False
        if retailprices.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:
            table_image_size = "80x80"
            products = (
                Product.objects.filter(retailprice__shop=kwargs["pk"])
                .distinct()
                .select_related()
                .annotate(
                    manufacturer_name=F("manufacturer__name"),
                    category_name=F("main_category__name"),
                )
            )
            for product in products:
                im = get_thumbnail(product.image, table_image_size)
                product.prod_img = im.url

            retailpricesdf = pd.DataFrame.from_records(
                retailprices.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                ],
            )

            retailpricesdf = retailpricesdf.loc[
                retailpricesdf.groupby(["product_id", "source_id"])[
                    "timestamp"
                ].idxmax()
            ].reset_index(drop=True)

            if not retailpricesdf.empty:
                latest_timestamp = retailpricesdf.sort_values(
                    by="timestamp", ascending=False
                )["timestamp"].iloc[0]

                if not latest_timestamp:
                    raise Http404(
                        "Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων"
                    )

                retailprices = (
                    retailprices.filter(id__in=retailpricesdf["id"])
                    .select_related()
                    .annotate(
                        product_manufacturer_name=F("product__manufacturer__name"),
                        product_category_name=F("product__main_category__name"),
                    )
                )

                for retailprice in retailprices:
                    im = get_thumbnail(retailprice.product.image, table_image_size)
                    retailprice.product_image = im.url

                retailpricesdf.sort_values(
                    by=["product_id", "price"], inplace=True, ascending=True
                )
                retailpricesdf.drop_duplicates(subset=["product_id"], inplace=True)

                conditions = [
                    retailpricesdf["price"] < retailpricesdf["curr_target_price"],
                    retailpricesdf["price"] == retailpricesdf["curr_target_price"],
                    retailpricesdf["price"] > retailpricesdf["curr_target_price"],
                ]
                choices = ["below", "equal", "above"]

                retailpricesdf["comparison"] = np.select(
                    conditions, choices, default=np.nan
                )

                products_below = retailpricesdf["comparison"].tolist().count("below")
                products_equal = retailpricesdf["comparison"].tolist().count("equal")
                products_above = retailpricesdf["comparison"].tolist().count("above")

            if not products:
                raise Http404("Δεν υπάρχουν προϊόντα")

            latest_timestamp = latest_timestamp.to_pydatetime()
            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
            context.update(
                {
                    "shop": shop,
                    "retailprices": retailprices,
                    "products": products,
                    "table_image_size": table_image_size,
                    "products_below": products_below,
                    "products_equal": products_equal,
                    "products_above": products_above,
                    "latest_timestamp": latest_timestamp,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        else:
            context.update(
                {
                    "shop": shop,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        return context


class CategoriesPage(TemplateView):
    template_name = "dashboard/categories_page.html"

    def get_context_data(self, **kwargs):
        context = super(CategoriesPage, self).get_context_data(**kwargs)
        user = self.request.user
        categories = Category.objects.all()
        products_below = 0
        products_ok = 0
        products = Product.objects.filter(active=True)
        seller_flag = is_seller(user)
        if seller_flag:
            retail_prices = RetailPrice.objects.filter(
                shop__seller=user,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            )
        else:
            retail_prices = RetailPrice.objects.filter(
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                )
            )

        data_exists = False
        if retail_prices.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:
            products_df = pd.DataFrame().from_records(
                products.values_list("id", "main_category"),
                columns=["product_id", "main_category"],
            )

            retail_prices_df = pd.DataFrame().from_records(
                retail_prices.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                ],
            )

            grouped = retail_prices_df.loc[
                retail_prices_df.groupby(["product_id", "source_id"])[
                    "timestamp"
                ].idxmax()
            ].reset_index(drop=True)
            grouped.sort_values(
                by=["product_id", "price"], inplace=True, ascending=True
            )
            grouped.drop_duplicates(subset=["product_id"], inplace=True)

            conditions = [
                grouped["price"] < grouped["curr_target_price"],
                grouped["price"] >= grouped["curr_target_price"],
            ]
            choices = ["below", "ok"]

            grouped["comparison"] = np.select(conditions, choices, default=np.nan)

            latest_timestamp = grouped.sort_values(by="timestamp", ascending=False)[
                "timestamp"
            ].iloc[0]
            if not latest_timestamp:
                raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")

            latest_timestamp = latest_timestamp.to_pydatetime()
            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")

            merged = pd.merge(grouped, products_df).reset_index()

            for category in categories:
                products_below = 0
                product_count = 0
                products_ok = 0
                full_tree = category.get_descendants(include_self=True)
                tree_ids = []
                for tree in full_tree:
                    tree_ids.append(tree.id)
                category_records = merged.loc[
                    merged["main_category"].isin(tree_ids)
                ].copy()
                if not category_records.empty:
                    products_below = (
                        category_records["comparison"].tolist().count("below")
                    )
                    products_ok = category_records["comparison"].tolist().count("ok")
                    product_count = products_ok + products_below
                category.products_below = products_below
                category.products_ok = products_ok
                category.product_count = product_count
                category.ansc_count = category.get_ancestors(
                    ascending=False, include_self=False
                )

            context.update(
                {
                    "categories": categories,
                    "latest_timestamp": latest_timestamp,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        else:
            context.update(
                {
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        return context


class CategoryInfo(TemplateView):
    template_name = "dashboard/category_info.html"

    def get_context_data(self, **kwargs):
        context = super(CategoryInfo, self).get_context_data(**kwargs)
        user = self.request.user
        seller_flag = is_seller(user)
        table_image_size = "80x80"
        category_descendants = Category.objects.get(id=kwargs["pk"]).get_descendants(
            include_self=True
        )
        children_id_list = []
        products_below = 0
        products_ok = 0
        shops_below = 0
        shops_equal = 0
        shops_above = 0

        for child in category_descendants:
            children_id_list.append(child.id)

        category = get_object_or_404(Category, id=kwargs["pk"])
        products = (
            Product.objects.filter(main_category__in=children_id_list)
            .select_related()
            .annotate(
                product_manufacturer=F("manufacturer__name"),
                product_category=F("main_category__name"),
            )
        )

        productsdf = pd.DataFrame().from_records(
            products.values_list(),
            columns=[
                "product_id",
                "manufacturer",
                "model",
                "sku",
                "active",
                "map_price",
                "main_category",
                "image",
                "image_url",
                "product_manufacturer",
                "product_category",
            ],
        )

        product_ids = productsdf["product_id"].tolist()

        active_products = productsdf.loc[productsdf["active"] == True].copy()

        if seller_flag:
            retailprices = RetailPrice.objects.filter(
                shop__seller=user,
                product__in=product_ids,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            )
        else:
            retailprices = RetailPrice.objects.filter(
                product__in=product_ids,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            )
        data_exists = False
        if retailprices.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:
            retailpricesdf = pd.DataFrame().from_records(
                retailprices.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                ],
            )

            latest_retailprices_for_products = (
                retailpricesdf.loc[
                    retailpricesdf.groupby(["product_id", "shop_id"])[
                        "timestamp"
                    ].idxmax()
                ]
                .reset_index(drop=True)
                .copy()
            )
            conditions = [
                latest_retailprices_for_products["price"]
                < latest_retailprices_for_products["curr_target_price"],
                latest_retailprices_for_products["price"]
                == latest_retailprices_for_products["curr_target_price"],
                latest_retailprices_for_products["price"]
                > latest_retailprices_for_products["curr_target_price"],
            ]
            choices = ["below", "equal", "above"]

            latest_retailprices_for_products["comparison"] = np.select(
                conditions, choices, default=np.nan
            )

            for product in products:
                shops_below = 0
                shops_equal = 0
                shops_above = 0
                product_records = latest_retailprices_for_products.loc[
                    latest_retailprices_for_products["product_id"] == product.id
                ].copy()
                if not product_records.empty:
                    shops_below = product_records["comparison"].tolist().count("below")
                    shops_equal = product_records["comparison"].tolist().count("equal")
                    shops_above = product_records["comparison"].tolist().count("above")
                product.shops_below = shops_below
                product.shops_equal = shops_equal
                product.shops_above = shops_above
                product.shop_count = shops_below + shops_equal + shops_above

                im = get_thumbnail(product.image, table_image_size)
                product.product_image = im.url

            retail_prices = (
                retailprices.filter(id__in=latest_retailprices_for_products["id"])
                .select_related()
                .annotate(
                    product_model=F("product__model"),
                    product_manufacturer=F("product__manufacturer__name"),
                    product_category=F("product__main_category__name"),
                    product_sku=F("product__sku"),
                    shop_name=F("shop__name"),
                    source_domain=F("source__domain"),
                )
            )

            latest_retailprices_for_products.sort_values(
                by=["product_id", "price"], inplace=True, ascending=True
            )
            latest_retailprices_for_products.drop_duplicates(
                subset=["product_id"], inplace=True
            )

            category.products_below = (
                latest_retailprices_for_products["comparison"].tolist().count("below")
            )
            category.products_ok = latest_retailprices_for_products[
                "comparison"
            ].tolist().count("equal") + latest_retailprices_for_products[
                "comparison"
            ].tolist().count(
                "above"
            )

            for retailprice in retail_prices:
                im = get_thumbnail(retailprice.product.image, table_image_size)
                retailprice.product_image = im.url

            latest_timestamp = latest_retailprices_for_products.sort_values(
                by="timestamp", ascending=False
            )["timestamp"].iloc[0]

            latest_timestamp = latest_timestamp.to_pydatetime()
            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")

            context.update(
                {
                    "category": category,
                    "products": products,
                    "retail_prices": retail_prices,
                    "table_image_size": table_image_size,
                    "latest_timestamp": latest_timestamp,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        else:
            context.update(
                {
                    "category": category,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )

        return context


class ManufacturersPage(TemplateView):
    template_name = "dashboard/manufacturers_page.html"

    def get_context_data(self, **kwargs):
        context = super(ManufacturersPage, self).get_context_data(**kwargs)
        user = self.request.user
        seller_flag = is_seller(user)
        manufacturers = Manufacturer.objects.all()
        products = Product.objects.filter(active=True)

        if seller_flag:
            retail_prices = RetailPrice.objects.filter(
                shop__seller=user,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            )
        else:
            retail_prices = RetailPrice.objects.filter(
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                )
            )

        data_exists = False
        if retail_prices.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:
            products_df = pd.DataFrame().from_records(
                products.values_list("id", "manufacturer"),
                columns=["product_id", "manufacturer"],
            )

            retail_prices_df = pd.DataFrame().from_records(
                retail_prices.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                ],
            )

            latest_retail_prices = retail_prices_df.loc[
                retail_prices_df.groupby(["product_id"])["timestamp"].idxmax()
            ].reset_index(drop=True)

            retail_prices_w_man = pd.merge(latest_retail_prices, products_df)

            for manufacturer in manufacturers:
                products_below = 0
                products_ok = 0
                products_above = 0
                manufacturer_products = products_df.loc[
                    products_df["manufacturer"] == manufacturer.id
                ].copy()
                product_count = manufacturer_products["product_id"].count()
                manufacturer_sellers_products = retail_prices_w_man.loc[
                    retail_prices_w_man["manufacturer"] == manufacturer.id
                ].copy()
                final_prices = retail_prices_w_man.loc[
                    retail_prices_w_man["manufacturer"] == manufacturer.id
                ].copy()
                if not final_prices.empty:
                    conditions = [
                        final_prices["price"] < final_prices["curr_target_price"],
                        final_prices["price"] >= final_prices["curr_target_price"],
                    ]
                    choices = ["below", "ok"]

                    final_prices["comparison"] = np.select(
                        conditions, choices, default=np.nan
                    )

                    products_below = final_prices["comparison"].tolist().count("below")
                    products_ok = product_count - products_below
                manufacturer.seller_product_count = (
                    manufacturer_sellers_products.drop_duplicates(
                        subset="product_id"
                    ).shape[0]
                )
                manufacturer.products_below = products_below
                manufacturer.products_ok = products_ok
                manufacturer.product_count = product_count

            latest_timestamp = latest_retail_prices.sort_values(
                by="timestamp", ascending=False
            )["timestamp"].iloc[0]

            if not latest_timestamp:
                raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")

            latest_timestamp = latest_timestamp.to_pydatetime()
            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
            context.update(
                {
                    "manufacturers": manufacturers,
                    "latest_timestamp": latest_timestamp,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        else:
            context.update(
                {
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )

        return context


class ManufacturerInfo(TemplateView):
    template_name = "dashboard/manufacturer_info.html"

    def get_context_data(self, **kwargs):
        context = super(ManufacturerInfo, self).get_context_data(**kwargs)
        user = self.request.user
        seller_flag = is_seller(user)
        table_image_size = "80x80"
        products_below = 0
        shops_below = 0
        shops_equal = 0
        shops_above = 0
        products_count = 0
        sources = Source.objects.all()

        manufacturer = Manufacturer.objects.get(id=kwargs["pk"])

        products = (
            Product.objects.filter(manufacturer=kwargs["pk"])
            .select_related()
            .annotate(
                product_category=F("main_category__name"),
            )
        )

        productsdf = pd.DataFrame().from_records(
            products.values_list(),
            columns=[
                "product_id",
                "manufacturer",
                "model",
                "sku",
                "active",
                "map_price",
                "main_category",
                "image",
                "image_url",
                "product_category",
            ],
        )

        product_ids = productsdf["product_id"].tolist()

        active_products = productsdf.loc[productsdf["active"] == True].copy()

        active_products = active_products["product_id"].tolist()

        if seller_flag:
            retailprices = RetailPrice.objects.filter(
                product__in=active_products,
                shop__seller=user,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            )
        else:
            retailprices = RetailPrice.objects.filter(
                product__in=active_products,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            )

        data_exists = False
        if retailprices.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:
            retailpricesdf = pd.DataFrame().from_records(
                retailprices.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                ],
            )

            latest_retailprices = (
                retailpricesdf.loc[
                    retailpricesdf.groupby(["product_id", "shop_id"])[
                        "timestamp"
                    ].idxmax()
                ]
                .reset_index(drop=True)
                .copy()
            )

            latest_retailprices_ids = latest_retailprices["id"].tolist()

            retailprices = (
                RetailPrice.objects.filter(id__in=latest_retailprices_ids)
                .select_related()
                .annotate(
                    product_model=F("product__model"),
                    product_manufacturer=F("product__manufacturer__name"),
                    product_category=F("product__main_category__name"),
                    product_sku=F("product__sku"),
                    shop_name=F("shop__name"),
                    source_domain=F("source__domain"),
                )
            )
            for retailprice in retailprices:
                im = get_thumbnail(retailprice.product.image, table_image_size)
                retailprice.product_image = im.url

            conditions = [
                latest_retailprices["price"] < latest_retailprices["curr_target_price"],
                latest_retailprices["price"]
                == latest_retailprices["curr_target_price"],
                latest_retailprices["price"] > latest_retailprices["curr_target_price"],
            ]
            choices = ["below", "equal", "above"]

            latest_retailprices["comparison"] = np.select(
                conditions, choices, default=np.nan
            )

            latest_retailprices_for_comparison = latest_retailprices.sort_values(
                by=["product_id", "price"], ascending=True
            ).copy()
            latest_retailprices_for_comparison.drop_duplicates(
                subset="product_id", inplace=True
            )

            manufacturer.products_below = (
                latest_retailprices_for_comparison["comparison"].tolist().count("below")
            )

            manufacturer.products_ok = latest_retailprices_for_comparison[
                "comparison"
            ].tolist().count("equal") + latest_retailprices_for_comparison[
                "comparison"
            ].tolist().count(
                "above"
            )

            for product in products:
                shops_below = 0
                shops_equal = 0
                shops_above = 0
                product_records = latest_retailprices.loc[
                    latest_retailprices["product_id"] == product.id
                ].copy()
                if not product_records.empty:
                    shops_below = product_records["comparison"].tolist().count("below")
                    shops_equal = product_records["comparison"].tolist().count("equal")
                    shops_above = product_records["comparison"].tolist().count("above")
                product.shops_below = shops_below
                product.shops_equal = shops_equal
                product.shops_above = shops_above
                product.shops_count = shops_below + shops_equal + shops_above

                im = get_thumbnail(product.image, table_image_size)
                product.product_image = im.url

            latest_timestamp = latest_retailprices.sort_values(
                by="timestamp", ascending=False
            )["timestamp"].iloc[0]

            if not latest_timestamp:
                raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")

            latest_timestamp = latest_timestamp.to_pydatetime()
            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")

            context.update(
                {
                    "manufacturer": manufacturer,
                    "products": products,
                    "retail_prices": retailprices,
                    "table_image_size": table_image_size,
                    "latest_timestamp": latest_timestamp,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        else:
            context.update(
                {
                    "manufacturer": manufacturer,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        return context


class ShopProductInfo(TemplateView):
    # TODO error handling in case no retail prices exist
    template_name = "dashboard/shop_product_info.html"

    def get_context_data(self, **kwargs):
        date_picker = DatePicker
        context = super(ShopProductInfo, self).get_context_data(**kwargs)
        product = Product.objects.get(id=kwargs["pk_product"])
        product.product_manufacturer = product.manufacturer.name
        # product = get_object_or_404(Product, id=kwargs["pk_product"])
        shop = get_object_or_404(Shop, id=kwargs["pk_shop"])
        urls = Page.objects.filter(product_id=kwargs["pk_product"])
        # urls = get_list_or_404(Page, product_id=kwargs["pk_product"])

        valid_urls = []
        invalid_urls = []
        for url in urls:
            if url.valid:
                valid_urls.append(url)
            else:
                invalid_urls.append(url)

        user = self.request.user
        seller_flag = is_seller(user)

        if seller_flag and not shop.seller == user:
            raise Http404("Το κατάστημα αυτό δεν σου ανήκει")

        retailprices = RetailPrice.objects.filter(
            product=kwargs["pk_product"],
            shop=shop,
            timestamp__range=(
                datetime.datetime.now() - datetime.timedelta(days=14),
                datetime.datetime.now(),
            ),
        )

        data_exists = False
        if retailprices.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:
            retailprices_df = pd.DataFrame().from_records(
                retailprices.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                ],
            )

            latest_retailprices = (
                retailprices_df.loc[
                    retailprices_df.groupby("source_id")["timestamp"].idxmax()
                ]
                .reset_index(drop=True)
                .copy()
            )

            latest_retailprices_ids = latest_retailprices["id"].tolist()

            table_retailprices = (
                RetailPrice.objects.filter(id__in=latest_retailprices_ids)
                .select_related()
                .annotate(
                    source_domain=F("source__domain"),
                )
            )

            latest_timestamp = latest_retailprices.sort_values(
                by="timestamp", ascending=False
            )["timestamp"].iloc[0]

            if not latest_timestamp:
                raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")

            latest_timestamp = latest_timestamp.to_pydatetime()
            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")

            min_retailprice_list = retailprices_df.copy()

            min_retailprice_list["price"] = pd.to_numeric(min_retailprice_list["price"])
            min_retailprice_list = (
                min_retailprice_list.loc[
                    min_retailprice_list.groupby("timestamp")["price"].idxmin()
                ]
                .reset_index(drop=True)
                .copy()
            )

            min_retailprice = min_retailprice_list.sort_values(
                by="price", ascending=True
            )["price"].iloc[0]
            max_retailprice = min_retailprice_list.sort_values(
                by="price", ascending=False
            )["price"].iloc[0]

            conditions = [
                min_retailprice_list["price"]
                < min_retailprice_list["curr_target_price"],
                min_retailprice_list["price"]
                == min_retailprice_list["curr_target_price"],
                min_retailprice_list["price"]
                > min_retailprice_list["curr_target_price"],
            ]
            choices = ["below", "equal", "above"]

            min_retailprice_list["comparison"] = np.select(
                conditions, choices, default=np.nan
            )

            prices_below = min_retailprice_list["comparison"].tolist().count("below")
            prices_equal = min_retailprice_list["comparison"].tolist().count("equal")
            prices_above = min_retailprice_list["comparison"].tolist().count("above")

            min_retailprice_list = min_retailprice_list["id"].tolist()
            min_retailprice_list = RetailPrice.objects.filter(
                id__in=min_retailprice_list
            )

            min_retailprice_list = min_retailprice_list.values(
                "timestamp", "price", "curr_target_price"
            )

            context.update(
                {
                    "product": product,
                    "shop": shop,
                    # "urls": urls,
                    "valid_urls": valid_urls,
                    "invalid_urls": invalid_urls,
                    "table_retailprices": table_retailprices,
                    "min_retailprice": min_retailprice,
                    "max_retailprice": max_retailprice,
                    "min_retailprice_list": min_retailprice_list,
                    "prices_below": prices_below,
                    "prices_equal": prices_equal,
                    "prices_above": prices_above,
                    "latest_timestamp": latest_timestamp,
                    "date_picker": date_picker,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        else:
            context.update(
                {
                    "product": product,
                    "shop": shop,
                    "valid_urls": valid_urls,
                    "invalid_urls": invalid_urls,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        return context


class ProductInfo(TemplateView):
    # TODO error handling in case no retail prices exist
    template_name = "dashboard/product_info.html"

    def get_context_data(self, **kwargs):
        date_picker = TimeDatePicker
        context = super(ProductInfo, self).get_context_data(**kwargs)
        product = get_object_or_404(Product, id=kwargs["pk"])
        urls = Page.objects.filter(product_id=kwargs["pk"])

        valid_urls = []
        invalid_urls = []
        if urls:
            for url in urls:
                if url.valid:
                    valid_urls.append(url)
                else:
                    invalid_urls.append(url)

        user = self.request.user
        seller_flag = is_seller(user)

        table_retailprices = RetailPrice.objects.none()

        if seller_flag:
            retailprices = RetailPrice.objects.filter(
                shop__seller=user,
                product=product,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=14),
                    datetime.datetime.now(),
                ),
            )
        else:
            retailprices = RetailPrice.objects.filter(
                product=product,
                timestamp__range=(
                    datetime.datetime.now() - datetime.timedelta(days=40),
                    datetime.datetime.now(),
                ),
            )

        data_exists = False
        if retailprices.exists():
            data_exists = True
        else:
            data_exists = False

        if data_exists:
            retailprices_df = pd.DataFrame().from_records(
                retailprices.values_list(),
                columns=[
                    "id",
                    "price",
                    "original_price",
                    "timestamp",
                    "product_id",
                    "shop_id",
                    "official_reseller",
                    "curr_target_price",
                    "source_id",
                ],
            )

            latest_retail_prices = (
                retailprices_df.loc[
                    retailprices_df.groupby(["shop_id", "source_id"])[
                        "timestamp"
                    ].idxmax()
                ]
                .reset_index(drop=True)
                .copy()
            )

            shop_ids = latest_retail_prices["shop_id"].drop_duplicates().to_list()

            shops_for_product = Shop.objects.filter(id__in=shop_ids)

            conditions = [
                latest_retail_prices["price"]
                < latest_retail_prices["curr_target_price"],
                latest_retail_prices["price"]
                == latest_retail_prices["curr_target_price"],
                latest_retail_prices["price"]
                > latest_retail_prices["curr_target_price"],
            ]
            choices = ["below", "equal", "above"]

            latest_retail_prices["comparison"] = np.select(
                conditions, choices, default=np.nan
            )

            prices_below = latest_retail_prices["comparison"].tolist().count("below")
            prices_equal = latest_retail_prices["comparison"].tolist().count("equal")
            prices_above = latest_retail_prices["comparison"].tolist().count("above")

            table_retailprices = (
                RetailPrice.objects.filter(id__in=latest_retail_prices["id"])
                .select_related()
                .annotate(
                    shop_name=F("shop__name"),
                    source_domain=F("source__domain"),
                )
            )

            min_retailprice_list = retailprices_df.copy()

            min_retailprice_list["price"] = pd.to_numeric(min_retailprice_list["price"])
            min_retailprice_list = (
                min_retailprice_list.loc[
                    min_retailprice_list.groupby("timestamp")["price"].idxmin()
                ]
                .reset_index(drop=True)
                .copy()
            )

            min_retailprice = min_retailprice_list.sort_values(
                by="price", ascending=True
            )["price"].iloc[0]

            max_retailprice = min_retailprice_list.sort_values(
                by="price", ascending=False
            )["price"].iloc[0]

            min_retailprice_list = min_retailprice_list["id"].tolist()
            min_retailprice_list = RetailPrice.objects.filter(
                id__in=min_retailprice_list
            )

            min_retailprice_list = min_retailprice_list.values(
                "timestamp", "price", "curr_target_price"
            )

            latest_timestamp = latest_retail_prices.sort_values(
                by="timestamp", ascending=False
            )["timestamp"].iloc[0]
            latest_timestamp = latest_timestamp.to_pydatetime()
            local_dt = timezone.localtime(latest_timestamp)
            latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
            context.update(
                {
                    "product": product,
                    "shops": shops_for_product,
                    # "urls": urls,
                    "valid_urls": valid_urls,
                    "invalid_urls": invalid_urls,
                    "retailprices": retailprices,
                    "table_retailprices": table_retailprices,
                    "min_retailprice": min_retailprice,
                    "max_retailprice": max_retailprice,
                    "min_retailprice_list": min_retailprice_list,
                    "prices_below": prices_below,
                    "prices_equal": prices_equal,
                    "prices_above": prices_above,
                    "latest_timestamp": latest_timestamp,
                    "date_picker": date_picker,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        else:
            context.update(
                {
                    "product": product,
                    # "urls": urls,
                    "valid_urls": valid_urls,
                    "invalid_urls": invalid_urls,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "data_exists": data_exists,
                }
            )
        return context


def unique(list1):
    # insert the list to the set
    list_set = set(list1)
    # convert the set to the list
    unique_list = list(list_set)
    return unique_list


def get_change(current, previous):
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return float("inf")


def update_table(filtered_retail_prices, seller_flag):
    updated_table = """<table id='table_1' class="data-table display">
                <thead>
                    <tr class="bg-light">
                        <th class="text-filter">Κατάστημα</th>
                        <th>Τιμή</th>
                        <th>Τιμή MAP</th>
                        <th>Διαφ.</th>
                        <th>Διαφ. %</th>
                        <th class="select-filter">Πηγή</th>
                        <th class="select-filter">Key Account</th>
                        <th class="select-filter">Επ. Μεταπωλ.</th>"""
    if not seller_flag:
        updated_table += """<th class="select-filter">Πωλητής</th>"""

    updated_table += """
                <th>Ημερομηνία</th>
                    </tr>
                    <tr class="bg-light head-filters">
                        <th class="text">Κατάστημα</th>
                        <th class="no-filter">Τιμή</th>
                        <th class="no-filter">Τιμή MAP</th>
                        <th class="no-filter">Διαφ.</th>
                        <th class="no-filter">Διαφ. %</th>
                        <th class="select">Πηγή</th>
                        <th class="select">Key Account</th>
                        <th class="select">Επ. Μεταπωλ.</th>"""

    if not seller_flag:
        updated_table += """<th class="select">Πωλητής</th>"""

    updated_table += """<th class="no-filter">Ημερομηνία</th>
                    </tr>
                </thead>"""
    # updated_table += """<th class="date-filter"><div id="reportrange" class="btn btn-secondary"> <span></span> <b class="caret"></b></div></th>
    #                 </tr>
    #             </thead>"""

    for retailprice in filtered_retail_prices:
        is_shop_official_reseller = retailprice.is_shop_official_reseller()
        local_dt = timezone.localtime(retailprice.timestamp)
        try:
            seller = retailprice.shop.seller.last_name
        except:
            seller = ""
        # TODO check date format in tables
        timestamp_tmp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        # change color of row depending on price diffs
        if retailprice.price < retailprice.curr_target_price:
            updated_table += '<tr class="bg-danger" style="--bs-bg-opacity: .1;">'
        else:
            updated_table += "<tr>"
            # print shop name, retail price and target price
        shop_info = reverse("shop_info", kwargs={"pk": retailprice.shop.id})
        updated_table += (
            '''<td><a href="'''
            + shop_info
            + """" class="link-dark">"""
            + retailprice.shop.name
            + """</a></td>
            <td>"""
            + str(retailprice.price)
            + """ €
            </td>
            <td>"""
            + str(retailprice.curr_target_price)
            + """  €
            </td>
            <td>"""
        )
        # print diff
        if retailprice.price < retailprice.curr_target_price:
            updated_table += '<p class="text-danger">'
        elif retailprice.price > retailprice.curr_target_price:
            updated_table += '<p class="text-success">'
        else:
            updated_table += '<p class="text-black">'
        updated_table += (
            str(round(retailprice.price - retailprice.curr_target_price, 2))
            + """  €</p>
                            </td>
                            <td>"""
        )
        # print diff %
        if retailprice.price < retailprice.curr_target_price:
            updated_table += '<p class="text-danger">'
        elif retailprice.price > retailprice.curr_target_price:
            updated_table += '<p class="text-success">'
        else:
            updated_table += '<p class="text-black">'
            # print is official reseller & timestamp
        updated_table += (
            str(
                round(
                    get_change(
                        float(retailprice.price), float(retailprice.curr_target_price)
                    ),
                    2,
                )
            )
            + """ %</p>
                            </td>
                            <td>"""
            + retailprice.source.domain
            + """</td>
                        <td>"""
            + retailprice.shop.is_key_account()
            + """</td>
                            <td>"""
            + is_shop_official_reseller
            + """</td>"""
        )
        if not seller_flag:
            updated_table += """<td>""" + seller + """</td>"""
        updated_table += (
            """<td>"""
            + str(timestamp_tmp)
            + """</td>
                            </tr>"""
        )
    updated_table += """</tbody>
                    </table>"""
    return updated_table


def update_date(request, product_id):
    if request.method == "POST":
        try:
            product = Product.objects.get(pk=product_id)
        except:
            raise Http404("Δεν υπάρχει το προϊόν")

        date_range = request.POST.get("datetime_range_with_predefined_ranges")
        shops = request.POST.get("shops_list").strip()
        date_range_list = [data.strip() for data in date_range.split(" - ")]
        shops_list = [data.strip() for data in shops.split(" ")]
        date_from = date_range_list[0]
        date_to = date_range_list[1]
        response_data = {}

        naive_query_date_from = datetime.datetime.strptime(date_from, "%d/%m/%Y, %H:%M")
        naive_query_date_to = datetime.datetime.strptime(date_to, "%d/%m/%Y, %H:%M")

        query_date_from = make_aware(naive_query_date_from)
        query_date_to = make_aware(naive_query_date_to).replace(
            second=59, microsecond=999999
        )
        # .replace(
        #     hour=23, minute=59, second=59, microsecond=999999
        # )

        try:
            filtered_retail_prices = RetailPrice.objects.filter(
                timestamp__range=(query_date_from, query_date_to),
                product=product,
                shop__in=shops_list,
            )
            timestamps = []
            if filtered_retail_prices:
                for price in filtered_retail_prices:
                    timestamps.append(price.timestamp)

                timestamps = unique(timestamps)
                timestamps.sort(reverse=False)

                target_prices = []
                timestamp_list = []
                for timestamp in timestamps:
                    local_dt = timezone.localtime(timestamp)
                    time_tmp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
                    timestamp_list.append(time_tmp)
                    if filtered_retail_prices.filter(timestamp=timestamp):
                        target_prices.append(
                            float(
                                filtered_retail_prices.filter(timestamp=timestamp)[
                                    0
                                ].curr_target_price
                            )
                        )
                    else:
                        target_prices.append(0)
                shops_objs = Shop.objects.filter(id__in=shops_list)

                shops_json_objs = []
                for shop in shops_objs:
                    tmp_price_list = []
                    for timestamp in timestamps:
                        local_dt = timezone.localtime(timestamp)
                        timestamp_tmp = datetime.datetime.strftime(
                            local_dt, "%d/%m/%Y, %H:%M"
                        )
                        if filtered_retail_prices.filter(
                            timestamp=timestamp, shop=shop
                        ):
                            for price in filtered_retail_prices.filter(
                                timestamp=timestamp, shop=shop
                            ):
                                tmp_price_list.append(
                                    {"y": str(price.price), "x": timestamp_tmp, "r": 10}
                                )
                    pricestr = []
                    for idx, price in enumerate(tmp_price_list):
                        key = "price" + str(idx)
                        pricestr.append(price)
                    shops_json_objs.append({"name": shop.name, "prices": pricestr})

                shops_below = 0
                shops_equal = 0
                shops_above = 0

                for price in filtered_retail_prices:
                    if price.price < price.curr_target_price:
                        shops_below += 1
                    elif price.price == price.curr_target_price:
                        shops_equal += 1
                    elif price.price > price.curr_target_price:
                        shops_above += 1

                retail_prices = serializers.serialize("json", filtered_retail_prices)

                response_data["date_from"] = date_from
                response_data["date_to"] = date_to
                response_data["shops_list"] = shops_json_objs
                response_data["target_prices"] = target_prices
                response_data["timestamp_list"] = timestamp_list
                response_data["shops_below"] = shops_below
                response_data["shops_equal"] = shops_equal
                response_data["shops_above"] = shops_above
                response_data["table"] = update_table(
                    filtered_retail_prices, is_seller(request.user)
                )

                return JsonResponse(response_data)
            else:
                raise ValueError("This is a happy little error")
        except:
            raise ValueError("There are no prices for this range")
            # raise Http404("There are no prices for this range")

    else:
        return HttpResponse(
            "This is not the place you are looking for"
            # json.dumps({"nothing to see": "this isn't happening"}),
            # content_type="application/json"
        )


# <a href="{% url 'product_info' product.id %}">
# {% thumbnail product.image table_image_size as im %}
#     <img src="{{ im.url }}" aria-src="{{ im.url|datalize }}" width="{{ im.width }}" height="{{ im.height }}" alt="{{product.name}}" class="prod-img">
# </a>
# {% endthumbnail %}

# TODO make search work with greek accents
def meerkat_search(products, categories, shops, manufacturers, div_id, col_class):
    img_size = "80x80"
    results = '<div class="container-fluid" ><div id="' + div_id + '" class="row">'
    if products:
        results += (
            '<div class="'
            + col_class
            + '"> <p class="text-bold result-header">Προϊόντα</p>'
        )
        for product in products:
            im = get_thumbnail(product.image, img_size)
            product_url = reverse("product_info", kwargs={"pk": product.id})
            results += (
                '<a class="link-dark mt-3" style="display:block;" href="'
                + product_url
                + '"><div class="row align-items-center"><div class="col-xl-3"><img src="'
                + im.url
                + '" alt="'
                + product.model
                + '" class="product_image_search"></div><div class="col-xl-9 align-middle">'
                + product.model
                + " - "
                + product.sku
                + "</div></div></a>"
            )
        results += "</div>"
    if categories:
        results += (
            '<div class="'
            + col_class
            + '"> <p class="text-bold result-header">Κατηγορίες</p>'
        )
        for category in categories:
            category_url = reverse("category_info", kwargs={"pk": category.id})
            results += (
                '<a class="link-dark mt-3" style="display:block;" href="'
                + category_url
                + '">'
                + category.name
                + "</a>"
            )
        results += "</div>"
    if shops:
        results += (
            '<div class="'
            + col_class
            + '"> <p class="text-bold result-header">Καταστήματα</p>'
        )
        for shop in shops:
            shop_url = reverse("shop_info", kwargs={"pk": shop.id})
            results += (
                '<a class="link-dark mt-3" style="display:block;" href="'
                + shop_url
                + '">'
                + shop.name
                + "</a>"
            )
        results += "</div>"
    if manufacturers:
        results += (
            '<div class="'
            + col_class
            + '"> <p class="text-bold result-header">Κατασκευαστές</p>'
        )
        for manufacturer in manufacturers:
            manufacturer_url = reverse(
                "manufacturer_info", kwargs={"pk": manufacturer.id}
            )
            results += (
                '<a class="link-dark mt-3" style="display:block;" href="'
                + manufacturer_url
                + '">'
                + manufacturer.name
                + "</a>"
            )
        results += "</div>"
    if results == '<div id="' + div_id + '">':
        results = '<div id="results" class="mt-4 text-bold result-header">Δεν βρέθηκαν αποτελέσματα</div>'
    else:
        results += "</div></div>"
    return results


def topbar_search(request):
    if request.method == "POST":
        term = request.POST.get("top-search")
        if request.headers.get("Triggeringevent") == "nosubmit":
            if len(term) >= 3 and not term == "":
                products = Product.objects.filter(
                    Q(model__icontains=term) | Q(sku__contains=term)
                )[:6]
                categories = Category.objects.filter(Q(name__unaccent__icontains=term))[
                    :6
                ]
                shops = Shop.objects.filter(Q(name__unaccent__icontains=term))[:6]
                manufacturers = Manufacturer.objects.filter(Q(name__icontains=term))[:6]
                div_id = "mini_search_results"
                col_class = "col-lg-12"
                results = meerkat_search(
                    products, categories, shops, manufacturers, div_id, col_class
                )
            else:
                results = ""
        else:
            term = request.POST.get("top-search")
            results = redirect(reverse("search_results", kwargs={"term": "s:" + term}))
            return results
        return HttpResponse(results)


class SearchResults(TemplateView):
    template_name = "dashboard/search_results.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        term = kwargs["term"][2:]
        context = super(SearchResults, self).get_context_data(**kwargs)
        if term == "" or len(term) < 3:
            results = ""
            context.update(
                {
                    "results": "Παρακαλώ εισάγετε τουλάχιστον 3 χαρακτήρες",
                    "term": term,
                }
            )
        else:
            products = Product.objects.filter(
                Q(model__icontains=term) | Q(sku__icontains=term)
            )
            categories = Category.objects.filter(Q(name__icontains=term))
            shops = Shop.objects.filter(Q(name__icontains=term))
            manufacturers = Manufacturer.objects.filter(Q(name__icontains=term))
            div_id = "full_search_results"
            col_class = "col-lg-3"
            results = meerkat_search(
                products, categories, shops, manufacturers, div_id, col_class
            )
            context.update(
                {
                    "results": results,
                    "term": term,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                }
            )
        return context


class CustomReport(TemplateView):
    # TODO error handling in case no retail prices exist
    template_name = "dashboard/custom_report.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        if is_sales_dep(user) or user.is_superuser or user.is_staff:
            date_picker = TimeDatePickerClearable
            context = super(CustomReport, self).get_context_data(**kwargs)

            # Get the categories we will show in the dropdown
            categories = Category.objects.all()
            shops = Shop.objects.filter(key_account=True)

            seller_flag = is_seller(user)

            context.update(
                {
                    "categories": categories,
                    "seller_flag": seller_flag,
                    "user": user,
                    "user_is_staff": user.is_staff,
                    "user_is_sales_dep": is_sales_dep(user),
                    "user_is_superuser": user.is_superuser,
                    "date_picker": date_picker,
                    "shops": shops,
                }
            )
            return context
        else:
            raise PermissionDenied()


def key_accounts_custom_report(request):
    if request.method == "POST":
        # try:
        categories = request.POST.get("categories_list").strip()
        categories_request = [data.strip() for data in categories.split(" ")]
        categories_list = Category.objects.filter(
            id__in=categories_request
        ).get_descendants(include_self=True)

        shops = request.POST.get("shops_list").strip()
        shops_request = [data.strip() for data in shops.split(" ")]
        key_accounts = Shop.objects.filter(id__in=shops_request)

        date_range = request.POST.get("datetime_range_with_predefined_ranges")

        if date_range:
            date_range_list = [data.strip() for data in date_range.split(" - ")]
            date_from = date_range_list[0]
            date_to = date_range_list[1]
            naive_query_date_from = datetime.datetime.strptime(
                date_from, "%d/%m/%Y, %H:%M"
            )
            naive_query_date_to = datetime.datetime.strptime(date_to, "%d/%m/%Y, %H:%M")

            query_date_from = make_aware(naive_query_date_from)
            query_date_to = make_aware(naive_query_date_to).replace(
                second=59, microsecond=999999
            )
        else:
            query_date_from = make_aware(
                datetime.datetime.now() - datetime.timedelta(days=14)
            )
            query_date_to = make_aware(datetime.datetime.now())

        retail_prices = (
            RetailPrice.objects.filter(
                shop__in=key_accounts,
                product__main_category__in=categories_list,
                product__active=True,
                timestamp__range=(query_date_from, query_date_to),
            )
            .select_related("product")
            .annotate(
                shop_name=F("shop__name"),
                product_category=F("product__main_category__name"),
                product_manufacturer=F("product__manufacturer__name"),
                product_model=F("product__model"),
                product_sku=F("product__sku"),
            )
        )

        retail_prices_df = pd.DataFrame.from_records(
            retail_prices.values_list(),
            columns=[
                "id",
                "price",
                "original_price",
                "timestamp",
                "product_id",
                "shop_id",
                "official_reseller",
                "curr_target_price",
                "source_id",
                "shop_name",
                "product_category",
                "product_manufacturer",
                "product_model",
                "product_sku",
            ],
        )

        if date_range:
            grouped_retailprices = retail_prices_df.groupby(
                ["product_id", "shop_name", "timestamp"]
            ).obj.reset_index(drop=True)
        else:
            grouped_retailprices = retail_prices_df.loc[
                retail_prices_df.groupby(["product_id", "shop_name"])[
                    "timestamp"
                ].idxmax()
            ].reset_index(drop=True)

        latest_timestamp = grouped_retailprices.sort_values(
            by="timestamp", ascending=False
        )["timestamp"].iloc[0]
        if not latest_timestamp:
            raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")

        latest_timestamp = latest_timestamp.to_pydatetime()

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")

        grouped_retailprices = grouped_retailprices.pivot(
            index=[
                "product_id",
                "product_category",
                "product_manufacturer",
                "product_model",
                "product_sku",
                "timestamp",
                "curr_target_price",
            ],
            columns=[
                "shop_name",
            ],
            values=["price", "original_price"],
        ).sort_values(
            by=["product_manufacturer", "product_category", "product_sku", "timestamp"]
        )

        cols = [
            "product_id",
            "product_category",
            "product_manufacturer",
            "product_model",
            "product_sku",
            "timestamp",
            "curr_target_price",
        ]

        cols_to_sort = cols[1:]

        title_cols = len(cols) - 1

        new_column_names = {}

        key_accounts_shops = []
        for shop in grouped_retailprices.columns:
            if shop[0] == "price":
                key_accounts_shops.append(shop[1])
            if shop[0] == "original_price":
                col_name = shop[1] + " Αρχ."
                col_name_cut = shop[1][:4] + " Αρχ."
                new_column_names[col_name] = col_name_cut
                key_accounts_shops.append(col_name)

        cols.extend(key_accounts_shops)

        grouped_retailprices.reset_index(inplace=True)

        grouped_retailprices.columns = cols

        grouped_retailprices.drop("product_id", axis=1, inplace=True)

        grouped_retailprices_cols = grouped_retailprices.columns.values.tolist()

        # Cheeky way to remove the fixed columns from the df columns list
        set1 = set(grouped_retailprices_cols)
        set2 = set(cols_to_sort)
        res = list(set1 - set2)
        res.sort()
        cols_to_sort.extend(res)

        grouped_retailprices = grouped_retailprices[cols_to_sort]

        grouped_retailprices.replace(0, np.nan, inplace=True)

        index_table = grouped_retailprices.copy()

        index_table["min_price"] = (
            grouped_retailprices.iloc[:, title_cols:].min(axis=1).values.astype(float)
        )

        index_table["result"] = np.where(
            index_table.min_price.astype(float).round(decimals=2)
            < index_table.curr_target_price.astype(float).round(decimals=2),
            True,
            False,
        )

        index_table_list = index_table.index[index_table["result"] == True].tolist()

        grouped_retailprices["timestamp"] = grouped_retailprices[
            "timestamp"
        ].dt.tz_convert(settings.TIME_ZONE)

        grouped_retailprices["timestamp"] = grouped_retailprices[
            "timestamp"
        ].dt.strftime("%d/%m/%Y, %H:%M")

        grouped_retailprices.fillna("-", inplace=True)

        columns = [
            {"title": "Κατηγορία"},
            {"title": "Κατασκευαστής"},
            {"title": "Μοντέλο"},
            {"title": "SKU"},
            {"title": "Ημερομηνία"},
            {"title": "Τιμή MAP"},
        ]

        response_data = {}
        for account in res:
            if account in new_column_names.keys():
                columns.append({"title": new_column_names[account]})
            else:
                columns.append({"title": account})
        parsed_df = grouped_retailprices.to_json(orient="values")

        response_data["columns"] = columns
        response_data["data_set"] = json.loads(parsed_df)
        response_data["rows_below"] = index_table_list
        response_data["latest_timestamp"] = latest_timestamp
        return JsonResponse(response_data, safe=False)

    # except:
    #     response_data = {}
    #     response_data["error"] = "An error occured!"
    #     return JsonResponse(response_data, safe=False)

    else:
        return HttpResponse("This is not the place you are looking for")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(settings.LOGIN_URL)


class FeedbackFormView(FormView):
    template_name = "feedback.html"
    form_class = FeedbackForm
    success_url = "/feedback/"

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(FeedbackFormView, self).get_context_data(**kwargs)

        seller_flag = is_seller(user)

        context.update(
            {
                "seller_flag": seller_flag,
                "user": user,
                "user_is_staff": user.is_staff,
                "user_is_sales_dep": is_sales_dep(user),
                "user_is_superuser": user.is_superuser,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            if form.cleaned_data["subject"] == "feature":
                subject = "Meerkat Feedback - Feature Request"
            elif form.cleaned_data["subject"] == "bug":
                subject = "Meerkat Feedback - Bug Report"
            message = form.cleaned_data["message"]
            sender = request.user.email
            cc_myself = form.cleaned_data["cc_myself"]
            recipients = ["n.zervos@soundstar.gr", "e.vakalis@soundstar.gr"]
            files = request.FILES.getlist("file_field")

            valid_extensions = [
                ".pdf",
                ".csv",
                ".doc",
                ".docx",
                ".xlsx",
                ".xlx",
                ".png",
                ".jpg",
            ]

            try:
                if cc_myself:
                    recipients.append(sender)
                email = EmailMessage(
                    subject,
                    message,
                    sender,
                    recipients,
                    # ['to1@example.com', 'to2@example.com'],
                    # ['bcc@example.com'],
                    # reply_to=['another@example.com'],
                    headers={"Message-ID": "Meerkat Feedback"},
                    # attachments=files,
                )
                invalid_files = []
                """
                * max_upload_size - a number indicating the maximum file size allowed for upload.
                    2.5MB - 2621440
                    5MB - 5242880
                    6MB - 6144000
                    10MB - 10485760
                    20MB - 20971520
                    50MB - 5242880
                    100MB - 104857600
                    250MB - 214958080
                    500MB - 429916160
                """
                max_upload_limit = 6144000
                total_size = 0
                file_error = False

                for f in files:
                    total_size += f.size
                    extension = os.path.splitext(f.name)[1]
                    if extension.lower() in valid_extensions:
                        email.attach(f.name, f.read(), f.content_type)
                    else:
                        invalid_files.append(f.name)

                if total_size > max_upload_limit:
                    form.add_error(
                        "file_field",
                        "Το συνολικό μέγεθος των αρχείων υπερβαίνει το όριο."
                        + " ".join(map(str, invalid_files)),
                    )
                    messages.error(
                        request,
                        "Το συνολικό μέγεθος των αρχείων υπερβαίνει το όριο. Το μύνημα δεν έχει αποσταλεί.",
                        extra_tags="danger",
                    )
                    file_error = True

                if len(invalid_files) > 0:
                    form.add_error(
                        "file_field",
                        "Αυτά τα αρχεία δεν έχουν επισυναπτεί: "
                        + " ".join(map(str, invalid_files)),
                    )
                    messages.error(
                        request,
                        "Ο τύπος κάποιου από τα αρχεία που επιλέξατε δεν είναι επιτρεπτός. Το μύνημα δεν έχει αποσταλεί.",
                        extra_tags="danger",
                    )
                    file_error = True

                if file_error:
                    return self.form_invalid(form)

                else:
                    email.send()
                    messages.success(request, "Το μύνημα εστάλει επιτυχώς.")
                    return self.form_valid(form)
            except:
                messages.error(
                    request,
                    "Παρουσιάστηκε ένα σφάλμα κατά την αποστολή του μύνήματος. Παρακαλώ προσπαθήστε ξανά.",
                    extra_tags="danger",
                )
                return self.form_invalid(form)

        else:
            messages.error(
                request, "Υπάχει σφάλμα στα πεδία της φόρμας.", extra_tags="danger"
            )
            return self.form_invalid(form)
