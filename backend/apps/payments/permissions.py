from rest_framework import permissions


class IsWalletOwner(permissions.BasePermission):
    """
    Allow access only to the wallet owner.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsPaymentOwner(permissions.BasePermission):
    """
    Allow access only to the payment owner or admin.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class CanWithdraw(permissions.BasePermission):
    """
    Allow withdrawal only to providers with sufficient balance.
    """
    def has_permission(self, request, view):
        if not hasattr(request.user, 'service_provider'):
            return False
        if hasattr(request.user, 'wallet'):
            return request.user.wallet.balance > 0
        return False
