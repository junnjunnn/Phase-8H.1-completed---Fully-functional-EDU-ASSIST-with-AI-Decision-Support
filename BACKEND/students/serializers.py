from rest_framework import serializers

from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'lrn', 'first_name', 'last_name', 'gender', 'birth_date', 'student_status']
