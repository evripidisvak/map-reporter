from django.urls import include, path
from dashboard import views
from django.conf import settings
from django.conf.urls.static import static

# from django.contrib.auth import views as auth_viewsA


urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("logout/", views.logout_view, name="log_out"),
    path("all_products/", views.AllProducts.as_view(), name="all_products"),
    path("product_info/<int:pk>/", views.ProductInfo.as_view(), name="product_info"),
    path("shops/", views.ShopsPage.as_view(), name="shops_page"),
    path("shop/<int:pk>/", views.ShopInfo.as_view(), name="shop_info"),
    path(
        "shop/<int:pk_shop>/product/<int:pk_product>/",
        views.ShopProductInfo.as_view(),
        name="shop_product_info",
    ),
    path("categories/", views.CategoriesPage.as_view(), name="categories_page"),
    path("category/<int:pk>/", views.CategoryInfo.as_view(), name="category_info"),
    path("manufacturers/", views.ManufacturersPage.as_view(), name="manufacturer_page"),
    path(
        "manufacturer/<int:pk>/",
        views.ManufacturerInfo.as_view(),
        name="manufacturer_info",
    ),
    path(
        "search_results/<str:term>",
        views.SearchResults.as_view(),
        name="search_results",
    ),
    path("topbar_seach/", views.topbar_search, name="topbar_search"),
    # path('__debug__/', include('debug_toolbar.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

htmx_urlpatterns = [
    path("update_date/<int:product_id>", views.update_date, name="update_date"),
]

urlpatterns += htmx_urlpatterns
