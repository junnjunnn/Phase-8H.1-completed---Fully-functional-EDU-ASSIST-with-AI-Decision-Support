# SPRINT 2 ACADEMIC STRUCTURE AUDIT

**Date:** 2026-08-18  
**Scope:** Backend models, serializers, APIs, permissions | Frontend pages and components | Database schema and relationships  
**Status:** AUDIT ONLY - NO MODIFICATIONS MADE

---

## 1. Current Architecture

### Backend Structure
- **ORM:** Django ORM with SQLite database (config.settings_sqlite)
- **API:** Django REST Framework with viewsets (LIST, RETRIEVE, CREATE, UPDATE)
- **Frontend:** React 18 with Vite, using axios for API calls
- **Authentication:** Django token-based (REST Framework auth), role-based permissions
- **Audit Logging:** AuditLog model tracks all CREATE/UPDATE operations

### Key Files
**Backend:**
- `BACKEND/academics/models.py` - 8 models (AcademicYear, GradeLevel, Section, Strand, Subject, TeacherAssignment, Enrollment, AcademicRecord)
- `BACKEND/academics/serializers.py` - 8 serializers with validation
- `BACKEND/academics/api.py` - 8 ViewSets (all use mixins: List, Retrieve, Create, Update)
- `BACKEND/accounts/permissions.py` - Role-based permission classes
- `BACKEND/common/authorization.py` - Scope-based queryset filtering

**Frontend:**
- `FRONTEND/src/pages/academics/` - 9 pages
  - AcademicsPage.jsx (dashboard/overview)
  - AcademicStructurePage.jsx (admin: manage years, grades, sections, subjects)
  - AcademicYearsPage.jsx (admin: manage academic years)
  - GradeLevelsPage.jsx (admin: manage grade levels)
  - SectionsPage.jsx (admin: manage sections)
  - SubjectsPage.jsx (admin: manage subjects)
  - GradeEncodingPage.jsx (teacher: encode grades)
  - TeacherAssignmentsPage.jsx (admin: assign teachers to sections/subjects)
  - MyClassesPage.jsx (teacher: view assigned classes)
- `FRONTEND/src/services/academicsService.ts` - API wrapper functions

### Database Relationships (Current)
```
AcademicYear (1) ──→ (∞) Section
              └───→ (∞) Enrollment
              └───→ (∞) AcademicRecord

GradeLevel  (1) ──→ (∞) Section
            ├───→ (∞) Enrollment
            ├───→ (∞) TeacherAssignment
            └───→ (∞) Subject

Section     (1) ──→ (∞) Enrollment
            └───→ (∞) TeacherAssignment
            └───→ (0-1) Adviser (User)

Strand      (0-1) ─→ (∞) Subject
            └───→ (∞) Enrollment

Subject     (0-1) ─→ (∞) AcademicRecord
            └───→ (∞) TeacherAssignment

Enrollment  (1) ──→ (∞) AcademicRecord
            └───→ (0-1) Section
            └───→ (0-1) Strand

User        (0-1) ─→ (∞) TeacherAssignment
            └───→ (∞) Section (as adviser)
```

---

## 2. Current Educational Level Structure

### Database Column
- **Model:** `GradeLevel`
- **Field:** `school_level` (CharField with choices)
- **Choices:**
  - 'Elementary'
  - 'Junior High School'
  - 'Senior High School'

### Current Behavior
- Grade levels are categorized by `school_level` in the GradeLevel model
- Frontend filters grade levels by educational level during enrollment wizard
- Sections inherit educational level through their associated grade level

### Existing Data (Live Database - 2026-08-18)
```
Grade Level Records:
1. "eloi" - Senior High School (code: eloi, order: not shown)
2. "jun" - Elementary (code: jun, order: not shown)
3. "Grade 9" - Junior High School (code: G9, order: 9)
4. "Grade 12" - Senior High School (code: G12, order: 12)
```

### Issues Identified
- Data integrity issue: "jun" is labeled as "Elementary" but conventionally "Jun" refers to "Junior High" (9-10 grade)
- Only 4 out of 12 expected grade levels exist (should have Grade 1-6 Elementary, 7-10 Junior High, 11-12 Senior High)
- Seed data includes test/placeholder grade levels ("eloi", "jun") alongside real ones

---

## 3. Current Grade Level Structure

