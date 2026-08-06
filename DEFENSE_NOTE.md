Capstone Defense Notes — Implementation Verification

Purpose: This document reports exactly what the current codebase implements. All statements are based only on the inspected source files in this repository.

1. Authentication
- Files verified:
  - BACKEND/accounts/views.py
  - BACKEND/accounts/serializers.py
  - BACKEND/accounts/models.py
  - BACKEND/accounts/urls.py
  - BACKEND/config/settings.py
  - BACKEND/config/settings_sqlite.py
  - FRONTEND/src/services/authService.js
  - FRONTEND/src/services/api.js
  - FRONTEND/src/context/AuthContext.jsx

- How users log in:
  - Implemented in `BACKEND/accounts/views.py` class `LoginView.post()`.
  - The view accepts JSON `username` and `password` (validated by `LoginSerializer`). It calls `authenticate(...)` and `login(request, user)` on success, then returns a JSON response containing `user` info and JWT `access` and `refresh` tokens created via `rest_framework_simplejwt.tokens.RefreshToken.for_user(user)`.
  - Failed logins return HTTP 401 and create an `AuditLog` record with `LOGIN_FAILED`.

- JWT/session implementation:
  - Backend uses `rest_framework_simplejwt` for JWTs (see `accounts/urls.py` registering `token/refresh/` and settings in `config/settings.py` `SIMPLE_JWT`).
  - REST framework authentication classes include `JWTAuthentication` and `SessionAuthentication` (see `config/settings.py`).
  - Frontend stores `access` and `refresh` tokens in `localStorage` via `setStoredTokens` in `FRONTEND/src/services/api.js` and `authService.js` stores tokens on login.
  - Axios in `api.js` includes an interceptor that adds `Authorization: Bearer <access>` header to requests and automatically posts to `/auth/token/refresh/` to refresh when a 401 occurs.

- Password hashing:
  - User accounts are created with `User.objects.create_user(...)` (e.g., in `accounts/views.UserListCreateView.create` and `accounts/serializers.UserCreateSerializer.create`) which delegates to Django's `set_password`.
  - The active password hasher configuration varies by settings file: `BACKEND/config/settings_sqlite.py` explicitly sets `PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']` (insecure for production). `BACKEND/config/settings.py` does not override `PASSWORD_HASHERS` (so default Django hashers apply unless `settings_sqlite` is used). The code uses Django's password validation (`validate_password`) in the create serializer.

- User roles:
  - Role model: `BACKEND/accounts/models.py` `UserProfile` stores `role_name` with choices `SUPER_ADMIN`, `SCHOOL_ADMIN`, `TEACHER`, `GUIDANCE`.
  - Permissions helpers in `accounts/permissions.py` and scope functions in `accounts/utils.py` read `user.profile.role_name` to implement role checks (e.g., `IsSchoolAdmin`, `IsAuthorizedStaff`).

- How accounts are created:
  - API endpoint: `POST /api/auth/users/` handled by `UserListCreateView` (`BACKEND/accounts/views.py`). It requires `IsSchoolAdmin` permission.
  - The serializer `UserCreateSerializer` validates `role_name` and password then calls `User.objects.create_user(...)` and creates a `UserProfile`.
  - `AuditLog` entry `USER_CREATED` is created on creation.

- Whether there is a User Management page or method:
  - Backend provides API endpoints to list/create/update users and endpoints to activate/deactivate (`/api/auth/users/`, `/api/auth/users/<pk>/`, `/api/auth/users/<pk>/activate/`, `/api/auth/users/<pk>/deactivate/`). See `BACKEND/accounts/urls.py` and `BACKEND/accounts/views.py`.
  - Frontend: There is no UI page under `FRONTEND/src/pages` named Users or User Management detected in the inspected frontend files. No React page or service calling `/api/auth/users/` was found during verification. Therefore: backend API exists; frontend user management view is not implemented in the source inspected.

Implementation completeness: Authentication API and JWT flow are implemented on the backend and integrated into the frontend HTTP client. Frontend UI for user management not implemented.


2. User Management
- Files verified:
  - BACKEND/accounts/views.py
  - BACKEND/accounts/serializers.py
  - BACKEND/accounts/models.py
  - BACKEND/accounts/urls.py
  - BACKEND/accounts/permissions.py
  - FRONTEND: no user-management page or API calls detected

- Can administrators create teacher accounts?
  - Yes (backend): `POST /api/auth/users/` via `UserListCreateView` (permission `IsSchoolAdmin`). `UserCreateSerializer` requires `role_name` (allowed values validated) and password and creates both the `User` and `UserProfile`.

