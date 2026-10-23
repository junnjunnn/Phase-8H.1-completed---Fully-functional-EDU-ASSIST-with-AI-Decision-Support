from collections import Counter

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models.functions import Lower

from accounts.models import UserProfile
from accounts.permissions import IsSchoolAdmin
from audit.models import AuditLog
from common.bulk_excel import (
    BulkImportConfirmBase,
    BulkImportPreviewBase,
)


User = get_user_model()

TEACHER_COLUMNS = (
    ('Username', 'username', True),
    ('First Name', 'first_name', True),
    ('Last Name', 'last_name', True),
    ('Email (Optional)', 'email', False),
    ('Employee ID (Optional)', 'employee_id', False),
    ('Department (Optional)', 'department', False),
    ('Phone Number (Optional)', 'phone_number', False),
)

TEACHER_HEADER_ALIASES = {
    'username': 'username',
    'firstname': 'first_name',
    'lastname': 'last_name',
    'email': 'email',
    'employeeid': 'employee_id',
    'department': 'department',
    'phonenumber': 'phone_number',
}

TEACHER_FIELD_LABELS = {
    'username': 'Username',
    'first_name': 'First name',
    'last_name': 'Last name',
    'email': 'Email',
    'employee_id': 'Employee ID',
    'department': 'Department',
    'phone_number': 'Phone number',
}

TEACHER_FIELD_LIMITS = {
    'username': User._meta.get_field('username').max_length,
    'first_name': User._meta.get_field('first_name').max_length,
    'last_name': User._meta.get_field('last_name').max_length,
    'email': User._meta.get_field('email').max_length,
    'employee_id': UserProfile._meta.get_field('employee_id').max_length,
    'department': UserProfile._meta.get_field('department').max_length,
    'phone_number': UserProfile._meta.get_field('phone_number').max_length,
}


def _row_errors(row, database_usernames, database_emails, database_employee_ids, file_counts):
    values = row['values']
    errors = list(row['errors'])
    for field_name, max_length in TEACHER_FIELD_LIMITS.items():
        value = values[field_name]
        if len(value) > max_length:
            errors.append(f'{TEACHER_FIELD_LABELS[field_name]} must be at most {max_length} characters.')

    if values['username']:
        try:
            User._meta.get_field('username').clean(values['username'], None)
        except DjangoValidationError as exc:
            errors.extend(exc.messages)
    if values['email']:
        try:
            validate_email(values['email'])
        except DjangoValidationError:
            errors.append('Email must be a valid email address.')

    for field_name, label, database_values in (
        ('username', 'Username', database_usernames),
        ('email', 'Email', database_emails),
        ('employee_id', 'Employee ID', database_employee_ids),
    ):
        value = values[field_name]
        key = value.casefold()
        if not value:
            continue
        if file_counts[field_name][key] > 1:
            errors.append(f'{label} appears more than once in the uploaded spreadsheet.')
        if key in database_values:
            errors.append(f'A teacher account with this {label.lower()} already exists.')
    return errors


