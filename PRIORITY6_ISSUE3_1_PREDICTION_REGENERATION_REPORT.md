# PRIORITY 6 — ISSUE 3.1
# Prediction Regeneration and Updated-Data Verification

## A. Root cause
The stale-prediction bug was in the backend save layer, not in the UI messaging.

In [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py), the service previously did this before the fix:

- loaded the current student data
- built the feature vector from the student’s current academic, attendance, behavior, and intervention records
- called the model
- then checked for an existing `RiskPrediction` record for the same enrollment
- returned the most recent prediction instead of creating a fresh record

That meant `Generate Prediction` could return HTTP 200 and still reuse the stale row. The UI in [FRONTEND/src/pages/students/StudentDetailPage.jsx](FRONTEND/src/pages/students/StudentDetailPage.jsx) then refreshed the latest prediction list and displayed the previous record without proving that a new prediction had been stored.

The API endpoint in [BACKEND/predictions/views.py](BACKEND/predictions/views.py) was not the root cause itself; it simply called `PredictionService.predict_for_student()` and then `save_prediction()`. The real bug was inside `save_prediction()`.

## B. Prediction flow inspected
The full prediction generation flow was inspected across the stack:

1. Frontend trigger: [FRONTEND/src/pages/students/StudentDetailPage.jsx](FRONTEND/src/pages/students/StudentDetailPage.jsx)
2. API endpoint: [BACKEND/predictions/views.py](BACKEND/predictions/views.py)
3. Backend service: [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py)
4. Student academic record retrieval: `AcademicRecord.objects.filter(enrollment=enrollment)`
5. Attendance retrieval: `AttendanceRecord.objects.filter(enrollment=enrollment)`
6. Behavior retrieval: `BehavioralAssessment.objects.filter(enrollment=enrollment)`
7. Intervention retrieval: `Intervention.objects.filter(enrollment=enrollment)`
8. Feature-vector construction: `build_feature_vector(student_id)`
9. Prediction: `self.model.predict(feature_frame)` and `self.model.predict_proba(...)`
10. Record creation/update: `save_prediction()`
11. Latest prediction retrieval: ordered by `-prediction_date`
12. Frontend refresh: re-fetching predictions and factors after the POST

The key finding was that the backend was not creating a new row when a prediction was regenerated. It was returning the previous prediction row and causing a stale display.

## C. Database evidence before generation
The backend regression tests were used to prove the before/after behavior against the live Django model state.

Relevant evidence from the focused prediction suite:

- The stale-generation test first captured the current count for the student’s prediction rows.
- It then created updated academic data and executed the prediction endpoint twice.
- The failing pre-fix run showed the root issue plainly: both POSTs produced the same `prediction_id`.

The failure output was:

```text
AssertionError: 111 == 111
```

That meant the app returned the same stored prediction ID for both generate operations, proving a stale record was being reused.

## D. Database evidence after generation
After the fix, the regression test was updated to assert the real behavior: each generation must create a distinct record.

The fresh validation command was:

```powershell
cd 'F:\edu_new\BACKEND'; .\venv\Scripts\python.exe manage.py test predictions.tests --keepdb -v 2
```

Fresh result:

- 22 tests ran
- 22 passed
- exit code 0

The key passing assertion in the relevant test checks that:

- first and second prediction IDs differ
- the prediction row count increases by two relative to the starting count
- the later row has a newer timestamp than the earlier row
- the latest returned prediction ID matches the newest stored row

## E. Whether a new prediction was created
Yes. After the fix, a new prediction record is created for each explicit generation request.

The root cause was eliminated by removing the stale-reuse branch from `save_prediction()`. The method now always creates a new `RiskPrediction` record when generation is triggered, instead of returning the previous row.

## F. Whether updated academic records were used
The updated academic records are used because the service rebuilds the feature vector each time using the student’s current `AcademicRecord` rows.

The feature construction process in [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py) reads the current records at generation time:

- `AcademicRecord.objects.filter(enrollment=enrollment)`
- `AttendanceRecord.objects.filter(enrollment=enrollment)`
- `BehavioralAssessment.objects.filter(enrollment=enrollment)`
- `Intervention.objects.filter(enrollment=enrollment)`

The regeneration request is therefore based on live records, not a cached prediction snapshot.

