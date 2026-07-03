from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from datetime import timedelta


class Wallet(models.Model):
    """
    User wallet for storing balance and managing funds.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('core.User', on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='BDT')
    
    # Account Status
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    
    # Statistics
    total_received = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_refunded = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.phone_number} - Balance: {self.balance}"
    
    def add_balance(self, amount, reason=''):
        """
        Add balance to wallet.
        """
        self.balance += amount
        self.total_received += amount
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            amount=amount,
            balance_after=self.balance,
            description=reason
        )
    
    def deduct_balance(self, amount, reason=''):
        """
        Deduct balance from wallet.
        """
        if self.balance < amount:
            return False
        
        self.balance -= amount
        self.total_spent += amount
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='debit',
            amount=amount,
            balance_after=self.balance,
            description=reason
        )
        return True


class WalletTransaction(models.Model):
    """
    Transaction history for wallet operations.
    """
    TRANSACTION_TYPES = (
        ('credit', _('Credit')),
        ('debit', _('Debit')),
        ('refund', _('Refund')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True)  # Booking ID, Payment ID, etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.wallet.user.phone_number} - {self.get_transaction_type_display()} {self.amount}"


class Payment(models.Model):
    """
    Payment transactions for bookings and services.
    """
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    )
    
    PAYMENT_METHODS = (
        ('card', _('Credit/Debit Card')),
        ('wallet', _('Wallet')),
        ('cash', _('Cash on Service')),
        ('bank_transfer', _('Bank Transfer')),
        ('mobile_banking', _('Mobile Banking')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='payments')
    
    # Booking Reference
    booking = models.OneToOneField('bookings.Booking', on_delete=models.SET_NULL, null=True, related_name='payment')
    
    # Amount
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='BDT')
    
    # Payment Details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Card Details (if applicable)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)
    
    # External Payment Gateway
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Discount/Coupon
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['booking']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} {self.currency}"
    
    def mark_completed(self):
        """
        Mark payment as completed.
        """
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        if self.booking:
            self.booking.is_paid = True
            self.booking.save()
    
    def mark_failed(self, reason=''):
        """
        Mark payment as failed.
        """
        self.status = 'failed'
        self.failure_reason = reason
        self.save()


class Refund(models.Model):
    """
    Refund management for payments.
    """
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('rejected', _('Rejected')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='refund')
    
    # Amount
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    refund_reason = models.TextField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Processing
    requested_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, related_name='refund_requests')
    approved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_refunds')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    gateway_refund_id = models.CharField(max_length=100, blank=True)
    
    # Notes
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Refund for Payment {self.payment.transaction_id}"


class Coupon(models.Model):
    """
    Discount coupons for promotions.
    """
    DISCOUNT_TYPES = (
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # Discount Type
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Eligibility
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    max_order_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    applicable_categories = models.ManyToManyField('services.Category', blank=True)
    
    # Usage Limits
    usage_limit = models.IntegerField(null=True, blank=True, help_text="Total usage limit")
    usage_limit_per_user = models.IntegerField(null=True, blank=True)
    current_usage = models.IntegerField(default=0)
    
    # Validity
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Metadata
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, related_name='created_coupons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.discount_value} {self.get_discount_type_display()}"
    
    def is_valid(self):
        """
        Check if coupon is valid for use.
        """
        now = timezone.now()
        return (self.is_active and
                self.valid_from <= now <= self.valid_until and
                (self.usage_limit is None or self.current_usage < self.usage_limit))
    
    def calculate_discount(self, order_amount):
        """
        Calculate discount for given order amount.
        """
        if not self.is_valid():
            return 0
        
        if order_amount < self.min_order_amount:
            return 0
        
        if self.max_order_amount and order_amount > self.max_order_amount:
            return 0
        
        if self.discount_type == 'percentage':
            discount = (order_amount * self.discount_value) / 100
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:  # fixed
            discount = min(self.discount_value, order_amount)
        
        return discount


class WithdrawalRequest(models.Model):
    """
    Provider withdrawal requests for earnings.
    """
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('rejected', _('Rejected')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Bank Details
    bank_name = models.CharField(max_length=100)
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    routing_number = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Processing
    approved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_withdrawals')
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    transaction_reference = models.CharField(max_length=100, blank=True)
    
    # Notes
    reason_for_rejection = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Withdrawal {self.id} - {self.user.phone_number}"
