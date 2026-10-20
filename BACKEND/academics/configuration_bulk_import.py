from collections import Counter

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.functions import Lower
from rest_framework import serializers

from accounts.permissions import IsSchoolAdmin
from audit.models import AuditLog
from common.bulk_excel import BulkImportConfirmBase, BulkImportPreviewBase

from .adviser_assignments import assign_section_adviser
from .models import (
    AcademicYear,
    GradeLevel,
    Section,
    Specialization,
    Strand,
    Subject,
    TeacherAssignment,
)
from .serializers import GradeLevelSerializer, SectionSerializer, TeacherAssignmentSerializer


User = get_user_model()

GRADE_LEVEL_COLUMNS = (
    ('Grade Level Name', 'name', True),
    ('Grade Level Code', 'code', True),
    ('School Level', 'school_level', True),
    ('Order', 'order', True),
)

GRADE_LEVEL_HEADER_ALIASES = {
    'gradelevelname': 'name',
    'name': 'name',
    'gradelevelcode': 'code',
    'code': 'code',
    'schoollevel': 'school_level',
    'order': 'order',
}

SECTION_COLUMNS = (
    ('Academic Year Name', 'academic_year_name', True),
    ('Grade Level Code', 'grade_level_code', True),
    ('Section Name', 'name', True),
    ('Capacity', 'capacity', True),
    ('Strand Code (Optional)', 'strand_code', False),
    ('Specialization Code (Optional)', 'specialization_code', False),
    ('Description (Optional)', 'description', False),
)

SECTION_HEADER_ALIASES = {
    'academicyearname': 'academic_year_name',
    'gradelevelcode': 'grade_level_code',
    'sectionname': 'name',
    'name': 'name',
    'capacity': 'capacity',
    'strandcode': 'strand_code',
    'specializationcode': 'specialization_code',
    'description': 'description',
}

ASSIGNMENT_COLUMNS = (
    ('Assignment Type (SUBJECT or ADVISER)', 'assignment_type', True),
    ('Teacher Username', 'teacher_username', True),
    ('Academic Year Name', 'academic_year_name', True),
    ('Grade Level Code', 'grade_level_code', True),
    ('Section Name', 'section_name', True),
    ('Subject Code (Required for SUBJECT)', 'subject_code', False),
)

ASSIGNMENT_HEADER_ALIASES = {
    'assignmenttype': 'assignment_type',
    'teacherusername': 'teacher_username',
    'academicyearname': 'academic_year_name',
    'gradelevelcode': 'grade_level_code',
    'sectionname': 'section_name',
    'subjectcode': 'subject_code',
}


def _flatten_errors(errors):
    flattened = []
    if isinstance(errors, dict):
        for field_name, messages in errors.items():
            for message in _flatten_errors(messages):
                flattened.append(f'{field_name.replace("_", " ").title()}: {message}')
    elif isinstance(errors, (list, tuple)):
        for message in errors:
            flattened.extend(_flatten_errors(message))
    else:
        flattened.append(str(errors))
    return flattened


