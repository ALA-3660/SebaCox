from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count

from .models import Booking, BookingStatusLog, Review
from .serializers import (
    BookingListSerializer, BookingDetailSerializer, CreateBookingSerializer,
    UpdateBookingSerializer, BookingAcceptSerializer, BookingCompleteSerializer,
    BookingCancelSerializer, ReviewSerializer, BookingStatusLogSerializer,
    ProviderBookingUpdateSerializer
)
from .permissions import (
    IsBookingCustomerOrProvider, IsBookingCustomer, IsBookingProvider,
    CanCancelBooking, CanCompleteBooking, CanAcceptBooking
)
from apps.core.permissions import IsAdminUser, IsPhoneVerified
import logging

logger = logging.getLogger(__name__)


class BookingViewSet(viewsets.ModelViewSet):
    """
    Booking management.
    GET /api/v1/bookings/ - List user's bookings
    POST /api/v1/bookings/ - Create booking
    GET /api/v1/bookings/{id}/ - Booking details
    """
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated, IsPhoneVerified]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_paid', 'booking_type']
    ordering_fields = ['scheduled_date', 'created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Booking.objects.all()
        
        # Show bookings where user is customer or provider
        if hasattr(user, 'service_provider'):
            return Booking.objects.filter(
                Q(customer=user) | Q(provider=user.service_provider)
            )
        return Booking.objects.filter(customer=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookingDetailSerializer
        elif self.action == 'create':
            return CreateBookingSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UpdateBookingSerializer
        return BookingListSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new booking.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking = Booking.objects.create(
            customer=request.user,
            **serializer.validated_data
        )
        
        # Log status
        BookingStatusLog.objects.create(
            booking=booking,
            from_status='',
            to_status='pending',
            changed_by=request.user,
            reason='Booking created'
        )
        
        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get booking details.
        """
        booking = self.get_object()
        self.check_object_permissions(request, booking)
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=False)
    def my_bookings(self, request):
        """
        Get current user's bookings.
        GET /api/v1/bookings/my_bookings/
        """
        bookings = self.get_queryset().filter(customer=request.user)
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def provider_bookings(self, request):
        """
        Get bookings for provider.
        GET /api/v1/bookings/provider_bookings/
        """
        if not hasattr(request.user, 'service_provider'):
            return Response(
                {'error': 'User is not a service provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bookings = Booking.objects.filter(provider=request.user.service_provider)
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept a booking (provider only).
        POST /api/v1/bookings/{id}/accept/
        """
        booking = self.get_object()
        
        if not hasattr(request.user, 'service_provider'):
            return Response(
                {'error': 'Only providers can accept bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'pending':
            return Response(
                {'error': 'Booking can only be accepted from pending status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = BookingAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking.provider = request.user.service_provider
        booking.status = 'accepted'
        booking.accepted_at = timezone.now()
        booking.save()
        
        # Log status change
        BookingStatusLog.objects.create(
            booking=booking,
            from_status='pending',
            to_status='accepted',
            changed_by=request.user,
            reason=serializer.validated_data.get('notes', '')
        )
        
        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start a booking (change to in_progress).
        POST /api/v1/bookings/{id}/start/
        """
        booking = self.get_object()
        
        if booking.provider.user != request.user:
            return Response(
                {'error': 'Only the assigned provider can start this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'accepted':
            return Response(
                {'error': 'Booking must be accepted before starting'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'in_progress'
        booking.started_at = timezone.now()
        booking.save()
        
        # Log status change
        BookingStatusLog.objects.create(
            booking=booking,
            from_status='accepted',
            to_status='in_progress',
            changed_by=request.user,
            reason='Service started'
        )
        
        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete a booking.
        POST /api/v1/bookings/{id}/complete/
        """
        booking = self.get_object()
        
        if booking.provider.user != request.user:
            return Response(
                {'error': 'Only the assigned provider can complete this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not booking.can_be_completed():
            return Response(
                {'error': 'Booking cannot be completed in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = BookingCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking.status = 'completed'
        booking.completed_at = timezone.now()
        booking.notes_from_provider = serializer.validated_data.get('completion_notes', '')
        booking.save()
        
        # Log status change
        BookingStatusLog.objects.create(
            booking=booking,
            from_status='in_progress',
            to_status='completed',
            changed_by=request.user,
            reason='Service completed'
        )
        
        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking.
        POST /api/v1/bookings/{id}/cancel/
        """
        booking = self.get_object()
        
        if not booking.can_be_cancelled():
            return Response(
                {'error': 'Booking cannot be cancelled in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if booking.customer != request.user and booking.provider.user != request.user:
            return Response(
                {'error': 'Only customer or provider can cancel booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = serializer.validated_data['reason']
        booking.save()
        
        # Log status change
        BookingStatusLog.objects.create(
            booking=booking,
            from_status=booking.status,
            to_status='cancelled',
            changed_by=request.user,
            reason=serializer.validated_data['reason']
        )
        
        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def add_notes(self, request, pk=None):
        """
        Add notes from provider.
        POST /api/v1/bookings/{id}/add_notes/
        """
        booking = self.get_object()
        
        if booking.provider.user != request.user:
            return Response(
                {'error': 'Only the provider can add notes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProviderBookingUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking.notes_from_provider = serializer.validated_data['notes_from_provider']
        booking.save()
        
        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_200_OK
        )


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Booking reviews/ratings.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['booking', 'rating']
    ordering_fields = ['rating', 'helpful_count', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(Q(reviewer=user) | Q(booking__customer=user))
    
    def create(self, request, *args, **kwargs):
        """
        Create a review for a completed booking.
        """
        booking_id = request.data.get('booking')
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if booking.customer != request.user:
            return Response(
                {'error': 'Only the booking customer can review'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'completed':
            return Response(
                {'error': 'Can only review completed bookings'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = Review.objects.create(
            reviewer=request.user,
            **serializer.validated_data
        )
        
        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )
