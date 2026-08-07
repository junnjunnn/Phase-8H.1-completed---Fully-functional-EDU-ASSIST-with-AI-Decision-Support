from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import AcademicRecord, AcademicYear, Enrollment, GradeLevel, Section, Strand, Subject, TeacherAssignment


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active']

    def validate_name(self, value):
        normalized_value = (value or '').strip()
        if not normalized_value:
            raise serializers.ValidationError('Academic year is required.')
        return normalized_value

    def validate(self, attrs):
        is_active = attrs.get('is_active', getattr(self.instance, 'is_active', False))
        if is_active:
            queryset = AcademicYear.objects.filter(is_active=True)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({'is_active': 'Only one academic year can be active at a time.'})
        return attrs


class GradeLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeLevel
        fields = ['id', 'name', 'code', 'school_level', 'order', 'is_active']

    def validate_name(self, value):
        normalized_value = (value or '').strip()
        if not normalized_value:
            raise serializers.ValidationError('Grade level name is required.')
        return normalized_value

    def validate_code(self, value):
        normalized_value = (value or '').strip().upper()
        if not normalized_value:
            raise serializers.ValidationError('Grade level code is required.')
        queryset = GradeLevel.objects.filter(code=normalized_value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A grade level with this code already exists.')
        return normalized_value


class SectionSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    academic_year_name = serializers.SerializerMethodField()
    grade_level_name = serializers.SerializerMethodField()
    adviser_name = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ['id', 'grade_level', 'academic_year', 'name', 'capacity', 'description', 'adviser', 'is_active', 'student_count', 'academic_year_name', 'grade_level_name', 'adviser_name']
        validators = [
            UniqueTogetherValidator(
                queryset=Section.objects.all(),
                fields=('grade_level', 'academic_year', 'name'),
                message='A section with this name already exists in the selected grade level and academic year.',
            )
        ]

    def get_student_count(self, obj):
        return obj.enrollments.filter(enrollment_status='active').count()

    def get_academic_year_name(self, obj):
        return obj.academic_year.name if obj.academic_year else None

    def get_grade_level_name(self, obj):
        return obj.grade_level.name if obj.grade_level else None

    def get_adviser_name(self, obj):
        if not obj.adviser:
            return None
        return f"{obj.adviser.first_name} {obj.adviser.last_name}".strip() or obj.adviser.username

    def validate_name(self, value):
        normalized_value = (value or '').strip()
        if not normalized_value:
            raise serializers.ValidationError('Section name is required.')
        return normalized_value

    def validate(self, attrs):
        grade_level = attrs.get('grade_level') or getattr(self.instance, 'grade_level', None)
        academic_year = attrs.get('academic_year') or getattr(self.instance, 'academic_year', None)
        name = attrs.get('name') or getattr(self.instance, 'name', None)
        capacity = attrs.get('capacity', getattr(self.instance, 'capacity', 0))

        if grade_level and academic_year and name:
            queryset = Section.objects.filter(grade_level=grade_level, academic_year=academic_year, name=name)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError('A section with this name already exists in the selected grade level and academic year.')
        if capacity is not None and capacity < 0:
            raise serializers.ValidationError({'capacity': 'Capacity cannot be negative.'})
        return attrs


class StrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Strand
        fields = ['id', 'name', 'code', 'description', 'is_active']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'code', 'name', 'description', 'category', 'grade_level', 'strand', 'is_active']

    def validate_code(self, value):
        normalized_value = (value or '').strip().upper()
        if not normalized_value:
            raise serializers.ValidationError('Subject code is required.')
        queryset = Subject.objects.filter(code=normalized_value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A subject with this code already exists.')
        return normalized_value

    def validate_name(self, value):
        normalized_value = (value or '').strip()
        if not normalized_value:
            raise serializers.ValidationError('Subject name is required.')
        return normalized_value


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAssignment
        fields = ['id', 'teacher', 'academic_year', 'grade_level', 'section', 'subject', 'is_active']
        validators = [
            UniqueTogetherValidator(
                queryset=TeacherAssignment.objects.all(),
                fields=('teacher', 'academic_year', 'grade_level', 'section', 'subject'),
                message='This teacher assignment already exists.',
            )
        ]

    def validate(self, attrs):
        teacher = attrs.get('teacher') or getattr(self.instance, 'teacher', None)
        academic_year = attrs.get('academic_year') or getattr(self.instance, 'academic_year', None)
        grade_level = attrs.get('grade_level') or getattr(self.instance, 'grade_level', None)
        section = attrs.get('section') or getattr(self.instance, 'section', None)
        subject = attrs.get('subject') or getattr(self.instance, 'subject', None)

        if section and grade_level and section.grade_level_id != grade_level.id:
            raise serializers.ValidationError({'section': 'The selected section does not belong to the selected grade level.'})

        if not teacher:
            raise serializers.ValidationError({'teacher': 'Teacher is required.'})
        if not academic_year:
            raise serializers.ValidationError({'academic_year': 'Academic year is required.'})
        if not grade_level:
            raise serializers.ValidationError({'grade_level': 'Grade level is required.'})
        if not section:
            raise serializers.ValidationError({'section': 'Section is required.'})
        if not subject:
            raise serializers.ValidationError({'subject': 'Subject is required.'})

        if teacher and academic_year and grade_level and section and subject:
            queryset = TeacherAssignment.objects.filter(
                teacher=teacher,
                academic_year=academic_year,
                grade_level=grade_level,
                section=section,
                subject=subject,
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError('This teacher assignment already exists.')

        return attrs


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'academic_year', 'grade_level', 'section', 'strand', 'enrollment_status', 'enrollment_date']
        extra_kwargs = {
            'academic_year': {'required': True},
            'grade_level': {'required': True},
            'section': {'required': True},
            'enrollment_status': {'required': True},
        }

    def validate(self, attrs):
        student = attrs.get('student') or getattr(self.instance, 'student', None)
        academic_year = attrs.get('academic_year') or getattr(self.instance, 'academic_year', None)
        grade_level = attrs.get('grade_level') or getattr(self.instance, 'grade_level', None)
        section = attrs.get('section') or getattr(self.instance, 'section', None)

        if student and academic_year:
            queryset = Enrollment.objects.filter(student=student, academic_year=academic_year)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError('A student can only have one enrollment per academic year.')

        if section and grade_level and section.grade_level_id != grade_level.id:
            raise serializers.ValidationError({'section': 'The selected section does not belong to the selected grade level.'})

        if not section:
            raise serializers.ValidationError({'section': 'Section is required.'})

        if student and academic_year and grade_level and section:
            duplicate_enrollment = Enrollment.objects.filter(student=student, academic_year=academic_year, grade_level=grade_level, section=section)
            if self.instance:
                duplicate_enrollment = duplicate_enrollment.exclude(pk=self.instance.pk)
            if duplicate_enrollment.exists():
                raise serializers.ValidationError('This student is already enrolled in the selected section for the academic year.')

        return attrs


class AcademicRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicRecord
        fields = ['id', 'enrollment', 'subject', 'academic_year', 'grading_period_type', 'quarter', 'semester', 'grade', 'final_grade', 'remarks', 'encoded_by']

    def validate_grade(self, value):
        if value is None:
            raise serializers.ValidationError('Grade is required.')
        if value < 0:
            raise serializers.ValidationError('Grade cannot be negative.')
        if value > 100:
            raise serializers.ValidationError('Grade cannot exceed 100.')
        return value

    def validate(self, attrs):
        enrollment = attrs.get('enrollment') or getattr(self.instance, 'enrollment', None)
        subject = attrs.get('subject') or getattr(self.instance, 'subject', None)
        academic_year = attrs.get('academic_year') or getattr(self.instance, 'academic_year', None)
        grading_period_type = attrs.get('grading_period_type') or getattr(self.instance, 'grading_period_type', None)
        quarter = attrs.get('quarter') if 'quarter' in attrs else getattr(self.instance, 'quarter', None)
        semester = attrs.get('semester') if 'semester' in attrs else getattr(self.instance, 'semester', None)

        if enrollment and subject and academic_year and grading_period_type:
            queryset = AcademicRecord.objects.filter(
                enrollment=enrollment,
                subject=subject,
                academic_year=academic_year,
                grading_period_type=grading_period_type,
            )
            if quarter is not None:
                queryset = queryset.filter(quarter=quarter)
            if semester is not None:
                queryset = queryset.filter(semester=semester)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError('An academic record for this student, subject, period, and academic year already exists.')

        return attrs
