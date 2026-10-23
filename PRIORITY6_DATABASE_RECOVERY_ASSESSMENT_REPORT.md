# PRIORITY 6 - DATABASE RECOVERY ASSESSMENT

## Investigation status

**Completed. Read-only investigation only.** No database restoration, import, migration, seed, flush, schema change, file deletion, backup modification, or Git history change was performed.

Investigation date: 2026-08-27

## 1. Current database state

### Confirmed facts

- Active Django settings: `BACKEND/config/settings.py`.
- Engine: `config.mysql_compat` using MariaDB compatibility.
- Database: `edu_assist`.
- Host and port: `127.0.0.1:3306`.
- User: `root`.
- Runtime mode: `DEBUG=True`.
- The live database is reachable and contains 34 tables.
- Read-only ORM counts:

| Table/model | Rows |
|---|---:|
| `auth_user` | 1 |
| `accounts_userprofile` | 1 |
| `students_student` | 0 |
| `academics_academicyear` | 1 |
| `academics_gradelevel` | 0 |
| `academics_section` | 0 |
| `academics_enrollment` | 0 |
| `academics_academicrecord` | 0 |
| `attendance_schoolcalendarday` | 0 |
| `attendance_attendancerecord` | 0 |
| `behavior_behavioralassessment` | 0 |
| `interventions_intervention` | 0 |
| `predictions_riskprediction` | 0 |
| `predictions_predictionfactor` | 0 |
| `audit_auditlog` | 0 |

### Observation

The database is reachable but contains almost none of the operational EDU ASSIST data expected before the reported flush.

## 2. Read-only confirmation

The investigation used only configuration reads, filesystem enumeration, Git read commands, Django migration-plan inspection, MySQL `SHOW` statements, `information_schema` reads, and Django ORM `COUNT`/read queries. No write SQL or write-capable Django command was executed.

## 3. Recovery sources searched

### Repository

- Database dumps and compressed dumps: `*.sql`, `*.sql.gz`, `*.bak`, `*.dump`.
- Backup, dump, fixture, seed, export, database, archive, Docker, MySQL, MariaDB, XAMPP, WAMP, and phpMyAdmin paths.
- JSON/CSV/SQLite candidates.
- Text references to `edu_assist`, `mysqldump`, `backup`, `fixture`, `loaddata`, `seed`, `dump`, and `sqlite`.
- Git history and deleted paths.

### Local environment

