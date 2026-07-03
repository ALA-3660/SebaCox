from rest_framework import permissions


class IsServiceProvider(permissions.BasePermission):
    """
    Allow access only to service providers.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                hasattr(request.user, 'service_provider'))


class IsProviderOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access only to the provider owner or admin.
    """
    def has_object_permission(self, request, view, obj):
        return (obj.user == request.user or
                request.user.is_staff or
                request.user.is_superuser)


class IsApprovedServiceProvider(permissions.BasePermission):
    """
    Allow access only to approved service providers.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'service_provider'):
            return request.user.service_provider.status == 'approved'
        return False
