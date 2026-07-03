from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, SubCategoryViewSet, ServiceProviderViewSet,
    ServiceReviewViewSet, ProviderDocumentViewSet
)

app_name = 'services'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubCategoryViewSet, basename='subcategory')
router.register(r'providers', ServiceProviderViewSet, basename='provider')
router.register(r'reviews', ServiceReviewViewSet, basename='review')
router.register(r'documents', ProviderDocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]
