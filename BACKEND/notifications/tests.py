from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment
from attendance.models import AttendanceRecord, RecurringSchoolCalendarEvent, SchoolCalendarDay
from students.models import Student

from .models import Notification
from .services import generate_notifications_for_user


class NotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(username='notification_admin', password='pass')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')
        self.teacher = user_model.objects.create_user(username='notification_teacher', password='pass')
        teacher_profile = UserProfile.objects.create(user=self.teacher, role_name='TEACHER')
        self.other_teacher = user_model.objects.create_user(username='notification_other', password='pass')
        UserProfile.objects.create(user=self.other_teacher, role_name='TEACHER')
        self.year = AcademicYear.objects.create(name='2026-2027', start_date=date.today() - timedelta(days=30), end_date=date.today() + timedelta(days=180), is_active=True)
        grade = GradeLevel.objects.get(code='G11')
        self.section = Section.objects.create(name='N', grade_level=grade, academic_year=self.year)
        teacher_profile.assigned_sections.add(self.section)
        student = Student.objects.create(first_name='Notify', last_name='Student', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.year, grade_level=grade, section=self.section, enrollment_status='active')
        self.attendance = AttendanceRecord.objects.create(enrollment=enrollment, month='June', school_days=1, days_present=1)

    def event(self, **kwargs):
        defaults = {'academic_year': self.year, 'calendar_date': date.today() + timedelta(days=2), 'day_type': 'SCHOOL_EVENT', 'title': 'Staff event', 'scope_type': 'SECTION_SPECIFIC', 'section': self.section, 'status': 'PUBLISHED'}
        defaults.update(kwargs)
        return SchoolCalendarDay.objects.create(**defaults)

    def test_creation_scope_and_duplicate_prevention(self):
        event = self.event()
        self.assertEqual(generate_notifications_for_user(self.teacher), 1)
        self.assertEqual(generate_notifications_for_user(self.teacher), 0)
        self.assertEqual(Notification.objects.filter(calendar_entry=event).count(), 1)
        self.assertEqual(generate_notifications_for_user(self.other_teacher), 0)

    def test_read_api_is_self_only_and_unauthenticated_is_rejected(self):
        event = self.event(calendar_date=date.today())
        generate_notifications_for_user(self.teacher)
        self.client.force_authenticate(self.teacher)
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        notification_id = response.data['results'][0]['id']
        self.assertEqual(self.client.post(f'/api/notifications/{notification_id}/mark_read/').status_code, 200)
        self.assertEqual(self.client.get('/api/notifications/unread_count/').data['count'], 0)
        self.client.force_authenticate(self.other_teacher)
        self.assertEqual(self.client.get(f'/api/notifications/{notification_id}/').status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/notifications/').status_code, 401)

    def test_pending_approval_only_notifies_authorized_approver(self):
        creator = get_user_model().objects.create_user(username='notification_creator', password='pass')
        UserProfile.objects.create(user=creator, role_name='TEACHER')
        event = self.event(status='PENDING_APPROVAL', created_by=creator)
        self.assertEqual(generate_notifications_for_user(self.admin), 1)
        self.assertEqual(generate_notifications_for_user(creator), 0)
        self.assertFalse(Notification.objects.filter(recipient=self.teacher, calendar_entry=event).exists())

    def test_deadline_examination_and_suspension_types(self):
        examination = self.event(day_type='EXAMINATION', title='Midterm', scope_type='SCHOOL_WIDE', examination_type='MIDTERM', section=None)
        deadline = self.event(day_type='ACADEMIC_DEADLINE', title='Grades due', scope_type='SCHOOL_WIDE', event_type='GRADE_SUBMISSION', section=None)
        suspension = self.event(day_type='SUSPENSION', title='Suspension', scope_type='SCHOOL_WIDE', classes_suspended=True, section=None, suspension_type='OTHER')
        enrollment = self.event(day_type='ENROLLMENT', title='Enrollment deadline', scope_type='SCHOOL_WIDE', event_type='ENROLLMENT_DEADLINE', section=None)
        generate_notifications_for_user(self.admin)
        self.assertEqual(set(Notification.objects.values_list('notification_type', flat=True)), {'EXAMINATION', 'ACADEMIC_DEADLINE', 'SUSPENSION', 'ENROLLMENT_DEADLINE'})
        self.assertEqual(Notification.objects.filter(calendar_entry__in=[examination, deadline, suspension, enrollment]).count(), 4)

    def test_cancelled_rejected_and_archived_events_are_suppressed(self):
        for status in ('CANCELLED', 'REJECTED', 'ARCHIVED'):
            self.event(title=status, status=status, cancellation_reason='No longer applicable' if status != 'REJECTED' else '', rejection_reason='Not approved' if status == 'REJECTED' else '')
        self.assertEqual(generate_notifications_for_user(self.admin), 0)

    def test_cancellation_suppresses_existing_due_notification(self):
        event = self.event(calendar_date=date.today())
        generate_notifications_for_user(self.teacher)
        event.status = 'CANCELLED'
        event.cancellation_reason = 'No longer applicable'
        event.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
        self.client.force_authenticate(self.teacher)
        self.assertEqual(self.client.get('/api/notifications/').data['count'], 0)

    def test_recurring_occurrence_links_without_generating_occurrences(self):
        recurring = RecurringSchoolCalendarEvent.objects.create(
            academic_year=self.year, title='Weekly meeting', day_type='SCHOOL_EVENT', start_date=date.today(), recurrence_end_date=date.today() + timedelta(days=10),
            frequency='DAILY', recurrence_interval=1, scope_type='SCHOOL_WIDE', active=True, created_by=self.admin,
        )
        event = self.event(title='Weekly meeting', scope_type='SCHOOL_WIDE', section=None, recurrence=recurring)
        before = SchoolCalendarDay.objects.count()
        generate_notifications_for_user(self.admin)
        self.assertEqual(SchoolCalendarDay.objects.count(), before)
        self.assertEqual(Notification.objects.get(calendar_entry=event).recurring_event_id, recurring.id)

    def test_attendance_count_is_unchanged(self):
        before = AttendanceRecord.objects.count()
        generate_notifications_for_user(self.admin)
        self.assertEqual(AttendanceRecord.objects.count(), before)