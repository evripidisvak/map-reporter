from django.contrib import admin
from django.db import models
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin, TreeRelatedFieldListFilter
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe
from .models import Manufacturer, Category, Product, Manufacturer, Source, Page, Shop, RetailPrice, MapPrice


# Replace the default ImageField with one that shows a preview of the uploaded image
class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and getattr(value, "url", None):
            image_url = value.url
            file_name = str(value)
            output.append(
                '<a href="{}" target="_blank"><img src="{}" alt="{}" style="max-height: 200px;"/></a>'.
                    format(image_url, image_url, file_name))
        output.append(super().render(name, value, attrs))
        return mark_safe(u''.join(output))


class PageInline(admin.TabularInline):
    model = Page
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    inlines = [PageInline]
    list_display = ('name', 'sku', 'map_price',
                    'key_acc_price', 'main_category', 'active')
    search_fields = ['name', 'sku']
    list_filter = (('main_category', TreeRelatedFieldListFilter), 'active',)
    list_select_related = ('main_category',)
    formfield_overrides = {
        models.ImageField: {'widget': AdminImageWidget},
    }


class CategoryAdmin(DraggableMPTTAdmin):
    search_fields = ['name']
    mptt_indent_field = "name"
    list_display = ('tree_actions', 'indented_title', 'parent', 'related_products_count', 'related_products_cumulative_count')
    list_display_links = ('indented_title',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Add cumulative product count
        qs = Category.objects.add_related_count(
                qs,
                Product,
                'main_category',
                'products_cumulative_count',
                cumulative=True)

        # Add non cumulative product count
        qs = Category.objects.add_related_count(
                 qs,
                 Product,
                 'main_category',
                 'products_count',
                 cumulative=False)
        return qs

    def related_products_count(self, instance):
        return instance.products_count
    related_products_count.short_description = 'Related products (for this specific category)'

    def related_products_cumulative_count(self, instance):
        return instance.products_cumulative_count
    related_products_cumulative_count.short_description = 'Related products (in tree)'


class MapPriceView(admin.ModelAdmin):
    list_display = ('product', 'price', 'timestamp')
    search_fields = ['product']
    list_filter = ['product']

class RetailPriceView(admin.ModelAdmin):
    list_display = ('product', 'price', 'shop', 'official_reseller', 'timestamp')
    list_filter = ['product', 'shop']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Manufacturer)
admin.site.register(Source)
admin.site.register(Page)
admin.site.register(Shop)
admin.site.register(RetailPrice, RetailPriceView)
admin.site.register(MapPrice, MapPriceView)
