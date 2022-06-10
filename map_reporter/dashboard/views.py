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
        retailprices = RetailPrice.objects.filter(product=kwargs['pk'])
        min_retailprices = retailprices.aggregate(Min('price'))
        max_retailprices = retailprices.aggregate(Max('price'))
        context.update({
            "product": Product.objects.get(id=kwargs['pk']),
            "urls": Page.objects.filter(product_id=kwargs['pk']),
            "retailprices": retailprices,
            "min_retailprices": min_retailprices,
            "max_retailprices": max_retailprices,
            "mapprices": MapPrice.objects.filter(product=kwargs['pk']),
            "keyaccprices": KeyAccPrice.objects.filter(product=kwargs['pk']),
        })
        return context
