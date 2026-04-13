from django.contrib import admin
from .models import Category, Product, ProductImage, CustomizationOption, CustomizationValue, ProductCustomization, Inventory


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductCustomizationInline(admin.TabularInline):
    model = ProductCustomization
    extra = 1


class CustomizationValueInline(admin.TabularInline):
    model = CustomizationValue
    extra = 1


class InventoryInline(admin.StackedInline):
    model = Inventory
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'base_price', 'sku', 'category', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'sku']
    inlines = [ProductImageInline, ProductCustomizationInline, InventoryInline]


@admin.register(CustomizationOption)
class CustomizationOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'option_type', 'is_required', 'display_order']
    list_filter = ['option_type', 'is_required']
    inlines = [CustomizationValueInline]


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'stock_quantity', 'low_stock_threshold', 'is_in_stock', 'is_low_stock']
    list_filter = []
    search_fields = ['product__name']
