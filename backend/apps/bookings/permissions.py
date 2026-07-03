from rest_framework import permissions


class IsBookingCustomer(permissions.BasePermission):
    """
    Allow access only to the booking customer.
    """
    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user


class IsBookingProvider(permissions.BasePermission):
    """
    Allow access only to the booking provider.
    """
    def has_object_permission(self, request, view, obj):
        return obj.provider.user == request.user


class IsBookingCustomerOrProvider(permissions.BasePermission):
    """
    Allow access to booking customer or provider.
    """
    def has_object_permission(self, request, view, obj):
        return (obj.customer == request.user or
                obj.provider.user == request.user or
                request.user.is_staff)


class CanCancelBooking(permissions.BasePermission):
    """
    Allow cancellation only if booking is in cancelable state.
    """
    def has_object_permission(self, request, view, obj):
        return obj.can_be_cancelled() and (obj.customer == request.user or obj.provider.user == request.user)


class CanCompleteBooking(permissions.BasePermission):
    """
    Allow completion only by provider and if booking is in completable state.
    """
    def has_object_permission(self, request, view, obj):
        return obj.can_be_completed() and obj.provider.user == request.user


class CanAcceptBooking(permissions.BasePermission):
    """
    Allow acceptance only by provider and if booking is pending.
    """
    def has_object_permission(self, request, view, obj):
        return obj.can_be_accepted() and obj.provider and obj.provider.user == request.user
