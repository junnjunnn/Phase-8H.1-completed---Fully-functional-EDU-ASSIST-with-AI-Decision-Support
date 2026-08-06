from django.contrib import admin
from .models import AcademicYear, GradeLevel, Section, Strand, Subject, Enrollment, AcademicRecord


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'school_level', 'order', 'is_active')
    list_filter = ('school_level', 'is_active')
    search_fields = ('name', 'code')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade_level', 'academic_year', 'is_active')
    list_filter = ('academic_year', 'grade_level', 'is_active')
    search_fields = ('name',)


@admin.register(Strand)
class StrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'grade_level', 'strand', 'is_active')
    list_filter = ('category', 'grade_level', 'is_active')
    search_fields = ('code', 'name')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'grade_level', 'section', 'enrollment_status')
    list_filter = ('academic_year', 'grade_level', 'enrollment_status')
    search_fields = ('student__first_name', 'student__last_name', 'student__lrn')


@admin.register(AcademicRecord)
class AcademicRecordAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'subject', 'grading_period_type', 'quarter', 'semester', 'grade', 'final_grade')
    list_filter = ('academic_year', 'grading_period_type')
    search_fields = ('enrollment__student__first_name', 'enrollment__student__last_name', 'subject__name')