### Database Model
- **Fields:**
  - `name` (CharField, 50 chars, unique)
  - `code` (CharField, 20 chars, unique)
  - `school_level` (CharField with choice restrictions)
  - `order` (PositiveInteger, default=1)
  - `is_active` (BooleanField, default=True)

### Current Behavior
- Grade levels are managed independently via `/api/grade-levels/` endpoint
- Frontend supports create/update/list via GradeLevelsPage.jsx
- Grade levels can be associated with subjects, sections, and enrollments
- Filtering by educational level works at API and frontend levels

### Missing Grade Levels
Expected grades should include:
- **Elementary:** Grade 1, 2, 3, 4, 5, 6
- **Junior High:** Grade 7, 8, 9, 10
- **Senior High:** Grade 11, 12

Current state has only 4 records with inconsistent naming.

---

## 4. Current Section Structure

### Database Model
- **Fields:**
  - `grade_level` (FK to GradeLevel, required)
  - `academic_year` (FK to AcademicYear, required)
  - `name` (CharField, 50 chars, required)
  - `capacity` (PositiveInteger, default=0)
  - `description` (TextField, blank=True)
  - `adviser` (FK to User, nullable, role=TEACHER/ADMIN)
  - `is_active` (BooleanField, default=True)
  - `created_at`, `updated_at` (timestamps)

- **Constraints:**
  - Unique together: (grade_level, academic_year, name)
  - Ordering: by grade_level.order, then name

### Frontend Display (SectionsPage.jsx)
- Shows section information in a table with columns:
  - Section name
  - Academic year
  - Grade level
  - Capacity
  - Adviser
  - Status

### Current Data (Live Database)
```
6 sections exist:
1. "ELOI22" - eloi (SHS) - 2031-2032
2. "Garnet" - jun (Elementary) - New School Year
3. "test" - jun (Elementary) - New School Year
4. "12313" - Grade 9 (JHS) - New School Year
5. "9A" - Grade 9 (JHS) - 2025-2026
6. "A" - Grade 12 (SHS) - 2028-2029
```

### Problems Found

**Problem 1: No strand association**
- **Current behavior:** Sections do NOT have a strand field
- **Why it's a problem:** Senior High School sections should be differentiated by strand, but currently all SHS sections are presented equally without strand context
- **File responsible:** `BACKEND/academics/models.py` (Section model)
- **Severity:** HIGH - SHS enrollment wizard requires strand selection, but sections don't expose their strand

**Problem 2: Unclear educational context in UI**
- **Current behavior:** Sections are shown in a flat table without educational level grouping
- **Why it's a problem:** Admin cannot visually distinguish whether a section belongs to Elementary, JHS, or SHS at a glance
- **File responsible:** `FRONTEND/src/pages/academics/SectionsPage.jsx`
- **Severity:** MEDIUM - Usability issue, can be filtered/searched but not grouped

**Problem 3: Section-Strand mismatch in enrollment**
- **Current behavior:** Enrollment model has separate `strand` field independent of section
- **Why it's a problem:** A student's enrollment strand and section's strand could theoretically conflict; no cross-validation
- **File responsible:** `BACKEND/academics/models.py` (Enrollment model)
- **Severity:** MEDIUM - Business logic flaw if not managed carefully

---

## 5. Current Strand Structure

### Database Model
- **Fields:**
  - `name` (CharField, 100 chars, unique)
  - `code` (CharField, 20 chars, unique, blank=True)
  - `description` (TextField, blank=True)
  - `is_active` (BooleanField, default=True)

### Frontend Display (SubjectsPage.jsx, TeacherAssignmentsPage.jsx)
- Strands shown as dropdown options in subject and teacher assignment forms
- No dedicated "StrandsPage" exists for CRUD operations on strands
- Strands managed only via AcademicStructurePage.jsx

### Current Data
```
0 strands exist in the database
```

### Problems Found

**Problem 1: No SHS-only restriction**
- **Current behavior:** Strands can be assigned to ANY grade level (Elementary, JHS, SHS)
- **Why it's a problem:** Business logic specifies strands should ONLY apply to SHS (Grade 11-12)
- **File responsible:** `BACKEND/academics/serializers.py` (SubjectSerializer) and `BACKEND/academics/models.py` (Subject model)
- **Severity:** HIGH - Violates business requirements and will cause confusion

