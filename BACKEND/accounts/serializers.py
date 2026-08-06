from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role_name', 'employee_id', 'department', 'phone_number', 'assigned_sections']
        read_only_fields = ['assigned_sections']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    role_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'date_joined', 'last_login', 'profile', 'role_name']
        read_only_fields = ['id', 'date_joined', 'last_login']

    def get_role_name(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.role_name if profile else 'TEACHER'


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    role_name = serializers.CharField(required=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'role_name', 'is_active']

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_role_name(self, value):
        allowed = {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'}
        if value not in allowed:
            raise serializers.ValidationError('Unsupported role.')
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        role_name = validated_data.pop('role_name')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role_name': role_name})
        profile.role_name = role_name
        profile.save(update_fields=['role_name'])
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(required=False, allow_blank=False, write_only=True)
    username = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'role_name']

    def validate_username(self, value):
        if self.instance and User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        if not self.instance and User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_email(self, value):
        if value and self.instance and User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        if value and not self.instance and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_role_name(self, value):
        allowed = {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'}
        if value not in allowed:
            raise serializers.ValidationError('Unsupported role.')
        return value

    def update(self, instance, validated_data):
        role_name = validated_data.pop('role_name', None)
        user = super().update(instance, validated_data)
        if role_name is not None:
            profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role_name': role_name})
            profile.role_name = role_name
            profile.save(update_fields=['role_name'])
        return user
