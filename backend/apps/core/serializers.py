from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User, UserAddress, Notification, Report, Setting, DeviceToken
import phonenumbers


class UserSerializer(serializers.ModelSerializer):
    """
    User profile serializer.
    """
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'first_name', 'last_name',
            'role', 'gender', 'date_of_birth', 'profile_picture', 'bio',
            'is_phone_verified', 'is_email_verified', 'is_active',
            'rating', 'total_reviews', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'rating', 'total_reviews']


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    User registration serializer.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['phone_number', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate_phone_number(self, value):
        try:
            parsed = phonenumbers.parse(value, "BD")
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError(_("Invalid phone number format"))
        except:
            raise serializers.ValidationError(_("Invalid phone number format"))
        
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(_("This phone number is already registered"))
        
        return value
    
    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password": _("Passwords do not match")})
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    User login serializer.
    """
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("Invalid credentials"))
        
        if not user.check_password(password):
            raise serializers.ValidationError(_("Invalid credentials"))
        
        if not user.is_active:
            raise serializers.ValidationError(_("User account is inactive"))
        
        data['user'] = user
        return data


class UserAddressSerializer(serializers.ModelSerializer):
    """
    User address serializer.
    """
    class Meta:
        model = UserAddress
        fields = [
            'id', 'address_type', 'street_address', 'apartment', 'city',
            'district', 'postal_code', 'latitude', 'longitude',
            'is_default', 'label', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Notification serializer.
    """
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'is_read',
            'content_type', 'object_id', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class ReportSerializer(serializers.ModelSerializer):
    """
    Report serializer.
    """
    reported_user_details = UserSerializer(source='reported_user', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'status', 'title', 'description',
            'content_type', 'object_id', 'reported_user', 'reported_user_details',
            'resolution_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SettingSerializer(serializers.ModelSerializer):
    """
    Setting serializer.
    """
    class Meta:
        model = Setting
        fields = ['id', 'key', 'value', 'data_type']
        read_only_fields = ['id']


class DeviceTokenSerializer(serializers.ModelSerializer):
    """
    Device token serializer.
    """
    class Meta:
        model = DeviceToken
        fields = ['id', 'device_id', 'device_type', 'push_token', 'is_active']
        read_only_fields = ['id']