**Problem 2: No strand-section connection**
- **Current behavior:** Sections do not have a strand field; only subjects and enrollments do
- **Why it's a problem:** A section in SHS should be explicitly associated with one strand, making it clear which students go to which section based on strand choice
- **File responsible:** `BACKEND/academics/models.py` (Section model)
- **Severity:** HIGH - Core SHS feature unsupported

**Problem 3: Missing strand master data**
- **Current behavior:** Database has 0 strands; frontend allows all 6 standard SHS strands
- **Why it's a problem:** No actual strand records to assign to subjects or use in enrollment
- **File responsible:** Seed data / initial data loading
- **Severity:** CRITICAL - Cannot properly test SHS enrollment workflow

---

## 6. Current Subject Structure

### Database Model
- **Fields:**
  - `code` (CharField, 30 chars, unique, required)
  - `name` (CharField, 150 chars, required)
  - `description` (TextField, blank=True)
  - `category` (CharField, choices: 'Learning Area', 'Core', 'Applied', 'Specialized')
  - `grade_level` (FK to GradeLevel, nullable)
  - `strand` (FK to Strand, nullable)
  - `is_active` (BooleanField, default=True)

### Frontend Display (SubjectsPage.jsx)
- Table with columns:
  - Code
  - Name
  - Category
  - Grade level
  - Strand
  - Status

### Current Data (Live Database)
```
4 subjects exist:
1. "JUNLOILAW" - Category: Core - Grade: eloi (SHS) - Strand: None
2. "Mathematics" - Category: Core - Grade: Grade 12 (SHS) - Strand: None
3. "Mathematics 9" - Category: Learning Area - Grade: Grade 9 (JHS) - Strand: None
4. "post" - Category: Learning Area - Grade: Grade 12 (SHS) - Strand: None
```

### Problems Found

**Problem 1: Insufficient SHS categorization**
- **Current behavior:** Categories are generic (Learning Area, Core, Applied, Specialized) but lack context for SHS strand differentiation
- **Why it's a problem:** SHS subjects need more nuanced categorization:
  - Core subjects (common to all strands)
  - Strand-specific subjects
  - Applied/specialized by strand
- **File responsible:** `BACKEND/academics/models.py` (Subject model category choices)
- **Severity:** MEDIUM - Can work around by using strand+category, but not explicit

**Problem 2: No validation of strand restriction**
- **Current behavior:** A subject can be assigned to strand even if grade_level is not SHS
- **Why it's a problem:** Elementary and JHS subjects should never have a strand; this violates business logic
- **File responsible:** `BACKEND/academics/serializers.py` (SubjectSerializer validate method)
- **Severity:** HIGH - Allows invalid data states

**Problem 3: Grade level optional for subjects**
- **Current behavior:** `grade_level` is nullable (can be blank)
- **Why it's a problem:** All subjects should be associated with at least one grade level to be meaningful
- **File responsible:** `BACKEND/academics/models.py` (Subject model)
- **Severity:** MEDIUM - Allows orphaned subjects

**Problem 4: No subject caching/querying for subjects by educational level**
- **Current behavior:** Frontend must load all subjects and filter client-side
- **Why it's a problem:** As subject count grows, performance degrades; API should support filtering by educational level or strand
- **File responsible:** `BACKEND/academics/api.py` (SubjectViewSet - no filter backends)
- **Severity:** LOW - Currently not filtered; could be optimized

**Problem 5: Placeholder/test subject data**
- **Current behavior:** "post" and "JUNLOILAW" appear to be test records
- **Why it's a problem:** Production data should not contain test subjects
- **File responsible:** Seed data
- **Severity:** LOW - Data quality issue

---

## 7. Current Teacher Assignment Structure

### Database Model
- **Fields:**
  - `teacher` (FK to User, required)
  - `academic_year` (FK to AcademicYear, required)
  - `grade_level` (FK to GradeLevel, required)
  - `section` (FK to Section, required)
  - `subject` (FK to Subject, required)
  - `is_active` (BooleanField, default=True)
  - `created_at`, `updated_at` (timestamps)

- **Constraints:**
  - Unique together: (teacher, academic_year, grade_level, section, subject)
  - Ordering: by -created_at

### Validation (Serializer)
- Section must belong to the selected grade level (cross-validation)
- All fields required

### Current Data
```
0 teacher assignments exist
```

