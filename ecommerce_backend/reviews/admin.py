from django.contrib import admin
from .models import Review, ReviewImage


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'is_verified', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_verified', 'is_approved']
    search_fields = ['user__email', 'product__name', 'comment']
    inlines = [ReviewImageInline]