def _whole_number(value, label, minimum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{label} must be a whole number.')
    if str(number) != value.strip():
        raise ValueError(f'{label} must be a whole number.')
    if number < minimum:
        raise ValueError(f'{label} must be at least {minimum}.')
    return number


def _casefold_index(objects, key_for):
    indexed = {}
    ambiguous = set()
    for item in objects:
        key = key_for(item)
        if key in indexed:
            ambiguous.add(key)
        else:
            indexed[key] = item
    for key in ambiguous:
        indexed.pop(key, None)
    return indexed, ambiguous


class GradeLevelImportView(BulkImportPreviewBase):
    permission_classes = [IsSchoolAdmin]
    columns = GRADE_LEVEL_COLUMNS
    required_fields = frozenset({'name', 'code', 'school_level', 'order'})
    header_aliases = GRADE_LEVEL_HEADER_ALIASES
    numeric_fields = frozenset({'order'})
    import_title = 'Grade Levels'
    row_label = 'Grade level'
    token_salt = 'grade-levels.bulk-registration'
    filename = 'edu-assist-grade-level-import-template.xlsx'

    def template_instructions(self):
        return [
            'All fields are required. School level must be Elementary, Junior High School, or Senior High School.',
            'Order must be a whole number greater than or equal to 1. New grade levels are active by default.',
            'Existing grade levels are never modified or reactivated by this import.',
        ]

    def review_rows(self, parsed_rows):
        counts = {
            field: Counter(
                row['values'][field].casefold()
                for row in parsed_rows if row['values'][field]
            )
            for field in ('name', 'code')
        }
        names_in_file = set(counts['name'])
        codes_in_file = set(counts['code'])
        existing_names = set(
            GradeLevel.objects.annotate(value_key=Lower('name'))
            .filter(value_key__in=names_in_file)
            .values_list('value_key', flat=True)
        )
        existing_codes = set(
            GradeLevel.objects.annotate(value_key=Lower('code'))
            .filter(value_key__in=codes_in_file)
            .values_list('value_key', flat=True)
        )

        preview_rows = []
        valid_records = []
        for row in parsed_rows:
            values = row['values']
            errors = list(row['errors'])
            try:
                order = _whole_number(values['order'], 'Order', 1)
            except ValueError as exc:
                order = None
                errors.append(str(exc))
            for field_name, label, existing in (
                ('name', 'Grade level name', existing_names),
                ('code', 'Grade level code', existing_codes),
            ):
                key = values[field_name].casefold()
                if counts[field_name][key] > 1:
                    errors.append(f'{label} appears more than once in the uploaded spreadsheet.')
                if key in existing:
                    errors.append(f'A grade level with this {label.lower()} already exists.')

            data = {
                'name': values['name'],
                'code': values['code'],
                'school_level': values['school_level'],
                'order': order,
            }
            serializer = None
            if not errors:
                serializer = GradeLevelSerializer(data=data)
                if not serializer.is_valid():
                    errors.extend(_flatten_errors(serializer.errors))
            preview_rows.append({
                'row': row['row'],
                'status': 'valid' if not errors else 'invalid',
                'summary': {
                    'name': values['name'],
                    'code': values['code'],
                    'school_level': values['school_level'],
                    'order': values['order'],
                },
                'errors': errors,
            })
            if not errors and serializer is not None:
                valid_records.append({'row': row['row'], 'data': data})
        return preview_rows, valid_records

    def persist_records(self, records, request):
        imported_rows = []
        with transaction.atomic():
            name_keys = [record['data']['name'].casefold() for record in records]
            code_keys = [record['data']['code'].casefold() for record in records]
            if (
                GradeLevel.objects.annotate(value_key=Lower('name')).filter(value_key__in=name_keys).exists()
                or GradeLevel.objects.annotate(value_key=Lower('code')).filter(value_key__in=code_keys).exists()
            ):
                raise IntegrityError('A grade level was registered after preview.')
            for record in records:
                serializer = GradeLevelSerializer(data=record['data'])
                serializer.is_valid(raise_exception=True)
                grade = serializer.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='CREATE',
                    module='academics',
                    object_type='GradeLevel',
                    object_id=str(grade.pk),
                )
                imported_rows.append(record['row'])
        return imported_rows


class GradeLevelImportConfirmView(BulkImportConfirmBase):
    permission_classes = [IsSchoolAdmin]
    importer_class = GradeLevelImportView


class GradeLevelImportTemplateView(GradeLevelImportView):
    http_method_names = ['get', 'head', 'options']


