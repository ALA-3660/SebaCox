from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
import logging

from .models import Wallet, WalletTransaction, Payment, Refund, Coupon, WithdrawalRequest
from .serializers import (
    WalletSerializer, WalletTransactionSerializer, PaymentSerializer,
    CreatePaymentSerializer, RefundSerializer, RequestRefundSerializer,
    CouponSerializer, WithdrawalRequestSerializer, CreateWithdrawalRequestSerializer
)
from .permissions import IsWalletOwner, IsPaymentOwner, CanWithdraw
from apps.core.permissions import IsAdminUser

logger = logging.getLogger(__name__)


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Wallet management.
    GET /api/v1/payments/wallet/
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False)
    def my_wallet(self, request):
        """
        Get user's wallet.
        GET /api/v1/payments/wallet/my_wallet/
        """
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)
    
    @action(detail=False)
    def balance(self, request):
        """
        Get wallet balance.
        GET /api/v1/payments/wallet/balance/
        """
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(user=request.user)
        
        return Response({
            'balance': str(wallet.balance),
            'currency': wallet.currency,
            'is_active': wallet.is_active
        })


class WalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Wallet transaction history.
    GET /api/v1/payments/transactions/
    """
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['transaction_type']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        try:
            wallet = Wallet.objects.get(user=self.request.user)
            return WalletTransaction.objects.filter(wallet=wallet)
        except Wallet.DoesNotExist:
            return WalletTransaction.objects.none()


class PaymentViewSet(viewsets.ModelViewSet):
    """
    Payment management.
    GET /api/v1/payments/payments/
    POST /api/v1/payments/payments/ - Create payment
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePaymentSerializer
        return PaymentSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a payment.
        """
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking_id = serializer.validated_data.get('booking')
        amount = serializer.validated_data.get('amount')
        payment_method = serializer.validated_data.get('payment_method')
        
        try:
            from apps.bookings.models import Booking
            booking = Booking.objects.get(id=booking_id)
        except:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Apply coupon if provided
        coupon_code = serializer.validated_data.get('coupon_code')
        coupon = None
        discount_amount = 0
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                discount_amount = coupon.calculate_discount(amount)
            except Coupon.DoesNotExist:
                return Response(
                    {'error': 'Invalid coupon code'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        final_amount = amount - discount_amount
        
        # Create payment
        payment = Payment.objects.create(
            user=request.user,
            booking=booking,
            amount=amount,
            payment_method=payment_method,
            coupon=coupon,
            discount_amount=discount_amount,
            final_amount=final_amount,
            status='pending',
            card_last_four=serializer.validated_data.get('card_last_four', ''),
            card_brand=serializer.validated_data.get('card_brand', ''),
            notes=serializer.validated_data.get('notes', '')
        )
        
        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm/complete a payment.
        POST /api/v1/payments/payments/{id}/confirm/
        """
        payment = self.get_object()
        
        if payment.status != 'pending':
            return Response(
                {'error': 'Payment is not in pending status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process payment based on method
        if payment.payment_method == 'wallet':
            wallet = Wallet.objects.get(user=request.user)
            if wallet.balance < payment.final_amount:
                return Response(
                    {'error': 'Insufficient wallet balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            wallet.deduct_balance(payment.final_amount, f"Payment for booking {payment.booking.id}")
        
        # Mark as completed
        payment.mark_completed()
        
        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a payment.
        POST /api/v1/payments/payments/{id}/cancel/
        """
        payment = self.get_object()
        
        if payment.status != 'pending':
            return Response(
                {'error': 'Only pending payments can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = 'cancelled'
        payment.save()
        
        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK
        )


class RefundViewSet(viewsets.ViewSet):
    """
    Refund management.
    POST /api/v1/payments/refunds/ - Request refund
    """
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """
        Request a refund.
        """
        serializer = RequestRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            payment = Payment.objects.get(id=serializer.validated_data['payment_id'])
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if payment.user != request.user:
            return Response(
                {'error': 'You can only refund your own payments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if payment.status != 'completed':
            return Response(
                {'error': 'Only completed payments can be refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if serializer.validated_data['refund_amount'] > payment.final_amount:
            return Response(
                {'error': 'Refund amount cannot exceed payment amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund = Refund.objects.create(
            payment=payment,
            refund_amount=serializer.validated_data['refund_amount'],
            refund_reason=serializer.validated_data['reason'],
            requested_by=request.user,
            status='pending'
        )
        
        return Response(
            RefundSerializer(refund).data,
            status=status.HTTP_201_CREATED
        )


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Coupon management.
    GET /api/v1/payments/coupons/
    """
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'description']
    
    @action(detail=False, methods=['post'])
    def validate_coupon(self, request):
        """
        Validate a coupon code.
        POST /api/v1/payments/coupons/validate_coupon/
        """
        code = request.data.get('code')
        order_amount = request.data.get('order_amount')
        
        if not code or not order_amount:
            return Response(
                {'error': 'Code and order_amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            coupon = Coupon.objects.get(code=code)
            if not coupon.is_valid():
                return Response(
                    {'valid': False, 'error': 'Coupon is not valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            discount = coupon.calculate_discount(float(order_amount))
            return Response({
                'valid': True,
                'discount': str(discount),
                'final_amount': str(float(order_amount) - discount)
            })
        except Coupon.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Invalid coupon code'},
                status=status.HTTP_400_BAD_REQUEST
            )


class WithdrawalViewSet(viewsets.ModelViewSet):
    """
    Withdrawal request management.
    GET /api/v1/payments/withdrawals/
    POST /api/v1/payments/withdrawals/ - Create withdrawal request
    """
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAuthenticated, CanWithdraw]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return WithdrawalRequest.objects.all()
        return WithdrawalRequest.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateWithdrawalRequestSerializer
        return WithdrawalRequestSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a withdrawal request.
        """
        serializer = CreateWithdrawalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet = Wallet.objects.get(user=request.user)
        amount = serializer.validated_data['amount']
        
        if wallet.balance < amount:
            return Response(
                {'error': 'Insufficient balance for withdrawal'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        withdrawal = WithdrawalRequest.objects.create(
            user=request.user,
            **serializer.validated_data
        )
        
        return Response(
            WithdrawalRequestSerializer(withdrawal).data,
            status=status.HTTP_201_CREATED
        )
