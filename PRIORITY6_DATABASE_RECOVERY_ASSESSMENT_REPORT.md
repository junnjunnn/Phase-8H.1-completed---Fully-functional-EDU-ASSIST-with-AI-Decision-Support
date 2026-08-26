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