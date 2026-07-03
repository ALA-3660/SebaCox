from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class Booking(models.Model):
    """
    Service bookings.
    """
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('on_hold', _('On Hold')),
    )
    
    BOOKING_TYPES = (
        ('one_time', _('One Time')),
        ('recurring', _('Recurring')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Users
    customer = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='bookings_as_customer')
    provider = models.ForeignKey('services.ServiceProvider', on_delete=models.SET_NULL, null=True, related_name='bookings')
    
    # Service Details
    service_category = models.ForeignKey('services.Category', on_delete=models.SET_NULL, null=True)
    service_subcategory = models.ForeignKey('services.SubCategory', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(help_text="Detailed description of the service needed")
    
    # Booking Type
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPES, default='one_time')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_updated_at = models.DateTimeField(auto_now=True)
    
    # Location
    booking_address = models.ForeignKey('core.UserAddress', on_delete=models.SET_NULL, null=True, related_name='bookings')
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Scheduling
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    preferred_time_start = models.TimeField(null=True, blank=True)
    preferred_time_end = models.TimeField(null=True, blank=True)
    
    # Pricing
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='BDT')
    
    # Additional Info
    urgency_level = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')],
        default='medium'
    )
    special_requests = models.TextField(blank=True)
    
    # Tracking
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Payment Status
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(
        max_length=20,
        choices=[('card', 'Card'), ('wallet', 'Wallet'), ('cash', 'Cash on Service'), ('bank', 'Bank Transfer')],
        default='cash'
    )
    
    # Metadata
    notes_to_provider = models.TextField(blank=True)
    notes_from_provider = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['is_paid']),
        ]
    
    def __str__(self):
        return f"Booking #{self.id} - {self.customer.phone_number}"
    
    def can_be_accepted(self):
        return self.status == 'pending'
    
    def can_be_completed(self):
        return self.status in ['accepted', 'in_progress']
    
    def can_be_cancelled(self):
        return self.status in ['pending', 'accepted']


class BookingStatusLog(models.Model):
    """
    Track booking status changes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_logs')
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'created_at']),
        ]
    
    def __str__(self):
        return f"Booking #{self.booking.id}: {self.from_status} -> {self.to_status}"


class Review(models.Model):
    """
    Customer reviews for completed bookings.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='booking_reviews')
    
    rating = models.IntegerField(validators=[MinValueValidator(1)], help_text="1-5 stars")
    title = models.CharField(max_length=200)
    comment = models.TextField(blank=True)
    
    # Detailed ratings
    quality_rating = models.IntegerField(default=5, validators=[MinValueValidator(1)])
    punctuality_rating = models.IntegerField(default=5, validators=[MinValueValidator(1)])
    professionalism_rating = models.IntegerField(default=5, validators=[MinValueValidator(1)])
    cleanliness_rating = models.IntegerField(default=5, validators=[MinValueValidator(1)], blank=True, null=True)
    
    # Media
    images = models.JSONField(default=list, blank=True)  # Array of image URLs
    
    would_recommend = models.BooleanField(default=True)
    helpful_count = models.IntegerField(default=0)
    unhelpful_count = models.IntegerField(default=0)
    
    is_verified_booking = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Review for Booking #{self.booking.id}"
    
    def get_average_rating(self):
        ratings = [
            self.quality_rating,
            self.punctuality_rating,
            self.professionalism_rating,
        ]
        if self.cleanliness_rating:
            ratings.append(self.cleanliness_rating)
        return sum(ratings) / len(ratings)