- MariaDB data directory: `F:\New folder\mysql\data\`.
- Relevant database directories: `edu_assist`, `edu_assist_db`, and `test_edu_assist`.
- Other clearly named local databases visible to the server: `test` and `edu_assist_db`.
- MariaDB binary-log status and data-directory configuration.

## 4. Recovery sources discovered

No verified recovery source containing the missing historical records was found.

| Source | Type/size/timestamp | Evidence and recoverability | Predates flush? | Confidence |
|---|---|---|---|---|
| `BACKEND/students/management/commands/seed_demo_data.py` | Source seed command; tracked Git file | Generates demo data; it is not an export of the prior database and cannot recover original records. It must not be executed during this investigation. | Not applicable | High |
| `BACKEND/verify_seed.py` | Source verification script | Verification tooling, not a data snapshot. | Not applicable | High |
| `BACKEND/scripts/dump_users_api.py` | Source/API dump utility | Concerns user API output, not a complete database backup. | Not established | High |
| `AI (ML)/dataset/*` and preprocessing CSVs | ML datasets/derived CSVs | Model training data, not EDU ASSIST application records. Must remain unchanged. | Not a database backup | High |
| `test_edu_assist` | Existing separate MariaDB database | Contains 45 migration rows and an obsolete `attendance_recurringcalendarevent` table, but zero users, students, academic years, enrollments, academic records, attendance, calendar, behavior, intervention, prediction, and audit rows. | Created/updated around 2026-08-25/26; not historical application data | High |
| `edu_assist_db` | Existing legacy MariaDB database | Different table naming/schema; relevant data tables are zero rows, with only 4 rows in `intervention_recommendations`. It is not a compatible snapshot of the current Django database. | Not established | High |
| `F:\New folder\mysql\data\edu_assist` | Live MariaDB schema directory | Physical files belong to the active database instance, not an independently verified backup. The current database contents are already known to be partial. | Not applicable | High |

No project-level SQL dump, fixture export, SQLite copy, ZIP backup, or other complete database snapshot was located in the repository search.

## 5. MySQL/MariaDB recovery metadata

### Confirmed facts

- Server version: MariaDB `10.4.32`.
- Configured data directory: `F:\New folder\mysql\data\`.
- `@@log_bin=0`.
- `SHOW MASTER STATUS` returned no usable status.
- `SHOW BINARY LOGS` reported that binary logging is not in use.
- Therefore, binary-log point-in-time recovery is not available from this server configuration.
- `test_edu_assist` exists but is not a usable recovery source based on its zero operational rows.

### Unknowns

- External backups, Windows volume snapshots, cloud backups, and copies outside the inspected locations were not available for verification.
- The exact flush timestamp and original pre-flush row counts are not independently recorded in the current database.

## 6. Git and project history

### Confirmed facts

- Branch: `main`.
- Current commit: `8618b34`.
- Tag `pre-uci-ai-model-integration` exists.
- The worktree was already dirty before this investigation, with modified source files and untracked reports/migrations. Those changes were preserved.
- Git history contains the demo seed command and ML data files, but no committed SQL dump or complete application database export was found.
- Git history contains `BACKEND/scripts/dump_users_api.py`, but that is not a full database backup.

### Migration state

Read-only `python manage.py showmigrations --plan` showed these attendance migrations applied:

- `attendance.0001_initial`
- `attendance.0002_schoolcalendarday_attendance_date`
- `attendance.0003_...`
- `attendance.0004_...`

These attendance migrations were unapplied in the current database:

- `attendance.0005_...`
- `attendance.0006_...`
- `attendance.0007_...`

This is a source/schema alignment issue to resolve later under an approved recovery plan. No migration was run.

## 7. Recoverability classification

# D. NO RECOVERY SOURCE FOUND

This classification means no verified source containing the missing historical EDU ASSIST records was found. The seed command, ML datasets, legacy database, and empty test database are not valid substitutes for a backup of the original application database.

## 8. Data that may be recoverable

- The missing student, enrollment, academic, attendance, calendar, behavioral, intervention, prediction, and audit records may still be recoverable from an external or uninspected backup, snapshot, export, or another machine.
- The single current user and academic-year records remain present in `edu_assist`, but they are not evidence that the missing historical data is recoverable.
- Git can recover source code and migration history, but not database rows that were never committed or exported.

## 9. Data not currently verified as recoverable

- Historical students and their identifiers/details.
- Sections, enrollments, and academic records.
- School calendar holidays, suspensions, events, and activities.
- Attendance records.
- Behavioral assessments and interventions.
- Risk predictions and prediction factors.
- Audit history.
- Original database timestamps and pre-flush row counts.

## 10. Recommended recovery strategy

1. Preserve the current `edu_assist` database and do not treat it as a complete source of truth.
2. Obtain an external SQL dump, MariaDB backup, Windows snapshot, or server-level backup from before the accidental flush.
3. Preserve any discovered backup as an immutable copy and verify its checksum and timestamp before inspection.
4. Restore only into an isolated MariaDB database first, never directly over `edu_assist`.
5. Compare restored schema, migration history, and row counts against the source tree and available project reports.
6. Obtain explicit approval before any production of a recovery database, import, merge, or replacement of `edu_assist`.

## 11. Safety risks

- The active `manage.py` configuration targets `edu_assist`, not a dedicated test database.
- A test database exists but is empty of useful application data and contains stale schema remnants; it is not a recovery copy.
- Running tests without deliberate database isolation can create or alter test databases.
- Running a seed command would create new demo records, not recover the original records.
- The database schema is not fully aligned with the current migration files because attendance migrations `0005`-`0007` are unapplied.
- Binary logging is disabled, eliminating one possible server-side recovery path.
- Existing uncommitted source changes must be preserved.

## 12. Commands/actions that MUST NOT be executed yet

Do not execute:

- `python manage.py flush`
- `python manage.py migrate`
- `python manage.py makemigrations`
- Any seed command, including `python manage.py seed_demo_data`
- Any fixture loading command, including `python manage.py loaddata`
- Any database reset, recreate, drop, truncate, or delete operation
- Any `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`, `DROP`, `ALTER`, or restore/import SQL
- Any `mysqldump` command directed at overwriting an existing file
- Any command that enables, disables, purges, or resets binary logs
- `git reset`, `git checkout`, `git restore`, `git clean`, or any revert/stash operation
- Any modification to the Random Forest model, UCI dataset, migrations, or Issues 5.1-5.4 implementation

## 13. Final recommendation

Stop database recovery actions at this point. The investigation is complete, no verified recovery source was found, and the correct classification is **D. NO RECOVERY SOURCE FOUND**. Continue only after locating and validating an external recovery source and receiving explicit approval for an isolated restoration procedure.

## Final safety record

- Investigation: completed.
- Recovery classification: D.
- Recovery source found: none verified.
- Current database: accessible, partially populated, and missing core operational records.
- Database writes: none.
- Source files modified: only this new report was created; application source and migrations were not modified.
- Git state changed: no. Existing dirty worktree was preserved.
- Report path: `PRIORITY6_DATABASE_RECOVERY_ASSESSMENT_REPORT.md`.

---

## Final reset-readiness follow-up — 2026-10-20

This is a read-only follow-up to the October 20 addendum. It is not authorization to reset. No credentials, data, schema, or Git history were changed, and no tests or automated verification suites were run.

### 1. Administrator password status

**NOT VERIFIED.** The required plaintext password is not available in the current context through an approved secure mechanism. The stored hash was not printed or compared; there was no login attempt and no credential or permission change. The existing `EDU_admin` account remains observed with the supported application role `SUPER_ADMIN`.

If a secure comparison later becomes possible, use a local, non-login comparison against Django's stored password hash without displaying either value or logging the input. If that comparison returns `NO MATCH`, stop and obtain separate approval before changing credentials. The approved correction procedure should prompt for the new password without echo or command-line arguments, hold it only in process memory, update via Django's password-setting API, save only the password field, and verify without outputting the secret. If role correction is separately approved, update only the existing profile's `role_name` to `SUPER_ADMIN`. Do not make either correction as part of a reset approval by implication.

### 2. Backup integrity, protection, and recoverability

- The reported backup exists at `BACKEND/db_backups/edu_assist_pre_reset_20261020.sql`.
- Current size: **253,081 bytes**. Current SHA-256 matches the report: `e56a4aaab04783cba2e7a43ae2e94f8e03afaaecd02b65c26bac21305debe86d`.
- Git inspection: the backup is **not tracked**, **not ignored**, and **not staged**. Git reports it as untracked (`??`). No repository ignore rule protects it from accidental staging.
- No independent protected copy of this exact backup is known or verified. The other visible older backups are different files and do not count as independent copies of this snapshot. Before any reset, create a second access-controlled copy outside the working tree and verify its checksum against the value above. Do not publish or stage either copy.
- Structure-only inspection found `CREATE TABLE` statements for all 37 active database tables and 1,133 single-row `INSERT` statements across 29 nonempty tables. The other eight tables were empty in the snapshot. The dump has a completed-dump marker and explicit database creation/selection statements. No row contents were printed.
- The active schema currently has zero stored routines, zero scheduled events, and zero triggers; the dump also has no routine/event/trigger definitions. Thus no such objects are currently omitted.
- This confirms dump structure and coverage, **not successful restoration**. The backup has not been imported or restored, and server grants, binary logs, uploaded/media files, and external model/data files are not covered.
- For any later recovery rehearsal, preserve the original dump unchanged. Because it contains `CREATE DATABASE`/`USE edu_assist`, prepare a separate temporary working copy with those database statements changed to a unique isolated database name before importing. Compare schema, constraints, and table counts only in that isolated database. Do not import this file directly into the active database.

No integrity discrepancy was found in the reported file size or checksum. The Git-protection and independent-copy risks remain unresolved readiness items.

### 3. Foreign-key findings and deletion semantics

The active database has **71 foreign-key constraints** across the 37 tables. Every inspected MariaDB constraint reports physical `DELETE_RULE=RESTRICT` and `UPDATE_RULE=RESTRICT`. Django model `on_delete` behavior is implemented by Django's deletion collector; it does not change these physical MariaDB rules. The loaded model definitions use `CASCADE` and `SET_NULL`; no `PROTECT` relation was found among the loaded models. Consequently, direct SQL deletes must explicitly follow child-before-parent order; an expected ORM cascade or set-null must not be assumed to happen in the database itself.

The only schema relations not mapped to a loaded Django model are the two token-blacklist relations (the blacklist tables are present in the database but the app is not loaded by active settings). Their physical foreign keys are still `RESTRICT`; both tables currently have zero rows and are proposed for clearing. The `accounts_userprofile.user_id` one-to-one relation is Django `CASCADE`.

The following registry lists every inspected FK by child column and referenced parent. The action in brackets is the Django model's `on_delete`; all listed physical MariaDB constraints are `RESTRICT`. Reading a link as `child.column -> parent.id` also identifies the incoming FK on the parent table.

| Child table | Outgoing foreign keys |
|---|---|
| `academics_academicrecord` | `encoded_by_id -> auth_user.id` (SET_NULL); `academic_year_id -> academics_academicyear.id` (CASCADE); `enrollment_id -> academics_enrollment.id` (CASCADE); `subject_id -> academics_subject.id` (CASCADE) |
| `academics_enrollment` | `student_id -> students_student.id` (CASCADE); `strand_id -> academics_strand.id` (SET_NULL); `section_id -> academics_section.id` (CASCADE); `grade_level_id -> academics_gradelevel.id` (CASCADE); `academic_year_id -> academics_academicyear.id` (CASCADE) |
| `academics_section` | `specialization_id -> academics_specialization.id` (SET_NULL); `grade_level_id -> academics_gradelevel.id` (CASCADE); `adviser_id -> auth_user.id` (SET_NULL); `academic_year_id -> academics_academicyear.id` (CASCADE); `strand_id -> academics_strand.id` (SET_NULL) |
| `academics_specialization` | `strand_id -> academics_strand.id` (CASCADE) |
| `academics_subject` | `strand_id -> academics_strand.id` (SET_NULL); `grade_level_id -> academics_gradelevel.id` (CASCADE) |
| `academics_subject_grade_levels` | `gradelevel_id -> academics_gradelevel.id` (CASCADE); `subject_id -> academics_subject.id` (CASCADE) |
| `academics_teacherassignment` | `section_id -> academics_section.id` (CASCADE); `grade_level_id -> academics_gradelevel.id` (CASCADE); `academic_year_id -> academics_academicyear.id` (CASCADE); `teacher_id -> auth_user.id` (CASCADE); `subject_id -> academics_subject.id` (CASCADE) |
| `accounts_userprofile` | `user_id -> auth_user.id` (CASCADE) |
| `accounts_userprofile_assigned_sections` | `userprofile_id -> accounts_userprofile.id` (CASCADE); `section_id -> academics_section.id` (CASCADE) |
| `attendance_attendancerecord` | `encoded_by_id -> auth_user.id` (SET_NULL); `enrollment_id -> academics_enrollment.id` (CASCADE) |
| `attendance_recurringschoolcalendarevent` | `created_by_id -> auth_user.id` (SET_NULL); `affected_grade_level_id -> academics_gradelevel.id` (SET_NULL); `academic_year_id -> academics_academicyear.id` (CASCADE); `section_id -> academics_section.id` (CASCADE) |
| `attendance_schoolcalendarday` | `affected_grade_level_id -> academics_gradelevel.id` (SET_NULL); `recurrence_id -> attendance_recurringschoolcalendarevent.id` (SET_NULL); `academic_year_id -> academics_academicyear.id` (CASCADE); `instructor_id -> auth_user.id` (SET_NULL); `submitted_by_id -> auth_user.id` (SET_NULL); `created_by_id -> auth_user.id` (SET_NULL); `subject_id -> academics_subject.id` (SET_NULL); `authorized_by_id -> auth_user.id` (SET_NULL); `section_id -> academics_section.id` (CASCADE); `approved_by_id -> auth_user.id` (SET_NULL); `rejected_by_id -> auth_user.id` (SET_NULL) |
| `audit_auditlog` | `user_id -> auth_user.id` (SET_NULL) |
| `auth_group_permissions` | `group_id -> auth_group.id` (CASCADE); `permission_id -> auth_permission.id` (CASCADE) |
| `auth_permission` | `content_type_id -> django_content_type.id` (CASCADE) |
| `auth_user_groups` | `user_id -> auth_user.id` (CASCADE); `group_id -> auth_group.id` (CASCADE) |
| `auth_user_user_permissions` | `user_id -> auth_user.id` (CASCADE); `permission_id -> auth_permission.id` (CASCADE) |
| `behavior_behavioralassessment` | `rating_id -> behavior_behavioralrating.id` (SET_NULL); `enrollment_id -> academics_enrollment.id` (CASCADE); `core_value_id -> behavior_corevalue.id` (CASCADE); `behavior_indicator_id -> behavior_behaviorindicator.id` (CASCADE); `assessed_by_id -> auth_user.id` (SET_NULL); `academic_year_id -> academics_academicyear.id` (CASCADE) |
| `behavior_behaviorindicator` | `core_value_id -> behavior_corevalue.id` (CASCADE) |
| `django_admin_log` | `content_type_id -> django_content_type.id` (SET_NULL); `user_id -> auth_user.id` (CASCADE) |
| `interventions_intervention` | `enrollment_id -> academics_enrollment.id` (CASCADE); `assigned_personnel_id -> auth_user.id` (SET_NULL) |
| `notifications_notification` | `recipient_id -> auth_user.id` (CASCADE); `recurring_event_id -> attendance_recurringschoolcalendarevent.id` (CASCADE); `calendar_entry_id -> attendance_schoolcalendarday.id` (CASCADE) |
| `predictions_predictionfactor` | `prediction_id -> predictions_riskprediction.id` (CASCADE) |
| `predictions_riskprediction` | `reviewed_by_id -> auth_user.id` (SET_NULL); `enrollment_id -> academics_enrollment.id` (CASCADE) |
| `token_blacklist_blacklistedtoken` | `token_id -> token_blacklist_outstandingtoken.id` (model not loaded; physical RESTRICT) |
| `token_blacklist_outstandingtoken` | `user_id -> auth_user.id` (model not loaded; physical RESTRICT) |
| `All other tables` | No outgoing FK constraints. Their incoming FKs, if any, are listed above under the child table. |

This registry contains 71 outgoing constraints. There is no FK cycle: a topological sort covered all 37 tables. The sequence below is a child-before-parent order for the proposed 29 `CLEAR`/`TARGETED DELETE` tables. The eight `PRESERVE` tables are deliberately excluded; each remains available as a referenced parent.

### 4. Complete table actions and dependency-aware deletion order

The row counts below are the current live counts observed during this follow-up and match the counts captured with the backup. `CLEAR` and `TARGETED DELETE` describe only a future proposal; no deletion has occurred.

| Order | Table | Rows | Proposed action |
|---:|---|---:|---|
| 1 | `academics_academicrecord` | 62 | CLEAR |
| 2 | `academics_subject_grade_levels` | 38 | CLEAR |
| 3 | `academics_teacherassignment` | 15 | CLEAR |
| 4 | `accounts_userprofile_assigned_sections` | 6 | TARGETED DELETE |
| 5 | `attendance_attendancerecord` | 30 | CLEAR |
| 6 | `audit_auditlog` | 404 | CLEAR |
| 7 | `auth_user_groups` | 0 | TARGETED DELETE |
| 8 | `auth_user_user_permissions` | 0 | TARGETED DELETE |
| 9 | `behavior_behavioralassessment` | 24 | CLEAR |
| 10 | `django_admin_log` | 0 | CLEAR |
| 11 | `django_session` | 96 | CLEAR |
| 12 | `interventions_intervention` | 3 | CLEAR |
| 13 | `notifications_notification` | 10 | CLEAR |
| 14 | `predictions_predictionfactor` | 52 | CLEAR |
| 15 | `token_blacklist_blacklistedtoken` | 0 | CLEAR |
| 16 | `accounts_userprofile` | 18 | TARGETED DELETE |
| 17 | `attendance_schoolcalendarday` | 52 | CLEAR |
| 18 | `predictions_riskprediction` | 14 | CLEAR |
| 19 | `token_blacklist_outstandingtoken` | 0 | CLEAR |
| 20 | `academics_subject` | 11 | CLEAR |
| 21 | `attendance_recurringschoolcalendarevent` | 0 | CLEAR |
| 22 | `academics_enrollment` | 11 | CLEAR |
| 23 | `academics_section` | 7 | CLEAR, subject to preserving any administrator-linked section discovered on the final recheck |
| 24 | `students_student` | 12 | CLEAR |
| 25 | `academics_academicyear` | 12 | CLEAR |
| 26 | `academics_gradelevel` | 14 | CLEAR |
| 27 | `academics_specialization` | 1 | CLEAR |
| 28 | `academics_strand` | 1 | CLEAR |
| 29 | `auth_user` | 18 | TARGETED DELETE |

| Table | Rows | Proposed action |
|---|---:|---|
| `auth_group` | 0 | PRESERVE |
| `auth_group_permissions` | 0 | PRESERVE |
| `auth_permission` | 116 | PRESERVE |
| `behavior_behavioralrating` | 4 | PRESERVE |
| `behavior_behaviorindicator` | 8 | PRESERVE |
| `behavior_corevalue` | 8 | PRESERVE |
| `django_content_type` | 29 | PRESERVE |
| `django_migrations` | 57 | PRESERVE |

The sequence resolves dependencies including grade/subject join rows, academic records before enrollment/year/subject, assessment factors before predictions, notifications before calendar entries, calendar entries before recurring events and their academic references, and non-admin profile joins/profiles before their referenced sections/users. No `PROTECT` relation or FK cycle was found. Because MariaDB physically enforces `RESTRICT`, the sequence must be followed explicitly for any approved SQL-level plan. ORM deletes must also be reviewed carefully: Django's collector may apply `CASCADE`/`SET_NULL` behavior not enforced by the database, and must not be allowed to remove the protected account/profile.

#### Exact preservation procedure if other accounts are in scope

Only after separate approval, re-read the target username and primary key and confirm its linked profile still has `role_name='SUPER_ADMIN'`. Define the protected user by that exact primary key, not by a broad username pattern. Perform only the targeted child/link cleanup in the order above. In `accounts_userprofile_assigned_sections`, preserve rows whose profile belongs to the protected user; in `accounts_userprofile`, preserve the exact profile row linked to that user; in `auth_user`, delete only rows whose primary key differs from the protected ID. Preserve any group/direct permission links for that same ID. Recheck any `assigned_sections` links immediately before deleting sections; the current account has none, but if any appear, retain their sections and the parent records they depend on. Verify the protected account/profile identifiers and canonical role after the approved operation. Never use `flush`, table-wide `TRUNCATE`, `DROP`, or table recreation.

### 5. Final readiness checklist

| Readiness item | Status | Finding / prerequisite |
|---|---|---|
| Backup file integrity | READY, limited to file integrity | Size and SHA-256 match the reported values; dump structure covers all 37 tables and all 1,133 rows. |
| Independent protected backup copy | READY, LOCAL COPY | A verified copy now exists at `C:\Users\user\Documents\EDU_ASSIST_Backups\edu_assist_pre_reset_20261020.sql`; see the final backup-protection follow-up below. It is on a separate partition but the same physical disk, so it does not protect against disk failure. |
| Git protection | PARTIALLY READY | The repository source remains untracked and not ignored, but is not staged or committed. The verified copy is outside the Git repository. Do not stage either file; an approved ignore/storage policy is still advisable. |
| Restore/recovery confidence | NOT VERIFIED | Dump has not been restored. Rehearse only in an isolated database using a temporary copy with its embedded database name redirected. |
| Admin account and profile preservation | READY AS OBSERVED; RECHECK REQUIRED | `EDU_admin` id 25 and profile id 25 exist; role is `SUPER_ADMIN`. Reconfirm exact IDs and role immediately before any approved reset. |
| Required admin password | NOT VERIFIED | Password was unavailable for safe non-login comparison; do not treat account credentials as confirmed. Follow the separate-approval correction procedure if needed. |
| Required framework and lookup data | PLAN READY | Preserve auth group/permission tables, content types, migration history, and behavior lookup tables. |
| Complete table scope and FK order | PLAN READY, RECHECK REQUIRED | All 37 tables and 71 FKs are represented; all physical FKs are RESTRICT; no cycle found. Recheck counts and admin section links before approval. |
| Data-loss scope | REVIEW REQUIRED | Proposed clears include 70 admin-linked audit entries, 33 calendar entries created by the account, and five admin notifications; these are not needed for authorization but would be lost. |
| Explicit approval | NOT GRANTED | This report is planning only. Do not perform any delete, reset, restore, migration, seed, or credential correction until the user reviews and explicitly approves the exact operation. |

**Readiness conclusion: NOT READY for a destructive reset.** The backup's file integrity and schema/data coverage are confirmed, and the FK plan is complete. The password remains unverified, restore compatibility has not been demonstrated, both backup copies share one physical disk, and explicit reset approval has not been granted. No reset or restore is authorized by this review.

---

## Addendum — pre-reset backup and administrator-preservation plan

Inspection date: 2026-10-20. This addendum records a newer read-only inspection and supersedes the earlier database counts and backup-availability observations above for the current reset proposal. The earlier report remains an accurate record of its 2026-08-27 inspection.

### Current database and backup

- Active Django settings: `BACKEND/config/settings.py`; engine: `config.mysql_compat`; database: `edu_assist`; host/port: `127.0.0.1:3306`; configured user: `root`.
- Current schema: 37 base tables and 1,133 rows at the backup snapshot.
- A new logical MariaDB backup was created at `BACKEND/db_backups/edu_assist_pre_reset_20261020.sql` (253,081 bytes).
- SHA-256: `e56a4aaab04783cba2e7a43ae2e94f8e03afaaecd02b65c26bac21305debe86d`.
- Verification: the dump contains DDL for all 37 database tables; the dump used one row per INSERT, and each table's INSERT count matched a fresh exact row count from the active database. The dump command requested routines, events, and triggers. No restore was attempted.
- This is a database logical backup, not a backup of MariaDB server grants, binary logs, uploaded/media files, or external model/data files. Keep this sensitive dump local, do not commit or upload it, and retain an independent protected copy plus checksum before any separately approved reset.

### Administrator account and authorization findings

- `EDU_admin` exists in `auth_user` with primary key `25`; `is_active=True`.
- Its linked `accounts_userprofile` row has primary key `25` and `role_name='SUPER_ADMIN'`. The requested `SUuperAdmin` is not a supported value; `SUPER_ADMIN` is the application-supported canonical role.
- The password field uses the `pbkdf2_sha256` Django hash format. The required plaintext password was not available in the context used for this inspection, so the stored hash could not be compared to it. No login was attempted, no password check was run, and no tests were run. The password match is **unverified**.
- `is_staff=False` and `is_superuser=False`. Application authorization is role-based: `accounts.permissions.IsSuperAdmin` grants the SuperAdmin permission when the authenticated user's profile role is exactly `SUPER_ADMIN`; `IsSchoolAdmin` also includes that role. Login uses Django `authenticate`, and the API issues JWTs. Therefore the profile role is what grants application SuperAdmin access. These flag values do not grant access to Django's built-in admin site.
- No Django `PASSWORD_HASHERS` override is set in active settings; the observed format is Django's `pbkdf2_sha256` format.
- Current auth links: no group memberships, direct user permissions, or assigned profile sections. The profile-to-section association table currently has no row for this account.
- Other nonzero account-linked data found: 33 school-calendar rows reference this user as creator, 70 audit rows reference this user, and 5 notifications have this user as recipient. These are application records, not dependencies required to authenticate or receive the `SUPER_ADMIN` role.

### Account dependency inventory

The following relationships must be considered when preparing a reset:

| Relationship/table | Reset treatment |
|---|---|
| `auth_user` row for `EDU_admin` | Preserve this exact row; never truncate or flush the shared table. |
| `accounts_userprofile` row for user id 25 | Preserve; its `role_name='SUPER_ADMIN'` is the application's administrator authorization source. |
| `accounts_userprofile_assigned_sections` | Preserve any rows for profile id 25 and any section rows they reference. There are currently zero such rows. |
| `auth_user_groups`, `auth_user_user_permissions` | Preserve any rows belonging to user id 25; currently both counts are zero. |
| `auth_group`, `auth_group_permissions`, `auth_permission`, `django_content_type` | Preserve authorization/catalog metadata; do not reset these shared framework tables. Current group tables are empty; permission and content-type catalogs are populated. |
| `django_migrations` | Preserve migration history; do not reset or modify schema metadata. |
| User-linked domain rows | These are not needed for authentication. Resetting them may remove audit/calendar history or notifications; include that data loss explicitly in the approved scope. |

Database foreign keys also connect `auth_user` to profiles, academic records/sections/teacher assignments, attendance/calendar records, audit logs, behavior assessments, interventions, notifications, prediction reviews, admin logs, and token records. The plan below clears or targets those data tables while retaining the account row; it must be applied in FK-safe child-first order and must not use `TRUNCATE`/`flush`.

### Proposed table-by-table reset plan — not approved or executed

“Clear” means remove table data as part of a future, explicitly approved reset. “Targeted” means retain the administrator's rows and only remove other account/link rows. “Preserve” means retain the table's current framework/reference rows.

| Table | Current rows | Proposed action | Administrator / dependency note |
|---|---:|---|---|
| `academics_academicrecord` | 62 | Clear | Business records; user-link fields are not required for authentication. |
| `academics_academicyear` | 12 | Clear | School data; not an auth dependency. |
| `academics_enrollment` | 11 | Clear | Business records. |
| `academics_gradelevel` | 14 | Clear | School data; not an auth dependency. |
| `academics_section` | 7 | Clear | No section is currently assigned to the admin profile; preserve any section referenced by an admin profile link if that changes before approval. |
| `academics_specialization` | 1 | Clear | School data. |
| `academics_strand` | 1 | Clear | School data. |
| `academics_subject` | 11 | Clear | School data. |
| `academics_subject_grade_levels` | 38 | Clear | Join data for school reference records. |
| `academics_teacherassignment` | 15 | Clear | Business assignments; none are an admin authorization dependency. |
| `accounts_userprofile` | 18 | Targeted | Preserve profile id 25 for `EDU_admin`; remove other profiles only if that is within the approved reset scope. |
| `accounts_userprofile_assigned_sections` | 6 | Targeted | Preserve links for profile id 25 and their referenced sections; currently the admin has zero links. |
| `attendance_attendancerecord` | 30 | Clear | Operational records. |
| `attendance_recurringschoolcalendarevent` | 0 | Clear | Operational records; no admin dependency identified. |
| `attendance_schoolcalendarday` | 52 | Clear | Includes 33 records created by the admin; these records are not needed for admin access. |
| `audit_auditlog` | 404 | Clear | Includes 70 rows linked to the admin; clearing loses history but does not remove the account. |
| `auth_group` | 0 | Preserve | Keep authorization framework catalog table/data. |
| `auth_group_permissions` | 0 | Preserve | Keep group-permission relationships intact. |
| `auth_permission` | 116 | Preserve | Keep permission catalog. |
| `auth_user` | 18 | Targeted | Preserve only the existing `EDU_admin` row (id 25); do not clear or truncate the shared user table. |
| `auth_user_groups` | 0 | Targeted | Preserve any `EDU_admin` memberships; currently none. |
| `auth_user_user_permissions` | 0 | Targeted | Preserve any direct `EDU_admin` permissions; currently none. |
| `behavior_behavioralassessment` | 24 | Clear | Operational records. |
| `behavior_behavioralrating` | 4 | Preserve | Reference/lookup values required by behavior workflows. |
| `behavior_behaviorindicator` | 8 | Preserve | Reference/lookup values required by behavior workflows. |
| `behavior_corevalue` | 8 | Preserve | Reference/lookup values required by behavior workflows. |
| `django_admin_log` | 0 | Clear | Historical admin-site log, not required for application authorization. |
| `django_content_type` | 29 | Preserve | Framework metadata used by permission records. |
| `django_migrations` | 57 | Preserve | Migration history; no migration is part of this plan. |
| `django_session` | 96 | Clear | Expire sessions; admin can authenticate again after reset. |
| `interventions_intervention` | 3 | Clear | Operational records. |
| `notifications_notification` | 10 | Clear | Includes 5 notifications for the admin; not required for login or permissions. |
| `predictions_predictionfactor` | 52 | Clear | Operational prediction data. |
| `predictions_riskprediction` | 14 | Clear | Operational prediction data. |
| `students_student` | 12 | Clear | Student records. |
| `token_blacklist_blacklistedtoken` | 0 | Clear | Token state can be discarded; not required to create a fresh login session. |
| `token_blacklist_outstandingtoken` | 0 | Clear | Token state can be discarded; not required to create a fresh login session. |

The proposed reset must use targeted deletes for the shared user/profile/auth-link tables and FK-aware deletes for operational tables. It must not use Django `flush`, table-wide `TRUNCATE`, `DROP`, or recreation, because those would remove the protected user and/or framework metadata. Whether to preserve academic setup data rather than clearing it is a reset-scope decision for review; this proposal treats it as school/business data and clears it.

### If credential verification or account correction is needed

The account and role are present, but the required password cannot currently be verified. Do not change either during this inspection phase. Before any reset, verify the intended password through an approved, local, non-login credential-comparison step that does not print or persist the plaintext. If the password does not match, or the account/role is later found missing or different, stop and obtain separate approval for correction. The safest correction would use Django's supported user/password APIs with a secure interactive secret prompt, and set only the linked profile role to the supported `SUPER_ADMIN` value if needed. If the account is missing, create it only after separate approval, using the Django user manager and creating its `UserProfile` with `role_name='SUPER_ADMIN'` in the same controlled transaction. Do not put the password in source, `.env`, command arguments/history, reports, or logs. Do not set `is_staff`/`is_superuser` unless Django built-in admin access is separately required and explicitly approved.

### Recovery and approval gate

No reset, delete, truncate, account change, migration, seed, or restore has been performed. Before a future reset, review this table and the backup path/hash; retain a protected second copy and verify its checksum. If recovery is needed, restore the dump only into a separate isolated MariaDB database first, compare its schema and per-table counts, and keep the original backup unchanged. Do not overwrite `edu_assist` or proceed with any destructive operation until the user explicitly approves the reviewed plan and backup details.

---

## Final backup-protection follow-up — 2026-10-20

This follow-up records the non-destructive copy step. No database connection or write was made during this step; no tests, builds, restore rehearsal, staging, commit, or publication occurred.

| Copy | Location | Size | SHA-256 | Verification |
|---|---|---:|---|---|
| Original | `BACKEND/db_backups/edu_assist_pre_reset_20261020.sql` | 253,081 bytes | `e56a4aaab04783cba2e7a43ae2e94f8e03afaaecd02b65c26bac21305debe86d` | Source checksum and size confirmed before copy; checksum remained unchanged after copy. |
| Independent local copy | `C:\Users\user\Documents\EDU_ASSIST_Backups\edu_assist_pre_reset_20261020.sql` | 253,081 bytes | `e56a4aaab04783cba2e7a43ae2e94f8e03afaaecd02b65c26bac21305debe86d` | Copied file size and SHA-256 exactly match the original. |

The destination is outside the Git repository on the `C:` partition; the source is on `F:`. Both partitions are on the same physical disk, so this is an independent copy against repository/worktree loss but not against physical disk failure. The destination folder ACL grants Full Control to the current user, SYSTEM, and Administrators. No third-party or network storage was used.

Git checks confirm the repository copy is untracked, not staged, not committed, and not ignored. The external copy is outside the repository and therefore is not staged or committed. Do not add either copy to Git. The report intentionally contains only paths, size, checksum, and verification status; no dump contents or credentials.

Backup-protection step: **COMPLETE**. This does not establish restore success or authorize a reset. The overall reset readiness remains **NOT READY** because the administrator password is **NOT VERIFIED**, restore compatibility is unverified, the two copies share a physical disk, and explicit reset approval has not been granted. Obtain separate protected storage on a different physical device before any reset if protection against disk failure is required. Stop here pending user review and explicit approval.