class TeacherImportView(BulkImportPreviewBase):
    permission_classes = [IsSchoolAdmin]
    columns = TEACHER_COLUMNS
    required_fields = frozenset({'username', 'first_name', 'last_name'})
    header_aliases = TEACHER_HEADER_ALIASES
    import_title = 'Teachers'
    row_label = 'Teacher'
    token_salt = 'teachers.bulk-registration'
    filename = 'edu-assist-teacher-import-template.xlsx'

    def template_instructions(self):
        return [
            'Required fields: username, first name, and last name. Email and employee details are optional.',
            'Every imported account receives the TEACHER role and is inactive until an administrator sets a password and activates it.',
            'Do not include a password. Use the existing user-management password reset and activation workflows after review.',
            'Usernames and any supplied email address or employee ID must be unique.',
            'Enter all values as text. Do not change the header row.',
        ]

    def template_column_guidance(self):
        return {
            'username': f'Required unique account username, up to {TEACHER_FIELD_LIMITS["username"]} characters. Do not include a password.',
            'first_name': f'Required first name, up to {TEACHER_FIELD_LIMITS["first_name"]} characters.',
            'last_name': f'Required last name, up to {TEACHER_FIELD_LIMITS["last_name"]} characters.',
            'email': f'Optional valid email address, up to {TEACHER_FIELD_LIMITS["email"]} characters. Supplied values must be unique.',
            'employee_id': f'Optional employee identifier, up to {TEACHER_FIELD_LIMITS["employee_id"]} characters. Supplied values must be unique.',
            'department': f'Optional department text, up to {TEACHER_FIELD_LIMITS["department"]} characters.',
            'phone_number': f'Optional phone number as text, up to {TEACHER_FIELD_LIMITS["phone_number"]} characters.',
        }

    def template_example_rows(self):
        candidates = [f'example.teacher{suffix}' for suffix in range(1, 100)]
        existing_usernames = set(
            User.objects.annotate(value_key=Lower('username'))
            .filter(value_key__in=[value.casefold() for value in candidates])
            .values_list('value_key', flat=True)
        )
        username = next(
            (value for value in candidates if value.casefold() not in existing_usernames),
            '',
        )
        if not username:
            return []
        return [{
            'username': username,
            'first_name': 'Jordan',
            'last_name': 'Reyes',
            'email': '',
            'employee_id': '',
            'department': 'Mathematics',
            'phone_number': '',
        }]

    def template_example_note(self):
        return (
            'This example uses a username not currently registered and leaves unique optional identifiers blank. '
            'The example worksheet is never an import source; use your school-approved account details on the first worksheet.'
        )

    def review_rows(self, parsed_rows):
        file_counts = {
            field_name: Counter(
                row['values'][field_name].casefold()
                for row in parsed_rows
                if row['values'][field_name]
            )
            for field_name in ('username', 'email', 'employee_id')
        }
        username_keys = set(file_counts['username'])
        email_keys = set(file_counts['email'])
        employee_id_keys = set(file_counts['employee_id'])

        database_usernames = set(
            User.objects.annotate(value_key=Lower('username'))
            .filter(value_key__in=username_keys)
            .values_list('value_key', flat=True)
        )
        database_emails = set(
            User.objects.annotate(value_key=Lower('email'))
            .filter(value_key__in=email_keys)
            .values_list('value_key', flat=True)
        )
        database_employee_ids = set(
            UserProfile.objects.annotate(value_key=Lower('employee_id'))
            .filter(value_key__in=employee_id_keys)
            .values_list('value_key', flat=True)
        )

        preview_rows = []
        valid_records = []
        for row in parsed_rows:
            values = row['values']
            errors = _row_errors(
                row,
                database_usernames,
                database_emails,
                database_employee_ids,
                file_counts,
            )
            preview_rows.append({
                'row': row['row'],
                'status': 'valid' if not errors else 'invalid',
                'summary': {
                    'username': values['username'],
                    'name': f"{values['first_name']} {values['last_name']}".strip(),
                    'email': values['email'],
                    'employee_id': values['employee_id'],
                },
                'errors': errors,
            })
            if not errors:
                valid_records.append({'row': row['row'], 'values': values})
        return preview_rows, valid_records

    def persist_records(self, records, request):
        imported_rows = []
        with transaction.atomic():
            usernames = [record['values']['username'] for record in records]
            emails = [record['values']['email'] for record in records if record['values']['email']]
            employee_ids = [record['values']['employee_id'] for record in records if record['values']['employee_id']]
            if (
                User.objects.annotate(value_key=Lower('username')).filter(value_key__in=[value.casefold() for value in usernames]).exists()
                or User.objects.annotate(value_key=Lower('email')).filter(value_key__in=[value.casefold() for value in emails]).exists()
                or UserProfile.objects.annotate(value_key=Lower('employee_id')).filter(value_key__in=[value.casefold() for value in employee_ids]).exists()
            ):
                raise IntegrityError('A teacher identifier was registered after preview.')

            for record in records:
                values = record['values']
                user = User.objects.create_user(
                    username=values['username'],
                    first_name=values['first_name'],
                    last_name=values['last_name'],
                    email=values['email'],
                    is_active=False,
                )
                user.set_unusable_password()
                user.save(update_fields=['password'])
                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role_name': 'TEACHER'},
                )
                profile.role_name = 'TEACHER'
                profile.employee_id = values['employee_id']
                profile.department = values['department']
                profile.phone_number = values['phone_number']
                profile.save(update_fields=['role_name', 'employee_id', 'department', 'phone_number'])
                AuditLog.objects.create(
                    user=request.user,
                    action='USER_CREATED',
                    module='auth',
                    object_type='user',
                    object_id=str(user.pk),
                )
                imported_rows.append(record['row'])
        return imported_rows


class TeacherImportConfirmView(BulkImportConfirmBase):
    permission_classes = [IsSchoolAdmin]
    importer_class = TeacherImportView


class TeacherImportTemplateView(TeacherImportView):
    http_method_names = ['get', 'head', 'options']
