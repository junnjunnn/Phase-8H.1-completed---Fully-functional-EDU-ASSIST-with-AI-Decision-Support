from collections import Counter

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.functions import Lower
from rest_framework import serializers

from accounts.permissions import IsSchoolAdmin
from audit.models import AuditLog
from common.bulk_excel import BulkImportConfirmBase, BulkImportPreviewBase

from .active_academic_year import get_active_academic_year
from .adviser_assignments import assign_section_adviser
from .bulk_import_utils import (
    grade_levels_for_import,
    invalid_grade_level_code_message,
    invalid_strand_code_message,
)
from .models import (
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
    ('Grade Level Code', 'grade_level_code', True),
    ('Section Name', 'name', True),
    ('Capacity', 'capacity', True),
    ('Strand Code (Optional)', 'strand_code', False),
    ('Specialization Code (Optional)', 'specialization_code', False),
    ('Description (Optional)', 'description', False),
)

SECTION_HEADER_ALIASES = {
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
    ('Grade Level Code', 'grade_level_code', True),
    ('Section Name', 'section_name', True),
    ('System-generated Subject Code (Required for SUBJECT)', 'subject_code', False),
)

ASSIGNMENT_HEADER_ALIASES = {
    'assignmenttype': 'assignment_type',
    'teacherusername': 'teacher_username',
    'gradelevelcode': 'grade_level_code',
    'sectionname': 'section_name',
    'subjectcode': 'subject_code',
    'subjectcoderequiredforsubject': 'subject_code',
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
        raise ValueError(f'{label} value "{value}" must be a whole number.')
    if str(number) != value.strip():
        raise ValueError(f'{label} value "{value}" must be a whole number.')
    if number < minimum:
        raise ValueError(f'{label} value "{value}" must be at least {minimum}.')
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
    allow_empty_rows = True

    def template_instructions(self):
        return [
            'All fields are required. School level must be Elementary, Junior High School, or Senior High School.',
            'Order must be a whole number greater than or equal to 1. New grade levels are active by default.',
            'The Grade Level Code is the code for the new record and is separate from its display name.',
            'Existing grade levels are never modified or reactivated by this import.',
        ]

    def template_dropdown_choices(self):
        return {
            'school_level': [choice[0] for choice in GradeLevel.SCHOOL_LEVEL_CHOICES],
        }

    def template_column_guidance(self):
        return {
            'name': 'Display name for the new grade level. Required, 1-50 characters, and must not already exist.',
            'code': 'New unique grade-level code, up to 20 characters. It is normalized to uppercase; do not enter a display name here.',
            'school_level': 'Choose Elementary, Junior High School, or Senior High School from the dropdown.',
            'order': 'Required whole number of at least 1. Controls grade-level ordering.',
        }

    def template_example_rows(self):
        candidates = [(f'Grade Level Example {suffix}', f'EXAMPLE-GL-{suffix}') for suffix in range(1, 100)]
        name_keys = [name.casefold() for name, _ in candidates]
        code_keys = [code.casefold() for _, code in candidates]
        existing_names = set(
            GradeLevel.objects.annotate(value_key=Lower('name'))
            .filter(value_key__in=name_keys)
            .values_list('value_key', flat=True)
        )
        existing_codes = set(
            GradeLevel.objects.annotate(value_key=Lower('code'))
            .filter(value_key__in=code_keys)
            .values_list('value_key', flat=True)
        )
        for name, code in candidates:
            if name.casefold() not in existing_names and code.casefold() not in existing_codes:
                return [{
                    'name': name,
                    'code': code,
                    'school_level': 'Elementary',
                    'order': 99,
                }]
        return []

    def template_example_note(self):
        return (
            'The sample uses a school-level value accepted by the importer and a name/code not currently in use. '
            'It is illustrative only; replace it with a real grade-level name and code before import.'
        )

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
    required_fields = frozenset({'grade_level_code', 'name', 'capacity'})
    header_aliases = SECTION_HEADER_ALIASES
    numeric_fields = frozenset({'capacity'})
    import_title = 'Sections'
    row_label = 'Section'
    token_salt = 'sections.bulk-registration'
    filename = 'edu-assist-section-import-template.xlsx'

    def template_instructions(self):
        return [
            'All fields except strand, specialization, and description are required. Capacity must be a positive whole number.',
            'New sections are assigned to the single active academic year automatically. Use the existing grade-level, strand, and specialization code dropdowns where applicable. Each section name is unique within its grade level and academic year.',
            'Senior High School sections may be shared across strands; leave Strand and Specialization blank for a shared section. If a section is strand-specific, select its existing active strand code. TVL specializations apply only to strand-specific sections and must belong to the selected strand.',
            'The specialization dropdown omits codes shared by multiple active strands; enter such a code manually and select its matching strand. The server validates the pair.',
            'Advisers are intentionally excluded; import adviser assignments through the teacher-assignment workflow.',
            'This import creates sections only. It does not change, archive, or move historical sections.',
        ]

    def template_column_guidance(self):
        return {
            'grade_level_code': 'Required existing active grade-level code. Use the code dropdown, not the grade display name.',
            'name': 'Required new section name, up to 50 characters. It must be unique within the selected grade level and active academic year.',
            'capacity': 'Required positive whole number.',
            'strand_code': 'Optional for Senior High School sections; leave blank for a section shared by students from different strands. If supplied, select an existing active strand code. Elementary and Junior High School sections cannot have a strand.',
            'specialization_code': 'Optional. TVL sections assigned to a specific strand require an active specialization code belonging to that strand. A code shared by multiple strands must be typed and matched to its strand.',
            'description': 'Optional free-text description.',
        }

    def template_example_rows(self):
        try:
            active_year = get_active_academic_year()
        except serializers.ValidationError:
            return []

        grades = list(GradeLevel.objects.filter(is_active=True).order_by('order', 'name'))
        grade_counts = Counter(item.code.casefold() for item in grades)
        grade = next(
            (
                item for item in grades
                if item.school_level != 'Senior High School'
                and grade_counts[item.code.casefold()] == 1
            ),
            None,
        )
        strand = None
        specialization = None
        if grade is None:
            grade = next(
                (
                    item for item in grades
                    if item.school_level == 'Senior High School'
                    and grade_counts[item.code.casefold()] == 1
                ),
                None,
            )
            active_strands = list(
                Strand.objects.filter(is_active=True).exclude(code='').order_by('name')
            )
            strand_counts = Counter(item.code.casefold() for item in active_strands)
            strand = next(
                (item for item in active_strands if strand_counts[item.code.casefold()] == 1),
                None,
            )
            if strand and strand.code.casefold() == 'tvl':
                active_specializations = list(
                    Specialization.objects.filter(
                        strand=strand,
                        is_active=True,
                    ).exclude(code='').order_by('name')
                )
                specialization_counts = Counter(
                    item.code.casefold() for item in active_specializations
                )
                specialization = next(
                    (
                        item for item in active_specializations
                        if specialization_counts[item.code.casefold()] == 1
                    ),
                    None,
                )
            if grade is None or (
                strand and strand.code.casefold() == 'tvl' and specialization is None
            ):
                return []

        names = [f'Example {grade.name[:30]} Section {suffix}' for suffix in range(1, 100)]
        existing_names = {
            value.casefold()
            for value in Section.objects.filter(
                academic_year=active_year,
                grade_level=grade,
            ).annotate(value_key=Lower('name'))
            .filter(value_key__in=[name.casefold() for name in names])
            .values_list('value_key', flat=True)
        }
        name = next((value for value in names if value.casefold() not in existing_names), '')
        if not name:
            return []

        return [{
            'grade_level_code': grade.code,
            'name': name,
            'capacity': 30,
            'strand_code': strand.code if strand else '',
            'specialization_code': specialization.code if specialization else '',
            'description': 'Example section for the active academic year.',
        }]

    def template_example_note(self):
        return (
            'The example uses a current active grade-level reference and, where applicable, an active strand/specialization; its section name is not currently used for that grade and active academic year. '
            'If no compatible active records or active academic year are available, no sample row is generated; use the reference dropdowns and preview your workbook.'
        )

    def template_reference_choices(self):
        specialization_codes = list(
            Specialization.objects.filter(is_active=True, strand__is_active=True)
            .exclude(code='')
            .values_list('code', flat=True)
            .order_by('code')
        )
        code_counts = Counter(code.casefold() for code in specialization_codes)
        grade_levels = GradeLevel.objects.filter(is_active=True).order_by('order', 'name')
        return {
            'grade_level_code': grade_levels.values_list('code', 'name'),
            'strand_code': Strand.objects.filter(is_active=True)
            .exclude(code='').order_by('name').values_list('code', flat=True),
            'specialization_code': [
                code for code in specialization_codes if code_counts[code.casefold()] == 1
            ],
        }

    def review_rows(self, parsed_rows):
        grade_keys = {row['values']['grade_level_code'].casefold() for row in parsed_rows if row['values']['grade_level_code']}
        strand_keys = {row['values']['strand_code'].casefold() for row in parsed_rows if row['values']['strand_code']}

        try:
            active_year = get_active_academic_year()
            active_year_error = ''
        except serializers.ValidationError as exc:
            active_year = None
            active_year_error = ' '.join(_flatten_errors(exc.detail))
        grades, ambiguous_grades, archived_grades = grade_levels_for_import(grade_keys)
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
            year = active_year
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
        available_grade_codes = None
        available_strand_codes = None
        preview_rows = []
        valid_records = []
        for row in parsed_rows:
            values = row['values']
            year, grade, strand, specialization = resolved[row['row']]
            errors = list(row['errors'])
            if active_year_error:
                errors.append(active_year_error)
            if grade is None and values['grade_level_code']:
                if available_grade_codes is None:
                    available_grade_codes = list(
                        GradeLevel.objects.filter(is_active=True)
                        .exclude(code='')
                        .order_by('code')
                        .values_list('code', flat=True)
                    )
                errors.append(invalid_grade_level_code_message(
                    values['grade_level_code'],
                    ambiguous_grades,
                    archived_grades,
                    available_grade_codes,
                ))
            if values['strand_code'] and strand is None:
                if available_strand_codes is None:
                    available_strand_codes = list(
                        Strand.objects.filter(is_active=True)
                        .exclude(code='')
                        .order_by('code')
                        .values_list('code', flat=True)
                    )
                errors.append(invalid_strand_code_message(
                    values['strand_code'],
                    ambiguous_strands,
                    available_strand_codes,
                ))
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
                    'academic_year': active_year.name if active_year else None,
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
            'Assignment type must be SUBJECT or ADVISER. Elementary, Junior High School, and Senior High School are grade-level school divisions, not assignment types. Choose the grade-level code and matching section name together; duplicate section names are disambiguated by grade. New assignments use the single active academic year automatically.',
            'A SUBJECT row requires the system-generated subject code associated with the selected grade level and section strand. Do not use the official curriculum subject code here. An ADVISER row must leave subject code blank.',
            'Only active teachers, the active academic year, grade levels, sections, and subjects may be newly assigned.',
            'The import rejects existing assignments and will not replace or deactivate an existing adviser.',
            'Adviser rows are processed by the established adviser-assignment service.',
        ]

    def template_column_guidance(self):
        return {
            'assignment_type': 'Choose SUBJECT or ADVISER. The school division is determined by the selected grade level, not this value.',
            'teacher_username': 'Required username of an existing active TEACHER account. Choose a current username from the dropdown.',
            'grade_level_code': 'Required code of an existing active grade level. Choose from the dropdown.',
            'section_name': 'Required name of an existing active section in the selected grade level and active academic year. Names are resolved with the grade code.',
            'subject_code': 'Required system-generated Subject Code for SUBJECT rows; it must be active and mapped to the selected grade/section strand. Leave blank for ADVISER rows. Do not use Official Subject Code.',
        }

    def template_example_rows(self):
        try:
            active_year = get_active_academic_year()
        except serializers.ValidationError:
            return []

        sections = list(Section.objects.filter(
            is_active=True,
            academic_year=active_year,
            grade_level__is_active=True,
        ).select_related('grade_level').order_by('grade_level__order', 'name'))
        teachers = list(User.objects.filter(
            is_active=True,
            profile__role_name='TEACHER',
        ).order_by('username'))
        teacher_counts = Counter(teacher.username.casefold() for teacher in teachers)
        teacher = next(
            (
                item for item in teachers
                if teacher_counts[item.username.casefold()] == 1
            ),
            None,
        )
        if teacher is None:
            return []
        section_name_counts = Counter(
            (section.grade_level_id, section.name.casefold())
            for section in sections
        )
        existing_adviser_section_ids = set(
            TeacherAssignment.objects.filter(
                is_active=True,
                assignment_type='ADVISER',
                academic_year=active_year,
                section_id__in=[section.pk for section in sections],
            ).values_list('section_id', flat=True)
        )
        for section in sections:
            if (
                section.adviser_id
                or section.pk in existing_adviser_section_ids
                or section_name_counts[(section.grade_level_id, section.name.casefold())] > 1
            ):
                continue
            return [{
                'assignment_type': 'ADVISER',
                'teacher_username': teacher.username,
                'grade_level_code': section.grade_level.code,
                'section_name': section.name,
                'subject_code': '',
            }]
        return []

    def template_example_note(self):
        return (
            'The example uses a current active teacher and an active section without an adviser. '
            'If no active academic year, teacher, or unassigned section is available, no valid sample row can be generated from current records.'
        )

    def template_dropdown_choices(self):
        return {
            'assignment_type': [choice[0] for choice in TeacherAssignment.ASSIGNMENT_TYPE_CHOICES],
        }

    def template_reference_choices(self):
        try:
            active_year = get_active_academic_year()
        except serializers.ValidationError:
            sections = Section.objects.none()
        else:
            sections = Section.objects.filter(
                is_active=True,
                academic_year=active_year,
                grade_level__is_active=True,
            )
        grade_levels = GradeLevel.objects.filter(is_active=True).order_by('order', 'name')
        return {
            'teacher_username': User.objects.filter(
                is_active=True,
                profile__role_name='TEACHER',
            ).order_by('username').values_list('username', flat=True),
            'grade_level_code': grade_levels.values_list('code', 'name'),
            'section_name': sections.order_by('grade_level__order', 'name').values_list('name', flat=True),
            'subject_code': Subject.objects.filter(is_active=True)
            .order_by('code').values_list('code', flat=True),
        }

    def review_rows(self, parsed_rows):
        values_by_row = {row['row']: row['values'] for row in parsed_rows}
        teacher_keys = {values['teacher_username'].casefold() for values in values_by_row.values() if values['teacher_username']}
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
        try:
            active_year = get_active_academic_year()
            active_year_error = ''
        except serializers.ValidationError as exc:
            active_year = None
            active_year_error = ' '.join(_flatten_errors(exc.detail))
        grades, ambiguous_grades, archived_grades = grade_levels_for_import(grade_keys)
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
            year = active_year
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
        available_grade_codes = None
        active_subject_codes = None
        preview_rows = []
        valid_records = []
        for row in parsed_rows:
            values = row['values']
            teacher, year, grade, subject = resolved[row['row']]
            errors = list(row['errors'])
            assignment_type = values['assignment_type'].upper()
            if assignment_type not in {'SUBJECT', 'ADVISER'}:
                errors.append('Assignment type must be SUBJECT or ADVISER; school division is determined by the selected grade level.')
            if teacher is None:
                if values['teacher_username'].casefold() in ambiguous_teachers:
                    errors.append(f'Teacher username "{values["teacher_username"]}" is ambiguous.')
                else:
                    errors.append(
                        f'Teacher username "{values["teacher_username"]}" does not match an active teacher account. '
                        'Choose an exact username from the template dropdown.'
                    )
            if active_year_error:
                errors.append(active_year_error)
            if grade is None and values['grade_level_code']:
                if available_grade_codes is None:
                    available_grade_codes = list(
                        GradeLevel.objects.filter(is_active=True)
                        .exclude(code='')
                        .order_by('code')
                        .values_list('code', flat=True)
                    )
                errors.append(invalid_grade_level_code_message(
                    values['grade_level_code'],
                    ambiguous_grades,
                    archived_grades,
                    available_grade_codes,
                ))

            section = None
            section_key = None
            if year and grade:
                section_key = (year.pk, grade.pk, values['section_name'].casefold())
                section = sections.get(section_key)
            if section is None:
                if section_key in ambiguous_sections:
                    errors.append(
                        f'Section name "{values["section_name"]}" matches more than one active section '
                        'in the selected academic year and grade level.'
                    )
                else:
                    errors.append(
                        f'Section name "{values["section_name"]}" does not match an active section '
                        f'for grade code "{values["grade_level_code"]}" in the active academic year.'
                    )

            if assignment_type == 'SUBJECT':
                if not values['subject_code']:
                    errors.append('Subject code is required for a SUBJECT assignment.')
                elif subject is None:
                    if values['subject_code'].casefold() in ambiguous_subjects:
                        errors.append(f'Subject code "{values["subject_code"]}" is ambiguous.')
                    else:
                        if active_subject_codes is None:
                            active_subject_codes = list(
                                Subject.objects.filter(is_active=True)
                                .order_by('code')
                                .values_list('code', flat=True)
                            )
                        available = ', '.join(active_subject_codes) or 'none are currently configured'
                        errors.append(
                            f'Subject code "{values["subject_code"]}" does not match an active subject. '
                            f'Available active system-generated subject codes: {available}.'
                        )
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
                    'academic_year': active_year.name if active_year else None,
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
