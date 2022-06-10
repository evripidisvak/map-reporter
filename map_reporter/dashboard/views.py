from array import array
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
    template_name = "dashboard/product_info.html"

    def get_context_data(self, **kwargs):
        context = context = super(ProductInfo, self).get_context_data(**kwargs)

        product = Product.objects.get(id=kwargs['pk'])
        urls = Page.objects.filter(product_id=kwargs['pk'])

        retailprices = RetailPrice.objects.filter(product=kwargs['pk'])
        
        min_retailprice_list  = retailprices.values(
            'timestamp').annotate(min_price=Min('price')).order_by()

        min_retailprice = min_retailprice_list.aggregate(Min('min_price'))
        max_retailprice = min_retailprice_list.aggregate(Max('min_price'))

        mapprices = MapPrice.objects.filter(product=kwargs['pk'])
        keyaccprices = KeyAccPrice.objects.filter(product=kwargs['pk'])

        productsbelow = 0
        productsequal = 0
        productsabove = 0

        for price in retailprices:
            if price.price < price.curr_target_price:
                productsbelow += 1
            elif price.price == price.curr_target_price:
                productsequal += 1
            elif price.price > price.curr_target_price:
                productsabove += 1


        # mapprices = mapprices.filter(timestamp__day='10')
        context.update({
            "product": product,
            "urls": urls,
            "retailprices": retailprices,
            "min_retailprice": min_retailprice,
            "max_retailprice": max_retailprice,
            "mapprices": mapprices,
            "keyaccprices": keyaccprices,
            "min_retailprice_list": min_retailprice_list,
            "productsbelow": productsbelow,
            "productsequal": productsequal,
            "productsabove": productsabove,
        })
        return context


class ShopsPage(TemplateView):
    template_name = "dashboard/shop_page.html"

    def get_context_data(self, **kwargs):
        context = super(ShopsPage, self).get_context_data(**kwargs)
        context.update({
            'shops': Shop.objects.all(),
        })
        return context


class ShopInfo(TemplateView):
    template_name = "dashboard/shop_info.html"

    def get_context_data(self, **kwargs):
        context = context = super(ShopInfo, self).get_context_data(**kwargs)
        context.update({
            "shop": Shop.objects.get(id=kwargs['pk']),
            "prices": RetailPrice.objects.filter(shop=kwargs['pk']),
            "products": RetailPrice.get_shop_products(shop_id=kwargs['pk']),
        })
        return context
