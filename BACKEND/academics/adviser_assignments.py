from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from accounts.models import UserProfile
from .models import Section, TeacherAssignment


def _set_section_adviser(section, teacher):
    previous_adviser_id = section.adviser_id
    if previous_adviser_id == getattr(teacher, 'pk', None):
        return
    section.adviser = teacher
    section.save(update_fields=['adviser', 'updated_at'])


def _grant_adviser_section_access(section, teacher):
    profile = UserProfile.objects.filter(user=teacher).first()
    if profile:
        profile.assigned_sections.add(section)


def _deactivate(assignment):
    if assignment.is_active:
        assignment.is_active = False
        assignment.save(update_fields=['is_active', 'updated_at'])


def assign_section_adviser(section, teacher, replacing_assignment=None):
    try:
        with transaction.atomic():
            section_ids = {section.pk}
            if replacing_assignment:
                section_ids.add(replacing_assignment.section_id)

            locked_sections = {
                item.pk: item
                for item in Section.objects.select_for_update().filter(pk__in=section_ids).order_by('pk')
            }
            target_section = locked_sections.get(section.pk)
            if target_section is None:
                raise ValidationError({'section': 'The selected section no longer exists.'})

            source_assignment = None
            if replacing_assignment:
                source_assignment = TeacherAssignment.objects.select_for_update().get(
                    pk=replacing_assignment.pk,
                )
                if source_assignment.assignment_type != 'ADVISER':
                    raise ValidationError({'assignment_type': 'Only adviser assignments can be reassigned here.'})
            source_was_active = bool(source_assignment and source_assignment.is_active)

            active_target_assignments = list(
                TeacherAssignment.objects.select_for_update()
                .filter(
                    section=target_section,
                    academic_year=target_section.academic_year,
                    assignment_type='ADVISER',
                    is_active=True,
                )
                .order_by('pk')
            )
            existing_for_teacher = next(
                (item for item in active_target_assignments if item.teacher_id == teacher.pk),
                None,
            )

            if (
                source_assignment
                and source_assignment.is_active
                and source_assignment.section_id == target_section.pk
                and source_assignment.teacher_id == teacher.pk
                and existing_for_teacher
                and existing_for_teacher.pk == source_assignment.pk
            ):
                _set_section_adviser(target_section, teacher)
                _grant_adviser_section_access(target_section, teacher)
                return source_assignment, False

            for assignment in active_target_assignments:
                if assignment is not existing_for_teacher:
                    _deactivate(assignment)

            if (
                source_assignment
                and source_assignment.is_active
                and source_assignment.section_id != target_section.pk
            ):
                _deactivate(source_assignment)
                source_section = locked_sections[source_assignment.section_id]
                remaining_source_assignment = TeacherAssignment.objects.filter(
                    section=source_section,
                    academic_year=source_section.academic_year,
                    assignment_type='ADVISER',
                    is_active=True,
                ).order_by('pk').first()
                _set_section_adviser(
                    source_section,
                    remaining_source_assignment.teacher if remaining_source_assignment else None,
                )

            if existing_for_teacher:
                assignment = existing_for_teacher
                changed = bool(
                    source_was_active
                    and source_assignment
                    and source_assignment.pk != existing_for_teacher.pk
                )
            else:
                if source_assignment and source_assignment.is_active:
                    if any(item.pk == source_assignment.pk for item in active_target_assignments):
                        source_assignment.is_active = False
                    else:
                        _deactivate(source_assignment)
                assignment = TeacherAssignment.objects.create(
                    teacher=teacher,
                    academic_year=target_section.academic_year,
                    grade_level=target_section.grade_level,
                    section=target_section,
                    subject=None,
                    assignment_type='ADVISER',
                    is_active=True,
                )
                changed = True

            _set_section_adviser(target_section, assignment.teacher)
            _grant_adviser_section_access(target_section, assignment.teacher)
            return assignment, changed
    except IntegrityError as exc:
        raise ValidationError({
            'adviser': 'This adviser assignment conflicts with an existing active assignment. Refresh and try again.',
        }) from exc


def remove_section_adviser(section, teacher_id=None, clear_legacy=False):
    try:
        with transaction.atomic():
            locked_section = Section.objects.select_for_update().filter(pk=section.pk).first()
            if locked_section is None:
                raise ValidationError({'section': 'The selected section no longer exists.'})

            active_assignments = list(
                TeacherAssignment.objects.select_for_update()
                .filter(
                    section=locked_section,
                    academic_year=locked_section.academic_year,
                    assignment_type='ADVISER',
                    is_active=True,
                )
                .order_by('pk')
            )
            matches = [
                item for item in active_assignments
                if teacher_id is None or item.teacher_id == teacher_id
            ]
            for assignment in matches:
                _deactivate(assignment)

            if matches or clear_legacy:
                remaining_assignment = next(
                    (item for item in active_assignments if item not in matches),
                    None,
                )
                _set_section_adviser(
                    locked_section,
                    remaining_assignment.teacher if remaining_assignment else None,
                )
            return matches
    except IntegrityError as exc:
        raise ValidationError({
            'adviser': 'The adviser assignment could not be deactivated because of an existing conflict.',
        }) from exc
