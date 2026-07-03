from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, UserAddress, Notification, Report, Setting,
    DeviceToken, EmailVerificationToken, PhoneVerificationToken
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'get_full_name', 'role', 'is_phone_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_phone_verified', 'is_email_verified', 'created_at']
    search_fields = ['phone_number', 'email', 'first_name', 'last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login_at']
    fieldsets = (
        (_('Personal Information'), {
            'fields': ('id', 'first_name', 'last_name', 'email', 'phone_number', 'gender', 'date_of_birth')
        }),
        (_('Profile'), {
            'fields': ('profile_picture', 'bio', 'rating', 'total_reviews')
        }),
        (_('Account Status'), {
            'fields': ('role', 'is_active', 'is_phone_verified', 'is_email_verified', 'is_approved')
        }),
        (_('Permissions'), {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'last_login_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address_type', 'is_default', 'city', 'created_at']
    list_filter = ['address_type', 'is_default', 'city', 'created_at']
    search_fields = ['user__phone_number', 'street_address']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__phone_number', 'title', 'message']
    readonly_fields = ['id', 'created_at', 'read_at']
    ordering = ['-created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'report_type', 'status', 'reported_by', 'reported_user', 'created_at']
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['reported_by__phone_number', 'reported_user__phone_number', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        (_('Report Information'), {
            'fields': ('id', 'report_type', 'status', 'title', 'description')
        }),
        (_('Users'), {
            'fields': ('reported_by', 'reported_user')
        }),
        (_('Reference'), {
            'fields': ('content_type', 'object_id')
        }),
        (_('Resolution'), {
            'fields': ('resolution_notes', 'resolved_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'data_type', 'value', 'updated_at']
    list_filter = ['data_type', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['key']


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'device_id', 'is_active', 'created_at']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__phone_number', 'device_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_used', 'expires_at', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__phone_number', 'token']
    readonly_fields = ['id', 'token', 'created_at']
    ordering = ['-created_at']


@admin.register(PhoneVerificationToken)
class PhoneVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'is_used', 'attempt_count', 'expires_at', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['phone_number', 'otp_code']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
