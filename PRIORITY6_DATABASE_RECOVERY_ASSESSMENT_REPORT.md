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