from array import array
from itertools import product
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import View
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


class ProductInfo(View):
    template = 'dashboard/product_info.html'

    def get(self, request):
        return render(request, self.template)