- Can accounts be edited?
  - Backend: `UserRetrieveUpdateView` (PUT/PATCH) exists and is protected by `IsSchoolAdmin`. `UserSerializer` exposes `username`, `is_active`, `date_joined`, `last_login`, and `profile` (profile is read-only in this serializer). So basic update is available. Activation/deactivation endpoints exist.
  - Frontend: No management UI detected for editing users.

- Can passwords be changed?
  - No explicit API endpoint for password change was found in `BACKEND/accounts` (no custom `change-password` view). Django admin and built-in `contrib.auth` password views exist in the project dependencies, but no API endpoint for password change is implemented in `accounts` source files. Therefore: password change via API is not implemented in the checked code; password changes can be done via Django admin or model methods (not via a documented REST endpoint here).

- Can accounts be disabled or deleted?
  - Disable (activate/deactivate): implemented via `activate_user` and `deactivate_user` functions (API endpoints protected by `IsSchoolAdmin`). They set `user.is_active`.
  - Delete: No custom delete endpoint for users is provided in `accounts.urls` or views. Deletion could be done in Django Admin or via ORM code, but no public API endpoint exists for deletion.

Implementation completeness: Backend supports admin creation, editing (limited), activation/deactivation. Password change and dedicated frontend user-management page are not implemented in the frontend.


3. Student Management
- Files verified:
  - BACKEND/students/models.py
  - BACKEND/students/api.py
  - BACKEND/students/serializers.py
  - FRONTEND/src/services/studentService.js
  - FRONTEND/src/pages/students/StudentsPage.jsx
  - FRONTEND/src/pages/students/StudentDetailPage.jsx

- How students are created:
  - Backend: `StudentViewSet` (in `BACKEND/students/api.py`) supports `CreateModelMixin` and `UpdateModelMixin`. `POST /api/students/` will create students via the `StudentSerializer`.
  - `StudentSerializer` fields: `id`, `lrn`, `first_name`, `last_name`, `gender`, `birth_date`, `student_status`.
  - `perform_create` and `perform_update` create `AuditLog` entries.

- Required fields:
  - The model `Student` has `first_name` and `last_name` as non-nullable fields; `lrn` is optional (blank=True, null=True). Therefore required at DB-level are `first_name` and `last_name`.

- Database model:
  - `BACKEND/students/models.py` `Student` model with fields `lrn`, `first_name`, `middle_name`, `last_name`, `suffix`, `gender`, `birth_date`, `student_status`, `created_at`, `updated_at`.

- API endpoints:
  - `GET/POST/PUT/PATCH /api/students/` (router registered in `config/urls.py` via `StudentViewSet`). Filtering and searching are supported; `get_queryset` calls `get_authorized_student_queryset` to limit data by role/assigned sections.

- Frontend workflow:
  - `FRONTEND/src/pages/students/StudentsPage.jsx` calls `getStudents` from `FRONTEND/src/services/studentService.js` which calls `apiClient.get('/students/')`.
  - `StudentDetailPage.jsx` loads student details and related records using `studentDetailService` endpoints for academic, attendance, behavior, interventions, predictions, and prediction factors.

Implementation completeness: Student creation and listing fully implemented on backend; frontend lists and detail pages consume these APIs. A dedicated UI for creating new student records in the frontend was not detected (no explicit create form component found). Creation likely expected via API or admin.


4. Academic Records
- Files verified:
  - BACKEND/academics/models.py
  - BACKEND/academics/serializers.py
  - BACKEND/academics/api.py
  - FRONTEND/src/services/academicsService.js
  - FRONTEND/src/pages/academics/AcademicsPage.jsx
  - BACKEND/debug scripts referencing academic records: `verify_seed.py`, `debug_api_predict.py`

- How grades are stored:
  - `AcademicRecord` model stores `grade` (DecimalField) and optional `final_grade` (DecimalField). It includes `grading_period_type` with choices `Quarter` or `Semester`, and `quarter`/`semester` fields. Each `AcademicRecord` is linked to an `Enrollment` and `Subject` and `AcademicYear`.

- Required subjects:
  - Subjects are modelled by `academics.Subject`. There is no enforced "required subjects" list in code; subjects exist as records and `PredictionService` maps certain subject names to feature keys (Mathematics, English, Science, Filipino, Araling Panlipunan, ESP, MAPEH, TLE) — that is a mapping in code but it's a heuristic used by the AI service, not an enforced DB constraint.

- How General Average is computed:
  - Verified in `BACKEND/predictions/services/prediction_service.py` `build_feature_vector`: general_average is computed as the arithmetic mean of `final_grade or grade or 0` across all `AcademicRecord` rows for the student's most recent `Enrollment`: `general_average = round(sum(grade_values) / len(grade_values), 2)` if `grade_values` non-empty; else 0.0.

- How Failed Subjects are computed:
  - In the same `build_feature_vector`, failed subjects are the count of `AcademicRecord` entries whose `(final_grade or grade or 0) < 75`.

Implementation completeness: Academic models and API are implemented. Computation logic (general average, failed subjects) exists in `PredictionService.build_feature_vector` and is used by prediction pipeline. Note: the grade-to-feature mapping is hard-coded (subject names), which is present and used by prediction code.


5. Attendance
- Files verified:
  - BACKEND/attendance/models.py
  - BACKEND/attendance/serializers.py
  - BACKEND/attendance/api.py
  - FRONTEND/src/services/attendanceService.js
  - FRONTEND/src/pages/attendance/AttendancePage.jsx

- How attendance records are entered:
  - Backend provides `AttendanceRecordViewSet` with `CreateModelMixin` and `UpdateModelMixin`. Fields: `enrollment`, `month`, `school_days`, `days_present`, `absences`, `times_tardy`, `encoded_by`.
  - The API endpoints are `POST /api/attendance-records/` and related retrieve/update endpoints.

- How Attendance Rate is calculated:
  - The prediction `build_feature_vector` aggregates attendance rows for the student's enrollment: sums `days_present` and `school_days` across months and computes `attendance_rate = round((present_days / school_days * 100) if school_days else 0.0, 2)`.
  - Absent/Late percentages are similarly calculated as ratios (absent_days / school_days * 100) and (late_days / school_days * 100) if `school_days` > 0.

- Where calculations occur:
  - Calculations are implemented in `BACKEND/predictions/services/prediction_service.py` inside `build_feature_vector`.

Implementation completeness: Attendance model and API implemented; rate calculation implemented inside prediction feature-building logic. No separate attendance analytics API was found (calculations are embedded in prediction logic and used by the AI pipeline).


6. Behavior
- Files verified:
  - BACKEND/behavior/models.py
  - BACKEND/behavior/serializers.py
  - BACKEND/behavior/api.py
  - FRONTEND/src/services/behaviorService.js
  - FRONTEND/src/pages/behavior/BehaviorPage.jsx

- How AO, SO, RO, and NO ratings are stored:
  - `BehavioralRating` model stores `code`, `label`, and optional `numeric_value`. Codes such as AO/SO/RO/NO are stored in `code` field (no enforcement of exact codes, but code field exists and is used by serializer).

- How teacher behavior evaluations are entered:
  - `BehavioralAssessment` model stores `enrollment`, `academic_year`, `grading_period_type`, `core_value`, `behavior_indicator`, `rating` (foreign key to `BehavioralRating`), `numeric_score`, `assessed_by`, `assessment_date`, and `remarks`.
  - API: `POST /api/behavioral-assessments/` via `BehavioralAssessmentViewSet` is available and protected by `IsAuthorizedStaff`.

- How behavior is converted into AI features:
  - `PredictionService.build_feature_vector` collects `behavior_assessments` and builds `behavior_ratings` array from `record.rating.code`. The most common code is chosen via `max(set(behavior_ratings), key=behavior_ratings.count)` as `behavior_rating`. Then `feature_values['behavior_teacher_rating'] = behavior_rating` is set, and `behavior_teacher_rating` is later expanded via encoder categories in feature mapping.
  - There is no separate mapping of AO/SO/RO/NO into numeric values in the prediction service beyond taking the code and later one-hot encoding per `feature_mapping` expectations.

Implementation completeness: Behavior recording and API implemented. AI conversion exists as a categorical code selection (most frequent rating code), then used as categorical input for encoding in the prediction pipeline.


7. Interventions
- Files verified:
  - BACKEND/interventions/models.py
  - BACKEND/interventions/serializers.py
  - BACKEND/interventions/api.py
  - FRONTEND/src/services/interventionService.js
  - FRONTEND/src/pages/interventions/InterventionsPage.jsx

- How intervention records are stored:
  - `Intervention` model stores `enrollment`, `risk_type`, `intervention_type`, `recommendation`, `assigned_personnel`, `status`, `priority`, `notes`, `start_date`, `end_date`, timestamps.

