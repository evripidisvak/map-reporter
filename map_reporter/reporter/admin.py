from django.contrib import admin
from .models import Category, Product, Source, Page, Shop, RetailPrice, MapPrice
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin, TreeRelatedFieldListFilter



class PageInline(admin.TabularInline):
    model = Page
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    inlines = [PageInline]
    list_display = ('product_name', 'sku', 'map_price',
                    'key_acc_price', 'main_category', 'active')
    search_fields = ['product_name', 'sku']
    list_filter = (('main_category', TreeRelatedFieldListFilter), 'active',)
    # list_filter = ['main_category', 'active']
    list_select_related = ('main_category',)


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    mptt_level_indent = 20
    list_display = ('name', 'parent')
    # ordering = ['-parent','name']



# admin.site.register(Category, CategoryAdmin)
admin.site.register(
    Category, 
    DraggableMPTTAdmin,
    list_display=('tree_actions', 'indented_title', 'parent',),
    list_display_links=('indented_title',),
    )
admin.site.register(Product, ProductAdmin)
admin.site.register(Source)
admin.site.register(Page)
admin.site.register(Shop)
admin.site.register(RetailPrice)
admin.site.register(MapPrice)
