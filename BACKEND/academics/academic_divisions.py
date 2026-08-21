from django.core.exceptions import ValidationError


ACADEMIC_DIVISIONS = {
    'ELEMENTARY': 'Elementary',
    'JUNIOR_HIGH_SCHOOL': 'Junior High School',
    'SENIOR_HIGH_SCHOOL': 'Senior High School',
}


def normalize_academic_division(value):
    if value is None:
        return None
    normalized = str(value).strip().upper().replace('-', '_').replace(' ', '_')
    aliases = {
        'ELEMENTARY': 'ELEMENTARY',
        'JUNIORHS': 'JUNIOR_HIGH_SCHOOL',
        'JUNIOR_HIGH': 'JUNIOR_HIGH_SCHOOL',
        'JUNIOR_HIGH_SCHOOL': 'JUNIOR_HIGH_SCHOOL',
        'SENIORHS': 'SENIOR_HIGH_SCHOOL',
        'SENIOR_HIGH': 'SENIOR_HIGH_SCHOOL',
        'SENIOR_HIGH_SCHOOL': 'SENIOR_HIGH_SCHOOL',
    }
    canonical = aliases.get(normalized)
    if not canonical:
        raise ValidationError({'academic_division': 'Choose Elementary, Junior High School, or Senior High School.'})
    return canonical


def grade_levels_for_division(division):
    from .models import GradeLevel

    canonical = normalize_academic_division(division)
    return GradeLevel.objects.filter(
        school_level=ACADEMIC_DIVISIONS[canonical],
        is_active=True,
    ).order_by('order', 'name')


def division_for_grade_levels(grade_levels):
    school_levels = {grade.school_level for grade in grade_levels if grade}
    if len(school_levels) != 1:
        return None
    for key, label in ACADEMIC_DIVISIONS.items():
        if school_levels == {label}:
            return key
    return None
