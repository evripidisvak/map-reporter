from django.urls import include, path
from dashboard import views

# app_name = 'dashboard'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('login/', views.Login.as_view(), name='login'),
    path('all_products/', views.AllProducts.as_view(), name='all_proucts'),
    path('product_info/<int:pk>/', views.ProductInfo.as_view(), name='product_info'),
    path('shops/', views.ShopsPage.as_view(), name='shops_page'),
    path('shop/<int:pk>/', views.ShopInfo.as_view(), name='shop_info'),
    path('categories/', views.CategoriesPage.as_view(), name='categories_page'),
    path('category/<int:pk>/', views.CategoryInfo.as_view(), name='category_info'),
]
