from rest_framework import serializers

from .models import AcademicRecord, AcademicYear, Enrollment, GradeLevel, Section, Strand, Subject


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active']


class GradeLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeLevel
        fields = ['id', 'name', 'code', 'school_level', 'order', 'is_active']


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'grade_level', 'academic_year', 'name', 'adviser', 'is_active']


class StrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Strand
        fields = ['id', 'name', 'code', 'description', 'is_active']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'code', 'name', 'category', 'grade_level', 'strand', 'is_active']


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