- Supported intervention fields:
  - See `Intervention` model fields listed above; `intervention_type` choices and `status` choices are enumerated in the model.

- How intervention count is used by AI:
  - In `PredictionService.build_feature_vector`, `interventions = Intervention.objects.filter(enrollment=enrollment)` and several derived features are set:
    - `'has_intervention'`: 1 if `interventions.exists()` else 0
    - `'number_of_interventions'`: `interventions.count()`
    - `'intervention_type'` and `'intervention_outcome'` are set to default strings (e.g., `No Intervention` or `Academic Monitoring`, `Not Yet Evaluated`) — these are coarse heuristics.

Implementation completeness: Interventions model and API implemented. Prediction service uses intervention existence and count (and sets simple categorical placeholders) when building features.


8. AI Prediction
- Files verified:
  - BACKEND/predictions/services/prediction_service.py
  - BACKEND/predictions/services/explanation_service.py
  - BACKEND/predictions/models.py
  - BACKEND/predictions/views.py
  - AI model artifacts (on disk referenced by code): `AI (ML)/models/risk_model.pkl`, `AI (ML)/models/label_encoder.pkl`, `AI (ML)/models/feature_mapping.json` (referenced by code — presence on disk not validated by this script, but paths are used).

- Complete workflow from clicking "Generate Prediction" to persistence (code-level):
  - Backend standalone endpoint: `POST /api/predictions/predict/<student_id>/` is implemented by `predictions.views.predict_student_view`. The endpoint:
    1. Instantiates `PredictionService()`.
    2. Calls `PredictionService.predict_for_student(student_id)` which:
       - Calls `build_feature_vector(student_id)` to gather academic records, attendance, behavior, interventions and build a pandas DataFrame `feature_frame` and `feature_values` mapping.
       - `_load_model`, `_load_label_map`, and `_load_feature_mapping` are called to load pickled Random Forest model, label mapping, and feature mapping JSON (paths defined at top of file).
       - Categorical columns are expanded into one-hot columns according to `feature_mapping['encoder_categories']`, numeric columns are coerced to numeric and missing values set to 0.
       - Model `predict` and `predict_proba` are invoked to get label and probability.
       - `ExplanationService.build_explanation(...)` is called to produce an explanation object using `model.feature_importances_` mapped to the `feature_frame` columns.
       - The service maps the top factors into a `top_contributing_features` list and builds an `explanation_summary` via `ExplanationService.build_summary`.
    3. `predict_for_student` returns a result dict with `prediction` (label), `probability`, `prediction_date`, `top_contributing_features`, `explanation`, and `explanation_summary`.
    4. Back in the view, `service.save_prediction(student_id, result=result)` is called which:
       - Finds the student's latest enrollment.
       - If an existing prediction for that enrollment exists, it returns it (no new save). Otherwise, it creates a `RiskPrediction` DB record with `probability`, `model_name='Random Forest'`, `model_version='1.0'`, `explanation=result.get('explanation_summary', '')`, and `review_status='Pending'`.
       - For each `top_contributing_feature`, a `PredictionFactor` record is created containing `feature_name`, `feature_value`, `contribution`, `direction`, `explanation_text`.

- Preprocessing, feature engineering, encoding, feature ordering:
  - Preprocessing and feature extraction occur in `PredictionService.build_feature_vector`: grades are normalized (`final_grade or grade or 0`), general average/fail counts computed, attendance aggregated, behavior aggregated (most common rating code), subject-specific grades mapped by subject name to specific feature keys.
  - Encoding: the method reads `feature_mapping.json` for `categorical_columns`, `numeric_columns` and `encoder_categories`. It constructs a DataFrame with categorical + numeric columns, then transforms categorical columns to one-hot columns by iterating `encoder_categories` and appending `_category` columns with 1/0 values. Ordering is determined by the order of `categorical_columns + numeric_columns` and the order of categories in `encoder_categories`.

- Random Forest model loading and prediction:
  - Model loaded with `pickle.load` from `AI (ML)/models/risk_model.pkl` in `_load_model`.
  - Prediction uses `self.model.predict(feature_frame)` and `self.model.predict_proba(feature_frame)`.

- Probability calculation:
  - `probability = float(self.model.predict_proba(feature_frame)[0][prediction])` where `prediction` is the predicted class index. Probability rounded and returned in result and persisted in `RiskPrediction.probability` (Decimal field).

