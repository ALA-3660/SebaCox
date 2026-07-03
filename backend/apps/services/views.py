from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, F

from .models import Category, SubCategory, ServiceProvider, ProviderDocument, ServiceReview, ServiceImage
from .serializers import (
    CategorySerializer, SubCategorySerializer, ServiceProviderListSerializer,
    ServiceProviderDetailSerializer, CreateServiceProviderSerializer,
    UpdateServiceProviderSerializer, ProviderDocumentSerializer,
    ServiceReviewSerializer, ServiceImageSerializer
)
from .permissions import IsServiceProvider, IsProviderOwnerOrAdmin, IsApprovedServiceProvider
from apps.core.permissions import IsOwnerOrAdmin, IsAdminUser
import logging

logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve service categories.
    GET /api/v1/services/categories/
    GET /api/v1/services/categories/{id}/
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    @action(detail=True)
    def subcategories(self, request, slug=None):
        """
        Get subcategories for a category.
        """
        category = self.get_object()
        subcategories = category.subcategories.filter(is_active=True)
        serializer = SubCategorySerializer(subcategories, many=True)
        return Response(serializer.data)


class SubCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve subcategories.
    GET /api/v1/services/subcategories/
    """
    queryset = SubCategory.objects.filter(is_active=True)
    serializer_class = SubCategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name']


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """
    Service provider management.
    GET /api/v1/services/providers/
    GET /api/v1/services/providers/{id}/
    POST /api/v1/services/providers/ (create)
    """
    serializer_class = ServiceProviderListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'subcategory', 'is_available']
    search_fields = ['business_name', 'service_area']
    ordering_fields = ['rating', 'total_jobs_completed', 'created_at']
    ordering = ['-rating', '-total_jobs_completed']
    
    def get_queryset(self):
        queryset = ServiceProvider.objects.filter(status='approved', is_verified=True)
        
        # Filter by location if provided
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        radius = self.request.query_params.get('radius', 10)  # Default 10 km
        
        if latitude and longitude:
            # TODO: Implement geospatial filtering
            pass
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ServiceProviderDetailSerializer
        elif self.action == 'create':
            return CreateServiceProviderSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UpdateServiceProviderSerializer
        return ServiceProviderListSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsProviderOwnerOrAdmin]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """
        Create service provider profile.
        """
        if hasattr(request.user, 'service_provider'):
            return Response(
                {'error': 'User already has a service provider profile'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        provider = ServiceProvider.objects.create(
            user=request.user,
            **serializer.validated_data
        )
        
        return Response(
            ServiceProviderDetailSerializer(provider).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update service provider profile.
        """
        provider = self.get_object()
        self.check_object_permissions(request, provider)
        return super().update(request, *args, **kwargs)
    
    @action(detail=False)
    def my_profile(self, request):
        """
        Get current user's service provider profile.
        GET /api/v1/services/providers/my_profile/
        """
        if not hasattr(request.user, 'service_provider'):
            return Response(
                {'error': 'User does not have a service provider profile'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ServiceProviderDetailSerializer(request.user.service_provider)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """
        Upload verification documents.
        POST /api/v1/services/providers/{id}/upload_document/
        """
        provider = self.get_object()
        self.check_object_permissions(request, provider)
        
        serializer = ProviderDocumentSerializer(data=request.data)
        if serializer.is_valid():
            document = ProviderDocument.objects.create(
                provider=provider,
                **serializer.validated_data
            )
            return Response(
                ProviderDocumentSerializer(document).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        """
        Upload portfolio images.
        POST /api/v1/services/providers/{id}/upload_image/
        """
        provider = self.get_object()
        self.check_object_permissions(request, provider)
        
        serializer = ServiceImageSerializer(data=request.data)
        if serializer.is_valid():
            image = ServiceImage.objects.create(
                provider=provider,
                **serializer.validated_data
            )
            return Response(
                ServiceImageSerializer(image).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServiceReviewViewSet(viewsets.ModelViewSet):
    """
    Service provider reviews.
    """
    serializer_class = ServiceReviewSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['provider', 'rating']
    ordering_fields = ['rating', 'helpful_count', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ServiceReview.objects.select_related('provider', 'reviewer')
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsAuthenticated]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """
        Create a review for a service provider.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = ServiceReview.objects.create(
            reviewer=request.user,
            **serializer.validated_data
        )
        
        # Update provider rating
        provider = review.provider
        avg_rating = ServiceReview.objects.filter(provider=provider).aggregate(Avg('rating'))['rating__avg']
        provider.rating = round(avg_rating, 1)
        provider.total_reviews = ServiceReview.objects.filter(provider=provider).count()
        provider.save()
        
        return Response(
            ServiceReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )


class ProviderDocumentViewSet(viewsets.ModelViewSet):
    """
    Provider verification documents.
    """
    serializer_class = ProviderDocumentSerializer
    permission_classes = [IsAuthenticated, IsProviderOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['provider', 'document_type', 'status']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return ProviderDocument.objects.all()
        if hasattr(user, 'service_provider'):
            return ProviderDocument.objects.filter(provider=user.service_provider)
        return ProviderDocument.objects.none()
