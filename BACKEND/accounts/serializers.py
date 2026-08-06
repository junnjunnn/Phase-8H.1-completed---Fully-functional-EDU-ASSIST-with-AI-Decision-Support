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

    class Meta:
        model = User
        fields = ['id', 'username', 'is_active', 'date_joined', 'last_login', 'profile']
        read_only_fields = ['id', 'date_joined', 'last_login']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    role_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'role_name', 'is_active']

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_role_name(self, value):
        allowed = {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'}
        if value not in allowed:
            raise serializers.ValidationError('Unsupported role.')
        return value

    def create(self, validated_data):
        role_name = validated_data.pop('role_name')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        UserProfile.objects.create(user=user, role_name=role_name)
        return user
