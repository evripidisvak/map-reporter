from array import array
from ast import And
from itertools import product
from this import d
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.views import generic
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.db.models import *
from reporter.models import *
from .forms import DatePicker
from django.http import JsonResponse
import json
import datetime
from datetime import timedelta
from django.core import serializers
from django.contrib.auth.views import *
from django.db.models import Q
from dashboard.templatetags import dashboard_tags
from sorl.thumbnail import get_thumbnail
from django.conf import settings
from .tables import ProductTable


def is_seller(user):
    return user.groups.filter(name="Seller").exists()


class Index(TemplateView):
    template_name = "dashboard/index.html"

    # def get(self, request):
    #     return render(request, self.template)

    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)

        user = self.request.user
        seller_flag = is_seller(user)
        table_image_size = "80x80"
        # products = Product.objects.all()
        products = get_list_or_404(Product, active=True)
        latest_timestamp = RetailPrice.objects.latest("timestamp").timestamp
        if not latest_timestamp:
            raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")
        # products = Product.objects.annotate(shop_count=Count('shop', distinct=True))
        retail_prices = []
        products_below = 0
        this_products_below = 0
        products_equal = 0
        this_products_equal = 0
        products_above = 0
        this_products_above = 0

        sources = Source.objects.all()

        for product in products:
            for source in sources:
                source_found = False
                try:
                    if seller_flag:
                        if RetailPrice.objects.filter(
                            product_id=product.id, shop__seller=user, source=source
                        ):
                            product_latest_timestamp = (
                                RetailPrice.objects.filter(
                                    product_id=product.id,
                                    shop__seller=user,
                                    source=source,
                                )
                                .latest("timestamp")
                                .timestamp
                            )
                            tmp = RetailPrice.objects.filter(
                                timestamp=product_latest_timestamp,
                                product=product,
                                shop__seller=user,
                                source=source,
                            )
                            source_found = True
                    else:
                        if RetailPrice.objects.filter(
                            product_id=product.id, source=source
                        ):
                            product_latest_timestamp = (
                                RetailPrice.objects.filter(
                                    product_id=product.id, source=source
                                )
                                .latest("timestamp")
                                .timestamp
                            )
                            tmp = RetailPrice.objects.filter(
                                timestamp=product_latest_timestamp,
                                product=product,
                                source=source,
                            )
                            source_found = True
                    this_products_below = 0
                    this_products_equal = 0
                    this_products_above = 0
                    if source_found:
                        for tmp_pr in tmp:
                            retail_prices.append(tmp_pr)
                            if tmp_pr.price < tmp_pr.curr_target_price:
                                products_below += 1
                                this_products_below += 1
                            elif tmp_pr.price == tmp_pr.curr_target_price:
                                products_equal += 1
                                this_products_equal += 1
                            elif tmp_pr.price > tmp_pr.curr_target_price:
                                products_above += 1
                                this_products_above += 1
                        product.shops_below = this_products_below
                        product.shops_equal = this_products_equal
                        product.shops_above = this_products_above
                        product.shop_count = (
                            this_products_below
                            + this_products_equal
                            + this_products_above
                        )

                except:
                    pass

        shops_below = 0
        shops_ok = 0

        if seller_flag:
            shops = Shop.objects.filter(seller=user)
        else:
            shops = Shop.objects.all()

        for shop in shops:
            this_shop_below = False
            retailprices = RetailPrice.objects.filter(shop=shop).order_by("-timestamp")
            for retailprice in retailprices:
                if (
                    retailprice.product.active
                    and retailprice.price < retailprice.curr_target_price
                ):
                    shops_below += 1
                    this_shop_below = True
            if not this_shop_below:
                shops_ok += 1

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        context.update(
            {
                "products": products,
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
            }
        )
        return context


