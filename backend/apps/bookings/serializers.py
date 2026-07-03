from rest_framework import serializers
from .models import Booking, BookingStatusLog, Review
from apps.core.serializers import UserSerializer
from apps.services.serializers import ServiceProviderListSerializer


class BookingStatusLogSerializer(serializers.ModelSerializer):
    """
    Booking status log serializer.
    """
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = BookingStatusLog
        fields = ['id', 'from_status', 'to_status', 'changed_by', 'changed_by_name', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    """
    Booking review serializer.
    """
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    reviewer_avatar = serializers.ImageField(source='reviewer.profile_picture', read_only=True)
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'booking', 'rating', 'title', 'comment',
            'quality_rating', 'punctuality_rating', 'professionalism_rating',
            'cleanliness_rating', 'would_recommend', 'helpful_count',
            'reviewer_name', 'reviewer_avatar', 'average_rating', 'created_at'
        ]
        read_only_fields = ['id', 'reviewer_name', 'reviewer_avatar', 'created_at']
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()


class BookingListSerializer(serializers.ModelSerializer):
    """
    Booking list serializer (lightweight).
    """
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    provider_name = serializers.CharField(source='provider.business_name', read_only=True)
    service_category_name = serializers.CharField(source='service_category.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'customer_name', 'provider_name', 'service_category_name',
            'status', 'total_amount', 'scheduled_date', 'scheduled_time',
            'is_paid', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Booking detail serializer (full).
    """
    customer = UserSerializer(read_only=True)
    provider = ServiceProviderListSerializer(read_only=True)
    status_logs = BookingStatusLogSerializer(many=True, read_only=True)
    review = ReviewSerializer(read_only=True)
    service_category_name = serializers.CharField(source='service_category.name', read_only=True)
    service_subcategory_name = serializers.CharField(source='service_subcategory.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'customer', 'provider', 'service_category', 'service_category_name',
            'service_subcategory', 'service_subcategory_name', 'description',
            'booking_type', 'status', 'status_logs', 'booking_address',
            'latitude', 'longitude', 'scheduled_date', 'scheduled_time',
            'preferred_time_start', 'preferred_time_end',
            'service_price', 'discount_amount', 'tax_amount', 'total_amount', 'currency',
            'urgency_level', 'special_requests', 'accepted_at', 'started_at',
            'completed_at', 'cancelled_at', 'cancellation_reason',
            'is_paid', 'payment_method', 'notes_to_provider', 'notes_from_provider',
            'review', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'customer', 'provider', 'status', 'status_logs',
            'accepted_at', 'started_at', 'completed_at', 'cancelled_at',
            'created_at', 'updated_at'
        ]


class CreateBookingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a booking.
    """
    class Meta:
        model = Booking
        fields = [
            'service_category', 'service_subcategory', 'description',
            'booking_type', 'booking_address', 'latitude', 'longitude',
            'scheduled_date', 'scheduled_time', 'preferred_time_start',
            'preferred_time_end', 'urgency_level', 'special_requests',
            'payment_method', 'notes_to_provider'
        ]
    
    def create(self, validated_data):
        # Calculate pricing
        service_price = validated_data.get('service_subcategory').category.base_price or 0
        discount_amount = 0
        tax_amount = service_price * 0.15  # 15% tax
        total_amount = service_price - discount_amount + tax_amount
        
        booking = Booking.objects.create(
            service_price=service_price,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            **validated_data
        )
        return booking


class UpdateBookingSerializer(serializers.ModelSerializer):
    """
    Serializer for updating booking details (customer side).
    """
    class Meta:
        model = Booking
        fields = [
            'description', 'scheduled_date', 'scheduled_time',
            'preferred_time_start', 'preferred_time_end',
            'urgency_level', 'special_requests', 'notes_to_provider'
        ]


class ProviderBookingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for provider to update booking (notes, etc).
    """
    class Meta:
        model = Booking
        fields = ['notes_from_provider']


class BookingAcceptSerializer(serializers.Serializer):
    """
    Serializer for accepting a booking.
    """
    notes = serializers.CharField(required=False, allow_blank=True)


class BookingCompleteSerializer(serializers.Serializer):
    """
    Serializer for completing a booking.
    """
    notes = serializers.CharField(required=False, allow_blank=True)
    completion_notes = serializers.CharField(required=False, allow_blank=True)


class BookingCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling a booking.
    """
    reason = serializers.CharField(required=True)
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
