# PRIORITY 6 - DATABASE REBUILD AND UAT FOUNDATION REPORT

## 1. Database used

- Database: `edu_assist`
- Engine: Django MySQL compatibility backend / MariaDB 10.4.32
- Host and port: `127.0.0.1:3306`
- User: `root`
- Settings: `config.settings`
- Runtime: `DEBUG=True`, environment resolved as `development`

This was the explicitly authorized disposable development database. No other database was modified.

## 2. Safety verification

Immediately before the destructive reset, the command printed and verified the database name, host, port, user, settings module, and debug state. `test_edu_assist` was not treated as a backup and was not deleted. The UCI dataset and ML model files were not modified.

The reset used `flush --noinput` only after that verification. The project-native seed command also refuses production-like environments, `DEBUG=False`, and database names outside `edu_assist` or `edu_assist_uat`.

## 3. Migration status

All current migrations are applied, including attendance migrations `0005`, `0006`, and `0007`. Django system checks passed with no issues. The live database contains 34 tables.

## 4. Seed data created

The deterministic command is:

```text
cd BACKEND
python manage.py reset_uat_data
```

The completed rebuild contains:

| Data set | Count |
|---|---:|
| Users | 5 |
| Academic years | 2 |
| Grade levels | 1 |
| Sections | 2 |
| Subjects | 8 |
| Students | 6 |
| Enrollments | 6 |
| Academic records | 48 |
| Attendance records | 7 |
| Calendar entries | 11 |
| Behavioral assessments | 6 |
| Interventions | 4 |
| Risk predictions | 6 |
| Prediction factors | 12 |
| Audit records | 6 |

No recurring-event table is present and no recurring events were created.

## 5. User accounts and roles

All accounts use deterministic UAT credentials:

| Username | Role | Password |
|---|---|---|
| `uat_admin` | SUPER_ADMIN | `UATAdmin123!` |
| `uat_registrar` | REGISTRAR | `UATRegistrar123!` |
| `uat_teacher` | TEACHER | `UATTeacher123!` |
| `uat_adviser` | TEACHER / adviser | `UATAdviser123!` |
| `uat_guidance` | GUIDANCE | `UATGuidance123!` |

The adviser and teacher are assigned to section `UAT 9-A`.

## 6. Academic structure

- Active year: `UAT 2025-2026`
- Previous year: `UAT 2024-2025` (inactive)
- Grade level: `UAT Grade 9` / `UAT-G9`
- Sections: `UAT 9-A` and `UAT 9-B`
- Subjects: Mathematics, English, Science, Filipino, Araling Panlipunan, ESP, MAPEH, and TLE
- Six active enrollments distribute students across both sections.

## 7. Student test scenarios

The six students are identified by LRNs `UAT-001` through `UAT-006`:

- `UAT-001`: normal-performing student
- `UAT-002`: low grades and tutoring intervention
- `UAT-003`: failed subjects and high risk
- `UAT-004`: attendance concern and attendance monitoring
- `UAT-005`: behavior concern and completed behavioral monitoring
- `UAT-006`: combined academic, attendance, behavior, and guidance indicators

## 8. Attendance test scenarios

Monthly summaries cover present, absent, and late values for all six students. A dated present record exercises date-aware validation. Calendar records include regular school days, a Philippine-import holiday, a weather-related suspension, and a grade-level school event. Attendance is not encoded on the holiday or suspension dates.

## 9. Behavior test scenarios

Six assessments use the existing `AO`, `SO`, `RO`, and `NO` rating codes. The live rating table was verified to contain all four codes. No new behavior logic was introduced.

## 10. Intervention test scenarios

Four linked interventions cover tutoring, attendance monitoring, behavioral monitoring, and guidance referral. They exercise `planned`, `in_progress`, and `completed` statuses plus medium and high priorities.

## 11. Calendar test scenarios

The calendar covers academic-year linkage, normal school days, a `PHILIPPINE_IMPORT` holiday, a school-wide weather suspension with approval metadata, and a published grade-level event with affected scope and time range. Issue 5.5 recurring events were not implemented.

## 12. Prediction test scenarios

Six deterministic `RiskPrediction` records cover Low, Moderate, and High risk levels, with Random Forest model metadata and two factors per prediction. Records are linked to the same academic, attendance, behavior, and intervention inputs used by the existing prediction service. Model artifacts were not changed.

## 13. UAT reset mechanism

`BACKEND/students/management/commands/reset_uat_data.py` prints `THIS COMMAND RESETS DISPOSABLE UAT DATA ONLY`, verifies the environment and authorized database name, deletes only UAT-prefixed records, and recreates the same baseline inside a transaction. It does not delete source code, migrations, ML artifacts, or the UCI dataset.

## 14. Tests executed

- `python manage.py check`: passed.
- `python manage.py migrate --noinput`: passed; three pending attendance migrations applied.
- `python manage.py showmigrations --plan`: no unapplied migrations after rebuild.
- Read-only ORM verification: passed for users, years, students, enrollments, academic records, attendance, behavior, interventions, calendar, predictions, factors, and audit records.
- `npm run lint`: passed.
- `npm run build`: passed.
- `git diff --check`: passed.
- Focused backend tests in an in-memory SQLite test database: 49 passed; one existing test module failed to import.

## 15. Test results

The disposable MariaDB database was rebuilt and seeded successfully. Counts and relationships were read back successfully. The existing prediction service could not be executed under the current Python 3.14 environment because importing the installed scikit-learn/joblib stack hung during multiprocessing import; no model or prediction code was changed.

The focused suite also exposed an existing import defect in `BACKEND/tests/test_authorization.py`: it imports `Enrollment` from `students.models`, although the model is defined in `academics.models`. The test database was in-memory and was destroyed after the run.

## 16. Known limitations

- The current environment prevents a completed Random Forest service execution until the scikit-learn/joblib/Python interpreter compatibility issue is resolved.
- The authorization test import defect remains outside this database task and was not changed.
- The seed command creates deterministic prediction rows for UI and reporting workflows; it does not regenerate or retrain the Random Forest model.
- Credentials in this report are development/UAT credentials only and must not be reused in production.