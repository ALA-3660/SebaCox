from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WalletViewSet, WalletTransactionViewSet, PaymentViewSet,
    RefundViewSet, CouponViewSet, WithdrawalViewSet
)

app_name = 'payments'

router = DefaultRouter()
router.register(r'wallet', WalletViewSet, basename='wallet')
router.register(r'transactions', WalletTransactionViewSet, basename='transaction')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'withdrawals', WithdrawalViewSet, basename='withdrawal')

urlpatterns = [
    path('', include(router.urls)),
    path('refunds/', RefundViewSet.as_view({'post': 'create'}), name='refund-create'),
]
