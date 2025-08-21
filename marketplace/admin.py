'''from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, License, DeveloperProfile, Product, 
    ProductFile, Download, Review, ModerationLog
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_commercial', 'created_at']
    list_filter = ['is_commercial']
    search_fields = ['name']

@admin.register(DeveloperProfile)
class DeveloperProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'is_verified', 'rating', 'total_sales']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'company_name']

class ProductFileInline(admin.TabularInline):
    model = ProductFile
    extra = 0
    readonly_fields = ['file_size', 'checksum', 'uploaded_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'developer', 'category', 'product_type', 'status', 'price', 'download_count']
    list_filter = ['status', 'product_type', 'category', 'is_free', 'created_at']
    search_fields = ['title', 'developer__user__username']
    readonly_fields = ['id', 'download_count', 'rating', 'review_count']
    inlines = [ProductFileInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('developer__user', 'category')

@admin.register(ProductFile)
class ProductFileAdmin(admin.ModelAdmin):
    list_display = ['product', 'file_type', 'filename', 'file_size', 'scan_status']
    list_filter = ['file_type', 'scan_status', 'uploaded_at']
    search_fields = ['product__title', 'filename']

@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'downloaded_at', 'ip_address']
    list_filter = ['downloaded_at']
    search_fields = ['user__username', 'product__title']
    readonly_fields = ['downloaded_at']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'product__title']

@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ['product', 'moderator', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['product__title', 'moderator__username']
    readonly_fields = ['created_at']'''