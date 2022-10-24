from django.contrib import admin, messages
from django.contrib.admin.widgets import AdminFileWidget
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext
from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter

from .models import (
    Category,
    Manufacturer,
    MapPrice,
    Page,
    Product,
    RetailPrice,
    Shop,
    Source,
)


# Replace the default ImageField with one that shows a preview of the uploaded image
class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and getattr(value, "url", None):
            image_url = value.url
            file_name = str(value)
            output.append(
                '<a href="{}" target="_blank"><img src="{}" alt="{}" style="max-height: 200px;"/></a>'.format(
                    image_url, image_url, file_name
                )
            )
        output.append(super().render(name, value, attrs))
        return mark_safe("".join(output))


class PageInline(admin.TabularInline):
    model = Page
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    inlines = [PageInline]
    list_display = ("name", "sku", "map_price", "main_category", "active")
    search_fields = ["sku", "model", "manufacturer__name"]
    list_filter = (
        "manufacturer",
        "active",
        ("page", admin.EmptyFieldListFilter),
        ("main_category", TreeRelatedFieldListFilter),
    )
    list_select_related = ("main_category",)
    formfield_overrides = {
        models.ImageField: {"widget": AdminImageWidget},
    }

    @admin.action(description="Deactivate selected products")
    def deactivate_products(self, request, queryset):
        updated = queryset.update(active=False)
        for product in queryset:
            product.save()

        self.message_user(
            request,
            ngettext(
                "%d product was successfully deactivated.",
                "%d products were successfully deactivated.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    @admin.action(description="Activate selected products")
    def activate_products(self, request, queryset):
        updated = queryset.update(active=True)
        for product in queryset:
            product.save()

        self.message_user(
            request,
            ngettext(
                "%d product was successfully activated.",
                "%d products were successfully activated.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    actions = [deactivate_products, activate_products]


class CategoryAdmin(DraggableMPTTAdmin):
    search_fields = ["name"]
    mptt_indent_field = "name"
    list_display = (
        "tree_actions",
        "indented_title",
        "parent",
        "related_products_count",
        "related_products_cumulative_count",
    )
    list_display_links = ("indented_title",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Add cumulative product count
        qs = Category.objects.add_related_count(
            qs, Product, "main_category", "products_cumulative_count", cumulative=True
        )

        # Add non cumulative product count
        qs = Category.objects.add_related_count(
            qs, Product, "main_category", "products_count", cumulative=False
        )
        return qs

    def related_products_count(self, instance):
        return instance.products_count

    related_products_count.short_description = (
        "Related products (for this specific category)"
    )

    def related_products_cumulative_count(self, instance):
        return instance.products_cumulative_count

    related_products_cumulative_count.short_description = "Related products (in tree)"


class MapPriceView(admin.ModelAdmin):
    list_display = ("product", "price", "timestamp")
    search_fields = ["product"]
    list_filter = ["product"]


class RetailPriceView(admin.ModelAdmin):
    list_display = (
        "product",
        "price",
        "shop",
        "official_reseller",
        "source",
        "timestamp",
    )
    search_fields = ["product__model", "shop__name"]


class ShopAdminView(admin.ModelAdmin):
    list_display = ("name", "key_account", "seller_last_name")
    list_filter = [
        "key_account",
        ("seller", admin.RelatedOnlyFieldListFilter),
        ("seller", admin.EmptyFieldListFilter),
    ]
    search_fields = ["name"]

    def seller_last_name(self, obj):
        if obj.seller:
            return obj.seller.last_name
        else:
            # return None # or
            return "Δεν υπάρχει"


class ManufacturerView(admin.ModelAdmin):
    search_fields = ["name"]


class PageAdminView(admin.ModelAdmin):
    search_fields = [
        "url",
        "product__model",
        "product__sku",
        "product__manufacturer__name",
    ]
    list_filter = ["valid", "source"]
    list_display = ("url", "product", "get_sku", "valid")

    @admin.display(description="Product SKU")
    def get_sku(self, obj):
        return obj.product.sku

    @admin.action(description="Invalidate selected pages")
    def invalidate_pages(self, request, queryset):
        updated = queryset.update(valid=False)
        for page in queryset:
            page.save()

        self.message_user(
            request,
            ngettext(
                "%d page was successfully invalidated.",
                "%d pages were successfully invalidated.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    @admin.action(description="Validate selected pages")
    def validate_pages(self, request, queryset):
        updated = queryset.update(valid=True)
        for page in queryset:
            page.save()

        self.message_user(
            request,
            ngettext(
                "%d page was successfully validated.",
                "%d pages were successfully validated.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    actions = [invalidate_pages, validate_pages]


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Manufacturer, ManufacturerView)
admin.site.register(Source)
admin.site.register(Page, PageAdminView)
admin.site.register(Shop, ShopAdminView)
admin.site.register(RetailPrice, RetailPriceView)
admin.site.register(MapPrice, MapPriceView)