### Authorization
- Admin can create/update/list teacher assignments
- Teachers can view their own assignments (filtered in GradeEncodingPage)

### Problems Found

**Problem 1: No validation that section matches academic year**
- **Current behavior:** Can create assignment with section from different academic year
- **Why it's a problem:** Teacher assignment should validate that the section belongs to the selected academic year
- **File responsible:** `BACKEND/academics/serializers.py` (TeacherAssignmentSerializer validate method)
- **Severity:** MEDIUM - Would cause data inconsistency

**Problem 2: No validation for SHS strand context**
- **Current behavior:** No check whether subject strand matches section's implicit strand
- **Why it's a problem:** For SHS, teacher should only be assigned to teach a subject in a section if the subject's strand matches the section's strand
- **File responsible:** `BACKEND/academics/serializers.py` (TeacherAssignmentSerializer)
- **Severity:** HIGH - Critical for SHS workflow correctness

---

## 8. Current Enrollment Relationship

### Database Model
- **Fields:**
  - `student` (FK to Student, required)
  - `academic_year` (FK to AcademicYear, required)
  - `grade_level` (FK to GradeLevel, required)
  - `section` (FK to Section, nullable)
  - `strand` (FK to Strand, nullable)
  - `enrollment_status` (CharField, choices: active, transferred, graduated, withdrawn, inactive)
  - `enrollment_date` (DateField, default=today)
  - `created_at`, `updated_at` (timestamps)

- **Constraints:**
  - Unique together: (student, academic_year)
  - Validation: section.grade_level must match enrollment.grade_level

### Enrollment Workflow (Frontend: EnrollmentPage.jsx)
1. Select School Year (active only)
2. Select Educational Level (Elementary, JHS, SHS)
3. Select Grade Level (filtered by educational level)
4. Select Strand (only if Grade 11 or 12)
5. Select Section (filtered by year + grade + visible strands)
6. Select Student (exclude already-enrolled in same year)
7. Review and confirm

### Business Logic
- Strand is optional for Elementary and JHS (ignored in wizard)
- Strand is required for SHS (Grade 11-12)
- Section selection filters to match year and grade
- Frontend hides strand step for non-SHS grades (gradeRequiresStrand)

### Current Data
```
4 enrollments exist:
1. Student: "Sprint Registrar Updated" - Year: "New School Year" - Grade: Grade 9 (JHS) - Section: 12313 - Strand: None
2-4. Other enrollments (created during Sprint 1 testing)
```

### Problems Found

**Problem 1: Section-Strand mismatch not enforced**
- **Current behavior:** Section does not have strand field; no validation prevents misalignment
- **Why it's a problem:** In SHS, a student enrolled in section "STEM-A" should have strand=STEM, but validation doesn't check
- **File responsible:** `BACKEND/academics/models.py` (Enrollment validation)
- **Severity:** HIGH - Data integrity risk for SHS

**Problem 2: Enrollments allow section=NULL**
- **Current behavior:** Section is nullable
- **Why it's a problem:** Enrollment without section is meaningless; all enrollments should be in a section
- **File responsible:** `BACKEND/academics/models.py` (Section model FK)
- **Severity:** HIGH - Would leave students without a class

**Problem 3: Duplicate enrollment prevention is per academic_year only**
- **Current behavior:** Unique(student, academic_year)
- **Why it's a problem:** Good, prevents double-enrollment in same year, but no check for section capacity
- **File responsible:** `BACKEND/academics/models.py` (Enrollment constraints)
- **Severity:** MEDIUM - Frontend has capacity check but not enforced at DB level

**Problem 4: No SHS validation logic**
- **Current behavior:** No database-level validation that SHS students must have a strand
- **Why it's a problem:** Invalid enrollments can exist via raw API calls without SHS strand
- **File responsible:** `BACKEND/academics/models.py` (Enrollment clean method)
- **Severity:** HIGH - Business rule not enforced

---

## 9. Existing Frontend Structure

### Pages Hierarchy
```
/academics (AcademicsPage) - Dashboard
  ├─ /academic-years (AcademicYearsPage) - Admin only
  ├─ /academic-structure (AcademicStructurePage) - Admin only (combined year, grade, section, subject management)
  ├─ /grade-levels (GradeLevelsPage) - Admin only
  ├─ /sections (SectionsPage) - Admin only
  ├─ /subjects (SubjectsPage) - Admin only
  ├─ /teacher-assignments (TeacherAssignmentsPage) - Admin only
  ├─ /enrollment (EnrollmentPage) - Registrar/Admin (7-step wizard)
  ├─ /academics/encode (GradeEncodingPage) - Teacher/Admin (grade input)
  └─ /my-classes (MyClassesPage) - Teacher only
```