class AllProducts(TemplateView):
    template_name = "dashboard/all_products.html"

    def get_context_data(self, **kwargs):
        context = super(AllProducts, self).get_context_data(**kwargs)
        user = self.request.user
        seller_flag = is_seller(user)
        table_image_size = "80x80"
        # products = Product.objects.all()
        products = get_list_or_404(Product)
        latest_timestamp = RetailPrice.objects.latest("timestamp").timestamp
        if not latest_timestamp:
            raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")
        # products = Product.objects.annotate(shop_count=Count('shop', distinct=True))
        retail_prices = []
        products_below = 0
        this_products_below = 0
        products_equal = 0
        this_products_equal = 0
        products_above = 0
        this_products_above = 0

        sources = Source.objects.all()

        for product in products:
            for source in sources:
                source_found = False
                try:
                    if seller_flag:
                        if RetailPrice.objects.filter(
                                product_id=product.id, shop__seller=user, source=source
                            ):
                            product_latest_timestamp = (
                                RetailPrice.objects.filter(
                                    product_id=product.id, shop__seller=user, source=source
                                )
                                .latest("timestamp")
                                .timestamp
                            )
                            tmp = RetailPrice.objects.filter(
                                timestamp=product_latest_timestamp,
                                product=product,
                                shop__seller=user,
                                source=source
                            )
                            source_found = True
                    else:
                        if RetailPrice.objects.filter(product_id=product.id, source=source):
                            product_latest_timestamp = (
                                RetailPrice.objects.filter(product_id=product.id, source=source)
                                .latest("timestamp")
                                .timestamp
                            )
                            tmp = RetailPrice.objects.filter(
                                timestamp=product_latest_timestamp,
                                product=product,
                                source=source
                            )
                            source_found = True
                    this_products_below = 0
                    this_products_equal = 0
                    this_products_above = 0
                    if source_found:
                        for tmp_pr in tmp:
                            retail_prices.append(tmp_pr)
                            if (
                                tmp_pr.product.active
                                and tmp_pr.price < tmp_pr.curr_target_price
                            ):
                                products_below += 1
                                this_products_below += 1
                            elif (
                                tmp_pr.product.active
                                and tmp_pr.price == tmp_pr.curr_target_price
                            ):
                                products_equal += 1
                                this_products_equal += 1
                            elif (
                                tmp_pr.product.active
                                and tmp_pr.price > tmp_pr.curr_target_price
                            ):
                                products_above += 1
                                this_products_above += 1
                        product.shops_below = this_products_below
                        product.shops_equal = this_products_equal
                        product.shops_above = this_products_above
                        product.shop_count = (
                            this_products_below + this_products_equal + this_products_above
                        )

                except:
                    pass

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        context.update(
            {
                "products": products,
                "retail_prices": retail_prices,
                "products_below": products_below,
                "products_equal": products_equal,
                "products_above": products_above,
                "table_image_size": table_image_size,
                "latest_timestamp": latest_timestamp,
                "seller_flag": seller_flag,
                "user": user,
                "user_is_staff": user.is_staff,
            }
        )
        return context


class ShopsPage(TemplateView):
    template_name = "dashboard/shops_page.html"

    def get_context_data(self, **kwargs):
        context = super(ShopsPage, self).get_context_data(**kwargs)
        # shops = Shop.objects.annotate(prod_count=Count('products', distinct=True))
        user = self.request.user
        seller_flag = is_seller(user)
        latest_timestamp = RetailPrice.objects.latest("timestamp").timestamp
        if not latest_timestamp:
            raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")
        # products = Product.objects.filter(active=True)
        products = get_list_or_404(Product, active=True)

        if seller_flag:
            # shops = Shop.objects.filter(seller=user)
            shops = get_list_or_404(Shop, seller=user)
        else:
            # shops = Shop.objects.all()
            shops = get_list_or_404(Shop)

        this_shop_below = 0
        this_shop_equal = 0
        this_shop_above = 0

        shops_below = 0
        shops_ok = 0
        
        for shop in shops:
            this_shop_below = 0
            this_shop_equal = 0
            this_shop_above = 0
            for product in products:
                try:
                    latest_price_records = RetailPrice.objects.filter(
                        shop=shop, product=product
                    ).latest("timestamp")
                    if latest_price_records.price < latest_price_records.curr_target_price:
                        this_shop_below += 1
                    elif latest_price_records.price == latest_price_records.curr_target_price:
                        this_shop_equal += 1
                    elif latest_price_records.price > latest_price_records.curr_target_price:
                        this_shop_above += 1
                except:
                    pass
            shop.this_shop_below = this_shop_below
            shop.this_shop_equal = this_shop_equal
            shop.this_shop_above = this_shop_above
            shop.prod_count = this_shop_below + this_shop_equal + this_shop_above

            if shop.this_shop_below >= 1:
                shops_below += 1
            else:
                shops_ok += 1

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
            }
        )
        return context