- Database persistence:
  - `RiskPrediction` is created in `PredictionService.save_prediction` and `PredictionFactor` records created for top contributing features.
  - The API view `predict_student_view` also creates an `AuditLog` entry with `PREDICTION_GENERATED` capturing student id, prediction id, result label and probability.

Implementation completeness: Backend AI prediction pipeline is implemented end-to-end (model loading, feature building, prediction, explanation generation, DB persistence, audit logging). Frontend has no UI trigger calling the `predict_student` endpoint detected — the endpoint is present but the frontend does not call it (no "generate" button wiring found). The AI model artifacts are expected at repository-relative paths; code references them explicitly.


9. Explainable AI
- Files verified:
  - BACKEND/predictions/services/explanation_service.py
  - BACKEND/predictions/services/prediction_service.py
  - BACKEND/predictions/models.py
  - FRONTEND displays: `StudentDetailPage.jsx` and prediction factor services

- How explanations are generated:
  - `ExplanationService.build_explanation` loads the same model and retrieves `model.feature_importances_` (Random Forest feature importances) and builds a pandas Series mapping feature importance to column names in `feature_frame`.
  - It ranks importances and selects top 5 positive importances; for each, it reads `feature_values` or the value from `feature_frame` and produces `feature_name`, `feature` (humanized via internal mapping), `current_value`, `importance`, and `influence` category.

- How top factors are selected:
  - Top factors are the top 5 features by `feature_importances_` as returned by the Random Forest model. It ignores non-positive importances.

- How explanation summaries are created:
  - `ExplanationService.build_summary` composes a short multi-line text listing the prediction and top factors (feature names and current values).
  - `PredictionService.predict_for_student` additionally prepares `top_contributing_features` with `feature_name`, `feature_value`, `importance` and `direction` and creates textual `explanation_text` for each.

- How `PredictionFactor` records are stored:
  - `PredictionService.save_prediction` persists `PredictionFactor` entries for each top contributing feature with `feature_name`, `feature_value`, `contribution` (Decimal), `direction`, and `explanation_text`.

- Whether explanations are regenerated or loaded from DB:
  - The backend `predict_student_view` runs the explanation generation on-the-fly via `predict_for_student` and then `save_prediction` persists a summary and factors.
  - When a prediction record already exists for an enrollment, `save_prediction` returns the existing prediction (no regeneration). Therefore: explanations are generated when `predict_student_view` runs; if a persisted prediction exists, the service will not regenerate but return the existing record.

Implementation completeness: Explanation generation and persistence are implemented server-side and the frontend reads persistent factors via `/prediction-factors/`. The explanation method uses model feature importances (global importance) rather than local perturbation methods (SHAP/LIME) — implementation is present and functional.


10. Dashboard
- Files verified:
  - BACKEND/predictions/api.py (DashboardViewSet)
  - FRONTEND/src/services/predictionService.js (`getDashboardSummary`)
  - FRONTEND/src/pages/dashboard/Dashboard.jsx

- How dashboard statistics are computed:
  - `DashboardViewSet.list()` in `BACKEND/predictions/api.py` composes the summary:
    - `student_qs`, `prediction_qs`, `intervention_qs`, `behavior_qs` are authorized querysets limited by `get_authorized_*` helpers.
    - Counts: totals for students and predictions, distinct student counts for risk levels, counts per risk level via annotate/Count.
    - `intervention_status_distribution`: aggregated counts by `status` from Intervention queryset.
    - `behavior_rating_distribution`: counts from behavioral assessments aggregated by `rating__label` and `rating__code`.
    - `academic_performance_distribution`: iterates `AcademicRecord` final grades for enrollments in `prediction_qs` and buckets them into 'Failing', 'Passing', 'Good', 'Excellent'.
    - `recent_predictions`, `attention_students`, `recent_completed_interventions`, and `recent_prediction_activity` are composed with `.values(...)` queries and simple ordering.

- Where the API is located:
  - `GET /api/dashboard-summary/` (router registers `DashboardViewSet` with basename `dashboard-summary` in `config/urls.py`).

- What database queries are used:
  - Queryset counts (`.count()`), `.values(...).annotate(count=Count('id'))`, `.order_by(...)`, `.filter(...)`, and a loop over `AcademicRecord.objects.filter(enrollment__in=prediction_qs.values('enrollment')).values_list('final_grade', flat=True)` to compute grade buckets.

- How recent predictions are generated:
  - `recent_predictions` is a simple query: top 10 predictions ordered by `-prediction_date` with selected fields via `.values(...)`.

