from django.db import transaction
from django.db.models.functions import Lower
from rest_framework import serializers

from accounts.permissions import IsSchoolAdmin
from audit.models import AuditLog
from common.bulk_excel import (
    BulkImportConfirmBase,
    BulkImportPreviewBase,
)

from .models import GradeLevel, Strand, Subject
from .bulk_import_utils import (
    grade_levels_for_import,
    invalid_grade_level_code_message,
    invalid_strand_code_message,
)
from .serializers import SubjectSerializer


SUBJECT_COLUMNS = (
    ('Subject Name', 'name', True),
    ('Official Subject Code (Optional)', 'official_subject_code', False),
    ('Category', 'category', True),
    ('Subject Type (STANDARD or SCHOOL_SPECIFIC)', 'subject_type', False),
    ('Grade Level Codes (Optional; separate with semicolons)', 'grade_level_codes', False),
    ('Strand Code (Optional)', 'strand_code', False),
    ('Description (Optional)', 'description', False),
)

SUBJECT_HEADER_ALIASES = {
    'subjectname': 'name',
    'name': 'name',
    'officialsubjectcode': 'official_subject_code',
    'officialcurriculumsubjectcode': 'official_subject_code',
    'category': 'category',
    'subjecttype': 'subject_type',
    'type': 'subject_type',
    'gradelevelcodes': 'grade_level_codes',
    'strandcode': 'strand_code',
    'description': 'description',
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


def _grade_codes(value):
    codes = [code.strip() for code in value.split(';') if code.strip()]
    if len({code.casefold() for code in codes}) != len(codes):
        raise ValueError('Grade level codes must not be repeated.')
    return codes


class SubjectImportView(BulkImportPreviewBase):
    permission_classes = [IsSchoolAdmin]
    columns = SUBJECT_COLUMNS
    required_fields = frozenset({'name', 'category'})
    header_aliases = SUBJECT_HEADER_ALIASES
    ignored_headers = ('Subject Code', 'Code')
    import_title = 'Subjects'
    row_label = 'Subject'
    token_salt = 'subjects.bulk-registration'
    filename = 'edu-assist-subject-import-template.xlsx'

    def template_instructions(self):
        return [
            'EDU ASSIST generates the internal subject code automatically. Enter a school-provided code only in Official Subject Code. Duplicate-code validation applies to Senior High School subjects with overlapping grades; Elementary and Junior High School codes are outside that uniqueness scope. Any Subject Code or Code column in a legacy workbook is ignored.',
            'Required fields: subject name and category. Use one of the existing categories: Learning Area, Core, Applied, or Specialized.',
            'Subject type may be STANDARD or SCHOOL_SPECIFIC. Blank values default to STANDARD.',
            'Grade level codes must match existing active grade-level codes exactly; select a code from the dropdown and separate multiple codes with semicolons. Leave blank if the subject is not yet associated with a grade level.',
            'A strand code must match an existing active strand. Grade level and strand/category compatibility follows the existing subject rules.',
            'Only explicitly supplied associations are imported. The import does not infer curriculum mappings or overwrite existing subjects.',
            'Enter all values as text. Do not change the header row.',
        ]

    def template_column_guidance(self):
        return {
            'name': f'Required subject display name, up to {Subject._meta.get_field("name").max_length} characters.',
            'official_subject_code': f'Optional school-provided/curriculum code, up to {Subject._meta.get_field("official_subject_code").max_length} characters. This is not the system-generated Subject Code.',
            'category': 'Required. Choose Learning Area, Core, Applied, or Specialized from the dropdown.',
            'subject_type': 'Optional. Choose STANDARD or SCHOOL_SPECIFIC. Blank imports as STANDARD.',
            'grade_level_codes': 'Optional active grade-level codes separated with semicolons, for example CODE1;CODE2. Do not repeat a code. Leave blank when no grade mapping is intended.',
            'strand_code': 'Optional existing active strand code. A strand requires explicit Senior High School grade-level code(s), and every selected grade must be Senior High School.',
            'description': 'Optional free-text description.',
        }

    def template_example_rows(self):
        return [{
            'name': 'Mathematics',
            'official_subject_code': '',
            'category': 'Learning Area',
            'subject_type': 'STANDARD',
            'grade_level_codes': '',
            'strand_code': '',
            'description': 'Example subject without an assigned grade or strand mapping.',
        }]

    def template_example_note(self):
        return (
            'This sample deliberately leaves grade and strand mappings blank, so it does not depend on any reference records. '
            'Add current active grade-level and strand codes only when those associations are intended.'
        )

    def template_dropdown_choices(self):
        return {
            'subject_type': [choice[0] for choice in Subject.SUBJECT_TYPE_CHOICES],
            'category': [choice[0] for choice in Subject.CATEGORY_CHOICES],
        }

    def template_reference_choices(self):
        return {
            'grade_level_codes': GradeLevel.objects.filter(is_active=True)
            .order_by('order', 'name').values_list('code', 'name'),
            'strand_code': Strand.objects.filter(is_active=True)
            .exclude(code='').order_by('name').values_list('code', flat=True),
        }

    def review_rows(self, parsed_rows):
        grade_codes_in_file = set()
        strand_codes_in_file = set()
        parsed_grade_codes = {}
        parsed_strand_codes = {}
        for row in parsed_rows:
            try:
                codes = _grade_codes(row['values']['grade_level_codes'])
                parsed_grade_codes[row['row']] = codes
                grade_codes_in_file.update(code.casefold() for code in codes)
            except ValueError as exc:
                parsed_grade_codes[row['row']] = []
                row['errors'].append(str(exc))
            strand_code = row['values']['strand_code']
            parsed_strand_codes[row['row']] = strand_code
            if strand_code:
                strand_codes_in_file.add(strand_code.casefold())

        grades_by_code, ambiguous_grade_codes, archived_grade_codes = (
            grade_levels_for_import(grade_codes_in_file)
        )
        strands_by_code = {}
        ambiguous_strand_codes = set()
        for strand in Strand.objects.filter(is_active=True).annotate(value_key=Lower('code')).filter(value_key__in=strand_codes_in_file):
            key = strand.code.casefold()
            if key in strands_by_code:
                ambiguous_strand_codes.add(key)
                strands_by_code.pop(key)
            elif key not in ambiguous_strand_codes:
                strands_by_code[key] = strand

        preview_rows = []
        valid_records = []
        valid_official_codes = []
        available_grade_codes = None
        available_strand_codes = None
        for row in parsed_rows:
            values = row['values']
            errors = list(row['errors'])
            if len(values['name']) > Subject._meta.get_field('name').max_length:
                errors.append(f"Subject name must be at most {Subject._meta.get_field('name').max_length} characters.")

            resolved_grades = []
            for grade_code in parsed_grade_codes[row['row']]:
                grade = grades_by_code.get(grade_code.casefold())
                if grade is None:
                    if available_grade_codes is None:
                        available_grade_codes = list(
                            GradeLevel.objects.filter(is_active=True)
                            .exclude(code='')
                            .order_by('code')
                            .values_list('code', flat=True)
                        )
                    errors.append(invalid_grade_level_code_message(
                        grade_code,
                        ambiguous_grade_codes,
                        archived_grade_codes,
                        available_grade_codes,
                    ))
                else:
                    resolved_grades.append(grade)

            strand_code = parsed_strand_codes[row['row']]
            strand = strands_by_code.get(strand_code.casefold()) if strand_code else None
            if strand_code and strand is None:
                if available_strand_codes is None:
                    available_strand_codes = list(
                        Strand.objects.filter(is_active=True)
                        .exclude(code='')
                        .order_by('code')
                        .values_list('code', flat=True)
                    )
                errors.append(invalid_strand_code_message(
                    strand_code,
                    ambiguous_strand_codes,
                    available_strand_codes,
                ))
            if strand and not resolved_grades:
                errors.append('A strand association requires an explicit senior high school grade-level association.')
            if strand and resolved_grades and any(
                grade.school_level != 'Senior High School' for grade in resolved_grades
            ):
                errors.append('A strand can only be associated with senior high school grade levels.')

            serializer = None
            if not errors:
                serializer = SubjectSerializer(data={
                    'name': values['name'],
                    'official_subject_code': values['official_subject_code'],
                    'description': values['description'],
                    'subject_type': values.get('subject_type') or 'STANDARD',
                    'category': values['category'],
                    'grade_levels': [grade.pk for grade in resolved_grades],
                    'strand': strand.pk if strand else None,
                })
                if not serializer.is_valid():
                    errors.extend(_flatten_errors(serializer.errors))
                elif values['official_subject_code'] and any(
                    set(grade.pk for grade in resolved_grades if grade.school_level == 'Senior High School')
                    & previous_grade_ids
                    for previous_code, previous_grade_ids in valid_official_codes
                    if previous_code == values['official_subject_code']
                ):
                    errors.append('This official subject code is already used by another valid row for an overlapping Senior High School grade.')

            preview_rows.append({
                'row': row['row'],
                'status': 'valid' if not errors else 'invalid',
                'summary': {
                    'name': values['name'],
                    'official_subject_code': values['official_subject_code'],
                    'category': values['category'],
                    'subject_type': values.get('subject_type') or 'STANDARD',
                    'grade_level_codes': '; '.join(parsed_grade_codes[row['row']]),
                    'strand_code': strand_code,
                },
                'errors': errors,
            })
            if not errors and serializer is not None:
                valid_records.append({
                    'row': row['row'],
                    'values': values,
                    'grade_ids': [grade.pk for grade in resolved_grades],
                    'strand_id': strand.pk if strand else None,
                })
                if values['official_subject_code']:
                    valid_official_codes.append((
                        values['official_subject_code'],
                        {
                            grade.pk for grade in resolved_grades
                            if grade.school_level == 'Senior High School'
                        },
                    ))
        return preview_rows, valid_records

    def persist_records(self, records, request):
        imported_rows = []
        with transaction.atomic():
            for record in records:
                values = record['values']
                serializer = SubjectSerializer(data={
                    'name': values['name'],
                    'official_subject_code': values['official_subject_code'],
                    'description': values['description'],
                    'subject_type': values.get('subject_type') or 'STANDARD',
                    'category': values['category'],
                    'grade_levels': record['grade_ids'],
                    'strand': record['strand_id'],
                })
                serializer.is_valid(raise_exception=True)
                subject = serializer.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='CREATE',
                    module='academics',
                    object_type='Subject',
                    object_id=str(subject.pk),
                )
                imported_rows.append(record['row'])
        return imported_rows


class SubjectImportConfirmView(BulkImportConfirmBase):
    permission_classes = [IsSchoolAdmin]
    importer_class = SubjectImportView


class SubjectImportTemplateView(SubjectImportView):
    http_method_names = ['get', 'head', 'options']