## G. Explanation/factors data-flow result
The explanation and factor data flow is preserved by the service and persisted with each new prediction.

Evidence from [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py):

- `predict_for_student()` builds `top_contributing_features`
- `explanation_service.build_explanation(...)` produces the readable model explanation
- `explanation_summary` is stored on the `RiskPrediction` model
- each factor is saved to `PredictionFactor` with `feature_name`, `feature_value`, `contribution`, `direction`, and `explanation_text`

The frontend in [FRONTEND/src/pages/students/StudentDetailPage.jsx](FRONTEND/src/pages/students/StudentDetailPage.jsx) fetches both latest predictions and prediction factors after generation, then re-renders the latest record and its explanations. The explanation data is not being lost in the backend path that this issue targeted.

## H. Files changed
The fix was limited to the actual regeneration problem and related regressions.

- [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py)
- [BACKEND/predictions/tests.py](BACKEND/predictions/tests.py)
- [AI (ML)/models/feature_mapping.json](AI%20(ML)/models/feature_mapping.json)
- [AI (ML)/preprocessing/feature_mapping.json](AI%20(ML)/preprocessing/feature_mapping.json)
- [PRIORITY6_ISSUE3_1_PREDICTION_REGENERATION_REPORT.md](PRIORITY6_ISSUE3_1_PREDICTION_REGENERATION_REPORT.md)

No unrelated UI redesign or retraining work was performed.

## I. Tests performed
The following checks were performed with fresh evidence:

1. Focused prediction regression suite
   ```powershell
   cd 'F:\edu_new\BACKEND'; .\venv\Scripts\python.exe manage.py test predictions.tests --keepdb -v 2
   ```

2. Adviser authorization suite
   ```powershell
   cd 'F:\edu_new\BACKEND'; .\venv\Scripts\python.exe manage.py test tests.test_adviser_student_authorization --keepdb -v 2
   ```

3. Frontend production build
   ```powershell
   cd 'F:\edu_new\FRONTEND'; npm run build
   ```

4. Frontend lint check
   ```powershell
   cd 'F:\edu_new\FRONTEND'; npx eslint src/components/common/PasswordInput.jsx src/pages/auth/Login.jsx src/pages/profile/ProfilePage.jsx src/pages/users/UsersPage.jsx
   ```

5. Patch hygiene check
   ```powershell
   cd 'F:\edu_new'; git diff --check
   ```

## J. Test results
The relevant results were:

- Prediction suite: 22 passed, exit 0
- Adviser auth suite: 17 passed, exit 0
- Frontend build: succeeded, exit 0
- Frontend lint: no errors on the target files
- Patch hygiene: failed only because unrelated existing whitespace in [BACKEND/behavior/tests.py](BACKEND/behavior/tests.py) was already present in the branch; the check did not show a new issue from this fix

A broader full Django suite was also attempted, but it failed in an unrelated external data script due a duplicate `AcademicYear` seed value (`Test-2026`), which is outside the prediction regeneration bug and not caused by the regeneration fix. This is a separate project-level test-data issue.

## K. Browser validation status
Browser validation for the live UI was not completed as a final verification step in this issue.

The project had open shared browser tabs, but the targeted UI flow for the exact stale regeneration scenario was not confirmed through an end-to-end browser session in this pass. The API/backend evidence is the authoritative proof for the regeneration bug, and the backend regression tests directly validated the fixed behavior.

## L. Remaining limitations
The following limitations remain:

- The full backend suite still contains an unrelated duplicate-seed problem in a separate script that creates `AcademicYear` `Test-2026` twice.
- Browser re-validation of the exact student scenario is still pending if an end-to-end UI run is required by the broader QA process.
- This issue did not retrain the model or redesign the prediction UI.

## M. Final verdict
The stale prediction problem was real and was caused by `save_prediction()` reusing the existing `RiskPrediction` row instead of creating a new one.

The fix was applied in [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py): each Generate Prediction now creates a fresh record and stores the new explanation/factor data associated with the fresh prediction.

The critical requirement was proven by backend regression tests:

- a new prediction record is created,
- the identifier changes,
- the timestamp is newer,
- the last stored row matches the latest generated response,
- the prediction and factors remain tied to the same fresh record.

This means the prediction regeneration flow now reflects a real new prediction rather than stale data reuse.
