from django.urls import include, path
from dashboard import views

# app_name = 'dashboard'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('login/', views.Login.as_view(), name='login'),
]