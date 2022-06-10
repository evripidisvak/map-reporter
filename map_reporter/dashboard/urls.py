from django.urls import include, path
from dashboard import views

# app_name = 'dashboard'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('login/', views.Login.as_view(), name='login'),
    path('product_info/<int:pk>/', views.ProductInfo.as_view(), name='product_info'),
    path('katastimata/', views.ShopsPage.as_view(), name='shops_page'),
    path('katastima/<int:pk>/', views.ShopInfo.as_view(), name='shop_info'),
]