class SectionImportView(BulkImportPreviewBase):
    permission_classes = [IsSchoolAdmin]
    columns = SECTION_COLUMNS
    required_fields = frozenset({'academic_year_name', 'grade_level_code', 'name', 'capacity'})
    header_aliases = SECTION_HEADER_ALIASES
    numeric_fields = frozenset({'capacity'})
    import_title = 'Sections'
    row_label = 'Section'
    token_salt = 'sections.bulk-registration'
    filename = 'edu-assist-section-import-template.xlsx'

    def template_instructions(self):
        return [
            'All fields except strand, specialization, and description are required. Capacity must be a positive whole number.',
            'Academic year name and grade-level code must match existing active records. Each section name is unique within its grade level and academic year.',
            'Senior high school sections require an existing active strand. TVL sections also require an active specialization belonging to that strand.',
            'Advisers are intentionally excluded; import adviser assignments through the teacher-assignment workflow.',
            'This import creates sections only. It does not change, archive, or move historical sections.',
        ]

    def review_rows(self, parsed_rows):
        year_keys = {row['values']['academic_year_name'].casefold() for row in parsed_rows if row['values']['academic_year_name']}
        grade_keys = {row['values']['grade_level_code'].casefold() for row in parsed_rows if row['values']['grade_level_code']}
        strand_keys = {row['values']['strand_code'].casefold() for row in parsed_rows if row['values']['strand_code']}

        years, ambiguous_years = _casefold_index(
            AcademicYear.objects.filter(is_active=True)
            .annotate(value_key=Lower('name'))
            .filter(value_key__in=year_keys),
            lambda item: item.name.casefold(),
        )
        grades, ambiguous_grades = _casefold_index(
            GradeLevel.objects.filter(is_active=True)
            .annotate(value_key=Lower('code'))
            .filter(value_key__in=grade_keys),
            lambda item: item.code.casefold(),
        )
        strands, ambiguous_strands = _casefold_index(
            Strand.objects.filter(is_active=True)
            .annotate(value_key=Lower('code'))
            .filter(value_key__in=strand_keys),
            lambda item: item.code.casefold(),
        )

        resolved = {}
        specialization_code_keys = set()
        resolved_strand_ids = set()
        for row in parsed_rows:
            values = row['values']
            year = years.get(values['academic_year_name'].casefold())
            grade = grades.get(values['grade_level_code'].casefold())
            strand = strands.get(values['strand_code'].casefold()) if values['strand_code'] else None
            if strand:
                resolved_strand_ids.add(strand.pk)
            if values['specialization_code']:
                specialization_code_keys.add(values['specialization_code'].casefold())
            resolved[row['row']] = (year, grade, strand, None)

        specialization_matches, ambiguous_specializations = _casefold_index(
            Specialization.objects.filter(
                strand_id__in=resolved_strand_ids,
                is_active=True,
            ).annotate(value_key=Lower('code')).filter(value_key__in=specialization_code_keys),
            lambda item: (item.strand_id, item.code.casefold()),
        )
        for row in parsed_rows:
            year, grade, strand, _ = resolved[row['row']]
            code = row['values']['specialization_code']
            specialization = (
                specialization_matches.get((strand.pk, code.casefold()))
                if strand and code
                else None
            )
            resolved[row['row']] = (year, grade, strand, specialization)

        year_ids = {value[0].pk for value in resolved.values() if value[0]}
        grade_ids = {value[1].pk for value in resolved.values() if value[1]}
        existing_keys = {
            (year_id, grade_id, name.casefold())
            for year_id, grade_id, name in Section.objects.filter(
                academic_year_id__in=year_ids,
                grade_level_id__in=grade_ids,
            ).values_list('academic_year_id', 'grade_level_id', 'name')
        }
        seen = Counter()
        preview_rows = []
        valid_records = []
        for row in parsed_rows:
            values = row['values']
            year, grade, strand, specialization = resolved[row['row']]
            errors = list(row['errors'])
            if year is None:
                errors.append(f'Academic year "{values["academic_year_name"]}" does not match an active academic year.')
            if grade is None:
                if values['grade_level_code'].casefold() in ambiguous_grades:
                    errors.append(f'Grade level code "{values["grade_level_code"]}" matches more than one active grade level.')
                else:
                    errors.append(f'Grade level code "{values["grade_level_code"]}" does not match an active grade level.')
            if year is None and values['academic_year_name'].casefold() in ambiguous_years:
                errors.append(f'Academic year name "{values["academic_year_name"]}" is ambiguous.')
            if values['strand_code'] and strand is None:
                if values['strand_code'].casefold() in ambiguous_strands:
                    errors.append(f'Strand code "{values["strand_code"]}" matches more than one active strand.')
                else:
                    errors.append(f'Strand code "{values["strand_code"]}" does not match an active strand.')
            if values['specialization_code'] and strand is None:
                errors.append('A specialization requires a valid strand code.')
            elif values['specialization_code'] and specialization is None:
                specialization_key = (strand.pk, values['specialization_code'].casefold())
                if specialization_key in ambiguous_specializations:
                    errors.append('The specialization code is ambiguous within the selected strand.')
                else:
                    errors.append(f'Specialization code "{values["specialization_code"]}" does not belong to the selected strand.')
            if len(values['name']) > Section._meta.get_field('name').max_length:
                errors.append(f'Section name must be at most {Section._meta.get_field("name").max_length} characters.')
            try:
                capacity = _whole_number(values['capacity'], 'Capacity', 1)
            except ValueError as exc:
                capacity = None
                errors.append(str(exc))

            key = (year.pk, grade.pk, values['name'].casefold()) if year and grade else None
            if key:
                seen[key] += 1
                if seen[key] > 1:
                    errors.append('This section name appears more than once for the same grade level and academic year in the workbook.')
                if key in existing_keys:
                    errors.append('A section with this name already exists for the selected grade level and academic year.')

            data = {
                'academic_year': year.pk if year else None,
                'grade_level': grade.pk if grade else None,
                'name': values['name'],
                'capacity': capacity,
                'description': values['description'],
                'strand': strand.pk if strand else None,
                'specialization': specialization.pk if specialization else None,
            }
            serializer = None
            if not errors:
                serializer = SectionSerializer(data=data)
                if not serializer.is_valid():
                    errors.extend(_flatten_errors(serializer.errors))
            preview_rows.append({
                'row': row['row'],
                'status': 'valid' if not errors else 'invalid',
                'summary': {
                    'academic_year': values['academic_year_name'],
                    'grade_level_code': values['grade_level_code'],
                    'name': values['name'],
                    'capacity': values['capacity'],
                    'strand_code': values['strand_code'],
                    'specialization_code': values['specialization_code'],
                },
                'errors': errors,
            })
            if not errors and serializer is not None:
                valid_records.append({'row': row['row'], 'data': data})
        return preview_rows, valid_records

    def persist_records(self, records, request):
        imported_rows = []
        with transaction.atomic():
            for record in records:
                serializer = SectionSerializer(data=record['data'])
                serializer.is_valid(raise_exception=True)
                section = serializer.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='CREATE',
                    module='academics',
                    object_type='Section',
                    object_id=str(section.pk),
                )
                imported_rows.append(record['row'])
        return imported_rows


