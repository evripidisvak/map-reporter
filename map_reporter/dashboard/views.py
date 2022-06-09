from array import array
from itertools import product
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic.base import TemplateView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from reporter.models import *
from django.views import generic
from django.urls import reverse


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


# class ProductInfo(View):
#     template = 'dashboard/product_info.html'

#     def get_

    # def get_queryset(self):
    #     return Product.objects.filter(pk = 2)

    # def get(self, request):
    #     return render(request, self.template)

# class ProductInfo(generic.DetailView):
#     model = Product
#     template_name = 'dashboard/product_info.html'

#     def get_queryset(self):
#         return Page.objects.filter(product_id = self.kwargs['pk'])

    # def get(self, request):
    #     return render(request, self.template)

class ProductInfo(TemplateView):
    template_name = "dashboard/product_info.html"

    def get_context_data(self, **kwargs):
        context = context = super(ProductInfo, self).get_context_data(**kwargs)
        context.update({
            "product": Product.objects.get(id=kwargs['pk']),
            "urls": Page.objects.filter(product_id=kwargs['pk'])
        })
        return context


class ShopInfo(TemplateView):
    template_name = "dashboard/shop_page.html"

    def get_context_data(self, **kwargs):
        context = context = super(ShopInfo, self).get_context_data(**kwargs)
        # context.update({
        #     "shop": Shop.objects.get(id=kwargs['pk']),
        #     # "urls": Page.objects.filter(product_id=kwargs['pk'])
        # })
        return context
