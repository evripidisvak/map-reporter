from django.urls import include, path
from dashboard import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('login/', views.Login.as_view(), name='login'),
    path('all_products/', views.AllProducts.as_view(), name='all_proucts'),
    path('product_info/<int:pk>/', views.ProductInfo.as_view(), name='product_info'),
    path('product_analysis/<int:pk>/', views.ProductAnalysis.as_view(), name='product_analysis'),
    path('shops/', views.ShopsPage.as_view(), name='shops_page'),
    path('shop/<int:pk>/', views.ShopInfo.as_view(), name='shop_info'),
    path('shop/<int:pk_shop>/product/<int:pk_product>/', views.ShopProductInfo.as_view(), name='shop_product_info'),
    path('categories/', views.CategoriesPage.as_view(), name='categories_page'),
    path('category/<int:pk>/', views.CategoryInfo.as_view(), name='category_info'),
    path('manufacturers/', views.ManufacturersPage.as_view(), name='manufacturer_page'),
    path('manufacturer/<int:pk>/', views.ManufacturerInfo.as_view(), name='manufacturer_info'),
    # path('update_date_range/', views.update_date, name='update_date'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

htmx_urlpatterns = [
    path('check_text/', views.check_text, name='check_text'),
    path('update_date/', views.update_date, name='update_date'),
]

urlpatterns += htmx_urlpatterns