Implementation completeness: Dashboard API fully implemented server-side and consumed by `FRONTEND/src/pages/dashboard/Dashboard.jsx` via `getDashboardSummary()`.


11. Audit Logging
- Files verified:
  - BACKEND/audit/models.py
  - Multiple backend viewset files where `AuditLog.objects.create(...)` is called (accounts/views.py, academics/api.py, attendance/api.py, behavior/api.py, interventions/api.py, predictions/api.py, students/api.py, predictions/views.py)

- What actions are logged:
  - The `AuditLog.ACTION_CHOICES` include CREATE, UPDATE, DELETE, LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT, ACCOUNT_ACTIVATED, ACCOUNT_DEACTIVATED, PASSWORD_CHANGED, USER_CREATED, VIEW_SENSITIVE_RECORD, EXPORT_REPORT, PREDICTION_GENERATED, INTERVENTION_CREATED.
  - Concrete usages observed: `LOGIN_FAILED`, `LOGIN_SUCCESS`, `LOGOUT`, `USER_CREATED`, `ACCOUNT_ACTIVATED`, `ACCOUNT_DEACTIVATED`, `CREATE` and `UPDATE` in viewset `perform_create`/`perform_update`, and `PREDICTION_GENERATED` when predictions are created.

- Where logging occurs:
  - Logging calls are placed in views and API viewsets: e.g., `accounts/views.py`, `students/api.py.perform_create`, `predictions/views.py.predict_student_view`, etc.

- What information is stored:
  - `AuditLog` fields stored: `user`, `action`, `module`, `object_type`, `object_id`, `timestamp` (auto), and optional `ip_address`.
  - Many audit calls set `object_id` to a string representation (IDs or composite string for predictions), and `module` to the app name.

- Limitations:
  - Audit entries are written synchronously in the request flow (no async/buffered logging); heavy write traffic could impact latency.
  - No retention policy or export tooling observed in code; logs are DB records only.
  - `PASSWORD_CHANGED` action is present in choices but no password-change API hook was observed to write that action.

Implementation completeness: Audit logging covers many key actions and is implemented at multiple places in the backend. Some action types are declared but not necessarily used where expected (e.g., PASSWORD_CHANGED). Logs are stored to DB via `BACKEND/audit/models.py`.


12. Security
- Files verified:
  - BACKEND/config/settings.py
  - BACKEND/config/settings_sqlite.py
  - BACKEND/accounts/permissions.py
  - FRONTEND/src/services/api.js
  - BACKEND/accounts/views.py

- Authentication:
  - JWT-based auth via `rest_framework_simplejwt` is used and tokens returned on login. Backend also uses `SessionAuthentication` enabling Django session support.

- Authorization:
  - Role-based permission classes defined in `accounts/permissions.py` are used in API viewsets (e.g., `IsAuthorizedStaff`, `IsTeacherOrSchoolAdmin`, `IsSchoolAdmin`). Many viewsets include permission_classes that require `IsAuthenticated` plus role-based permission.

- Protected routes:
  - Backend APIs protect create/update operations with permission classes; for example, academic records creation requires `IsTeacherOrSchoolAdmin` in `AcademicRecordViewSet.get_permissions`.
  - Frontend route protection: `FRONTEND/src/routes/ProtectedRoute.jsx` and `RoleRoute.jsx` use `AuthContext` roles to gate pages; `AppRoutes.jsx` uses `ProtectedRoute`/`RoleRoute` to protect pages (e.g., `Students`, `Predictions`, etc.).

- Password hashing:
  - See section 1. Code uses Django `create_user` & password validators; the test/dev `settings_sqlite.py` sets MD5 hasher explicitly (insecure). The main `settings.py` does not override `PASSWORD_HASHERS`.

- Audit logs:
  - Implemented as DB-backed `AuditLog` records for many important actions. See section 11.

- API protection:
  - DRF permissions and authentication applied. The frontend also supplies JWT tokens via `Authorization` header. CORS origins configured in `config/settings.py`.

Limitations: The repository includes `settings_sqlite.py` which sets MD5 password hasher; if that settings file is used in any environment, passwords will be hashed insecurely. No rate limiting, no API key throttling, and no CSRF exemptions beyond DRF defaults were observed. The frontend stores tokens in `localStorage` (common but has XSS risk), and frontend lacks explicit UI for logout invalidation beyond posting refresh token to `/auth/logout/` which blacklists refresh token if provided.


