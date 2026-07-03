from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Category(models.Model):
    """
    Main service categories.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='category_icons/', null=True, blank=True)
    image = models.ImageField(upload_to='category_images/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class SubCategory(models.Model):
    """
    Sub-categories under main categories.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='subcategory_icons/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = ('category', 'slug')
        verbose_name_plural = 'SubCategories'
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class ServiceProvider(models.Model):
    """
    Service provider profiles.
    """
    STATUS_CHOICES = (
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('suspended', _('Suspended')),
        ('rejected', _('Rejected')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('core.User', on_delete=models.CASCADE, related_name='service_provider')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='providers')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='providers')
    
    # Business Information
    business_name = models.CharField(max_length=255)
    business_description = models.TextField()
    business_registration_number = models.CharField(max_length=100, blank=True)
    years_of_experience = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Location
    latitude = models.FloatField()
    longitude = models.FloatField()
    service_area = models.CharField(max_length=200, help_text="e.g., Cox's Bazar City, Nearby areas")
    
    # Rating and Stats
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    total_reviews = models.IntegerField(default=0)
    total_jobs_completed = models.IntegerField(default=0)
    response_rate = models.FloatField(default=100.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    avg_response_time = models.IntegerField(default=0, help_text="In minutes")
    
    # Verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Service Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='BDT')
    
    # Availability
    is_available = models.BooleanField(default=True)
    available_from = models.TimeField(null=True, blank=True)
    available_until = models.TimeField(null=True, blank=True)
    
    # Contact
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-rating', '-total_jobs_completed']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"{self.business_name} - {self.user.phone_number}"
    
    def get_average_rating(self):
        return round(self.rating, 1)


class ProviderDocument(models.Model):
    """
    Service provider verification documents.
    """
    DOCUMENT_TYPES = (
        ('nid', _('National ID')),
        ('passport', _('Passport')),
        ('trade_license', _('Trade License')),
        ('tax_certificate', _('Tax Certificate')),
        ('certification', _('Professional Certification')),
        ('experience_letter', _('Experience Letter')),
        ('police_clearance', _('Police Clearance')),
        ('other', _('Other')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('expired', _('Expired')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to='provider_documents/')
    document_number = models.CharField(max_length=100, blank=True)
    
    # Expiry
    expiry_date = models.DateField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)
    
    # Verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('provider', 'document_type', 'document_number')
        indexes = [
            models.Index(fields=['provider', 'status']),
        ]
    
    def __str__(self):
        return f"{self.provider.business_name} - {self.get_document_type_display()}"


class ServiceReview(models.Model):
    """
    Reviews for service providers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='service_reviews')
    booking = models.OneToOneField('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='service_review')
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField(blank=True)
    
    # Review Criteria
    quality_rating = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    professionalism_rating = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    punctuality_rating = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    unhelpful_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('provider', 'reviewer', 'booking')
        indexes = [
            models.Index(fields=['provider', 'rating']),
        ]
    
    def __str__(self):
        return f"{self.provider.business_name} - {self.rating} stars"


class ServiceImage(models.Model):
    """
    Service provider portfolio images.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='provider_portfolio/')
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.provider.business_name} - Image"
