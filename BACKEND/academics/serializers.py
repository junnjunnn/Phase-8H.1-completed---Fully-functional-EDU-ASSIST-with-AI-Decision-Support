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


class AcademicRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicRecord
        fields = ['id', 'enrollment', 'subject', 'academic_year', 'grading_period_type', 'quarter', 'semester', 'grade', 'final_grade', 'remarks', 'encoded_by']
