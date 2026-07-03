from rest_framework import viewsets, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import User, UserAddress, Notification, Report, Setting, PhoneVerificationToken
from .serializers import (
    UserSerializer, UserRegisterSerializer, UserLoginSerializer,
    UserAddressSerializer, NotificationSerializer, ReportSerializer, SettingSerializer
)
from .permissions import IsOwnerOrAdmin, IsAdminUser, IsPhoneVerified
import logging

logger = logging.getLogger(__name__)


class UserRegisterView(views.APIView):
    """
    User registration endpoint.
    POST /api/v1/users/register/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'user': UserSerializer(user).data,
                    'message': 'User registered successfully. Please verify your phone number.'
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(views.APIView):
    """
    User login endpoint.
    POST /api/v1/users/login/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.last_login_at = timezone.now()
            user.save()
            
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(views.APIView):
    """
    Get and update user profile.
    GET /api/v1/users/profile/
    PUT /api/v1/users/profile/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAddressViewSet(viewsets.ModelViewSet):
    """
    User address management.
    CRUD operations for user addresses.
    """
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set this address as default.
        """
        address = self.get_object()
        address.is_default = True
        address.save()
        return Response({'status': 'Address set as default'})


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Notification management.
    Get user notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark notification as read.
        """
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response({'status': 'Notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Mark all notifications as read.
        """
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'status': 'All notifications marked as read'})
    
    @action(detail=False)
    def unread_count(self, request):
        """
        Get count of unread notifications.
        """
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


class ReportViewSet(viewsets.ModelViewSet):
    """
    Report management.
    Create and manage user reports/complaints.
    """
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_admin_user():
            return Report.objects.all()
        return Report.objects.filter(reported_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)


class SettingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public settings/configuration.
    """
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    permission_classes = [AllowAny]
    lookup_field = 'key'
