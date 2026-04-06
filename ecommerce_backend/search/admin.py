from django.contrib import admin
from products.models import Product


@admin.register(Product)
class ProductSearchAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'base_price', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category']
    search_fields = ['name', 'description', 'sku']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Pricing & SKU', {
            'fields': ('base_price', 'sku')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
