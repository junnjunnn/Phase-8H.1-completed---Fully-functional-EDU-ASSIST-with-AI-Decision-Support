from collections import Counter

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
from .serializers import SubjectSerializer


SUBJECT_COLUMNS = (
    ('Subject Code', 'code', True),
    ('Subject Name', 'name', True),
    ('Category', 'category', True),
    ('Grade Level Codes (Optional; separate with semicolons)', 'grade_level_codes', False),
    ('Strand Code (Optional)', 'strand_code', False),
    ('Description (Optional)', 'description', False),
)

SUBJECT_HEADER_ALIASES = {
    'subjectcode': 'code',
    'code': 'code',
    'subjectname': 'name',
    'name': 'name',
    'category': 'category',
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
    required_fields = frozenset({'code', 'name', 'category'})
    header_aliases = SUBJECT_HEADER_ALIASES
    import_title = 'Subjects'
    row_label = 'Subject'
    token_salt = 'subjects.bulk-registration'
    filename = 'edu-assist-subject-import-template.xlsx'

    def template_instructions(self):
        return [
            'Required fields: subject code, subject name, and category. Use one of the existing categories: Learning Area, Core, Applied, or Specialized.',
            'Grade level codes must match existing active grade-level codes exactly; separate multiple codes with semicolons. Leave blank if the subject is not yet associated with a grade level.',
            'A strand code must match an existing active strand. Grade level and strand/category compatibility follows the existing subject rules.',
            'Only explicitly supplied associations are imported. The import does not infer curriculum mappings or overwrite existing subjects.',
            'Enter all values as text. Do not change the header row.',
        ]

    def review_rows(self, parsed_rows):
        code_counts = Counter(
            row['values']['code'].casefold()
            for row in parsed_rows
            if row['values']['code']
        )
        existing_codes = set(
            Subject.objects.annotate(value_key=Lower('code'))
            .filter(value_key__in=set(code_counts))
            .values_list('value_key', flat=True)
        )

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

        grades_by_code = {
            grade.code.casefold(): grade
            for grade in GradeLevel.objects.filter(is_active=True)
            .annotate(value_key=Lower('code'))
            .filter(value_key__in=grade_codes_in_file)
        }
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
        for row in parsed_rows:
            values = row['values']
            errors = list(row['errors'])
            code = values['code']
            if len(code) > Subject._meta.get_field('code').max_length:
                errors.append(f"Subject code must be at most {Subject._meta.get_field('code').max_length} characters.")
            if len(values['name']) > Subject._meta.get_field('name').max_length:
                errors.append(f"Subject name must be at most {Subject._meta.get_field('name').max_length} characters.")
            if code and code_counts[code.casefold()] > 1:
                errors.append('This subject code appears more than once in the uploaded spreadsheet.')
            if code and code.casefold() in existing_codes:
                errors.append('A subject with this code already exists.')

            resolved_grades = []
            for grade_code in parsed_grade_codes[row['row']]:
                grade = grades_by_code.get(grade_code.casefold())
                if grade is None:
                    errors.append(f'Grade level code "{grade_code}" does not match an existing active grade level.')
                else:
                    resolved_grades.append(grade)

            strand_code = parsed_strand_codes[row['row']]
            strand = strands_by_code.get(strand_code.casefold()) if strand_code else None
            if strand_code and strand is None:
                if strand_code.casefold() in ambiguous_strand_codes:
                    errors.append(f'Strand code "{strand_code}" matches more than one active strand.')
                else:
                    errors.append(f'Strand code "{strand_code}" does not match an existing active strand.')
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
                    'description': values['description'],
                    'category': values['category'],
                    'grade_levels': [grade.pk for grade in resolved_grades],
                    'strand': strand.pk if strand else None,
                })
                if not serializer.is_valid():
                    errors.extend(_flatten_errors(serializer.errors))

            preview_rows.append({
                'row': row['row'],
                'status': 'valid' if not errors else 'invalid',
                'summary': {
                    'code': code,
                    'name': values['name'],
                    'category': values['category'],
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
        return preview_rows, valid_records

    def persist_records(self, records, request):
        imported_rows = []
        with transaction.atomic():
            code_keys = [record['values']['code'].casefold() for record in records]
            if Subject.objects.annotate(value_key=Lower('code')).filter(value_key__in=code_keys).exists():
                raise serializers.ValidationError({
                    'detail': 'A subject code was registered after preview. Refresh the preview before retrying.',
                })

            for record in records:
                values = record['values']
                serializer = SubjectSerializer(data={
                    'name': values['name'],
                    'description': values['description'],
                    'category': values['category'],
                    'grade_levels': record['grade_ids'],
                    'strand': record['strand_id'],
                })
                serializer.is_valid(raise_exception=True)
                subject = serializer.save(code=values['code'])
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