### Access Control (Navigation)
- Academic Years: SUPER_ADMIN, SCHOOL_ADMIN only
- Grade Levels: SUPER_ADMIN, SCHOOL_ADMIN only
- Sections: SUPER_ADMIN, SCHOOL_ADMIN only
- Subjects: SUPER_ADMIN, SCHOOL_ADMIN only
- Teacher Assignments: SUPER_ADMIN, SCHOOL_ADMIN only
- Enrollment: SUPER_ADMIN, SCHOOL_ADMIN, REGISTRAR
- Grade Encoding: SUPER_ADMIN, SCHOOL_ADMIN, TEACHER
- My Classes: TEACHER only

### Components
- AcademicsService (`academicsService.ts`) provides API wrappers
- AdviserSelect component for user selection (teachers/admins)
- Standard table, form, pagination components

### Problems Found

**Problem 1: No "Strands Page"**
- **Current behavior:** Strands managed only via AcademicStructurePage (embedded in form)
- **Why it's a problem:** No dedicated UI for strand CRUD, making it hard to discover and manage
- **File responsible:** `FRONTEND/src/pages/academics/` (no StrandsPage.jsx)
- **Severity:** MEDIUM - Workaround exists but not intuitive

**Problem 2: No "Educational Structure Diagram"**
- **Current behavior:** Users must understand relationships implicitly through separate pages
- **Why it's a problem:** Admin cannot visualize the full academic structure (which grades, sections, subjects belong to which educational level)
- **File responsible:** UI design
- **Severity:** LOW - Not required for MVP but helpful for understanding

**Problem 3: No SHS-specific section grouping**
- **Current behavior:** Sections displayed as flat list
- **Why it's a problem:** For SHS, sections should be grouped by strand to show structure
- **File responsible:** `FRONTEND/src/pages/academics/SectionsPage.jsx`
- **Severity:** MEDIUM - Usability issue for larger schools

**Problem 4: AcademicStructurePage is multi-modal**
- **Current behavior:** Years, Grades, Sections, Subjects all on one page with separate forms
- **Why it's a problem:** Long page with multiple concerns; hard to maintain; hard to test individual concerns
- **File responsible:** `FRONTEND/src/pages/academics/AcademicStructurePage.jsx`
- **Severity:** LOW - Works but not ideal architecture

---

## 10. Problems Found (Summary)

| Problem | Severity | Component | Impact |
|---------|----------|-----------|--------|
| No section-strand association | **CRITICAL** | Model | SHS sections cannot be differentiated by strand |
| No strands in database | **CRITICAL** | Data | Cannot test/use SHS enrollment features |
| No SHS strand validation | **CRITICAL** | Validation | Invalid enrollments possible (SHS without strand) |
| Grade level data incomplete | **HIGH** | Data | Only 4 of 12 expected grades exist |
| Grade level naming inconsistent | **HIGH** | Data | "jun" labeled as Elementary but implies Junior High |
| Strand not restricted to SHS | **HIGH** | Validation | Elementary/JHS subjects can have strands (invalid) |
| No section-year validation | **HIGH** | Validation | Teacher assignment can reference wrong academic year |
| No SHS strand-subject-section validation | **HIGH** | Validation | SHS teacher could be assigned to wrong strand section |
| Section capacity not enforced at DB | **MEDIUM** | Database | Enrollment bypasses capacity check |
| Subject grade_level optional | **MEDIUM** | Model | Orphaned subjects possible |
| Enrollments allow section=NULL | **MEDIUM** | Model | Students could exist without a class |
| No strand-dedicated UI page | **MEDIUM** | Frontend | Strands hard to discover and manage |
| Subjects not filterable by educational level | **MEDIUM** | API | Performance/usability degradation at scale |
| Section-strand mismatch not enforced | **MEDIUM** | Validation | Data integrity risk for SHS |
| Placeholder subject/grade data exists | **LOW** | Data | Test data mixed with real data |
| Sections not grouped by educational level | **LOW** | Frontend | Usability issue for visualization |

