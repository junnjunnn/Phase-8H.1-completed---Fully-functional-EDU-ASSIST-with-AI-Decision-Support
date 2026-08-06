import logging

from django.contrib.auth import authenticate, get_user_model, login, logout
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from audit.models import AuditLog
from .models import UserProfile
from .permissions import IsSchoolAdmin
from .serializers import LoginSerializer, UserCreateSerializer, UserSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(username=serializer.validated_data['username'], password=serializer.validated_data['password'])
        if user is None or not user.is_active:
            AuditLog.objects.create(action='LOGIN_FAILED', module='auth', object_type='user', object_id=serializer.validated_data['username'], ip_address=self._get_client_ip(request))
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        refresh = RefreshToken.for_user(user)
        try:
            profile = user.profile
            role = profile.role_name if profile else 'NONE'
        except UserProfile.DoesNotExist:
            role = 'NONE'
        AuditLog.objects.create(action='LOGIN_SUCCESS', module='auth', object_type='user', object_id=str(user.pk), ip_address=self._get_client_ip(request))
        return Response({
            'user': {'id': user.pk, 'username': user.username, 'role': role},
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
            role = profile.role_name if profile else 'NONE'
        except UserProfile.DoesNotExist:
            role = 'NONE'
        return Response({
            'id': request.user.pk,
            'username': request.user.username,
            'role': role,
            'is_active': request.user.is_active,
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass

        logout(request)
        AuditLog.objects.create(action='LOGOUT', module='auth', object_type='user', object_id=str(request.user.pk), ip_address=self._get_client_ip(request))
        return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsSchoolAdmin]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create_user(username=serializer.validated_data['username'], password=serializer.validated_data['password'])
        role_name = serializer.validated_data.get('role_name', 'TEACHER')
        UserProfile.objects.get_or_create(user=user, defaults={'role_name': role_name})
        AuditLog.objects.create(action='USER_CREATED', module='auth', object_type='user', object_id=serializer.validated_data['username'], ip_address=self._get_client_ip(request))
        return Response({'detail': 'User created.'}, status=status.HTTP_201_CREATED)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class UserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsSchoolAdmin]


@api_view(['POST'])
@permission_classes([IsSchoolAdmin])
def activate_user(request, pk):
    user = User.objects.get(pk=pk)
    user.is_active = True
    user.save(update_fields=['is_active'])
    AuditLog.objects.create(action='ACCOUNT_ACTIVATED', module='auth', object_type='user', object_id=str(user.pk))
    return Response({'detail': 'User activated.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsSchoolAdmin])
def deactivate_user(request, pk):
    user = User.objects.get(pk=pk)
    user.is_active = False
    user.save(update_fields=['is_active'])
    AuditLog.objects.create(action='ACCOUNT_DEACTIVATED', module='auth', object_type='user', object_id=str(user.pk))
    return Response({'detail': 'User deactivated.'}, status=status.HTTP_200_OK)
