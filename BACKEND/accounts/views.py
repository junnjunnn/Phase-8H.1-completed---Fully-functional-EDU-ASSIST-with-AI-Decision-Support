import logging

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from audit.models import AuditLog
from .models import UserProfile
from .permissions import IsSchoolAdmin, IsAuthorizedStaff
from .serializers import LoginSerializer, UserCreateSerializer, UserSerializer, UserUpdateSerializer

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
            profile = None
            role = 'NONE'
        return Response({
            'id': request.user.pk,
            'username': request.user.username,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'role': role,
            'is_active': request.user.is_active,
            'date_joined': request.user.date_joined,
            'employee_id': profile.employee_id if profile else '',
            'department': profile.department if profile else '',
            'phone_number': profile.phone_number if profile else '',
        })

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get(request)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')

        if not request.user.check_password(current_password):
            return Response({'current_password': ['Current password is incorrect.']}, status=status.HTTP_400_BAD_REQUEST)

        if not new_password or len(new_password) < 8:
            return Response({'new_password': ['Password must be at least 8 characters long.']}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'confirm_password': ['Passwords do not match.']}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, request.user)
        except Exception as exc:
            return Response({'new_password': exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save(update_fields=['password'])
        return Response({'detail': 'Password updated.'}, status=status.HTTP_200_OK)


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
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAuthorizedStaff()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create_user(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            email=serializer.validated_data.get('email', ''),
            is_active=serializer.validated_data.get('is_active', True),
        )
        role_name = serializer.validated_data.get('role_name', 'TEACHER')
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role_name': role_name})
        profile.role_name = role_name
        profile.save(update_fields=['role_name'])
        AuditLog.objects.create(action='USER_CREATED', module='auth', object_type='user', object_id=serializer.validated_data['username'], ip_address=self._get_client_ip(request))
        return Response({'detail': 'User created.'}, status=status.HTTP_201_CREATED)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class UserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsSchoolAdmin]

    def get_serializer_class(self):
        if self.request.method in {'PUT', 'PATCH'}:
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        AuditLog.objects.create(action='UPDATE', module='auth', object_type='user', object_id=str(instance.pk), ip_address=self._get_client_ip(request))
        response_serializer = UserSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


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


@api_view(['POST'])
@permission_classes([IsSchoolAdmin])
def reset_password(request, pk):
    user = User.objects.get(pk=pk)
    new_password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    if not new_password or len(new_password) < 8:
        return Response({'password': ['Password must be at least 8 characters long.']}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({'confirm_password': ['Passwords do not match.']}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save(update_fields=['password'])
    AuditLog.objects.create(action='PASSWORD_CHANGED', module='auth', object_type='user', object_id=str(user.pk))
    return Response({'detail': 'Password updated.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthorizedStaff])
def advisers_list(request):
    """Return a small list of potential advisers filtered by role and search query.

    Query params:
      - q: search text matched against first_name, last_name, username, email
    Returns list of { id, username, first_name, last_name, full_name }
    """
    q = request.query_params.get('q', '').strip()
    allowed_roles = {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER'}
    qs = User.objects.filter(is_active=True)
    qs = qs.filter(profile__role_name__in=allowed_roles)
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q) | Q(email__icontains=q)
        )
    qs = qs.order_by('first_name', 'last_name')[:50]
    results = []
    for u in qs:
        full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username
        results.append({
            'id': u.pk,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'full_name': full_name,
        })
    return Response(results)