class ShopInfo(TemplateView):
    template_name = "dashboard/shop_info.html"

    def get_context_data(self, **kwargs):
        context = super(ShopInfo, self).get_context_data(**kwargs)
        # shop = Shop.objects.get(id=kwargs['pk'])
        shop = get_object_or_404(Shop, id=kwargs["pk"])
        user = self.request.user
        seller_flag = is_seller(user)
        if seller_flag and not shop.seller == user:
            raise Http404("Δεν έχετε πρόσβαση σε αυτό το κατάστημα.")
        latest_timestamp = RetailPrice.objects.latest("timestamp").timestamp
        if not latest_timestamp:
            raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")
        products_below = 0
        products_equal = 0
        products_above = 0
        table_image_size = "80x80"
        products = RetailPrice.get_shop_products(shop_id=kwargs["pk"])
        if not products:
            raise Http404("Δεν υπάρχουν προϊόντα")
        retail_prices = []
        retail_prices_min = []
        sources = Source.objects.all()

        for product in products:
            retail_prices_tmp = []
            for source in sources:
                if RetailPrice.objects.filter(shop=shop, product=product, source=source):
                    try:
                        latest_timestamp = (
                            RetailPrice.objects.filter(shop=shop, product=product, source=source)
                            .latest("timestamp")
                            .timestamp
                        )
                        found_retail_price = RetailPrice.objects.filter(
                            shop=shop, product=product, timestamp=latest_timestamp, source=source
                        )
                        for tmp in found_retail_price:
                            retail_prices.append(tmp)
                            retail_prices_tmp.append(tmp)
                    except:
                        pass
            min_price_record = retail_prices_tmp[0]
            for retail_price in retail_prices_tmp:
                if min_price_record.price > retail_price.price:
                    min_price_record = retail_price
            retail_prices_min.append(min_price_record)

        for retail_price in retail_prices_min:
            if retail_price.price < retail_price.curr_target_price:
                products_below += 1
            elif retail_price.price == retail_price.curr_target_price:
                products_equal += 1
            elif retail_price.price > retail_price.curr_target_price:
                products_above += 1

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        context.update(
            {
                "shop": shop,
                "retail_prices": retail_prices,
                "products": products,
                "table_image_size": table_image_size,
                "products_below": products_below,
                "products_equal": products_equal,
                "products_above": products_above,
                "latest_timestamp": latest_timestamp,
                "user": user,
                "user_is_staff": user.is_staff,
            }
        )
        return context


