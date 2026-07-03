from rest_framework import serializers
from .models import Category, SubCategory, ServiceProvider, ProviderDocument, ServiceReview, ServiceImage
from apps.core.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    """
    Category serializer.
    """
    subcategories_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'image', 'is_active', 'order', 'subcategories_count']
        read_only_fields = ['id']
    
    def get_subcategories_count(self, obj):
        return obj.subcategories.filter(is_active=True).count()


class SubCategorySerializer(serializers.ModelSerializer):
    """
    Sub-category serializer.
    """
    class Meta:
        model = SubCategory
        fields = ['id', 'category', 'name', 'slug', 'description', 'icon', 'is_active', 'order']
        read_only_fields = ['id']


class ServiceImageSerializer(serializers.ModelSerializer):
    """
    Service image serializer.
    """
    class Meta:
        model = ServiceImage
        fields = ['id', 'image', 'title', 'description', 'order']
        read_only_fields = ['id']


class ProviderDocumentSerializer(serializers.ModelSerializer):
    """
    Provider document serializer.
    """
    class Meta:
        model = ProviderDocument
        fields = ['id', 'document_type', 'document_name', 'document_number', 'status', 'verified_at']
        read_only_fields = ['id', 'status', 'verified_at']


class ServiceReviewSerializer(serializers.ModelSerializer):
    """
    Service review serializer.
    """
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    reviewer_avatar = serializers.ImageField(source='reviewer.profile_picture', read_only=True)
    
    class Meta:
        model = ServiceReview
        fields = [
            'id', 'provider', 'rating', 'title', 'comment',
            'quality_rating', 'professionalism_rating', 'punctuality_rating',
            'is_verified_purchase', 'helpful_count', 'reviewer_name', 'reviewer_avatar',
            'created_at'
        ]
        read_only_fields = ['id', 'reviewer_name', 'reviewer_avatar', 'created_at']


class ServiceProviderListSerializer(serializers.ModelSerializer):
    """
    Service provider list serializer (lightweight).
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'business_name', 'category', 'category_name', 'subcategory_name',
            'rating', 'total_reviews', 'total_jobs_completed',
            'service_area', 'latitude', 'longitude', 'is_available',
            'base_price', 'images', 'is_featured'
        ]
        read_only_fields = ['id', 'rating', 'total_reviews', 'total_jobs_completed']


class ServiceProviderDetailSerializer(serializers.ModelSerializer):
    """
    Service provider detail serializer (full).
    """
    user = UserSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    documents = ProviderDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'user', 'business_name', 'business_description', 'business_registration_number',
            'category', 'category_name', 'subcategory', 'subcategory_name',
            'years_of_experience', 'rating', 'total_reviews', 'total_jobs_completed',
            'response_rate', 'avg_response_time', 'status', 'is_verified', 'is_featured',
            'service_area', 'latitude', 'longitude', 'base_price', 'currency',
            'is_available', 'available_from', 'available_until', 'whatsapp_number',
            'images', 'recent_reviews', 'documents', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'rating', 'total_reviews', 'status', 'is_verified']
    
    def get_recent_reviews(self, obj):
        reviews = obj.reviews.all()[:5]
        return ServiceReviewSerializer(reviews, many=True).data


class CreateServiceProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for creating service provider profile.
    """
    class Meta:
        model = ServiceProvider
        fields = [
            'business_name', 'business_description', 'business_registration_number',
            'category', 'subcategory', 'years_of_experience',
            'latitude', 'longitude', 'service_area', 'base_price',
            'available_from', 'available_until', 'whatsapp_number'
        ]


class UpdateServiceProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for updating service provider profile.
    """
    class Meta:
        model = ServiceProvider
        fields = [
            'business_name', 'business_description', 'years_of_experience',
            'latitude', 'longitude', 'service_area', 'base_price',
            'available_from', 'available_until', 'whatsapp_number', 'is_available'
        ]
