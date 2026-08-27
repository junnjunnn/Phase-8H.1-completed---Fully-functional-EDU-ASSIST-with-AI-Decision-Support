from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment, Subject
from students.models import Student
from .models import AttendanceRecord, RecurringSchoolCalendarEvent, SchoolCalendarDay


class AttendanceRecordAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.superadmin = self.user_model.objects.create_user(username='superadmin_attendance', password='SuperPass1!')
        UserProfile.objects.create(user=self.superadmin, role_name='SUPER_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='teacher_attendance', password='TeacherPass1!')
        teacher_profile = UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        # Use the grade level from Phase 1 migration (0004)
        grade_level = GradeLevel.objects.get(code='G11')
        section_a = Section.objects.create(name='A', grade_level=grade_level, academic_year=academic_year)
        self.section_b = Section.objects.create(name='B', grade_level=grade_level, academic_year=academic_year)
        teacher_profile.assigned_sections.add(section_a)

        self.student_a = Student.objects.create(first_name='Alice', last_name='Anderson', gender='Female', student_status='active')
        self.student_b = Student.objects.create(first_name='Bob', last_name='Baker', gender='Male', student_status='active')

        self.enrollment_a = Enrollment.objects.create(student=self.student_a, academic_year=academic_year, grade_level=grade_level, section=section_a, enrollment_status='active')
        self.enrollment_b = Enrollment.objects.create(student=self.student_b, academic_year=academic_year, grade_level=grade_level, section=self.section_b, enrollment_status='active')

        self.attendance_a = AttendanceRecord.objects.create(enrollment=self.enrollment_a, month='June', school_days=20, days_present=18, absences=2, times_tardy=1)
        self.attendance_b = AttendanceRecord.objects.create(enrollment=self.enrollment_b, month='June', school_days=20, days_present=19, absences=1, times_tardy=0)

    def test_teacher_only_sees_assigned_section_attendance_records(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/attendance-records/')
        self.assertEqual(response.status_code, 200)
        record_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.attendance_a.id, record_ids)
        self.assertNotIn(self.attendance_b.id, record_ids)

    def test_superadmin_sees_all_attendance_records(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/attendance-records/')
        self.assertEqual(response.status_code, 200)
        record_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.attendance_a.id, record_ids)
        self.assertIn(self.attendance_b.id, record_ids)

    def test_teacher_cannot_create_attendance_for_unauthorized_enrollment(self):
        """Critical: Teacher should NOT be able to create attendance for unauthorized enrollment."""
        self.client.force_authenticate(user=self.teacher)

        response = self.client.post('/api/attendance-records/', {
            'enrollment': self.enrollment_b.id,
            'month': 'July',
            'school_days': 20,
            'days_present': 18,
            'absences': 2,
            'times_tardy': 0,
        })

        self.assertIn(response.status_code, [400, 403],
            f"Teacher should not create attendance for unauthorized enrollment. Got {response.status_code}: {response.data}")


class SchoolCalendarDayAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.admin = self.user_model.objects.create_user(username='school_admin_calendar', password='SchoolPass1!')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='teacher_calendar', password='TeacherPass1!')
        UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        self.grade_level = GradeLevel.objects.get(code='G11')
        self.section = Section.objects.create(name='A', grade_level=self.grade_level, academic_year=self.academic_year)

    def test_school_calendar_marks_weekend_as_not_expected(self):
        saturday = SchoolCalendarDay.objects.create(
            academic_year=self.academic_year,
            calendar_date='2025-06-07',
            day_type='WEEKEND',
            title='Weekend',
            attendance_expected=False,
            classes_suspended=False,
            created_by=self.admin,
        )
        self.assertFalse(saturday.attendance_expected)
        self.assertFalse(saturday.is_attendance_expected())

    def test_school_calendar_marks_holiday_as_not_expected(self):
        holiday = SchoolCalendarDay.objects.create(
            academic_year=self.academic_year,
            calendar_date='2025-06-12',
            day_type='HOLIDAY',
            title='Independence Day',
            attendance_expected=False,
            classes_suspended=False,
            created_by=self.admin,
        )
        self.assertFalse(holiday.attendance_expected)
    def test_school_calendar_marks_class_suspension_as_not_expected(self):
        suspension = SchoolCalendarDay.objects.create(
            academic_year=self.academic_year,
            calendar_date='2025-06-16',
            day_type='SUSPENSION',
            title='Heavy Rainfall',
            attendance_expected=False,
            classes_suspended=True,
            created_by=self.admin,
            scope_type='SCHOOL_WIDE',
            remarks='Flooding in the area.'
        )
        self.assertFalse(suspension.attendance_expected)
        self.assertTrue(suspension.classes_suspended)

    def test_special_non_class_day_is_not_expected(self):
        special = SchoolCalendarDay.objects.create(
            academic_year=self.academic_year,
            calendar_date='2025-06-20',
            day_type='SPECIAL_NON_CLASS_DAY',
            title='School Development Day',
            attendance_expected=False,
            classes_suspended=False,
            created_by=self.admin,
        )
        self.assertFalse(special.attendance_expected)

    def test_school_calendar_isolated_by_academic_year(self):
        next_year = AcademicYear.objects.create(name='2026-2027', start_date='2026-06-01', end_date='2027-03-31', is_active=False)
        entry = SchoolCalendarDay.objects.create(
            academic_year=next_year,
            calendar_date='2026-06-07',
            day_type='WEEKEND',
            title='Weekend',
            attendance_expected=False,
            classes_suspended=False,
            created_by=self.admin,
        )
        self.assertFalse(entry.is_attendance_expected())

    def test_authorized_staff_can_create_school_calendar_entry(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-06-09',
            'day_type': 'HOLIDAY',
            'title': 'Holiday',
            'attendance_expected': False,
            'classes_suspended': False,
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn(response.data['status'], ['DRAFT', 'PENDING_APPROVAL'])

    def test_authorized_user_can_create_suspension(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-06-17',
            'day_type': 'SUSPENSION',
            'title': 'Local Government Suspension',
            'remarks': 'Typhoon signal no. 2.',
            'attendance_expected': False,
            'classes_suspended': True,
            'scope_type': 'SCHOOL_WIDE',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['day_type'], 'SUSPENSION')
        self.assertFalse(response.data['attendance_expected'])

    def test_suspension_scopes_and_academic_year_are_supported(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-06-18',
            'day_type': 'SUSPENSION',
            'title': 'Grade suspension',
            'scope_type': 'GRADE_LEVEL',
            'affected_grade_level': self.grade_level.id,
            'suspension_type': 'SCHOOL_ADMINISTRATION',
            'reason': 'Institutional decision',
        }
        response = self.client.post('/api/school-calendar-days/', payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['academic_year'], self.academic_year.id)
        self.assertEqual(response.data['scope_type'], 'GRADE_LEVEL')

    def test_suspension_rejects_invalid_time_range(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-06-19',
            'day_type': 'SUSPENSION',
            'title': 'Invalid time',
            'scope_type': 'SCHOOL_WIDE',
            'start_time': '15:00',
            'end_time': '14:00',
            'suspension_type': 'OTHER',
        })
        self.assertEqual(response.status_code, 400)


    def test_event_can_be_cancelled_and_remains_retrievable(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-06-20',
            'day_type': 'SCHOOL_EVENT',
            'title': 'Foundation Day',
            'location': 'AVR Room',
            'status': 'PUBLISHED',
        })
        self.assertEqual(response.status_code, 201)
        entry_id = response.data['id']
        cancelled = self.client.post(f'/api/school-calendar-days/{entry_id}/cancel/', {'cancellation_reason': 'Weather advisory'})
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data['status'], 'CANCELLED')
        self.assertEqual(cancelled.data['cancellation_reason'], 'Weather advisory')
        retrieved = self.client.get(f'/api/school-calendar-days/{entry_id}/')
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(retrieved.data['title'], 'Foundation Day')

    def test_school_calendar_expected_days_excludes_non_school_dates(self):
        SchoolCalendarDay.objects.create(
            academic_year=self.academic_year,
            calendar_date='2025-06-02',
            day_type='SCHOOL_DAY',
            title='School Day',
            attendance_expected=True,
            classes_suspended=False,
            created_by=self.admin,
        )
        SchoolCalendarDay.objects.create(
            academic_year=self.academic_year,
            calendar_date='2025-06-07',
            day_type='WEEKEND',
            title='Weekend',
            attendance_expected=False,
            classes_suspended=False,
            created_by=self.admin,
        )
        SchoolCalendarDay.objects.create(
            academic_year=self.academic_year,
            calendar_date='2025-06-09',
            day_type='HOLIDAY',
            title='Holiday',
            attendance_expected=False,
            classes_suspended=False,
            created_by=self.admin,
        )
        expected_days = SchoolCalendarDay.get_expected_school_days(self.academic_year, '2025-06-01', '2025-06-30')
        self.assertEqual(expected_days, 1)

    def test_historical_attendance_record_remains_preserved_on_calendar_day(self):
        record = AttendanceRecord.objects.create(
            enrollment=Enrollment.objects.create(
                student=Student.objects.create(first_name='Cora', last_name='Dela Cruz', gender='Female', student_status='active'),
                academic_year=self.academic_year,
                grade_level=self.grade_level,
                section=self.section,
                enrollment_status='active',
            ),
            month='2025-06-16',
            school_days=1,
            days_present=1,
            absences=0,
            times_tardy=0,
        )
        self.assertTrue(AttendanceRecord.objects.filter(pk=record.pk).exists())
        self.assertEqual(record.month, '2025-06-16')

    def test_admin_can_create_enrollment_period_with_academic_year_and_range(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-06-10',
            'end_date': '2025-06-20',
            'day_type': 'ENROLLMENT',
            'event_type': 'ENROLLMENT_PERIOD',
            'title': 'Enrollment for AY 2025-2026',
            'target_participants': 'Incoming students',
            'status': 'PUBLISHED',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['day_type'], 'ENROLLMENT')
        self.assertEqual(response.data['event_type'], 'ENROLLMENT_PERIOD')
        self.assertEqual(response.data['end_date'], '2025-06-20')
        self.assertFalse(response.data['attendance_expected'])

    def test_admin_can_create_academic_deadline_without_attendance_side_effect(self):
        self.client.force_authenticate(user=self.admin)
        before_records = AttendanceRecord.objects.count()
        response = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-07-15',
            'day_type': 'ACADEMIC_DEADLINE',
            'event_type': 'GRADE_SUBMISSION',
            'title': 'Grade Submission',
            'start_time': '17:00',
            'target_participants': 'Faculty',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['day_type'], 'ACADEMIC_DEADLINE')
        self.assertEqual(response.data['event_type'], 'GRADE_SUBMISSION')
        self.assertFalse(response.data['attendance_expected'])
        self.assertEqual(AttendanceRecord.objects.count(), before_records)
        self.assertEqual(SchoolCalendarDay.get_expected_school_days(self.academic_year), 0)

    def test_enrollment_dates_must_belong_to_academic_year_and_be_ordered(self):
        self.client.force_authenticate(user=self.admin)
        out_of_range = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2026-04-01',
            'day_type': 'ENROLLMENT',
            'event_type': 'ENROLLMENT_OPENS',
            'title': 'Out of range',
        }, format='json')
        self.assertEqual(out_of_range.status_code, 400)
        self.assertIn('calendar_date', out_of_range.data)
        invalid_range = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-06-20',
            'end_date': '2025-06-10',
            'day_type': 'ENROLLMENT',
            'event_type': 'ENROLLMENT_PERIOD',
            'title': 'Invalid range',
        }, format='json')
        self.assertEqual(invalid_range.status_code, 400)
        self.assertIn('end_date', invalid_range.data)

    def test_authorized_staff_can_create_deadlines(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-08-01',
            'day_type': 'ACADEMIC_DEADLINE',
            'event_type': 'CLEARANCE',
            'title': 'Clearance deadline',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn(response.data['status'], ['DRAFT', 'PENDING_APPROVAL'])

    def test_cancelled_deadline_remains_historical(self):
        self.client.force_authenticate(user=self.admin)
        created = self.client.post('/api/school-calendar-days/', {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-08-15',
            'day_type': 'ACADEMIC_DEADLINE',
            'event_type': 'LIBRARY_RETURN',
            'title': 'Library return',
        }, format='json')
        self.assertEqual(created.status_code, 201)
        cancelled = self.client.post(f"/api/school-calendar-days/{created.data['id']}/cancel/", {
            'cancellation_reason': 'Rescheduled by the registrar',
        })
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data['status'], 'CANCELLED')
        retrieved = self.client.get(f"/api/school-calendar-days/{created.data['id']}/")
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(retrieved.data['event_type'], 'LIBRARY_RETURN')


class SchoolCalendarApprovalWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.teacher = self.user_model.objects.create_user(username='approval_teacher', password='TeacherPass1!')
        UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        self.admin = self.user_model.objects.create_user(username='approval_admin', password='SchoolPass1!')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')

        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)

    def _create_event(self, user, **overrides):
        payload = {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-06-15',
            'day_type': 'SCHOOL_EVENT',
            'title': 'School Science Fair',
            'location': 'Science Lab',
            'organizer': 'Science Department',
            'status': 'DRAFT',
        }
        payload.update(overrides)
        self.client.force_authenticate(user=user)
        return self.client.post('/api/school-calendar-days/', payload, format='json')

    def test_teacher_can_create_event_and_submit_for_approval(self):
        created = self._create_event(self.teacher)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data['status'], 'PENDING_APPROVAL')

        submitted = self.client.post(f"/api/school-calendar-days/{created.data['id']}/submit-for-approval/", {})
        self.assertEqual(submitted.status_code, 400)
        self.assertIn('Only draft or rejected events can be submitted', str(submitted.data.get('detail', '')))

    def test_approver_can_approve_pending_event(self):
        created = self._create_event(self.teacher)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data['status'], 'PENDING_APPROVAL')

        self.client.force_authenticate(user=self.admin)
        approved = self.client.post(f"/api/school-calendar-days/{created.data['id']}/approve/", {})
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.data['status'], 'APPROVED')

    def test_creator_cannot_approve_own_event(self):
        created = self._create_event(self.teacher)
        self.client.post(f"/api/school-calendar-days/{created.data['id']}/submit-for-approval/", {})

        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(f"/api/school-calendar-days/{created.data['id']}/approve/", {})
        self.assertIn(response.status_code, [400, 403])
        self.assertTrue('self' in str(response.data).lower() or 'permission' in str(response.data).lower() or 'school administrators' in str(response.data).lower())

    def test_rejection_requires_reason(self):
        created = self._create_event(self.teacher)
        self.client.post(f"/api/school-calendar-days/{created.data['id']}/submit-for-approval/", {})

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f"/api/school-calendar-days/{created.data['id']}/reject/", {})
        self.assertEqual(response.status_code, 400)
        self.assertIn('rejection_reason', response.data)

    def test_unapproved_event_cannot_be_published(self):
        created = self._create_event(self.teacher)
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f"/api/school-calendar-days/{created.data['id']}/publish/", {})
        self.assertEqual(response.status_code, 400)
        self.assertIn('APPROVED', str(response.data).upper())

    def test_approved_event_can_be_published(self):
        created = self._create_event(self.teacher)
        self.client.post(f"/api/school-calendar-days/{created.data['id']}/submit-for-approval/", {})
        self.client.force_authenticate(user=self.admin)
        self.client.post(f"/api/school-calendar-days/{created.data['id']}/approve/", {})
        published = self.client.post(f"/api/school-calendar-days/{created.data['id']}/publish/", {})
        self.assertEqual(published.status_code, 200)
        self.assertEqual(published.data['status'], 'PUBLISHED')


class ExaminationCalendarAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(username='examination_admin', password='SchoolPass1!')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')
        self.teacher = user_model.objects.create_user(username='examination_teacher', password='TeacherPass1!', first_name='Exam', last_name='Teacher')
        UserProfile.objects.create(user=self.teacher, role_name='TEACHER')
        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        self.grade_level = GradeLevel.objects.get(code='G11')
        self.section = Section.objects.create(name='Exam-A', grade_level=self.grade_level, academic_year=self.academic_year)
        self.subject = Subject.objects.create(code='MATH-EXAM', name='Mathematics', category='Core', grade_level=self.grade_level)

    def _payload(self, **overrides):
        payload = {
            'academic_year': self.academic_year.id,
            'calendar_date': '2025-10-12',
            'day_type': 'EXAMINATION',
            'title': 'Midterm Examination',
            'examination_type': 'MIDTERM',
            'examination_period': 'MIDTERM',
            'start_time': '08:00',
            'end_time': '10:00',
            'scope_type': 'SECTION_SPECIFIC',
            'section': self.section.id,
            'subject': self.subject.id,
            'instructor': self.teacher.id,
            'location': 'Room 204',
            'attendance_expected': True,
        }
        payload.update(overrides)
        return payload

    def test_authorized_admin_can_create_examination_in_school_calendar(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/', self._payload(), format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['day_type'], 'EXAMINATION')
        self.assertEqual(response.data['academic_year'], self.academic_year.id)
        self.assertTrue(SchoolCalendarDay.objects.filter(pk=response.data['id'], day_type='EXAMINATION').exists())

    def test_authorized_staff_can_create_examination(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/school-calendar-days/', self._payload(), format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn(response.data['status'], ['DRAFT', 'PENDING_APPROVAL'])

    def test_examination_requires_academic_year(self):
        self.client.force_authenticate(user=self.admin)
        payload = self._payload()
        payload.pop('academic_year')
        response = self.client.post('/api/school-calendar-days/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('academic_year', response.data)

    def test_examination_date_and_time_are_validated(self):
        self.client.force_authenticate(user=self.admin)
        out_of_range = self.client.post('/api/school-calendar-days/', self._payload(calendar_date='2026-04-01'), format='json')
        self.assertEqual(out_of_range.status_code, 400)
        self.assertIn('calendar_date', out_of_range.data)
        invalid_time = self.client.post('/api/school-calendar-days/', self._payload(start_time='10:00', end_time='08:00'), format='json')
        self.assertEqual(invalid_time.status_code, 400)
        self.assertIn('end_time', invalid_time.data)

    def test_examination_subject_must_match_section_grade(self):
        other_grade = GradeLevel.objects.exclude(pk=self.grade_level.pk).first()
        other_section = Section.objects.create(name='Other-Exam', grade_level=other_grade, academic_year=self.academic_year)
        other_subject = Subject.objects.create(code='OTHER-EXAM', name='Other Subject', category='Learning Area', grade_level=other_grade)
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/', self._payload(section=other_section.id, subject=self.subject.id), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('subject', response.data)
        valid = self.client.post('/api/school-calendar-days/', self._payload(section=other_section.id, subject=other_subject.id), format='json')
        self.assertEqual(valid.status_code, 201)

    def test_examination_is_listed_without_creating_attendance(self):
        self.client.force_authenticate(user=self.admin)
        before = AttendanceRecord.objects.count()
        created = self.client.post('/api/school-calendar-days/', self._payload(), format='json')
        listed = self.client.get('/api/school-calendar-days/', {'academic_year': self.academic_year.id, 'day_type': 'EXAMINATION'})
        self.assertEqual(created.status_code, 201)
        self.assertEqual(listed.status_code, 200)
        self.assertTrue(any(item['id'] == created.data['id'] for item in listed.data['results']))
        self.assertEqual(AttendanceRecord.objects.count(), before)


class PhilippineHolidayImportAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.admin = self.user_model.objects.create_user(username='phil_holiday_admin', password='SchoolPass1!')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='phil_holiday_teacher', password='TeacherPass1!')
        UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        self.out_of_range_year = AcademicYear.objects.create(name='2026-2027', start_date='2026-06-01', end_date='2027-03-31', is_active=False)

    def test_authorized_admin_can_import_philippine_holidays(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/import-philippine-holidays/', {'academic_year': self.academic_year.id})

        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data['imported'], 0)
        self.assertTrue(SchoolCalendarDay.objects.filter(academic_year=self.academic_year, day_type='HOLIDAY').exists())

    def test_unauthorized_user_cannot_import_philippine_holidays(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/school-calendar-days/import-philippine-holidays/', {'academic_year': self.academic_year.id})

        self.assertIn(response.status_code, [400, 403])

    def test_imported_holidays_are_linked_to_selected_academic_year(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/import-philippine-holidays/', {'academic_year': self.academic_year.id})

        self.assertEqual(response.status_code, 200)
        records = SchoolCalendarDay.objects.filter(academic_year=self.academic_year, day_type='HOLIDAY')
        self.assertTrue(records.exists())
        self.assertTrue(all(record.academic_year_id == self.academic_year.id for record in records))

    def test_holidays_outside_academic_year_scope_are_not_imported(self):
        from attendance.holiday_import import PhilippineHolidayImportService

        service = PhilippineHolidayImportService()
        result = service.import_holidays(
            self.out_of_range_year,
            [{'date': '2025-01-01', 'name': 'Out Of Range Holiday', 'category': 'REGULAR_HOLIDAY'}],
        )

        self.assertEqual(result['imported'], 0)
        self.assertEqual(result['skipped'], 1)
        self.assertFalse(SchoolCalendarDay.objects.filter(academic_year=self.out_of_range_year, day_type='HOLIDAY').exists())

    def test_repeated_import_does_not_duplicate_holidays(self):
        self.client.force_authenticate(user=self.admin)
        first = self.client.post('/api/school-calendar-days/import-philippine-holidays/', {'academic_year': self.academic_year.id})
        second = self.client.post('/api/school-calendar-days/import-philippine-holidays/', {'academic_year': self.academic_year.id})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertGreater(first.data['imported'], 0)
        self.assertEqual(second.data['imported'], 0)
        self.assertGreater(second.data['already_existing'], 0)
        self.assertEqual(
            SchoolCalendarDay.objects.filter(academic_year=self.academic_year, day_type='HOLIDAY').count(),
            first.data['imported']
        )

    def test_invalid_daily_data_is_rejected_safely(self):
        from attendance.holiday_import import PhilippineHolidayImportService

        service = PhilippineHolidayImportService()
        result = service.import_holidays(self.academic_year, [
            {'date': 'not-a-date', 'name': 'Bad Entry', 'category': 'Regular Holiday'},
        ])

        self.assertEqual(result['imported'], 0)
        self.assertEqual(result['errors'], 1)

    def test_external_provider_failure_does_not_corrupt_calendar_data(self):
        from attendance.holiday_import import PhilippineHolidayImportService
        from unittest.mock import patch

        service = PhilippineHolidayImportService()
        with patch('attendance.holiday_import.PhilippineHolidayProvider.fetch_holidays', side_effect=ConnectionError('timeout')):
            result = service.import_holidays(self.academic_year)

        self.assertEqual(result['imported'], 0)
        self.assertEqual(result['errors'], 1)
        self.assertFalse(SchoolCalendarDay.objects.filter(academic_year=self.academic_year).exists())

    def test_manual_holiday_creation_still_works(self):
        holiday = SchoolCalendarDay.objects.create(
            academic_year=self.academic_year,
            calendar_date='2025-06-12',
            day_type='HOLIDAY',
            title='Independence Day',
            attendance_expected=False,
            classes_suspended=False,
            created_by=self.admin,
            holiday_category='REGULAR_HOLIDAY',
        )

        self.assertEqual(holiday.title, 'Independence Day')
        self.assertFalse(holiday.attendance_expected)


class RecurringSchoolCalendarEventTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(username='recurrence_admin', password='SchoolPass1!')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')
        self.teacher = user_model.objects.create_user(username='recurrence_teacher', password='TeacherPass1!')
        UserProfile.objects.create(user=self.teacher, role_name='TEACHER')
        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)

    def _create(self, **overrides):
        payload = {
            'academic_year': self.academic_year.id,
            'title': 'Faculty Meeting',
            'day_type': 'SCHOOL_EVENT',
            'start_date': '2025-06-06',
            'recurrence_end_date': '2025-06-27',
            'start_time': '15:00',
            'end_time': '17:00',
            'frequency': 'WEEKLY',
            'recurrence_weekday': 4,
            'recurrence_interval': 1,
        }
        payload.update(overrides)
        self.client.force_authenticate(user=self.admin)
        return self.client.post('/api/recurring-school-calendar-events/', payload, format='json')

    def test_weekly_event_generates_expected_occurrences(self):
        response = self._create()
        self.assertEqual(response.status_code, 201)
        event = RecurringSchoolCalendarEvent.objects.get(pk=response.data['id'])
        self.assertEqual(list(event.occurrences.values_list('calendar_date', flat=True)), [
            date(2025, 6, 6), date(2025, 6, 13), date(2025, 6, 20), date(2025, 6, 27)
        ])

    def test_generation_is_idempotent(self):
        response = self._create()
        self.client.post(f"/api/recurring-school-calendar-events/{response.data['id']}/generate/")
        self.assertEqual(SchoolCalendarDay.objects.filter(recurrence_id=response.data['id']).count(), 4)

    def test_monthly_first_friday_event(self):
        response = self._create(
            start_date='2025-06-01', recurrence_end_date='2025-09-30', frequency='MONTHLY',
            recurrence_weekday=4, recurrence_week=1,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(list(SchoolCalendarDay.objects.filter(recurrence_id=response.data['id']).values_list('calendar_date', flat=True)), [
            date(2025, 6, 6), date(2025, 7, 4), date(2025, 8, 1), date(2025, 9, 5)
        ])

    def test_yearly_event_and_boundaries(self):
        response = self._create(
            start_date='2025-08-15', recurrence_end_date='2026-03-31', frequency='YEARLY',
            recurrence_month=8, recurrence_month_day=15, recurrence_weekday=None,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SchoolCalendarDay.objects.filter(recurrence_id=response.data['id']).count(), 1)
        self.assertTrue(SchoolCalendarDay.objects.filter(recurrence_id=response.data['id'], calendar_date='2025-08-15').exists())

    def test_recurrence_is_linked_to_academic_year(self):
        response = self._create()
        occurrence = SchoolCalendarDay.objects.filter(recurrence_id=response.data['id']).first()
        self.assertEqual(response.data['academic_year'], self.academic_year.id)
        self.assertEqual(occurrence.academic_year_id, self.academic_year.id)

    def test_unauthorized_user_cannot_manage_recurrence(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/recurring-school-calendar-events/', {
            'academic_year': self.academic_year.id, 'title': 'Nope', 'day_type': 'SCHOOL_EVENT',
            'start_date': '2025-06-06', 'recurrence_end_date': '2025-06-06', 'frequency': 'DAILY',
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_deactivation_preserves_historical_occurrences(self):
        response = self._create()
        event_id = response.data['id']
        deactivated = self.client.post(f'/api/recurring-school-calendar-events/{event_id}/deactivate/')
        self.assertEqual(deactivated.status_code, 200)
        self.assertFalse(RecurringSchoolCalendarEvent.objects.get(pk=event_id).active)
        self.assertEqual(SchoolCalendarDay.objects.filter(recurrence_id=event_id).count(), 4)

    def test_holiday_precedence_remains_unchanged(self):
        self._create(day_type='SCHOOL_DAY', attendance_expected=True)
        SchoolCalendarDay.objects.create(
            academic_year=self.academic_year, calendar_date='2025-06-13', day_type='HOLIDAY',
            title='Holiday', attendance_expected=False, created_by=self.admin,
        )
        self.assertFalse(SchoolCalendarDay.get_day_status_for_date(self.academic_year, '2025-06-13').attendance_expected)


class SchoolCalendarConflictDetectionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(username='conflict_admin', password='ConflictPass1!')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')
        self.teacher = user_model.objects.create_user(username='conflict_teacher', password='ConflictPass2!')
        UserProfile.objects.create(user=self.teacher, role_name='TEACHER')
        self.year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        grade = GradeLevel.objects.get(code='G11')
        self.section_a = Section.objects.create(name='Conflict A', grade_level=grade, academic_year=self.year)
        self.section_b = Section.objects.create(name='Conflict B', grade_level=grade, academic_year=self.year)

    def event(self, **overrides):
        values = {
            'academic_year': self.year, 'calendar_date': date(2025, 7, 10), 'day_type': 'SCHOOL_EVENT',
            'title': 'Existing event', 'scope_type': 'SECTION_SPECIFIC', 'section': self.section_a,
            'start_time': time(9), 'end_time': time(10), 'location': 'Room 1', 'status': 'APPROVED',
        }
        values.update(overrides)
        return SchoolCalendarDay.objects.create(**values)

    def payload(self, **overrides):
        values = {
            'academic_year': self.year.id, 'calendar_date': '2025-07-10', 'day_type': 'SCHOOL_EVENT',
            'title': 'New event', 'scope_type': 'SECTION_SPECIFIC', 'section': self.section_a.id,
            'start_time': '09:30', 'end_time': '10:30', 'location': 'Room 1',
        }
        values.update(overrides)
        return values

    def test_authentication_and_unrelated_dates_have_no_conflict(self):
        self.event()
        response = self.client.post('/api/school-calendar-days/check-conflicts/', self.payload(calendar_date='2025-07-11'), format='json')
        self.assertEqual(response.status_code, 401)
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/check-conflicts/', self.payload(calendar_date='2025-07-11', location='Room 2'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['has_conflicts'])

    def test_non_overlapping_times_have_no_conflict(self):
        self.event()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/check-conflicts/', self.payload(start_time='10:00', end_time='11:00', location='Room 2'), format='json')
        self.assertFalse(response.data['has_conflicts'])

    def test_time_overlap_is_warning_for_different_sections_and_rooms(self):
        self.event()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/check-conflicts/', self.payload(section=self.section_b.id, location='Room 2'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['conflicts'][0]['conflict_types'], ['TIME_OVERLAP'])
        self.assertEqual(response.data['conflicts'][0]['severity'], 'WARNING')

    def test_location_section_and_scope_conflicts_block_create(self):
        existing = self.event()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/', self.payload(), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('conflicts', response.data)
        self.assertEqual(SchoolCalendarDay.objects.get(pk=existing.pk).title, 'Existing event')

    def test_different_sections_do_not_conflict_but_school_scope_does(self):
        self.event()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/check-conflicts/', self.payload(section=self.section_b.id, location='Room 2'), format='json')
        self.assertEqual(response.data['conflicts'][0]['conflict_types'], ['TIME_OVERLAP'])
        response = self.client.post('/api/school-calendar-days/check-conflicts/', self.payload(scope_type='SCHOOL_WIDE', section=None, location='Room 2'), format='json')
        self.assertIn('SCOPE_CONFLICT', response.data['conflicts'][0]['conflict_types'])

    def test_examination_and_recurring_occurrences_use_existing_calendar_rows(self):
        self.event(day_type='EXAMINATION', title='Midterm exam', examination_type='MIDTERM')
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/school-calendar-days/check-conflicts/', self.payload(location='Room 2'), format='json')
        self.assertTrue(response.data['has_conflicts'])
        recurrence = RecurringSchoolCalendarEvent.objects.create(
            academic_year=self.year, title='Recurring event', day_type='SCHOOL_EVENT', scope_type='SECTION_SPECIFIC',
            section=self.section_a, start_date=date(2025, 7, 10), recurrence_end_date=date(2025, 7, 10),
            start_time=time(9), end_time=time(10), location='Room 3', frequency='DAILY', created_by=self.admin,
        )
        from .conflicts import detect_conflicts
        from .recurrence import generate_occurrences
        generate_occurrences(recurrence)
        occurrence = SchoolCalendarDay.objects.get(recurrence=recurrence)
        self.assertTrue(any('TIME_OVERLAP' in item['conflict_types'] for item in detect_conflicts(occurrence)))

    def test_update_and_checker_are_read_only_and_attendance_is_unchanged(self):
        existing = self.event(title='First')
        other = self.event(calendar_date=date(2025, 7, 11), title='Second', location='Room 2')
        before_calendar = list(SchoolCalendarDay.objects.values_list('id', 'title', 'calendar_date'))
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f'/api/school-calendar-days/{other.id}/', self.payload(calendar_date='2025-07-10', title='Changed'), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(list(SchoolCalendarDay.objects.values_list('id', 'title', 'calendar_date')), before_calendar)
        before_attendance = AttendanceRecord.objects.count()
        self.client.post('/api/school-calendar-days/check-conflicts/', self.payload(), format='json')
        self.assertEqual(AttendanceRecord.objects.count(), before_attendance)
        self.assertTrue(SchoolCalendarDay.objects.filter(pk=existing.pk).exists())
