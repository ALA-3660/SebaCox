from rest_framework import serializers
from .models import Wallet, WalletTransaction, Payment, Refund, Coupon, WithdrawalRequest
from apps.core.serializers import UserSerializer


class WalletTransactionSerializer(serializers.ModelSerializer):
    """
    Wallet transaction serializer.
    """
    class Meta:
        model = WalletTransaction
        fields = ['id', 'transaction_type', 'amount', 'balance_after', 'description', 'reference_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class WalletSerializer(serializers.ModelSerializer):
    """
    Wallet serializer.
    """
    user = UserSerializer(read_only=True)
    recent_transactions = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'balance', 'currency', 'is_active', 'is_blocked',
            'total_received', 'total_spent', 'total_refunded',
            'recent_transactions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'balance', 'total_received', 'total_spent', 'total_refunded', 'created_at']
    
    def get_recent_transactions(self, obj):
        transactions = obj.transactions.all()[:10]
        return WalletTransactionSerializer(transactions, many=True).data


class CouponSerializer(serializers.ModelSerializer):
    """
    Coupon serializer.
    """
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'max_discount_amount', 'min_order_amount', 'is_active',
            'valid_from', 'valid_until'
        ]
        read_only_fields = ['id']


class PaymentSerializer(serializers.ModelSerializer):
    """
    Payment serializer.
    """
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_name', 'booking', 'amount', 'currency',
            'payment_method', 'status', 'coupon_code', 'discount_amount',
            'final_amount', 'transaction_id', 'card_brand', 'card_last_four',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'transaction_id', 'created_at']


class CreatePaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a payment.
    """
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Payment
        fields = [
            'booking', 'amount', 'payment_method', 'coupon_code',
            'card_last_four', 'card_brand', 'notes'
        ]
    
    def validate_coupon_code(self, value):
        if value:
            try:
                coupon = Coupon.objects.get(code=value)
                if not coupon.is_valid():
                    raise serializers.ValidationError("Coupon is not valid")
            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Invalid coupon code")
        return value


class RefundSerializer(serializers.ModelSerializer):
    """
    Refund serializer.
    """
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'refund_amount', 'refund_reason', 'status',
            'approved_at', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'approved_at', 'completed_at', 'created_at']


class RequestRefundSerializer(serializers.Serializer):
    """
    Serializer for requesting a refund.
    """
    payment_id = serializers.UUIDField()
    refund_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    reason = serializers.CharField()


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    """
    Withdrawal request serializer.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'user', 'user_name', 'amount', 'bank_name',
            'account_holder_name', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'created_at']


class CreateWithdrawalRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for creating withdrawal request.
    """
    class Meta:
        model = WithdrawalRequest
        fields = [
            'amount', 'bank_name', 'account_holder_name',
            'account_number', 'routing_number'
        ]