---

## 11. Required Changes

### Backend Changes

**1. Add Strand Field to Section Model**
- Add `strand` (FK to Strand, nullable, blank=True) to Section
- Update SectionSerializer to include strand
- Update SectionViewSet filtering/permissions
- Add migration

**2. Add Validation: Strand Restricted to SHS Only**
- Add clean() method to Subject to validate: if strand is set, grade_level must be Grade 11 or 12
- Add clean() method to Enrollment to validate: if grade is SHS, strand must be set

**3. Add Validation: Section-Strand Consistency for SHS**
- Update Enrollment clean() to validate: if section has a strand, enrollment.strand must match

**4. Add Validation: Subject Grade Level Required**
- Change `grade_level` to `null=False, blank=False` in Subject model
- Add migration to backfill existing subjects

**5. Add Validation: Enrollment Section Required**
- Change `section` to `null=False, blank=False` in Enrollment model
- Add migration (will require handling existing NULL sections)

**6. Add Teacher Assignment Validation**
- Update TeacherAssignmentSerializer to validate:
  - Section.academic_year matches TeacherAssignment.academic_year
  - For SHS: Subject.strand matches Section.strand

**7. Add API Filtering for Subjects**
- Add `filterset_fields` to SubjectViewSet: ['grade_level', 'strand', 'category', 'school_level']
- Add SearchFilter for subject name/code

### Frontend Changes

**1. Create StrandsPage Component**
- Dedicated page for strand CRUD operations
- Add to navigation (admin only)
- Link from subject/section/enrollment pages

**2. Update SectionsPage to Show Strand for SHS**
- Add strand column to section table
- Add strand field to section form
- Filter section list to show strand context for SHS

**3. Update SubjectsPage to Validate SHS**
- Hide/disable strand field for non-SHS grades
- Show visual indicator when subject is SHS-only

**4. Update EnrollmentPage for Strand-Section Mapping**
- In step 5 (Section selection), ensure sections are grouped/filtered by strand
- Show strand context alongside section name for SHS

**5. Update AcademicStructurePage**
- Add strand management section (forms + table)
- Or refactor to separate modal/page

**6. Add Academic Structure Visualization (Optional)**
- Create diagram showing: Educational Level → Grade → Strand (SHS) → Section → Student
- Display on AcademicsPage for admin

### Database/Migration Changes

**Migration 1: Add Strand to Section**
```python
field = models.ForeignKey(Strand, on_delete=models.SET_NULL, null=True, blank=True)
AddField('Section', 'strand', field)
```

**Migration 2: Make Subject.grade_level Required**
```python
- Backfill: Subjects with null grade_level get Elementary as default
AlterField('Subject', 'grade_level', models.ForeignKey(..., null=False, blank=False))
```

**Migration 3: Seed Complete Academic Structure**
```python
- Add Grade 1-6 (Elementary)
- Add Grade 7-10 (Junior High)
- Rename/fix existing grades
- Add 6 SHS Strands (STEM, ABM, HUMSS, GAS, TVL ICT, TVL HE)
- Add sample subjects for each grade level
- Add sample sections for new grades
```

**Migration 4: Fix Enrollment Section Requirement (Complex)**
```python
- Check for enrollments with section=NULL
- Assign to default section or require manual intervention
- AlterField('Enrollment', 'section', models.ForeignKey(..., null=False))
```

---

## 12. Data Migration Risks

### Risk 1: Orphaned Subjects with NULL Grade Level
- **Current:** Subject.grade_level can be NULL (optional)
- **Plan:** Backfill with Elementary as default; then make required
- **Risk:** Wrong default assignment for existing subjects
- **Mitigation:** Manual review of existing subjects before running migration

### Risk 2: Enrollments with NULL Section
- **Current:** Enrollment.section can be NULL (valid state)
- **Plan:** Make section required
- **Risk:** Some enrollments might be in NULL state; cannot migrate without knowing where to assign
- **Mitigation:** Run query to identify enrollments with NULL section; manual assignment or data cleanup

### Risk 3: Incomplete Grade Level Data
- **Current:** Only 4 of 12 expected grades exist
- **Plan:** Add missing grades (1-6, 7-10)
- **Risk:** Existing sections for incomplete grades won't exist
- **Mitigation:** Identify which grades are "in use" before adding new ones; no conflict expected

