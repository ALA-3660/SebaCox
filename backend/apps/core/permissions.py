from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    """
    Allow access only to customers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'customer'


class IsProvider(permissions.BasePermission):
    """
    Allow access only to service providers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'provider'


class IsApprovedProvider(permissions.BasePermission):
    """
    Allow access only to approved service providers.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                request.user.role == 'provider' and request.user.is_approved)


class IsAdminUser(permissions.BasePermission):
    """
    Allow access only to administrators.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin_user()


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access only to the object owner or admin.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_admin_user()
        return obj == request.user or request.user.is_admin_user()


class IsPhoneVerified(permissions.BasePermission):
    """
    Allow access only to phone verified users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_phone_verified
