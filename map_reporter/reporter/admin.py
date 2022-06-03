from django.contrib import admin
from .models import Category, Product, Page, Shop, RetailPrice


class PageInline(admin.TabularInline):
    model = Page
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    inlines = [PageInline]
    list_display = ('product_name', 'sku', 'map_price',
                    'key_acc_price', 'main_category', 'active')
    search_fields = ['product_name', 'sku']
    list_filter = ['main_category', 'active']
    list_select_related = ('main_category',)


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    # ordering = ['-parent','name']


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Page)
admin.site.register(Shop)
admin.site.register(RetailPrice)
