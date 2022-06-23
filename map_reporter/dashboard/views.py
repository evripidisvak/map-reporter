from array import array
from ast import And
from itertools import product
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic.base import TemplateView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.views import generic
from django.urls import reverse
from django.db.models import *
from reporter.models import *



class Index(View):
    template = 'dashboard/index.html'

    def get(self, request):
        return render(request, self.template)


class Login(View):
    template = 'dashboard/login.html'

    def get(self, request):
        form = AuthenticationForm()
        return render(request, self.template, {'form': form})

    def post(self, request):
        form = AuthenticationForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/')
        else:
            return render(request, self.template, {'form': form})


class ProductInfo(TemplateView):
    template_name = 'dashboard/product_info.html'

    def get_context_data(self, **kwargs):
        context = context = super(ProductInfo, self).get_context_data(**kwargs)

        product = Product.objects.get(id=kwargs['pk'])
        urls = Page.objects.filter(product_id=kwargs['pk'])

        retailprices = RetailPrice.objects.filter(product=kwargs['pk'])
        latest_timestamp = RetailPrice.objects.filter(product=kwargs['pk']).latest('timestamp').timestamp

        min_retailprice_list = (
            retailprices.values('timestamp').annotate(min_price=Min('price')).order_by()
        )

        min_retailprice = min_retailprice_list.aggregate(Min('min_price'))
        max_retailprice = min_retailprice_list.aggregate(Max('min_price'))

        mapprices = MapPrice.objects.filter(product=kwargs['pk'])
        keyaccprices = KeyAccPrice.objects.filter(product=kwargs['pk'])

        shops_below = 0
        shops_equal = 0
        shops_above = 0

        for price in retailprices:
            if price.price < price.curr_target_price:
                shops_below += 1
            elif price.price == price.curr_target_price:
                shops_equal += 1
            elif price.price > price.curr_target_price:
                shops_above += 1

        context.update(
            {
                'product': product,
                'urls': urls,
                'retailprices': retailprices,
                'min_retailprice': min_retailprice,
                'max_retailprice': max_retailprice,
                'mapprices': mapprices,
                'keyaccprices': keyaccprices,
                'min_retailprice_list': min_retailprice_list,
                'shops_below': shops_below,
                'shops_equal': shops_equal,
                'shops_above': shops_above,
                'latest_timestamp': latest_timestamp,
            }
        )
        return context


class ShopProductInfo(TemplateView):
    template_name = 'dashboard/shop_product_info.html'

    def get_context_data(self, **kwargs):
        context = context = super(ShopProductInfo, self).get_context_data(**kwargs)

        product = Product.objects.get(id=kwargs['pk_product'])
        urls = Page.objects.filter(product_id=kwargs['pk_product'])
        shop = Shop.objects.get(id=kwargs['pk_shop'])

        retailprices = RetailPrice.objects.filter(product=kwargs['pk_product'], shop=kwargs['pk_shop'])
        latest_timestamp = RetailPrice.objects.filter(product=kwargs['pk_product'], shop=kwargs['pk_shop']).latest('timestamp').timestamp

        min_retailprice_list = (
            retailprices.values('timestamp').annotate(min_price=Min('price')).order_by()
        )

        min_retailprice = min_retailprice_list.aggregate(Min('min_price'))
        max_retailprice = min_retailprice_list.aggregate(Max('min_price'))

        mapprices = MapPrice.objects.filter(product=kwargs['pk_product'])
        keyaccprices = KeyAccPrice.objects.filter(product=kwargs['pk_product'])

        prices_below = 0
        prices_equal = 0
        prices_above = 0

        for price in retailprices:
            if price.price < price.curr_target_price:
                prices_below += 1
            elif price.price == price.curr_target_price:
                prices_equal += 1
            elif price.price > price.curr_target_price:
                prices_above += 1

        context.update(
            {
                'product': product,
                'urls': urls,
                'retailprices': retailprices,
                'min_retailprice': min_retailprice,
                'max_retailprice': max_retailprice,
                'mapprices': mapprices,
                'keyaccprices': keyaccprices,
                'min_retailprice_list': min_retailprice_list,
                'prices_below': prices_below,
                'prices_equal': prices_equal,
                'prices_above': prices_above,
                'latest_timestamp': latest_timestamp,
                'shop':shop,
            }
        )
        return context


class AllProducts(TemplateView):
    template_name = 'dashboard/all_products.html'

    def get_context_data(self, **kwargs):
        context = super(AllProducts, self).get_context_data(**kwargs)

        table_image_size = '80x80'
        products = Product.objects.all()
        latest_timestamp = RetailPrice.objects.latest('timestamp').timestamp
        # products = Product.objects.annotate(shop_count=Count('shop', distinct=True))
        retailprices = []
        products_below = 0
        this_products_below = 0
        products_equal = 0
        this_products_equal = 0
        products_above = 0
        this_products_above = 0

        for product in products:
            try:
                product_latest_timestamp = RetailPrice.objects.filter(
                    product_id=product.id).latest('timestamp').timestamp
                this_products_below = 0
                this_products_equal = 0
                this_products_above = 0
                tmp = RetailPrice.objects.filter(
                    timestamp=product_latest_timestamp, product=product)
                for tmp_pr in tmp:
                    retailprices.append(tmp_pr)
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
                    this_products_below + this_products_equal + this_products_above
                )

            except:
                pass

        context.update(
            {
                'products': products,
                'retailprices': retailprices,
                'products_below': products_below,
                'products_equal': products_equal,
                'products_above': products_above,
                'table_image_size': table_image_size,
                'latest_timestamp': latest_timestamp,
            }
        )
        return context


