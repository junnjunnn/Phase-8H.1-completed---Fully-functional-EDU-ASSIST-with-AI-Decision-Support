from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, Enrollment, GradeLevel, Section
from students.models import Student

from .models import SchoolCalendarDay
from .school_day_service import get_school_day_summary


class SchoolDayServiceTests(TestCase):
    def setUp(self):
        self.year = AcademicYear.objects.create(
            name='2025-2026', start_date=date(2025, 6, 1), end_date=date(2026, 3, 31), is_active=True,
        )

    def add_day(self, calendar_date, day_type='SCHOOL_DAY', attendance_expected=True):
        return SchoolCalendarDay.objects.create(
            academic_year=self.year,
            calendar_date=calendar_date,
            day_type=day_type,
            title=day_type,
            attendance_expected=attendance_expected,
            classes_suspended=day_type == 'SUSPENSION',
        )

    def test_counts_designated_school_days_only(self):
        self.add_day(date(2025, 6, 2))
        self.add_day(date(2025, 6, 3))
        self.assertEqual(get_school_day_summary(today=date(2025, 6, 3))['school_days'], 2)

    def test_excludes_weekends_holidays_suspensions_and_non_school_dates(self):
        self.add_day(date(2025, 6, 7), 'WEEKEND', False)
        self.add_day(date(2025, 6, 9), 'HOLIDAY', False)
        self.add_day(date(2025, 6, 10), 'SUSPENSION', False)
        self.add_day(date(2025, 6, 11), 'SPECIAL_NON_CLASS_DAY', False)
        self.add_day(date(2025, 6, 12))
        self.assertEqual(get_school_day_summary(today=date(2025, 6, 12))['school_days'], 1)

    def test_excludes_dates_outside_academic_year_boundaries(self):
        self.add_day(date(2025, 5, 31))
        self.add_day(date(2025, 6, 1))
        self.add_day(date(2026, 3, 31))
        self.add_day(date(2026, 4, 1))
        self.assertEqual(get_school_day_summary(today=date(2026, 4, 1))['school_days'], 2)

    def test_current_active_year_uses_reporting_cutoff(self):
        self.add_day(date(2025, 6, 2))
        self.add_day(date(2025, 6, 3))
        self.add_day(date(2025, 6, 4))
        self.assertEqual(get_school_day_summary(today=date(2025, 6, 3))['school_days'], 2)

    def test_historical_year_counts_to_selected_reporting_date(self):
        self.year.is_active = False
        self.year.save(update_fields=['is_active'])
        self.add_day(date(2025, 6, 2))
        self.add_day(date(2025, 6, 3))
        self.add_day(date(2025, 6, 4))
        self.assertEqual(get_school_day_summary(self.year.id, reporting_date='2025-06-03')['school_days'], 2)

    def test_archived_students_and_multiple_students_do_not_change_calendar_count(self):
        grade = GradeLevel.objects.get(code='G11')
        section = Section.objects.create(name='A', grade_level=grade, academic_year=self.year)
        for status in ('active', 'active', 'archived'):
            student = Student.objects.create(first_name=status, last_name='Student', student_status=status)
            Enrollment.objects.create(student=student, academic_year=self.year, grade_level=grade, section=section, enrollment_status='active')
        self.add_day(date(2025, 6, 2))
        self.assertEqual(get_school_day_summary(today=date(2025, 6, 2))['school_days'], 1)

    def test_missing_calendar_and_inactive_year_are_safe(self):
        self.year.is_active = False
        self.year.save(update_fields=['is_active'])
        self.assertEqual(get_school_day_summary()['school_days'], 0)
        self.assertFalse(get_school_day_summary()['calendar_available'])


class DashboardSchoolDayAPITests(TestCase):
    def test_school_day_summary_endpoint_returns_json_safe_academic_year_and_date(self):
        user = get_user_model().objects.create_user(username='school_days_admin_summary', password='pass')
        UserProfile.objects.create(user=user, role_name='SUPER_ADMIN')
        year = AcademicYear.objects.create(name='2025-2026', start_date=date(2025, 6, 1), end_date=date(2026, 3, 31), is_active=True)
        SchoolCalendarDay.objects.create(
            academic_year=year,
            calendar_date=date(2025, 6, 2),
            day_type='SCHOOL_DAY',
            title='School day',
            attendance_expected=True,
            classes_suspended=False,
        )

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/attendance-records/school-day-summary/', {
            'academic_year_id': year.id,
            'reporting_date': '2025-06-02',
            'today': '2025-06-02',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.headers.get('Content-Type', ''))
        self.assertEqual(response.data['school_days'], 1)
        self.assertEqual(response.data['academic_year']['id'], year.id)
        self.assertEqual(response.data['academic_year']['name'], year.name)
        self.assertEqual(response.data['calendar_available'], True)
        self.assertEqual(response.data['reporting_date'], '2025-06-02')

    def test_dashboard_returns_calendar_days_once_not_per_student(self):
        user = get_user_model().objects.create_user(username='school_days_admin', password='pass')
        UserProfile.objects.create(user=user, role_name='SUPER_ADMIN')
        year = AcademicYear.objects.create(name='2025-2026', start_date=date(2025, 6, 1), end_date=date(2026, 3, 31), is_active=True)
        grade = GradeLevel.objects.get(code='G11')
        section = Section.objects.create(name='A', grade_level=grade, academic_year=year)
        for first_name in ('One', 'Two'):
            student = Student.objects.create(first_name=first_name, last_name='Student', student_status='active')
            Enrollment.objects.create(student=student, academic_year=year, grade_level=grade, section=section, enrollment_status='active')
        SchoolCalendarDay.objects.create(academic_year=year, calendar_date=date(2025, 6, 2), day_type='SCHOOL_DAY', title='School day', attendance_expected=True)

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/api/dashboard-summary/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['school_days'], 1)
        self.assertEqual(response.data['attendance_summary']['school_days'], 1)