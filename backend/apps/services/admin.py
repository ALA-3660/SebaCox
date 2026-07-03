from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Category, SubCategory, ServiceProvider, ProviderDocument, ServiceReview, ServiceImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'order']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['order', 'name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'is_active', 'order']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'category__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['order', 'name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'category', 'status', 'is_verified', 'rating', 'total_jobs_completed', 'is_available']
    list_filter = ['status', 'is_verified', 'is_available', 'category', 'created_at']
    search_fields = ['business_name', 'user__phone_number', 'service_area']
    readonly_fields = ['id', 'rating', 'total_reviews', 'total_jobs_completed', 'response_rate', 'created_at', 'updated_at']
    fieldsets = (
        (_('Business Information'), {
            'fields': ('id', 'user', 'business_name', 'business_description', 'business_registration_number', 'category', 'subcategory')
        }),
        (_('Experience'), {
            'fields': ('years_of_experience', 'rating', 'total_reviews', 'total_jobs_completed')
        }),
        (_('Location & Service Area'), {
            'fields': ('latitude', 'longitude', 'service_area')
        }),
        (_('Pricing & Availability'), {
            'fields': ('base_price', 'currency', 'is_available', 'available_from', 'available_until')
        }),
        (_('Verification & Status'), {
            'fields': ('status', 'is_verified', 'is_featured', 'response_rate', 'avg_response_time')
        }),
        (_('Contact'), {
            'fields': ('whatsapp_number',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(ProviderDocument)
class ProviderDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_name', 'provider', 'document_type', 'status', 'verified_at']
    list_filter = ['document_type', 'status', 'created_at']
    search_fields = ['provider__business_name', 'document_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        (_('Document Information'), {
            'fields': ('id', 'provider', 'document_type', 'document_name', 'document_file', 'document_number')
        }),
        (_('Expiry'), {
            'fields': ('expiry_date', 'is_expired')
        }),
        (_('Verification'), {
            'fields': ('status', 'verified_by', 'verified_at', 'rejection_reason')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ['provider', 'reviewer', 'rating', 'is_verified_purchase', 'helpful_count', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['provider__business_name', 'reviewer__phone_number', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ['provider', 'title', 'order']
    list_filter = ['created_at']
    search_fields = ['provider__business_name', 'title']
    readonly_fields = ['id', 'created_at']
    ordering = ['provider', 'order']