class SectionImportConfirmView(BulkImportConfirmBase):
    permission_classes = [IsSchoolAdmin]
    importer_class = SectionImportView


class SectionImportTemplateView(SectionImportView):
    http_method_names = ['get', 'head', 'options']


class TeacherAssignmentImportView(BulkImportPreviewBase):
    permission_classes = [IsSchoolAdmin]
    columns = ASSIGNMENT_COLUMNS
    required_fields = frozenset({
        'assignment_type',
        'teacher_username',
        'academic_year_name',
        'grade_level_code',
        'section_name',
    })
    header_aliases = ASSIGNMENT_HEADER_ALIASES
    import_title = 'Teacher Assignments'
    row_label = 'Teacher assignment'
    token_salt = 'teacher-assignments.bulk-registration'
    filename = 'edu-assist-teacher-assignment-import-template.xlsx'

    def template_instructions(self):
        return [
            'Assignment type must be SUBJECT or ADVISER. Use existing active teacher usernames, academic year names, grade-level codes, and section names.',
            'A SUBJECT row requires a subject code associated with the selected grade level and section strand. An ADVISER row must leave subject code blank.',
            'Only active teachers, academic years, grade levels, sections, and subjects may be newly assigned.',
            'The import rejects existing assignments and will not replace or deactivate an existing adviser.',
            'Adviser rows are processed by the established adviser-assignment service.',
        ]

    def review_rows(self, parsed_rows):
        values_by_row = {row['row']: row['values'] for row in parsed_rows}
        teacher_keys = {values['teacher_username'].casefold() for values in values_by_row.values() if values['teacher_username']}
        year_keys = {values['academic_year_name'].casefold() for values in values_by_row.values() if values['academic_year_name']}
        grade_keys = {values['grade_level_code'].casefold() for values in values_by_row.values() if values['grade_level_code']}
        subject_keys = {values['subject_code'].casefold() for values in values_by_row.values() if values['subject_code']}

        teachers, ambiguous_teachers = _casefold_index(
            User.objects.filter(
                is_active=True,
                profile__role_name='TEACHER',
            ).annotate(value_key=Lower('username'))
            .filter(value_key__in=teacher_keys),
            lambda item: item.username.casefold(),
        )
        years, ambiguous_years = _casefold_index(
            AcademicYear.objects.filter(is_active=True)
            .annotate(value_key=Lower('name')).filter(value_key__in=year_keys),
            lambda item: item.name.casefold(),
        )
        grades, ambiguous_grades = _casefold_index(
            GradeLevel.objects.filter(is_active=True)
            .annotate(value_key=Lower('code')).filter(value_key__in=grade_keys),
            lambda item: item.code.casefold(),
        )
        subjects, ambiguous_subjects = _casefold_index(
            Subject.objects.filter(is_active=True)
            .annotate(value_key=Lower('code')).filter(value_key__in=subject_keys),
            lambda item: item.code.casefold(),
        )

        resolved = {}
        year_ids = set()
        grade_ids = set()
        for row_number, values in values_by_row.items():
            teacher = teachers.get(values['teacher_username'].casefold())
            year = years.get(values['academic_year_name'].casefold())
            grade = grades.get(values['grade_level_code'].casefold())
            subject = subjects.get(values['subject_code'].casefold()) if values['subject_code'] else None
            if year:
                year_ids.add(year.pk)
            if grade:
                grade_ids.add(grade.pk)
            resolved[row_number] = (teacher, year, grade, subject)

        sections = {}
        ambiguous_sections = set()
        if year_ids and grade_ids:
            for section in Section.objects.filter(
                    is_active=True,
                    academic_year__is_active=True,
                    grade_level__is_active=True,
                    academic_year_id__in=year_ids,
                    grade_level_id__in=grade_ids,
                ).select_related('academic_year', 'grade_level', 'strand', 'adviser'):
                key = (section.academic_year_id, section.grade_level_id, section.name.casefold())
                if key in sections:
                    ambiguous_sections.add(key)
                    sections.pop(key)
                elif key not in ambiguous_sections:
                    sections[key] = section

        existing_assignments = list(
            TeacherAssignment.objects.filter(
                is_active=True,
                academic_year_id__in=year_ids,
                grade_level_id__in=grade_ids,
            ).values_list(
                'teacher_id', 'academic_year_id', 'grade_level_id', 'section_id',
                'subject_id', 'assignment_type',
            )
        )
        existing_subject_keys = {
            row[:5] for row in existing_assignments if row[5] == 'SUBJECT'
        }
        existing_adviser_keys = {
            (row[1], row[3]) for row in existing_assignments if row[5] == 'ADVISER'
        }

        seen_subjects = set()
        seen_advisers = set()
        preview_rows = []
        valid_records = []
        for row in parsed_rows:
            values = row['values']
            teacher, year, grade, subject = resolved[row['row']]
            errors = list(row['errors'])
            assignment_type = values['assignment_type'].upper()
            if assignment_type not in {'SUBJECT', 'ADVISER'}:
                errors.append('Assignment type must be SUBJECT or ADVISER.')
            if teacher is None:
                if values['teacher_username'].casefold() in ambiguous_teachers:
                    errors.append(f'Teacher username "{values["teacher_username"]}" is ambiguous.')
                else:
                    errors.append(f'Teacher username "{values["teacher_username"]}" does not match an active teacher account.')
            if year is None:
                if values['academic_year_name'].casefold() in ambiguous_years:
                    errors.append(f'Academic year name "{values["academic_year_name"]}" is ambiguous.')
                else:
                    errors.append(f'Academic year "{values["academic_year_name"]}" does not match an active academic year.')
            if grade is None:
                if values['grade_level_code'].casefold() in ambiguous_grades:
                    errors.append(f'Grade level code "{values["grade_level_code"]}" is ambiguous.')
                else:
                    errors.append(f'Grade level code "{values["grade_level_code"]}" does not match an active grade level.')

            section = None
            section_key = None
            if year and grade:
                section_key = (year.pk, grade.pk, values['section_name'].casefold())
                section = sections.get(section_key)
            if section is None:
                if section_key in ambiguous_sections:
                    errors.append('Section name matches more than one active section in the selected academic year and grade level.')
                else:
                    errors.append('Section name does not match an active section in the selected academic year and grade level.')

            if assignment_type == 'SUBJECT':
                if not values['subject_code']:
                    errors.append('Subject code is required for a SUBJECT assignment.')
                elif subject is None:
                    if values['subject_code'].casefold() in ambiguous_subjects:
                        errors.append(f'Subject code "{values["subject_code"]}" is ambiguous.')
                    else:
                        errors.append(f'Subject code "{values["subject_code"]}" does not match an active subject.')
            elif assignment_type == 'ADVISER':
                if values['subject_code']:
                    errors.append('ADVISER assignments must not include a subject code.')
                if section and (section.adviser_id or (year.pk, section.pk) in existing_adviser_keys):
                    errors.append('This section already has an adviser; the import will not replace an existing assignment.')

            duplicate_key = None
            if teacher and year and grade and section and assignment_type == 'SUBJECT' and subject:
                duplicate_key = (teacher.pk, year.pk, grade.pk, section.pk, subject.pk)
                if duplicate_key in existing_subject_keys:
                    errors.append('This active subject assignment already exists.')
                if duplicate_key in seen_subjects:
                    errors.append('This subject assignment appears more than once in the uploaded spreadsheet.')
                seen_subjects.add(duplicate_key)
            elif teacher and year and section and assignment_type == 'ADVISER':
                duplicate_key = (year.pk, section.pk)
                if duplicate_key in seen_advisers:
                    errors.append('This adviser assignment appears more than once for the section in the uploaded spreadsheet.')
                seen_advisers.add(duplicate_key)

            data = {
                'teacher': teacher.pk if teacher else None,
                'academic_year': year.pk if year else None,
                'grade_level': grade.pk if grade else None,
                'section': section.pk if section else None,
                'subject': subject.pk if subject and assignment_type == 'SUBJECT' else None,
                'assignment_type': assignment_type,
            }
            serializer = None
            if not errors:
                serializer = TeacherAssignmentSerializer(data=data)
                if not serializer.is_valid():
                    errors.extend(_flatten_errors(serializer.errors))

            preview_rows.append({
                'row': row['row'],
                'status': 'valid' if not errors else 'invalid',
                'summary': {
                    'assignment_type': assignment_type,
                    'teacher': values['teacher_username'],
                    'academic_year': values['academic_year_name'],
                    'grade_level_code': values['grade_level_code'],
                    'section': values['section_name'],
                    'subject_code': values['subject_code'],
                },
                'errors': errors,
            })
            if not errors and serializer is not None:
                valid_records.append({'row': row['row'], 'data': data})
        return preview_rows, valid_records

    def persist_records(self, records, request):
        imported_rows = []
        with transaction.atomic():
            for record in records:
                serializer = TeacherAssignmentSerializer(data=record['data'])
                serializer.is_valid(raise_exception=True)
                values = serializer.validated_data
                if values['assignment_type'] == 'ADVISER':
                    section = Section.objects.select_for_update().get(pk=values['section'].pk)
                    if (
                        section.adviser_id
                        or TeacherAssignment.objects.select_for_update().filter(
                            academic_year=values['academic_year'],
                            section=section,
                            assignment_type='ADVISER',
                            is_active=True,
                        ).exists()
                    ):
                        raise serializers.ValidationError({
                            'detail': 'An adviser assignment changed after preview. Refresh the preview before retrying.',
                        })
                    assignment, created = assign_section_adviser(section, values['teacher'])
                    if not created:
                        raise serializers.ValidationError({
                            'detail': 'The adviser assignment changed after preview. Refresh the preview before retrying.',
                        })
                else:
                    assignment = serializer.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='CREATE',
                    module='academics',
                    object_type='TeacherAssignment',
                    object_id=str(assignment.pk),
                )
                imported_rows.append(record['row'])
        return imported_rows


class TeacherAssignmentImportConfirmView(BulkImportConfirmBase):
    permission_classes = [IsSchoolAdmin]
    importer_class = TeacherAssignmentImportView


class TeacherAssignmentImportTemplateView(TeacherAssignmentImportView):
    http_method_names = ['get', 'head', 'options']
