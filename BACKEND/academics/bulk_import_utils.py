from django.db.models.functions import Lower

from .models import GradeLevel, Strand


def grade_levels_for_import(code_keys):
    active_by_code = {}
    ambiguous_active_codes = set()
    archived_codes = set()

    grades = GradeLevel.objects.annotate(value_key=Lower('code')).filter(
        value_key__in=code_keys
    )
    for grade in grades:
        key = grade.code.casefold()
        if not grade.is_active:
            archived_codes.add(key)
        elif key in active_by_code:
            ambiguous_active_codes.add(key)
            active_by_code.pop(key)
        elif key not in ambiguous_active_codes:
            active_by_code[key] = grade

    return active_by_code, ambiguous_active_codes, archived_codes


def invalid_grade_level_code_message(code, ambiguous_codes, archived_codes, available_codes=None):
    key = code.casefold()
    if key in ambiguous_codes:
        return f'Grade level code "{code}" matches more than one active grade level.'
    if key in archived_codes:
        return (
            f'Grade level code "{code}" belongs to an archived grade level. '
            'Restore that grade level before importing.'
        )
    active_codes = available_codes
    if active_codes is None:
        active_codes = list(
            GradeLevel.objects.filter(is_active=True)
            .exclude(code='')
            .order_by('code')
            .values_list('code', flat=True)
        )
    available = ', '.join(active_codes) if active_codes else 'none are currently configured'
    return (
        f'Unknown grade level code "{code}". Enter an exact active code, not the '
        f'grade-level display name. Available active codes: {available}.'
    )


def invalid_strand_code_message(code, ambiguous_codes, available_codes=None):
    active_codes = available_codes
    if active_codes is None:
        active_codes = list(
            Strand.objects.filter(is_active=True)
            .exclude(code='')
            .order_by('code')
            .values_list('code', flat=True)
        )
    available = ', '.join(active_codes) if active_codes else 'none are currently configured'
    if code.casefold() in ambiguous_codes:
        return (
            f'Strand code "{code}" matches more than one active strand. '
            f'Available active strand codes: {available}.'
        )
    return (
        f'Strand code "{code}" does not match an active strand. '
        f'Available active strand codes: {available}.'
    )