# add number of products for each shop
class ShopsPage(TemplateView):
    template_name = 'dashboard/shops_page.html'

    def get_context_data(self, **kwargs):
        context = super(ShopsPage, self).get_context_data(**kwargs)
        # shops = Shop.objects.annotate(prod_count=Count('products', distinct=True))

        products = Product.objects.filter(active=True)

        shops = Shop.objects.all()

        this_shop_below = 0
        this_shop_equal = 0
        this_shop_above = 0

        shops_below = 0
        shops_equal = 0
        shops_above = 0

        for shop in shops:
            this_shop_below = 0
            this_shop_equal = 0
            this_shop_above = 0
            for product in products:
                try:
                    ltst_pr_rec = RetailPrice.objects.filter(
                        shop=shop, product=product
                    ).latest('timestamp')
                    if ltst_pr_rec.price < ltst_pr_rec.curr_target_price:
                        this_shop_below += 1
                        shops_below += 1
                    elif ltst_pr_rec.price == ltst_pr_rec.curr_target_price:
                        this_shop_equal += 1
                        shops_equal += 1
                    elif ltst_pr_rec.price > ltst_pr_rec.curr_target_price:
                        this_shop_above += 1
                        shops_above += 1
                except:
                    pass
            shop.this_shop_below = this_shop_below
            shop.this_shop_equal = this_shop_equal
            shop.this_shop_above = this_shop_above
            shop.prod_count = this_shop_below + this_shop_equal + this_shop_above

        context.update({
            'shops': shops,
            'shops_below': shops_below,
            'shops_equal': shops_equal,
            'shops_above': shops_above,
        })
        return context


class ShopInfo(TemplateView):
    template_name = 'dashboard/shop_info.html'

    def get_context_data(self, **kwargs):
        table_image_size = '80x80'
        context = context = super(ShopInfo, self).get_context_data(**kwargs)
        context.update(
            {
                'shop': Shop.objects.get(id=kwargs['pk']),
                'prices': RetailPrice.objects.filter(shop=kwargs['pk']),
                'products': RetailPrice.get_shop_products(shop_id=kwargs['pk']),
                'table_image_size': table_image_size,
            }
        )
        return context


class CategoriesPage(TemplateView):
    template_name = 'dashboard/categories_page.html'

    def get_context_data(self, **kwargs):
        context = super(CategoriesPage, self).get_context_data(**kwargs)
        categories = Category.objects.all()
        products_below = 0
        products_ok = 0
        for category in categories:
            products_below = 0
            products_ok = 0
            products = Product.objects.filter(main_category__in=category.get_descendants(include_self=True), active=True)
            category.products_list = products
            product_count = products.count()
            category.ansc_count = category.get_ancestors(ascending=False, include_self=False)
            for product in products:
                try:
                    latest_timestamp = RetailPrice.objects.filter(product=product).latest('timestamp').timestamp
                    ltst_pr_rec = RetailPrice.objects.filter(product=product, timestamp=latest_timestamp)
                    for retail_price in ltst_pr_rec:
                        if retail_price.price < retail_price.curr_target_price:
                            products_below += 1
                            break
                except:
                    pass
            category.products_below = products_below
            category.product_count = product_count
            category.products_ok = product_count - products_below

        context.update({
            'categories': categories,
        })
        return context


class CategoryInfo(TemplateView):
    template_name = 'dashboard/category_info.html'

    def get_context_data(self, **kwargs):
        context = context = super(CategoryInfo, self).get_context_data(**kwargs)
        table_image_size = '80x80'
        category_descendants = Category.objects.get(id=kwargs["pk"]).get_descendants(include_self=True)
        children_id_list = []
        products_below = 0
        products_ok = 0
        shops_below = 0
        shops_equal = 0
        shops_above = 0

        for child in category_descendants:
            children_id_list.append(child.id)

        category = Category.objects.get(id=kwargs['pk'])
        products = Product.objects.filter(main_category__in=children_id_list)
        products_count = products.count()
        latest_timestamp = RetailPrice.objects.filter(product__main_category__in=children_id_list).latest('timestamp').timestamp
        retailprices = []

        for product in products:
            shops_below = 0
            shops_equal = 0
            shops_above = 0
            try:
                product_latest_timestamp = RetailPrice.objects.filter(product=product).latest('timestamp').timestamp
                ltst_pr_rec = RetailPrice.objects.filter(product=product, timestamp=product_latest_timestamp)
                products_below_increased = False
                for retail_price in ltst_pr_rec:
                    if retail_price.product.active:
                        retailprices.append(retail_price)
                    if retail_price.price < retail_price.curr_target_price:
                        if  not products_below_increased:
                            products_below += 1
                            products_below_increased = True
                        shops_below += 1
                    elif retail_price.price == retail_price.curr_target_price:
                        shops_equal += 1
                    elif retail_price.price > retail_price.curr_target_price:
                        shops_above += 1
            except:
                pass
            product.shops_below = shops_below
            product.shops_equal = shops_equal
            product.shops_above = shops_above
            product.shops_count = shops_below + shops_equal + shops_above
            category.products_below = products_below
            category.products_count = products_count
            category.products_ok = products_count - products_below
            

        context.update({
            'category': category,
            'products': products,
            'retailprices': retailprices,
            'table_image_size': table_image_size,
            'latest_timestamp': latest_timestamp,
        })

        return context
