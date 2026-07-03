from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegisterView, UserLoginView, UserProfileView,
    UserAddressViewSet, NotificationViewSet, ReportViewSet, SettingViewSet
)

app_name = 'core'

router = DefaultRouter()
router.register(r'addresses', UserAddressViewSet, basename='address')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'settings', SettingViewSet, basename='setting')

urlpatterns = [
    # Authentication
    path('users/register/', UserRegisterView.as_view(), name='register'),
    path('users/login/', UserLoginView.as_view(), name='login'),
    path('users/profile/', UserProfileView.as_view(), name='profile'),
    
    # Router URLs
    path('', include(router.urls)),
]