### Risk 4: No Existing Strand Data
- **Current:** 0 strands in database
- **Plan:** Create 6 standard SHS strands
- **Risk:** No risk; adding new data
- **Mitigation:** Verify strand codes match subject/enrollment expectations

### Risk 5: Section-Strand Addition
- **Current:** Sections do not have strand FK
- **Plan:** Add strand FK (nullable initially, then populate for SHS sections)
- **Risk:** Requires identifying which sections are SHS and assigning correct strand
- **Mitigation:** Populate based on section's grade_level; manual review for ambiguous cases

---

## 13. Sprint 1 Regression Risks

### Sprint 1 Protected Features
1. **Registrar Role:** Can access students and enrollment endpoints
2. **Registrar Student Access:** Can read/create students
3. **Registrar Enrollment Access:** Can read/create enrollments
4. **Admin-Only User Management:** /users endpoint blocked from registrar
5. **Enrollment Wizard:** All 7 steps functional and accessible
6. **Student Registration:** Can register new students
7. **Authorization Behavior:** Role-based access controls working

### Potential Regression Points

**Risk 1: Permission Changes**
- **Issue:** If SectionViewSet or SubjectViewSet permissions are modified to support new strand features
- **Sprint 1 impact:** Registrar must retain read access to sections and subjects in enrollment wizard
- **Mitigation:** Keep IsAcademicReferenceAccessAllowed permission class for read-only operations

**Risk 2: Enrollment Validation Strictness**
- **Issue:** Adding new validations (strand required for SHS, section required, etc.)
- **Sprint 1 impact:** Existing enrollments must remain valid; wizard must pass all new validations
- **Mitigation:** Ensure wizard enforces all validations client-side; test existing enrollment flow

**Risk 3: Database Schema Changes**
- **Issue:** Adding strand FK to Section, making fields required, etc.
- **Sprint 1 impact:** Existing sections and enrollments must remain queryable and modifiable
- **Mitigation:** Ensure nullable=True, blank=True initially; backfill data before making required

**Risk 4: Serializer Changes**
- **Issue:** Adding strand field to SectionSerializer could break existing API contracts
- **Sprint 1 impact:** Frontend enrollment page expects certain Section response format
- **Mitigation:** Ensure backward-compatible serializer changes; test with existing frontend

### Regression Test Checklist (Do NOT Start Yet)
- [ ] Registrar can log in and access /students
- [ ] Registrar can access /enrollment
- [ ] Registrar can view academic years
- [ ] Registrar can view grade levels
- [ ] Registrar can view sections
- [ ] Registrar can view students
- [ ] Registrar can create enrollments (all 7 steps)
- [ ] Registrar is blocked from /users
- [ ] Admin can still manage academic structure
- [ ] Teacher access unchanged
- [ ] Guidance access unchanged

---

## 14. Recommended Sprint 2 Implementation Order

### Phase 1: Prepare (Database & Validation)
1. ✅ Create complete grade level master data (Grades 1-6, 7-10, 11-12)
2. ✅ Fix grade level naming/categorization (rename "jun" if needed)
3. ✅ Create SHS strand master data (STEM, ABM, HUMSS, GAS, TVL ICT, TVL HE)
4. ✅ Create sample subjects for each grade level and strand
5. ✅ Add Subject clean() validation: strand only for SHS
6. ✅ Add Enrollment clean() validation: strand required for SHS
7. ✅ Migration 1: Add Strand FK to Section

### Phase 2: Core Model Changes
1. ✅ Update Section model: add strand FK (nullable)
2. ✅ Update SectionSerializer: include strand
3. ✅ Add Enrollment validation: section-strand consistency for SHS
4. ✅ Add TeacherAssignment validation: academic_year match, strand match for SHS
5. ✅ Migration 2: Backfill and make Subject.grade_level required
6. ✅ Update Subject model: grade_level not null

### Phase 3: API & Backend
1. ✅ Add strand filtering to SubjectViewSet
2. ✅ Create StrandViewSet (if not exists) with proper permissions
3. ✅ Update SectionViewSet to handle strand
4. ✅ Update EnrollmentViewSet validation
5. ✅ Update TeacherAssignmentViewSet validation
6. ✅ Backend tests: validate SHS strand logic, section-strand consistency

