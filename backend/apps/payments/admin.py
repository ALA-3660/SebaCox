from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Wallet, WalletTransaction, Payment, Refund, Coupon, WithdrawalRequest


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'is_active', 'is_blocked', 'total_received', 'total_spent']
    list_filter = ['is_active', 'is_blocked', 'created_at']
    search_fields = ['user__phone_number', 'user__email']
    readonly_fields = ['id', 'total_received', 'total_spent', 'total_refunded', 'created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user__phone_number', 'reference_id']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'amount', 'payment_method', 'status', 'booking', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__phone_number', 'transaction_id', 'booking__id']
    readonly_fields = ['id', 'transaction_id', 'created_at', 'updated_at', 'completed_at']
    fieldsets = (
        (_('Payment Information'), {
            'fields': ('id', 'user', 'booking', 'amount', 'currency', 'final_amount')
        }),
        (_('Payment Method'), {
            'fields': ('payment_method', 'transaction_id', 'card_brand', 'card_last_four')
        }),
        (_('Discount'), {
            'fields': ('coupon', 'discount_amount')
        }),
        (_('Status'), {
            'fields': ('status', 'failure_reason')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['payment', 'refund_amount', 'status', 'approved_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['payment__transaction_id', 'refund_reason']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'is_active', 'valid_from', 'valid_until', 'current_usage']
    list_filter = ['is_active', 'discount_type', 'created_at']
    search_fields = ['code', 'description']
    readonly_fields = ['id', 'current_usage', 'created_at', 'updated_at']
    filter_horizontal = ['applicable_categories']
    ordering = ['-created_at']


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'bank_name', 'approved_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__phone_number', 'account_number', 'transaction_reference']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        (_('Request Information'), {
            'fields': ('id', 'user', 'amount', 'status')
        }),
        (_('Bank Details'), {
            'fields': ('bank_name', 'account_holder_name', 'account_number', 'routing_number')
        }),
        (_('Processing'), {
            'fields': ('approved_by', 'approved_at', 'completed_at', 'transaction_reference')
        }),
        (_('Notes'), {
            'fields': ('reason_for_rejection', 'admin_notes'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']
