from __future__ import annotations

import re
from datetime import date
from typing import Any

from django.db import transaction

from academics.models import AcademicYear
from .models import SchoolCalendarDay


class PhilippineHolidayProvider:
    """Minimal provider abstraction that can be replaced by a real external source later."""

    @staticmethod
    def fetch_holidays(year: int):
        """Return a list of Philippine holiday entries for the given calendar year.

        This intentionally avoids hard-coded large holiday lists in the frontend and
        keeps the contract safe for a future real API integration.
        """
        year_str = str(year)
        return [
            {
                'date': f'{year_str}-01-01',
                'name': "New Year's Day",
                'category': 'REGULAR_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
            {
                'date': f'{year_str}-04-09',
                'name': 'Araw ng Kagitingan',
                'category': 'REGULAR_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
            {
                'date': f'{year_str}-05-01',
                'name': 'Labor Day',
                'category': 'REGULAR_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
            {
                'date': f'{year_str}-06-12',
                'name': 'Independence Day',
                'category': 'REGULAR_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
            {
                'date': f'{year_str}-08-31',
                'name': 'National Heroes Day',
                'category': 'REGULAR_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
            {
                'date': f'{year_str}-11-30',
                'name': 'Bonifacio Day',
                'category': 'REGULAR_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
            {
                'date': f'{year_str}-12-25',
                'name': 'Christmas Day',
                'category': 'REGULAR_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
            {
                'date': f'{year_str}-12-30',
                'name': 'Rizal Day',
                'category': 'REGULAR_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
            {
                'date': f'{year_str}-08-21',
                'name': 'Ninoy Aquino Day',
                'category': 'SPECIAL_NON_WORKING_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
            {
                'date': f'{year_str}-11-01',
                'name': "All Saints' Day",
                'category': 'SPECIAL_NON_WORKING_HOLIDAY',
                'class_status': 'NO_CLASSES',
            },
        ]


class PhilippineHolidayImportService:
    supported_categories = {
        'REGULAR_HOLIDAY',
        'SPECIAL_NON_WORKING_HOLIDAY',
        'LOCAL_HOLIDAY',
        'SCHOOL_HOLIDAY',
    }

    @staticmethod
    def _parse_date(raw_value):
        if not raw_value:
            return None
        if isinstance(raw_value, date):
            return raw_value
        if not isinstance(raw_value, str):
            return None
        try:
            return date.fromisoformat(raw_value)
        except ValueError:
            return None

    @staticmethod
    def _parse_year_date(raw_value):
        parsed = PhilippineHolidayImportService._parse_date(raw_value)
        if parsed:
            return parsed
        if isinstance(raw_value, str):
            try:
                return date.fromisoformat(str(raw_value).split('T', 1)[0])
            except ValueError:
                return None
        return None

    @staticmethod
    def _normalize_category(raw_category):
        if not raw_category:
            return None
        value = str(raw_category).strip().upper()
        if value in PhilippineHolidayImportService.supported_categories:
            return value
        alias_map = {
            'REGULAR': 'REGULAR_HOLIDAY',
            'SPECIAL_NON_WORKING': 'SPECIAL_NON_WORKING_HOLIDAY',
            'SPECIAL NON WORKING': 'SPECIAL_NON_WORKING_HOLIDAY',
            'LOCAL': 'LOCAL_HOLIDAY',
            'SCHOOL': 'SCHOOL_HOLIDAY',
        }
        return alias_map.get(value)

    @staticmethod
    def _coerce_class_status(raw_status):
        if not raw_status:
            return 'NO_CLASSES'
        value = str(raw_status).strip().upper()
        allowed = {'NO_CLASSES', 'CLASSES_CONTINUE', 'TO_BE_DETERMINED'}
        return value if value in allowed else 'NO_CLASSES'

    def import_holidays(self, academic_year, raw_holidays=None, user=None):
        if not isinstance(academic_year, AcademicYear):
            return {'imported': 0, 'already_existing': 0, 'updated': 0, 'skipped': 0, 'errors': 1, 'message': 'A valid academic year is required.'}

        academic_year_start = self._parse_year_date(getattr(academic_year, 'start_date', None))
        academic_year_end = self._parse_year_date(getattr(academic_year, 'end_date', None))
        if academic_year_start is None or academic_year_end is None:
            return {'imported': 0, 'already_existing': 0, 'updated': 0, 'skipped': 0, 'errors': 1, 'message': 'Academic year dates are invalid.'}

        if raw_holidays is None:
            try:
                raw_holidays = PhilippineHolidayProvider.fetch_holidays(academic_year_start.year)
            except Exception:
                return {'imported': 0, 'already_existing': 0, 'updated': 0, 'skipped': 0, 'errors': 1, 'message': 'Philippine holiday provider is unavailable.'}

        created_count = 0
        already_existing = 0
        updated = 0
        skipped = 0
        errors = 0

        if not isinstance(raw_holidays, list):
            return {'imported': 0, 'already_existing': 0, 'updated': 0, 'skipped': 0, 'errors': 1, 'message': 'Holiday data format is invalid.'}

        for item in raw_holidays:
            if not isinstance(item, dict):
                errors += 1
                skipped += 1
                continue

            holiday_name = str(item.get('name') or item.get('title') or '').strip()
            holiday_date = self._parse_date(item.get('date'))
            holiday_category = self._normalize_category(item.get('category'))

            if not holiday_name or not holiday_date or not holiday_category:
                errors += 1
                skipped += 1
                continue

            if holiday_date < academic_year_start or holiday_date > academic_year_end:
                skipped += 1
                continue

            normalized_name = re.sub(r'\s+', ' ', holiday_name).strip()
            existing = SchoolCalendarDay.objects.filter(
                academic_year=academic_year,
                calendar_date=holiday_date,
                day_type='HOLIDAY',
            ).first()

            if existing:
                if existing.title != normalized_name or existing.holiday_category != holiday_category:
                    existing.title = normalized_name
                    existing.holiday_category = holiday_category
                    existing.holiday_source = 'PHILIPPINE_IMPORT'
                    existing.remarks = str(item.get('remarks') or existing.remarks or '')
                    existing.classes_suspended = False
                    existing.attendance_expected = False
                    existing.clean()
                    existing.save(update_fields=['title', 'holiday_category', 'holiday_source', 'remarks', 'classes_suspended', 'attendance_expected', 'updated_at'])
                    updated += 1
                else:
                    already_existing += 1
                continue

            with transaction.atomic():
                SchoolCalendarDay.objects.create(
                    academic_year=academic_year,
                    calendar_date=holiday_date,
                    day_type='HOLIDAY',
                    title=normalized_name,
                    remarks=str(item.get('remarks') or ''),
                    attendance_expected=False,
                    classes_suspended=False,
                    scope_type='SCHOOL_WIDE',
                    holiday_category=holiday_category,
                    holiday_source='PHILIPPINE_IMPORT',
                    created_by=user,
                )
            created_count += 1

        return {
            'imported': created_count,
            'already_existing': already_existing,
            'updated': updated,
            'skipped': skipped,
            'errors': errors,
            'message': f'Philippine holidays imported successfully. Imported: {created_count}. Already existed: {already_existing}. Updated: {updated}. Skipped: {skipped}. Errors: {errors}.'
        }