### Phase 4: Frontend
1. ✅ Create StrandsPage for dedicated strand management
2. ✅ Update SectionsPage to show/manage strand for SHS
3. ✅ Update SubjectsPage to validate strand-educational level
4. ✅ Update EnrollmentPage to show strand context in section selection
5. ✅ Update AcademicStructurePage to include strands
6. ✅ Frontend tests: validate SHS enrollment with strands

### Phase 5: Testing & Polish
1. ✅ Full end-to-end test: SHS enrollment with strand selection
2. ✅ Regression tests: All Sprint 1 features still work
3. ✅ Data validation tests: Correct subject-strand assignments
4. ✅ Teacher assignment tests: Strand-section matching
5. ✅ Permission tests: Registrar/teacher/admin access still correct

### Phase 6: Optional Enhancements (Sprint 2 Extended)
1. Academic structure diagram/visualization
2. Bulk import for grades, subjects, strands
3. Strand-aware reporting
4. Section capacity and enrollment analytics by strand

---

## 15. Files That Would Need Modification

### Backend Files (Code Changes)
```
BACKEND/academics/models.py
  - Add strand FK to Section
  - Add validation methods

BACKEND/academics/serializers.py
  - Update SectionSerializer
  - Add strand-related validation
  - Add filtering to SubjectSerializer

BACKEND/academics/api.py
  - Update SectionViewSet
  - Add filtering to SubjectViewSet
  - Add filtering to StrandViewSet (if new)

BACKEND/academics/migrations/000X_*.py (NEW)
  - Add strand to Section
  - Backfill and change Subject.grade_level

BACKEND/academics/tests.py
  - Add tests for SHS strand logic
  - Add tests for validation

BACKEND/accounts/permissions.py (POSSIBLY)
  - No changes expected (registrar access preserved)

BACKEND/common/authorization.py (POSSIBLY)
  - No changes expected
```

### Frontend Files (Code Changes)
```
FRONTEND/src/pages/academics/SectionsPage.jsx
  - Add strand field to form
  - Add strand column to table
  - Update section filtering/display

FRONTEND/src/pages/academics/SubjectsPage.jsx
  - Add strand validation logic
  - Hide/disable strand for non-SHS

FRONTEND/src/pages/academics/AcademicStructurePage.jsx
  - Add strand management section
  - OR refactor to separate pages

FRONTEND/src/pages/academics/StrandsPage.jsx (NEW)
  - Create dedicated strand management page

FRONTEND/src/pages/students/EnrollmentPage.jsx
  - Update section filtering for strand context
  - Update UI to show strand in section display
  - Ensure SHS strand step is working correctly

FRONTEND/src/pages/academics/GradeEncodingPage.jsx (POSSIBLY)
  - No changes expected (teacher grades, not structure)

FRONTEND/src/pages/academics/TeacherAssignmentsPage.jsx (POSSIBLY)
  - Possibly update to show strand context
  - Validate strand-section match

FRONTEND/src/config/navigation.js
  - Add Strands link (admin only)
  - Potentially reorganize academic structure links

FRONTEND/src/services/academicsService.ts
  - Add strand API wrappers (getStrands, createStrand, updateStrand)
```

### No Changes Required (Sprint 1 Preserved)
```
FRONTEND/src/context/AuthContext.jsx
  - No changes

BACKEND/accounts/permissions.py
  - No changes (unless new permissions needed)

BACKEND/students/
  - No changes

FRONTEND/src/pages/students/StudentsPage.jsx
  - No changes

FRONTEND/src/routes/AppRoutes.jsx
  - Possibly add Strands route

FRONTEND/src/routes/RoleRoute.jsx
  - No changes
```

---

## Summary

The current academic structure supports the basic requirements (elementary, JHS, SHS with configurable grades and sections), but **SHS strand support is incomplete**:

- ✅ Grade levels categorized by educational level
- ✅ Sections linked to grade levels
- ✅ Subjects can be tagged with grades and strands
- ❌ **Sections NOT linked to strands** (critical gap)
- ❌ **No SHS-only validation** for strands
- ❌ **No strand master data** (0 strands exist)
- ❌ **No dedicated Strands UI page**

**Sprint 1 regression risk:** Low, as long as read access to academic reference data is preserved for registrar.

**Recommended approach:** Start with Phase 1 (data preparation and validation), then Phase 2-3 (core changes), ensuring Sprint 1 functionality is tested at each step.

---

*End of Audit Report*
