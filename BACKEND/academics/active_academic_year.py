from rest_framework.exceptions import ValidationError

from .models import AcademicYear


def get_active_academic_year():
    active_years = list(AcademicYear.objects.filter(is_active=True).order_by('pk')[:2])
    if not active_years:
        raise ValidationError({
            'academic_year': 'No active academic year is configured. Ask an administrator to activate one in Academic Year Management.',
        })
    if len(active_years) > 1:
        raise ValidationError({
            'academic_year': 'More than one active academic year is configured. Ask an administrator to leave exactly one active in Academic Year Management.',
        })
    active_year = active_years[0]
    if active_year.start_date >= active_year.end_date:
        raise ValidationError({
            'academic_year': 'The active academic year has invalid dates. Ask an administrator to correct it in Academic Year Management.',
        })
    return active_year
