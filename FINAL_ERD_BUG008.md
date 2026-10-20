# EDU ASSIST Final ERD

Generated from Django model metadata in `BACKEND/config/settings.py` on 2026-09-08. Foreign-key and many-to-many edges below are taken from the loaded final model definitions; fields shown are the concrete model fields.

```mermaid
erDiagram
    USER ||--|| USERPROFILE : profile
    USERPROFILE }o--o{ SECTION : assigned_sections
    USER ||--o{ SECTION : advises
    USER ||--o{ TEACHERASSIGNMENT : teaches
    USER ||--o{ ACADEMICRECORD : encodes
    USER ||--o{ SCHOOLCALENDAR : authorizes_submits_approves
    USER ||--o{ RECURRINGEVENT : creates
    USER ||--o{ ATTENDANCERECORD : encodes
    USER ||--o{ BEHAVIORALASSESSMENT : assesses
    USER ||--o{ INTERVENTION : assigned_personnel
    USER ||--o{ RISKPREDICTION : reviews
    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ AUDITLOG : writes

    ACADEMICYEAR ||--o{ SECTION : contains
    ACADEMICYEAR ||--o{ TEACHERASSIGNMENT : scopes
    ACADEMICYEAR ||--o{ ENROLLMENT : scopes
    ACADEMICYEAR ||--o{ ACADEMICRECORD : scopes
    ACADEMICYEAR ||--o{ SCHOOLCALENDAR : schedules
    ACADEMICYEAR ||--o{ RECURRINGEVENT : schedules
    ACADEMICYEAR ||--o{ BEHAVIORALASSESSMENT : scopes

    GRADELEVEL ||--o{ SECTION : contains
    GRADELEVEL ||--o{ SUBJECT : targets
    GRADELEVEL }o--o{ SUBJECT : applicable_subjects
    GRADELEVEL ||--o{ TEACHERASSIGNMENT : scopes
    GRADELEVEL ||--o{ ENROLLMENT : scopes
    GRADELEVEL ||--o{ SCHOOLCALENDAR : affects
    GRADELEVEL ||--o{ RECURRINGEVENT : affects
    STRAND ||--o{ SECTION : classifies
    STRAND ||--o{ SUBJECT : classifies
    STRAND ||--o{ ENROLLMENT : classifies

    SECTION ||--o{ TEACHERASSIGNMENT : receives
    SECTION ||--o{ ENROLLMENT : contains
    SECTION ||--o{ SCHOOLCALENDAR : scopes
    SECTION ||--o{ RECURRINGEVENT : scopes

    SUBJECT ||--o{ TEACHERASSIGNMENT : assigned
    SUBJECT ||--o{ ACADEMICRECORD : records
    SUBJECT ||--o{ SCHOOLCALENDAR : examines

    STUDENT ||--o{ ENROLLMENT : has
    ENROLLMENT ||--o{ ACADEMICRECORD : has
    ENROLLMENT ||--o{ ATTENDANCERECORD : has
    ENROLLMENT ||--o{ BEHAVIORALASSESSMENT : has
    ENROLLMENT ||--o{ INTERVENTION : has
    ENROLLMENT ||--o{ RISKPREDICTION : has

    COREVALUE ||--o{ BEHAVIORINDICATOR : defines
    COREVALUE ||--o{ BEHAVIORALASSESSMENT : measures
    BEHAVIORINDICATOR ||--o{ BEHAVIORALASSESSMENT : measures
    BEHAVIORALRATING ||--o{ BEHAVIORALASSESSMENT : rates

    RECURRINGEVENT ||--o{ SCHOOLCALENDAR : generates
    SCHOOLCALENDAR ||--o{ NOTIFICATION : notifies
    RECURRINGEVENT ||--o{ NOTIFICATION : notifies
    RISKPREDICTION ||--o{ PREDICTIONFACTOR : explains

    USER {
        int id PK
        string username
        string password
        boolean is_active
        boolean is_staff
        boolean is_superuser
    }
    USERPROFILE { int id PK; int user FK; string role_name; string employee_id }
    ACADEMICYEAR { int id PK; string name; date start_date; date end_date; boolean is_active }
    GRADELEVEL { int id PK; string name; string code; string school_level; boolean is_active }
    SECTION { int id PK; int grade_level FK; int academic_year FK; int adviser FK; int strand FK; boolean is_active }
    STRAND { int id PK; string name; string code; boolean is_active }
    SUBJECT { int id PK; string code; string name; int grade_level FK; int strand FK; boolean is_active }
    TEACHERASSIGNMENT { int id PK; int teacher FK; int academic_year FK; int grade_level FK; int section FK; int subject FK; boolean is_active }
    STUDENT { int id PK; string lrn; string first_name; string last_name; string student_status }
    ENROLLMENT { int id PK; int student FK; int academic_year FK; int grade_level FK; int section FK; int strand FK; string enrollment_status }
    ACADEMICRECORD { int id PK; int enrollment FK; int subject FK; int academic_year FK; int encoded_by FK; decimal grade; decimal final_grade }
    ATTENDANCERECORD { int id PK; int enrollment FK; date attendance_date; string month; int days_present; int absences }
    SCHOOLCALENDAR { int id PK; int academic_year FK; int section FK; int affected_grade_level FK; int subject FK; int recurrence FK; int created_by FK }
    RECURRINGEVENT { int id PK; int academic_year FK; int section FK; int affected_grade_level FK; int created_by FK; boolean active }
    COREVALUE { int id PK; string name; boolean is_active }
    BEHAVIORINDICATOR { int id PK; int core_value FK; string name; boolean is_active }
    BEHAVIORALRATING { int id PK; string code; decimal numeric_value; boolean is_active }
    BEHAVIORALASSESSMENT { int id PK; int enrollment FK; int academic_year FK; int core_value FK; int behavior_indicator FK; int rating FK; int assessed_by FK }
    INTERVENTION { int id PK; int enrollment FK; int assigned_personnel FK; string status; string priority }
    RISKPREDICTION { int id PK; int enrollment FK; int reviewed_by FK; string risk_level; decimal probability }
    PREDICTIONFACTOR { int id PK; int prediction FK; string feature_name; decimal contribution }
    NOTIFICATION { int id PK; int recipient FK; int calendar_entry FK; int recurring_event FK; string title }
    AUDITLOG { int id PK; int user FK; string action; string module; string object_type; string object_id }
```

`auth.Group` and `auth.Permission` are Django framework tables and are omitted from the domain diagram except for the standard many-to-many user permission/group relationships.