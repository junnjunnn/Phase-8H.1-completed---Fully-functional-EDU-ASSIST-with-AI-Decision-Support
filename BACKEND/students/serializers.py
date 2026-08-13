from rest_framework import serializers

from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    middle_name = serializers.CharField(required=False, allow_blank=True)
    suffix = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)
    guardian_name = serializers.CharField(required=False, allow_blank=True)
    parent_contact = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    current_enrollment = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'lrn', 'first_name', 'middle_name', 'last_name', 'suffix', 'gender', 'birth_date',
            'address', 'guardian_name', 'parent_contact', 'email', 'student_status', 'current_enrollment'
        ]
        extra_kwargs = {
            'lrn': {'required': True, 'allow_blank': False},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def get_current_enrollment(self, obj):
        latest_enrollment = obj.enrollments.select_related('academic_year', 'grade_level', 'section').order_by('-academic_year__start_date', '-created_at').first()
        if not latest_enrollment:
            return None

        return {
            'id': latest_enrollment.id,
            'academic_year': latest_enrollment.academic_year.name if latest_enrollment.academic_year else None,
            'grade_level': latest_enrollment.grade_level.name if latest_enrollment.grade_level else None,
            'section': latest_enrollment.section.name if latest_enrollment.section else None,
            'enrollment_status': latest_enrollment.enrollment_status,
        }

    def validate_lrn(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError('Student ID is required.')

        normalized_value = str(value).strip()
        queryset = Student.objects.filter(lrn=normalized_value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('A student with this Student ID already exists.')

        return normalized_value

    def validate_first_name(self, value):
        return value.strip() if value else value

    def validate_last_name(self, value):
        return value.strip() if value else value
