# Priority 6 Issue 2 — Behavior Canonicalization Report

## A. Existing behavior architecture inspected

The project already had a behavior domain with a clear canonical model and API structure.

- Model layer: `BACKEND/behavior/models.py`
  - `CoreValue`
  - `BehaviorIndicator`
  - `BehavioralRating`
  - `BehavioralAssessment`
- API layer: `BACKEND/behavior/api.py`
  - `CoreValueViewSet`
  - `BehaviorIndicatorViewSet`
  - `BehavioralRatingViewSet`
  - `BehavioralAssessmentViewSet`
- Serialization: `BACKEND/behavior/serializers.py`
- Reference mapping: `BACKEND/behavior/reference_data.py`
- Sync command: `BACKEND/behavior/management/commands/sync_deped_behavior.py`
- Frontend behavior entry: `FRONTEND/src/pages/behavior/BehaviorEncodingPage.jsx`
- Monitoring display: `FRONTEND/src/pages/behavior/BehaviorPage.jsx` and `FRONTEND/src/pages/students/StudentDetailPage.jsx`

The architecture uses the existing academic-period model (`academic_year`, `grading_period_type`, `quarter`, `semester`) and retains enrollment-scoped access control.

## B. Current legacy values found

The database originally contained legacy core values and indicator labels that were not aligned with the DepEd behavioral structure:

- Respect
- Discipline
- Respectful Behavior
- Compliance with school rules

These were found in the application database during inspection and were not blindly deleted. Historical records were preserved intact and the reference-data sync marked them inactive rather than rewriting them.

## C. Required canonical values

The canonical behavior core values required for new records are:

1. Maka-Diyos
2. Makatao
3. Maka-Kalikasan
4. Makabansa

The canonical values are already defined in the reference data and used as the active default set for new behavior creation.

## D. Root cause

The root cause was not a frontend-only issue. The system had both:

1. legacy records already stored in the database, and
2. reference data that did not strictly enforce canonical values for new submissions.

This allowed new records to be created with old labels while the AI prediction pipeline later consumed `behavior_core_value` and `behavior_indicator` directly. Because these values were historical/legacy, they created a vocabulary mismatch outside the saved model contract.

## E. Database/data assessment

Database assessment results:

- Legacy values were present in `CoreValue` and `BehaviorIndicator` tables.
- Historical `BehavioralAssessment` records were still tied to those legacy values.
- Historical records were preserved.
- Canonical values were added to the database and the legacy values were marked inactive.
- No destructive rewrite of historical assessment rows was performed.

This satisfies the requirement to preserve historical data and distinguish legacy content from canonical data.

## F. Files changed

Files changed during this fix include:

- `BACKEND/behavior/serializers.py`
- `BACKEND/behavior/api.py`
- `BACKEND/behavior/tests.py`
- `BACKEND/behavior/management/commands/sync_deped_behavior.py`
- `PRIORITY6_ISSUE2_BEHAVIOR_CANONICALIZATION_REPORT.md`

## G. Models/serializers/API changes

### Models
The existing behavior model design was retained. The model already had the required structure:

- `core_value` foreign key
- `behavior_indicator` foreign key
- `rating` foreign key
- `grading_period_type`
- `quarter`
- `semester`
- `academic_year`
- `enrollment`
- `assessed_by`

No duplicate behavior system was introduced.

### Serializer validation
The behavioral assessment serializer now blocks new records that use inactive/legacy core values or inactive behavior indicators.

This enforcement is in the backend and prevents invalid values from being accepted even if the UI is bypassed.

### API behavior
The behavior API now defaults to active-only core values, indicators, and ratings when the caller does not explicitly request inactive records.

This keeps the new-record workflow aligned with the canonical DepEd structure without deleting historical rows.

## H. Frontend changes

The frontend already uses the active reference values from the backend, and the active selection set is now restricted to the canonical values. The behavior form continues to show the current active reference set rather than exposing legacy names.

The existing behavior monitoring and student-detail screens continue to display the stored values without silently rewriting history. Legacy values remain identifiable as historical data rather than being renamed in-place.

## I. Historical-record handling

Historical records are intentionally preserved.

- Legacy records were not deleted.
- Legacy values were marked inactive to prevent future use.
- Historical records remain available for audit/history and are not silently renamed.
- New records cannot be created with those legacy values from the backend.

This is the safe handling policy required for integrational continuity and data integrity.

## J. Authorization verification

The existing authorization model was not weakened.

- Read access remains scoped by authorized enrollment.
- Writes remain limited to permitted staff.
- Advisers are still restricted to students in authorized/advisory scope.
- Admin-level behavior reference changes are preserved under school-admin permissions.

No broad authorization redesign was introduced as part of this issue.

## K. AI compatibility findings

This issue does not retrain or modify the model.

The AI model compatibility problem remains a separate concern for Priority 6 Issue 3.

The current findings are:

- New canonical behavior records now use the expected DepEd core-value names.
- Historical legacy records remain in the database and are preserved intact.
- The prediction model continues to consume behavior feature strings from the application; the saved model vocabulary mismatch is still a separate issue if legacy values appear in historical or converted data.
- This task intentionally does not modify the Random Forest model or its vocabulary.

## L. Regression tests

Focused behavioral regression tests were added/updated to cover:

- canonical core values active after sync
- inactive legacy values blocked
- valid creation of Maka-Diyos, Makatao, Maka-Kalikasan, and Makabansa assessments
- AO, SO, RO, and NO rating validation
- active reference filtering on endpoints
- historical record preservation
- adviser authorization behavior

## M. Browser/manual validation

Manual browser validation is still recommended for the UI workflow under a real authenticated session, specifically:

1. Open the behavior encoding page.
2. Confirm the core-value picklist contains only:
   - Maka-Diyos
   - Makatao
   - Maka-Kalikasan
   - Makabansa
3. Save a canonical record.
4. Confirm the record appears in behavior monitoring/student detail screens.
5. Confirm historical legacy values remain preserved and identifiable.
6. Confirm adviser access remains scoped correctly.

## N. Remaining limitations

### Fixed in Issue 2
- Canonical DepEd behavior values are now active for new records.
- Legacy values are blocked for new behavior assessments at the backend.
- Active reference endpoints filter out legacy values by default.
- Historical records are preserved.

### Intentionally deferred to Issue 3
- Random Forest retraining or vocabulary alignment.
- AI model compatibility remediation for historical legacy values.
- Prediction feature-vocabulary repair after model update.

### Historical limitations
- Older data in the existing database may still contain legacy labels such as Respect and Discipline.
- Those records are preserved as historical records and are not silently re-labeled.
- They should be interpreted as legacy data until the dedicated AI/model compatibility issue is handled.

## Final status

Priority 6 Issue 2 is scoped to the canonical behavior data model and new-record enforcement.

The core problem is fixed for new behavior creation and the application now defaults to the required DepEd canonical values while keeping historical legacy records intact.
