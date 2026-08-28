# Priority 6 Issue 5.11 Notifications & Reminders Report

## 1. Architecture inspected

The existing `attendance.SchoolCalendarDay` remains the dated calendar source, and `attendance.RecurringSchoolCalendarEvent` remains the recurrence definition. Existing approval, publishing, cancellation, conflict detection, academic-year, role, section, audit, frontend routing, and notification drawer paths were inspected.

## 2. Existing notification infrastructure

No backend notification model, service, API, or verified external notification infrastructure existed. The frontend drawer contained prediction dashboard placeholders and the top-bar badge was hard-coded to zero.

## 3. Architecture selected

A separate `notifications` Django app was added. `Notification` stores the recipient, type, title, message, dated calendar entry, recurring definition link, scheduled time, read time, expiration, creation time, and a unique idempotency key. Notifications are informational in-system records only; no email, SMS, push, or external delivery is performed.

## 4. Files changed

- `BACKEND/notifications/apps.py`
- `BACKEND/notifications/models.py`
- `BACKEND/notifications/services.py`
- `BACKEND/notifications/serializers.py`
- `BACKEND/notifications/api.py`
- `BACKEND/notifications/tests.py`
- `BACKEND/notifications/migrations/0001_initial.py`
- `BACKEND/config/settings.py`
- `BACKEND/config/urls.py`
- `FRONTEND/src/services/attendanceService.js`
- `FRONTEND/src/components/layout/NotificationDrawer.jsx`
- `FRONTEND/src/components/layout/TopBar.jsx`
- `PRIORITY6_ISSUE5_11_NOTIFICATIONS_REMINDERS_REPORT.md`

Existing uncommitted attendance models/migrations, UAT tooling, and earlier reports were preserved.

## 5. API changes

Added authenticated `GET /api/notifications/`, `GET /api/notifications/unread_count/`, `GET /api/notifications/{id}/`, `POST /api/notifications/{id}/mark_read/`, and `POST /api/notifications/mark-all-read/`. Querysets are restricted to the authenticated recipient and due, unexpired notifications. No arbitrary notification creation or administrative mutation endpoint is exposed.

## 6. Frontend changes

The existing notification drawer now reads calendar notifications, displays title/message/read state, marks an item read when opened, and links calendar notifications to the existing calendar page. The existing top-bar bell now retrieves and displays the authenticated user's unread count.

## 7. Notification types

- `APPROVAL_PENDING`
- `CALENDAR_EVENT`
- `EXAMINATION`
- `ENROLLMENT_DEADLINE`
- `ACADEMIC_DEADLINE`
- `SUSPENSION`

## 8. Reminder scheduling behavior

Pending approval reminders are scheduled immediately for authorized school administrators. Upcoming dated events are prepared for a deterministic 09:00 Asia/Manila reminder on the day before the event, with same-day events due immediately. API reads expose only reminders whose scheduled time has arrived. The service uses existing dated calendar occurrences and does not generate recurrence occurrences.

## 9. Duplicate prevention

A unique database-backed idempotency key combines recipient, event, and notification/reminder type. Repeated generation returns no duplicate rows.

## 10. Authorization and scope behavior

Only the recipient can list, retrieve, read, or mark a notification. Administrators, registrars, and guidance personnel receive permitted school calendar reminders. Teachers receive published school-wide reminders, assigned section/grade/department reminders, or events for which they are the instructor. Section and grade checks use existing teacher assignment/adviser relationships.

## 11. Approval integration

Only `PENDING_APPROVAL` events produce approval reminders, and only school administrators receive them. The creator is excluded. Approved/published event reminders do not imply approval for a creator's pending event.

## 12. Cancellation/rejection behavior

`CANCELLED`, `REJECTED`, and `ARCHIVED` events are excluded from generation. Existing future reminders are naturally suppressed from API reads when their event is no longer an eligible dated occurrence; no attendance data is touched.

## 13. Recurring-event behavior

Notifications are created against already-generated `SchoolCalendarDay` occurrences and retain the related `RecurringSchoolCalendarEvent` reference. Notification generation does not call occurrence generation and does not create calendar rows.

## 14. Attendance safety verification

Focused tests verify `AttendanceRecord` count stability and no attendance mutation during notification generation. No attendance algorithm, expected-school-day logic, attendance status, holiday behavior, suspension behavior, or encoding code was changed.

## 15. ML artifact safety verification

No prediction service, Random Forest code, model artifact, label encoder, feature mapping, or prediction methodology was modified or regenerated.

## 16. UCI dataset verification

No UCI or dataset file was modified. No dataset regeneration was run.

## 17. Migration status

`notifications.0001_initial` was created and inspected. It was used by isolated Django tests only and was not applied to the live `edu_assist` database. `makemigrations --check --dry-run` reports only pre-existing drift in `accounts` and `audit`; no Issue 5.11 drift remains.

## 18. Exact test results

- `manage.py check`: passed.
- Focused Issue 5.11 tests: 8 passed.
- Exact required regression command `manage.py test attendance.tests predictions.tests tests.test_authorization --keepdb`: 62 passed; Django discovered 85 test entries in the repository setup.
- Focused frontend ESLint for changed files: passed.
- `npm run build`: passed; Vite reported the existing large-chunk warning.
- `git diff --check`: passed.

## 19. Database safety verification

Django test commands used the isolated test database (`--keepdb` test database), not `edu_assist`. No live migration, destructive command, reset, flush, delete, truncate, drop, database recreation, or production data creation was run. No UAT administrator account or temporary live record was created.

## 20. Known limitations

- Generation is triggered when the authenticated user reads notifications or unread count; a background scheduler is not installed.
- Participant records do not have user accounts in the existing schema, so recipient scope is based on existing staff roles, teacher assignments, adviser sections, instructor, grade, department, and calendar scope.
- Frontend navigation opens the existing calendar page rather than a date-specific calendar route.
- Browser-level UAT verification was not repeated in this implementation pass.
- Existing repository-wide migration drift in `accounts` and `audit` remains unrelated and unapplied.

## 21. Final implementation classification

**IMPLEMENTED WITH LIMITATIONS**. Issue 5.11 is implemented as a controlled, authenticated, idempotent in-system reminder layer on the existing calendar architecture, with approval/lifecycle/scope protections and attendance/ML safety checks. No external notifications are sent.