class CategoriesPage(TemplateView):
    template_name = "dashboard/categories_page.html"

    def get_context_data(self, **kwargs):
        context = super(CategoriesPage, self).get_context_data(**kwargs)
        user = self.request.user
        # categories = Category.objects.all()
        categories = get_list_or_404(Category)
        latest_timestamp = RetailPrice.objects.latest("timestamp").timestamp
        if not latest_timestamp:
            raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")
        products_below = 0
        products_ok = 0
        for category in categories:
            products_below = 0
            products_ok = 0
            products = Product.objects.filter(
                main_category__in=category.get_descendants(include_self=True),
                active=True,
            )
            product_count = products.count()
            category.ansc_count = category.get_ancestors(
                ascending=False, include_self=False
            )

            sources = Source.objects.all()

            for product in products:
                for source in sources:
                    try:
                        if RetailPrice.objects.filter(product=product,source=source):
                            price_below_found = False
                            latest_timestamp = (
                                RetailPrice.objects.filter(
                                    product=product,
                                    source=source)
                                .latest("timestamp")
                                .timestamp
                            )
                            latest_price_records = RetailPrice.objects.filter(
                                product=product,
                                timestamp=latest_timestamp,
                                source=source
                            )
                            for retail_price in latest_price_records:
                                if retail_price.price < retail_price.curr_target_price:
                                    products_below += 1
                                    price_below_found = True
                                    break
                            if price_below_found:
                                break
                    except:
                        pass
            category.products_below = products_below
            category.product_count = product_count
            category.products_ok = product_count - products_below

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        context.update(
            {
                "categories": categories,
                "latest_timestamp": latest_timestamp,
                "user": user,
                "user_is_staff": user.is_staff,
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
        if not category_descendants:
            raise Http404("Δεν υπάρχει η κατηγορία")
        children_id_list = []
        products_below = 0
        products_ok = 0
        shops_below = 0
        shops_equal = 0
        shops_above = 0
        products_count = 0

        for child in category_descendants:
            children_id_list.append(child.id)

        category = get_object_or_404(Category, id=kwargs["pk"])
        products = get_list_or_404(Product, main_category__in=children_id_list)
        #products_count = len(products)
        latest_timestamp = (
            RetailPrice.objects.filter(product__main_category__in=children_id_list)
            .latest("timestamp")
            .timestamp
        )
        if not latest_timestamp:
            raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")
        # retail_prices = []
        retailprices = RetailPrice.objects.none()

        sources = Source.objects.all()

        for product in products:
            if product.active:
                products_count += 1
                latest_price_records = RetailPrice.objects.none()
                shops_below = 0
                shops_equal = 0
                shops_above = 0
                for source in sources:
                    # source_found = False
                    try:
                        if seller_flag:
                            if RetailPrice.objects.filter(product=product, source=source, shop__seller=user):
                                product_latest_timestamp = (
                                    RetailPrice.objects.filter(
                                        product=product, shop__seller=user, source=source
                                    )
                                    .latest("timestamp")
                                    .timestamp
                                )
                                latest_price_records.append(
                                    RetailPrice.objects.filter(
                                        product=product,
                                        timestamp=product_latest_timestamp,
                                        shop__seller=user,
                                        source=source
                                    )
                                )
                        else:
                            if RetailPrice.objects.filter(product=product, source=source):
                                product_latest_timestamp = (
                                    RetailPrice.objects.filter(
                                        product=product, source=source
                                    )
                                    .latest("timestamp")
                                    .timestamp
                                )
                                latest_price_records = latest_price_records | RetailPrice.objects.filter(
                                    product=product,
                                    timestamp=product_latest_timestamp,
                                    source=source,
                                )
                                
                    except:
                        pass
                retailprices = retailprices | latest_price_records
                    
                for retail_price in latest_price_records:
                    if retail_price.price < retail_price.curr_target_price:
                        products_below += 1
                        break
                    
                unique_shops_min = {}
                for retail_price in latest_price_records:
                    if retail_price.shop.id in unique_shops_min:
                        if unique_shops_min[retail_price.shop.id]['price'] < retail_price.price:
                            unique_shops_min[retail_price.shop.id] = {'price': retail_price.price, 'target': retail_price.curr_target_price}
                    else:
                        unique_shops_min[retail_price.shop.id] = {'price': retail_price.price, 'target': retail_price.curr_target_price}
            
                for unique_shop in unique_shops_min:
                    if unique_shops_min[unique_shop]['price'] < unique_shops_min[unique_shop]['target']:
                        shops_below += 1    
                    if unique_shops_min[unique_shop]['price'] == unique_shops_min[unique_shop]['target']:
                        shops_equal += 1    
                    if unique_shops_min[unique_shop]['price'] > unique_shops_min[unique_shop]['target']:
                        shops_above += 1    
                # products_below_increased = False
                # if source_found:
                #     for retail_price in latest_price_records:
                #         if retail_price.product.active:
                #             retail_prices.append(retail_price)
                #         if retail_price.price < retail_price.curr_target_price:
                #             if not products_below_increased:
                #                 products_below += 1
                #                 products_below_increased = True
                #             shops_below += 1
                #         elif retail_price.price == retail_price.curr_target_price:
                #             shops_equal += 1
                #         elif retail_price.price > retail_price.curr_target_price:
                #             shops_above += 1
                    
                product.shops_below = shops_below
                product.shops_equal = shops_equal
                product.shops_above = shops_above
                product.shop_count = shops_below + shops_equal + shops_above

        category.products_below = products_below
        category.products_count = products_count
        category.products_ok = products_count - products_below

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        context.update(
            {
                "category": category,
                "products": products,
                "retail_prices": retailprices,
                "table_image_size": table_image_size,
                "latest_timestamp": latest_timestamp,
                "seller_flag": seller_flag,
                "user": user,
                "user_is_staff": user.is_staff,
            }
        )

        return context


class ManufacturersPage(TemplateView):
    template_name = "dashboard/manufacturers_page.html"

    def get_context_data(self, **kwargs):
        context = super(ManufacturersPage, self).get_context_data(**kwargs)
        user = self.request.user
        seller_flag = is_seller(user)
        # manufacturers = Manufacturer.objects.all()
        manufacturers = get_list_or_404(Manufacturer)
        latest_timestamp = RetailPrice.objects.latest("timestamp").timestamp
        if not latest_timestamp:
            raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")

        products_below = 0
        for manufacturer in manufacturers:
            products_below = 0
            manufacturer_products = Product.objects.filter(
                manufacturer=manufacturer, active=True
            )
            product_count = manufacturer_products.count()
            for product in manufacturer_products:
                try:
                    if seller_flag:
                        product_latest_timestamp = (
                            RetailPrice.objects.filter(
                                product_id=product.id, shop__seller=user
                            )
                            .latest("timestamp")
                            .timestamp
                        )
                        retail_prices = RetailPrice.objects.filter(
                            product=product,
                            timestamp=product_latest_timestamp,
                            shop__seller=user,
                        )
                    else:
                        product_latest_timestamp = (
                            RetailPrice.objects.filter(product_id=product.id)
                            .latest("timestamp")
                            .timestamp
                        )
                        retail_prices = RetailPrice.objects.filter(
                            product=product, timestamp=product_latest_timestamp
                        )
                    for price in retail_prices:
                        if price.price < price.curr_target_price:
                            products_below += 1
                            break
                except:
                    pass
            manufacturer.products_below = products_below
            manufacturer.product_count = product_count
            manufacturer.products_ok = product_count - products_below

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        context.update(
            {
                "manufacturers": manufacturers,
                "latest_timestamp": latest_timestamp,
                "seller_flag": seller_flag,
                "user": user,
                "user_is_staff": user.is_staff,
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

        manufacturer = get_object_or_404(Manufacturer, id=kwargs["pk"])
        products = get_list_or_404(Product, manufacturer=kwargs["pk"])
        if seller_flag:
            latest_timestamp = (
                RetailPrice.objects.filter(
                    product__manufacturer=kwargs["pk"], shop__seller=user
                )
                .latest("timestamp")
                .timestamp
            )
        else:
            latest_timestamp = (
                RetailPrice.objects.filter(product__manufacturer=kwargs["pk"])
                .latest("timestamp")
                .timestamp
            )
        retailprices = RetailPrice.objects.none()

        for product in products:
            if product.active:
                products_count += 1
                latest_price_records = RetailPrice.objects.none()
                shops_below = 0
                shops_equal = 0
                shops_above = 0
                for source in sources:
                    try:
                        if seller_flag:
                            if RetailPrice.objects.filter(product=product, shop__seller=user, source=source):
                                product_latest_timestamp = (
                                    RetailPrice.objects.filter(product=product, shop__seller=user, source=source)
                                    .latest("timestamp")
                                    .timestamp
                                )
                                latest_price_records = latest_price_records | RetailPrice.objects.filter(
                                    product=product,
                                    timestamp=product_latest_timestamp,
                                    source=source,
                                    shop__seller=user,
                                )
                        else:
                            if RetailPrice.objects.filter(product=product, source=source):
                                product_latest_timestamp = (
                                    RetailPrice.objects.filter(product=product, source=source)
                                    .latest("timestamp")
                                    .timestamp
                                )
                                latest_price_records = latest_price_records | RetailPrice.objects.filter(
                                    product=product, source=source, timestamp=product_latest_timestamp
                                )
                
                    except:
                        pass
                retailprices = retailprices | latest_price_records
                
                for retail_price in latest_price_records:
                    if retail_price.price < retail_price.curr_target_price:
                        products_below += 1
                        break
                
                unique_shops_min = {}
                for retail_price in latest_price_records:
                    if retail_price.shop.id in unique_shops_min:
                        if unique_shops_min[retail_price.shop.id]['price'] < retail_price.price:
                            unique_shops_min[retail_price.shop.id] = {'price': retail_price.price, 'target': retail_price.curr_target_price}
                    else:
                        unique_shops_min[retail_price.shop.id] = {'price': retail_price.price, 'target': retail_price.curr_target_price}
                
                for unique_shop in unique_shops_min:
                    if unique_shops_min[unique_shop]['price'] < unique_shops_min[unique_shop]['target']:
                        shops_below += 1    
                    if unique_shops_min[unique_shop]['price'] == unique_shops_min[unique_shop]['target']:
                        shops_equal += 1    
                    if unique_shops_min[unique_shop]['price'] > unique_shops_min[unique_shop]['target']:
                        shops_above += 1    

            product.shops_below = shops_below
            product.shops_equal = shops_equal
            product.shops_above = shops_above
            product.shops_count = shops_below + shops_equal + shops_above
            
        manufacturer.products_below = products_below
        manufacturer.products_count = products_count
        manufacturer.products_ok = products_count - products_below

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
            }
        )

        return context


class ShopProductInfo(TemplateView):
    # TODO error handling in case no retail prices exist
    template_name = "dashboard/shop_product_info.html"

    def get_context_data(self, **kwargs):
        date_picker = DatePicker
        context = super(ShopProductInfo, self).get_context_data(**kwargs)
        # product = Product.objects.get(id=kwargs['pk'])
        product = get_object_or_404(Product, id=kwargs["pk_product"])
        shop = get_object_or_404(Shop, id=kwargs["pk_shop"])
        # urls = Page.objects.filter(product_id=kwargs['pk_product'])
        urls = get_list_or_404(Page, product_id=kwargs["pk_product"])

        user = self.request.user
        seller_flag = is_seller(user)

        sources = Source.objects.all()
        table_retailprices = RetailPrice.objects.none()

        try:
            if seller_flag:
                retailprices = RetailPrice.objects.filter(
                    product=kwargs["pk_product"], shop__seller=user, shop=shop,
                    timestamp__range=(datetime.datetime.now() - datetime.timedelta(days=30), datetime.datetime.now()),
                )
                latest_timestamp = (
                    RetailPrice.objects.filter(product=kwargs["pk_product"], shop__seller=user, shop=shop)
                    .latest("timestamp")
                    .timestamp
                )
                latest_retailprices = RetailPrice.objects.filter(
                    product=kwargs["pk_product"], shop__seller=user, timestamp=latest_timestamp, shop=shop
                )
                for source in sources:
                    if RetailPrice.objects.filter(product=kwargs["pk_product"],source=source, shop=shop):
                        tmp_timestamp = RetailPrice.objects.filter(
                            product=kwargs["pk_product"],
                            source=source,
                            shop__seller=user
                        ).latest("timestamp").timestamp

                        table_retailprices = table_retailprices | RetailPrice.objects.filter(
                            product=kwargs["pk_product"],
                            source=source,
                            timestamp=tmp_timestamp,
                            shop=shop,
                            shop__seller=user
                        )
            else:
                retailprices = RetailPrice.objects.filter(
                    product=kwargs["pk_product"],
                    timestamp__range=(datetime.datetime.now() - datetime.timedelta(days=30), datetime.datetime.now()),
                    shop=shop
                    )
                latest_timestamp = (
                    RetailPrice.objects.filter(product=kwargs["pk_product"], shop=shop)
                    .latest("timestamp")
                    .timestamp
                )
                latest_retailprices = RetailPrice.objects.filter(
                    product=kwargs["pk_product"], timestamp=latest_timestamp, shop=shop
                )
                for source in sources:
                    if RetailPrice.objects.filter(product=kwargs["pk_product"],source=source, shop=shop):
                        tmp_timestamp = RetailPrice.objects.filter(
                            product=kwargs["pk_product"],
                            source=source,
                        ).latest("timestamp").timestamp

                        table_retailprices = table_retailprices | RetailPrice.objects.filter(
                            product=kwargs["pk_product"],
                            source=source,
                            timestamp=tmp_timestamp,
                            shop=shop
                        )

            min_retailprice_list = (
                retailprices.values("timestamp", "curr_target_price")
                .annotate(min_price=Min("price"))
                .order_by()
            )

            min_retailprice = min_retailprice_list.aggregate(Min("min_price"))
            max_retailprice = min_retailprice_list.aggregate(Max("min_price"))

            mapprices = MapPrice.objects.filter(product=kwargs["pk_product"])

            shops_below = 0
            shops_equal = 0
            shops_above = 0
            for price in min_retailprice_list:
                if price['min_price'] < price['curr_target_price']:
                    shops_below += 1
                elif price['min_price'] == price['curr_target_price']:
                    shops_equal += 1
                elif price['min_price'] > price['curr_target_price']:
                    shops_above += 1
        except:
            pass

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        context.update(
            {
                "product": product,
                "shop": shop,
                "urls": urls,
                # "retailprices": retailprices,
                "table_retailprices": table_retailprices,
                "min_retailprice": min_retailprice,
                "max_retailprice": max_retailprice,
                "mapprices": mapprices,
                "min_retailprice_list": min_retailprice_list,
                "shops_below": shops_below,
                "shops_equal": shops_equal,
                "shops_above": shops_above,
                "latest_timestamp": latest_timestamp,
                "date_picker": date_picker,
                "seller_flag": seller_flag,
                "user": user,
                "user_is_staff": user.is_staff,
            }
        )
        return context


class ProductInfo(TemplateView):
    # TODO error handling in case no retail prices exist
    template_name = "dashboard/product_info.html"

    def get_context_data(self, **kwargs):
        date_picker = DatePicker
        context = super(ProductInfo, self).get_context_data(**kwargs)
        # product = Product.objects.get(id=kwargs['pk'])
        product = get_object_or_404(Product, id=kwargs["pk"])
        # urls = Page.objects.filter(product_id=kwargs['pk'])
        urls = get_list_or_404(Page, product_id=kwargs["pk"])

        user = self.request.user
        seller_flag = is_seller(user)
        if seller_flag:
            shops_for_product = RetailPrice.get_valid_product_shops(product.id, user)
        else:
            shops_for_product = RetailPrice.get_valid_product_shops(product.id)

        sources = Source.objects.all()
        table_retailprices = RetailPrice.objects.none()

        try:
            if seller_flag:
                retailprices = RetailPrice.objects.filter(
                    product=kwargs["pk"], shop__seller=user,
                    timestamp__range=(datetime.datetime.now() - datetime.timedelta(days=30), datetime.datetime.now())
                )
                latest_timestamp = (
                    RetailPrice.objects.filter(product=kwargs["pk"], shop__seller=user)
                    .latest("timestamp")
                    .timestamp
                )
                latest_retailprices = RetailPrice.objects.filter(
                    product=kwargs["pk"], shop__seller=user, timestamp=latest_timestamp
                )
                for source in sources:
                    if RetailPrice.objects.filter(product=kwargs["pk"],source=source, shop__seller=user):
                        tmp_timestamp = RetailPrice.objects.filter(
                            product=kwargs["pk"],
                            source=source,
                            shop__seller=user
                        ).latest("timestamp").timestamp

                        table_retailprices = table_retailprices | RetailPrice.objects.filter(
                            product=kwargs["pk"],
                            source=source,
                            timestamp=tmp_timestamp,
                            shop__seller=user
                        )
            else:
                retailprices = RetailPrice.objects.filter(
                    product=kwargs["pk"],
                    timestamp__range=(datetime.datetime.now() - datetime.timedelta(days=30), datetime.datetime.now())
                    )
                latest_timestamp = (
                    RetailPrice.objects.filter(product=kwargs["pk"])
                    .latest("timestamp")
                    .timestamp
                )
                latest_retailprices = RetailPrice.objects.filter(
                    product=kwargs["pk"], timestamp=latest_timestamp
                )
                for source in sources:
                    if RetailPrice.objects.filter(product=kwargs["pk"],source=source):
                        tmp_timestamp = RetailPrice.objects.filter(
                            product=kwargs["pk"],
                            source=source,
                        ).latest("timestamp").timestamp

                        table_retailprices = table_retailprices | RetailPrice.objects.filter(
                            product=kwargs["pk"],
                            source=source,
                            timestamp=tmp_timestamp,
                        )

            min_retailprice_list = (
                retailprices.values("timestamp", "curr_target_price")
                .annotate(min_price=Min("price"))
                .order_by()
            )

            min_retailprice = min_retailprice_list.aggregate(Min("min_price"))
            max_retailprice = min_retailprice_list.aggregate(Max("min_price"))

            mapprices = MapPrice.objects.filter(product=kwargs["pk"])

            shops_below = 0
            shops_equal = 0
            shops_above = 0

            for price in latest_retailprices:
                if price.price < price.curr_target_price:
                    shops_below += 1
                elif price.price == price.curr_target_price:
                    shops_equal += 1
                elif price.price > price.curr_target_price:
                    shops_above += 1
        except:
            pass

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        context.update(
            {
                "product": product,
                "shops": shops_for_product,
                "urls": urls,
                "retailprices": retailprices,
                "table_retailprices": table_retailprices,
                "min_retailprice": min_retailprice,
                "max_retailprice": max_retailprice,
                "mapprices": mapprices,
                "min_retailprice_list": min_retailprice_list,
                "shops_below": shops_below,
                "shops_equal": shops_equal,
                "shops_above": shops_above,
                "latest_timestamp": latest_timestamp,
                "date_picker": date_picker,
                "seller_flag": seller_flag,
                "user": user,
                "user_is_staff": user.is_staff,
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

    updated_table += """<th class="date-filter"><div id="reportrange" class="btn btn-secondary"> <span></span> <b class="caret"></b></div></th>
                    </tr>
                </thead>"""

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
                            <td>"""+
                            retailprice.source.domain
                        +"""</td>
                        <td>"""+
                            retailprice.shop.is_key_account()
                        +"""</td>
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

        date_range = request.POST.get("date_range_with_predefined_ranges")
        shops = request.POST.get("shops_list").strip()
        date_range_list = [data.strip() for data in date_range.split(" - ")]
        shops_list = [data.strip() for data in shops.split(" ")]
        date_from = date_range_list[0]
        date_to = date_range_list[1]
        response_data = {}

        naive_query_date_from = datetime.datetime.strptime(date_from, "%d/%m/%Y")
        naive_query_date_to = datetime.datetime.strptime(date_to, "%d/%m/%Y")

        query_date_from = make_aware(naive_query_date_from)
        query_date_to = make_aware(naive_query_date_to).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

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
                + '"><div class="row align-items-center"><div class="col-3"><img src="'
                + im.url
                + '" alt="'
                + product.model
                + '" class="prod-img"></div><div class="col-9 align-middle">'
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
                categories = Category.objects.filter(Q(name__icontains=term))[:6]
                shops = Shop.objects.filter(Q(name__icontains=term))[:6]
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
                }
            )
        return context


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(settings.LOGIN_URL)


class DataTables(TemplateView):
    template_name = "dashboard/datatable.html"

    def get_context_data(self, **kwargs):
        context = super(DataTables, self).get_context_data(**kwargs)
        user = self.request.user
        seller_flag = is_seller(user)
        table_image_size = "80x80"
        # products = Product.objects.all()
        products = get_list_or_404(Product)
        latest_timestamp = RetailPrice.objects.latest("timestamp").timestamp
        if not latest_timestamp:
            raise Http404("Δεν υπάρχουν καταχωρημένες τιμές πώλησης καταστημάτων")
        # products = Product.objects.annotate(shop_count=Count('shop', distinct=True))
        retail_prices = []
        products_below = 0
        this_products_below = 0
        products_equal = 0
        this_products_equal = 0
        products_above = 0
        this_products_above = 0

        for product in products:
            try:
                if seller_flag:
                    product_latest_timestamp = (
                        RetailPrice.objects.filter(
                            product_id=product.id, shop__seller=user
                        )
                        .latest("timestamp")
                        .timestamp
                    )
                    tmp = RetailPrice.objects.filter(
                        timestamp=product_latest_timestamp,
                        product=product,
                        shop__seller=user,
                    )
                else:
                    product_latest_timestamp = (
                        RetailPrice.objects.filter(product_id=product.id)
                        .latest("timestamp")
                        .timestamp
                    )
                    tmp = RetailPrice.objects.filter(
                        timestamp=product_latest_timestamp, product=product
                    )
                this_products_below = 0
                this_products_equal = 0
                this_products_above = 0
                for tmp_pr in tmp:
                    retail_prices.append(tmp_pr)
                    if (
                        tmp_pr.product.active
                        and tmp_pr.price < tmp_pr.curr_target_price
                    ):
                        products_below += 1
                        this_products_below += 1
                    elif (
                        tmp_pr.product.active
                        and tmp_pr.price == tmp_pr.curr_target_price
                    ):
                        products_equal += 1
                        this_products_equal += 1
                    elif (
                        tmp_pr.product.active
                        and tmp_pr.price > tmp_pr.curr_target_price
                    ):
                        products_above += 1
                        this_products_above += 1
                product.shops_below = this_products_below
                product.shops_equal = this_products_equal
                product.shops_above = this_products_above
                product.shop_count = (
                    this_products_below + this_products_equal + this_products_above
                )

            except:
                pass

        local_dt = timezone.localtime(latest_timestamp)
        latest_timestamp = datetime.datetime.strftime(local_dt, "%d/%m/%Y, %H:%M")
        daterange_timestamp = datetime.datetime.strftime(local_dt, "%Y-%m-%d %H:%M:%S")
        context.update(
            {
                "products": products,
                "retail_prices": retail_prices,
                "products_below": products_below,
                "products_equal": products_equal,
                "products_above": products_above,
                "table_image_size": table_image_size,
                "latest_timestamp": latest_timestamp,
                "daterange_timestamp": daterange_timestamp,
                "seller_flag": seller_flag,
                "user": user,
                "user_is_staff": user.is_staff,
            }
        )
        return context