13. Frontend
- Files verified:
  - FRONTEND/src/App.jsx
  - FRONTEND/src/routes/AppRoutes.jsx
  - FRONTEND/src/routes/ProtectedRoute.jsx
  - FRONTEND/src/routes/RoleRoute.jsx
  - FRONTEND/src/context/AuthContext.jsx
  - FRONTEND/src/services/api.js
  - FRONTEND/src/services/authService.js
  - FRONTEND/src/pages/* (dashboard, students, student detail, predictions, behavior, attendance, interventions)

- Routing:
  - `AppRoutes.jsx` defines React Router routes: `/login`, `/dashboard`, `/students`, `/students/:id`, `/predictions`, `/academics`, `/attendance`, `/behavior`, `/interventions`, etc. Protected routes use `ProtectedRoute` and role-protected routes use `RoleRoute`.

- Layouts:
  - `AppLayout.jsx` provides topbar, navigation, and content `Outlet` wrapper. `AuthContext` state is used to show user info and restrict nav items.

- Dashboard:
  - `Dashboard.jsx` calls `getDashboardSummary()` and renders the returned JSON into stat cards, charts and lists. The frontend expects the exact fields returned by `DashboardViewSet`.

- Student detail:
  - `StudentDetailPage.jsx` uses `studentDetailService` to fetch a suite of related resources: academic records, attendance, behavior assessments, interventions, risk predictions, and prediction factors. It renders prediction history and factors, but the frontend does not implement a direct UI action calling the `predict_student` API endpoint.

- Prediction page:
  - `PredictionsPage.jsx` lists persisted `risk-predictions` via `getRiskPredictions()` and displays recent predictions. No UI button detected to call the server `predict_student_view` endpoint to generate a new prediction on demand.

- How API services communicate with Django:
  - `FRONTEND/src/services/api.js` creates an Axios client with base URL `VITE_API_BASE_URL || 'http://localhost:8000/api'`. It attaches `Authorization` header from localStorage tokens and handles refresh flow with `/auth/token/refresh/`.

Implementation completeness: Frontend routing, layouts, and list/detail pages are implemented and consume the backend APIs. The frontend lacks an explicit client-side call to trigger prediction generation (the backend endpoint exists). Some management UIs (user management, create-student UI) are not present.


14. Overall System Workflow (code-observed end-to-end summary)
- Administrator login
  - `POST /api/auth/login/` -> `BACKEND/accounts/views.LoginView.post()` authenticates, logs in session, returns JWT tokens. Frontend stores tokens in `localStorage` via `FRONTEND/src/services/authService.js`.

- Creating users (if supported)
  - `POST /api/auth/users/` -> `BACKEND/accounts/views.UserListCreateView.create()` (Requires `IsSchoolAdmin`). Creates `User` and `UserProfile`, writes `AuditLog.USER_CREATED`.
  - Frontend UI for this is not present in inspected code.

- Adding students
  - `POST /api/students/` -> `BACKEND/students/api.StudentViewSet.perform_create()` creates student record and `AuditLog.CREATE`.
  - No dedicated frontend create form for students found; listing and detail views exist.

- Entering grades
  - `POST /api/academic-records/` -> `AcademicRecordViewSet.perform_create()` stores grades (`grade`, `final_grade`) and `encoded_by` and writes `AuditLog.CREATE`.

- Entering attendance
  - `POST /api/attendance-records/` -> `AttendanceRecordViewSet.perform_create()` stores monthly attendance records with `school_days`, `days_present`, `absences`, `times_tardy` and writes `AuditLog.CREATE`.

- Entering behavior
  - `POST /api/behavioral-assessments/` -> `BehavioralAssessmentViewSet.perform_create()` stores core value, indicator, rating, numeric score and writes `AuditLog.CREATE`.

- Entering interventions
  - `POST /api/interventions/` -> `InterventionViewSet.perform_create()` stores intervention details and writes `AuditLog.CREATE`.

- Generating AI prediction (server-side)
  - `POST /api/predictions/predict/<student_id>/` -> `predictions.views.predict_student_view` calls `PredictionService.predict_for_student` which:
    - Builds feature vector from DB (academic records, attendance, behavior, interventions).
    - Loads model/label map/feature mapping from `AI (ML)/models/*`.
    - Encodes categorical columns to one-hot using `feature_mapping` categories.
    - Calls `model.predict` and `model.predict_proba`.
    - Calls `ExplanationService.build_explanation` to produce top factors using `model.feature_importances_`.
  - `save_prediction` persists `RiskPrediction` and `PredictionFactor` records and `predict_student_view` writes `AuditLog.PREDICTION_GENERATED`.
  - Note: frontend trigger for this endpoint was not found; the endpoint must be called via API or admin/CLI.

- Saving prediction
  - `PredictionService.save_prediction` persists `RiskPrediction` and related `PredictionFactor` rows (first existing prediction is returned; duplicates are not created for same enrollment if one exists).

- Generating explanation
  - `ExplanationService.build_explanation` computes top factors from model `feature_importances_` and returns a top-factors list and summary. `PredictionService` packages these and `save_prediction` persists summary and factors.

- Updating dashboard
  - DashboardViewSet aggregates counts and recent items from the DB and returns JSON consumed by `Dashboard.jsx`.

- Viewing prediction history
  - `GET /api/risk-predictions/` and `GET /api/prediction-factors/` supply persisted prediction records and per-prediction factors. `StudentDetailPage.jsx` and `PredictionsPage.jsx` consume these.


Final Summary Table (code-verified)
| Feature | Fully Implemented | Partially Implemented | Not Implemented | Files Verified |
|---|---:|---:|---:|---|
| Authentication (login, JWT) | Yes | | | BACKEND/accounts/views.py, BACKEND/accounts/urls.py, FRONTEND/src/services/authService.js, FRONTEND/src/services/api.js |
| Password hashing config | | Partially (dev/test uses MD5) | | BACKEND/config/settings_sqlite.py, BACKEND/config/settings.py |
| User creation (API) | Yes | | | BACKEND/accounts/views.py, BACKEND/accounts/serializers.py |
| Frontend user-management UI | | | Yes | (no frontend user management files found) |
| User edit / activate/deactivate (API) | Yes | | | BACKEND/accounts/views.py, BACKEND/accounts/urls.py |
| Student model & APIs | Yes | | | BACKEND/students/models.py, BACKEND/students/api.py, FRONTEND/src/pages/students |
| Frontend student create UI | | | Yes (no create form detected) | FRONTEND/src/pages/students |
| Academic records model & APIs | Yes | | | BACKEND/academics/models.py, BACKEND/academics/api.py |
| General average & failed subjects (AI logic) | Yes (in prediction service) | | | BACKEND/predictions/services/prediction_service.py |
| Attendance model & APIs | Yes | | | BACKEND/attendance/models.py, BACKEND/attendance/api.py |
| Attendance Rate (AI feature) | Yes (computed in prediction service) | | | BACKEND/predictions/services/prediction_service.py |
| Behavior models & APIs | Yes | | | BACKEND/behavior/models.py, BACKEND/behavior/api.py |
| Behavior -> AI conversion | Yes (categorical code selection) | | | BACKEND/predictions/services/prediction_service.py |
| Interventions model & APIs | Yes | | | BACKEND/interventions/models.py, BACKEND/interventions/api.py |
| Intervention usage in AI | Yes (has_intervention, number_of_interventions) | | | BACKEND/predictions/services/prediction_service.py |
| Prediction endpoint & service | Yes (server-side, end-to-end) | | | BACKEND/predictions/views.py, BACKEND/predictions/services/prediction_service.py |
| Frontend trigger to generate prediction | | | Yes (no client post to `/api/predictions/predict/<id>/` found) | FRONTEND/src/pages/** (searched) |
| Explanation (feature importances, persistence) | Yes | | | BACKEND/predictions/services/explanation_service.py, BACKEND/predictions/models.py |
| Dashboard summary API & frontend | Yes | | | BACKEND/predictions/api.py (DashboardViewSet), FRONTEND/src/pages/dashboard/Dashboard.jsx |
| Audit logging | Yes | | | BACKEND/audit/models.py and many viewset files (e.g., accounts/views.py, students/api.py, predictions/views.py) |
| API protection, permissions & role-based authorization | Yes | | | BACKEND/accounts/permissions.py, various viewsets (academics/api.py, predictions/api.py) |


Notes and next steps you may want before defense:
- Confirm presence and versioning of `AI (ML)/models/risk_model.pkl` and `feature_mapping.json` in the repo when demonstrating the model run; the code expects them at repository-relative paths.
- If you plan to demo creating predictions from the UI, add a small frontend action/button that calls `POST /api/predictions/predict/<student_id>/` and display the returned explanation; the backend endpoint is ready.
- Replace `MD5PasswordHasher` usage in `settings_sqlite.py` before any production demo; show using Django default PBKDF2 or Argon2 (this file currently forces MD5 for test convenience).


End of code-verified notes.
