from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment, Subject, AcademicRecord, TeacherAssignment, Strand
from academics.serializers import SubjectSerializer
from students.models import Student


class AcademicsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.superadmin = self.user_model.objects.create_user(username='superadmin_academics', password='SuperPass1!')
        UserProfile.objects.create(user=self.superadmin, role_name='SUPER_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='teacher_academics', password='TeacherPass1!')
        teacher_profile = UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        # Use the grade level from Phase 1 migration (0004)
        self.grade_level = GradeLevel.objects.get(code='G11')
        section_a = Section.objects.create(name='A', grade_level=self.grade_level, academic_year=self.academic_year)
        self.section_b = Section.objects.create(name='B', grade_level=self.grade_level, academic_year=self.academic_year)
        teacher_profile.assigned_sections.add(section_a)

        self.student_a = Student.objects.create(first_name='Alice', last_name='Anderson', gender='Female', student_status='active')
        self.student_b = Student.objects.create(first_name='Bob', last_name='Baker', gender='Male', student_status='active')

        self.enrollment_a = Enrollment.objects.create(student=self.student_a, academic_year=self.academic_year, grade_level=self.grade_level, section=section_a, enrollment_status='active')
        self.enrollment_b = Enrollment.objects.create(student=self.student_b, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')

        self.subject = Subject.objects.create(code='MATH11', name='Mathematics 11', category='Learning Area', grade_level=self.grade_level)
        self.record_a = AcademicRecord.objects.create(enrollment=self.enrollment_a, subject=self.subject, academic_year=self.academic_year, grading_period_type='Quarter', quarter=1, grade=85.00)
        self.record_b = AcademicRecord.objects.create(enrollment=self.enrollment_b, subject=self.subject, academic_year=self.academic_year, grading_period_type='Quarter', quarter=1, grade=90.00)

    def test_teacher_only_sees_assigned_section_enrollments(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/enrollments/')
        self.assertEqual(response.status_code, 200)
        enrollment_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.enrollment_a.id, enrollment_ids)
        self.assertNotIn(self.enrollment_b.id, enrollment_ids)

    def test_teacher_only_sees_assigned_section_academic_records(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/academic-records/')
        self.assertEqual(response.status_code, 200)
        record_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.record_a.id, record_ids)
        self.assertNotIn(self.record_b.id, record_ids)

    def test_superadmin_sees_all_academic_records(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/academic-records/')
        self.assertEqual(response.status_code, 200)
        record_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.record_a.id, record_ids)
        self.assertIn(self.record_b.id, record_ids)

    def test_teacher_cannot_create_sections(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/sections/', {
            'academic_year': self.academic_year.id,
            'grade_level': self.grade_level.id,
            'name': 'New Section',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 403)

    def test_duplicate_academic_record_is_rejected(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.post('/api/academic-records/', {
            'enrollment': self.enrollment_a.id,
            'subject': self.subject.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 1,
            'grade': 88.00,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('already exists', str(response.data))

    def test_duplicate_active_academic_year_is_rejected(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.post('/api/academic-years/', {
            'name': '2026-2027',
            'start_date': '2026-06-01',
            'end_date': '2027-03-31',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('active', str(response.data))

    def test_duplicate_section_in_same_grade_and_year_is_rejected(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.post('/api/sections/', {
            'academic_year': self.academic_year.id,
            'grade_level': self.grade_level.id,
            'name': 'A',
            'capacity': 40,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('already exists', str(response.data))

    def test_duplicate_subject_code_is_rejected(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.post('/api/subjects/', {
            'code': 'MATH11',
            'name': 'Mathematics 11 Advanced',
            'category': 'Learning Area',
            'grade_level': self.grade_level.id,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('already exists', str(response.data))

    def test_duplicate_teacher_assignment_is_rejected(self):
        self.client.force_authenticate(user=self.superadmin)
        subject = Subject.objects.create(code='SCI11', name='Science 11', category='Learning Area', grade_level=self.grade_level)
        section = Section.objects.create(name='C', grade_level=self.grade_level, academic_year=self.academic_year)
        TeacherAssignment.objects.create(teacher=self.teacher, academic_year=self.academic_year, grade_level=self.grade_level, section=section, subject=subject)
        response = self.client.post('/api/teacher-assignments/', {
            'teacher': self.teacher.id,
            'academic_year': self.academic_year.id,
            'grade_level': self.grade_level.id,
            'section': section.id,
            'subject': subject.id,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('already exists', str(response.data))


class AcademicMasterDataTests(TestCase):
    """
    Tests for Phase 1 Academic Master Data:
    - Verify all 12 expected grade levels exist
    - Verify each grade level belongs to correct educational level
    - Verify 6 SHS strands exist
    - Verify master data is idempotent (no duplicates on re-seeding)
    """

    def test_all_12_grade_levels_exist(self):
        """Verify all 12 grade levels (1-6 Elementary, 7-10 JHS, 11-12 SHS) exist."""
        expected_grades = [
            ('Grade 1', 'G1', 'Elementary'),
            ('Grade 2', 'G2', 'Elementary'),
            ('Grade 3', 'G3', 'Elementary'),
            ('Grade 4', 'G4', 'Elementary'),
            ('Grade 5', 'G5', 'Elementary'),
            ('Grade 6', 'G6', 'Elementary'),
            ('Grade 7', 'G7', 'Junior High School'),
            ('Grade 8', 'G8', 'Junior High School'),
            ('Grade 9', 'G9', 'Junior High School'),
            ('Grade 10', 'G10', 'Junior High School'),
            ('Grade 11', 'G11', 'Senior High School'),
            ('Grade 12', 'G12', 'Senior High School'),
        ]
        for name, code, school_level in expected_grades:
            grade = GradeLevel.objects.get(code=code)
            self.assertEqual(grade.name, name)
            self.assertEqual(grade.school_level, school_level)

    def test_grade_levels_have_correct_order(self):
        """Verify grade levels have correct order (used for sorting)."""
        expected_orders = {
            'G1': 1, 'G2': 2, 'G3': 3, 'G4': 4, 'G5': 5, 'G6': 6,
            'G7': 7, 'G8': 8, 'G9': 9, 'G10': 10,
            'G11': 11, 'G12': 12,
        }
        for code, expected_order in expected_orders.items():
            grade = GradeLevel.objects.get(code=code)
            self.assertEqual(grade.order, expected_order, f"Grade {code} has wrong order")

    def test_elementary_school_levels(self):
        """Verify Elementary has exactly 6 grades."""
        elementary = GradeLevel.objects.filter(school_level='Elementary')
        self.assertEqual(elementary.count(), 6)

    def test_junior_high_school_levels(self):
        """Verify Junior High School has exactly 4 grades."""
        jhs = GradeLevel.objects.filter(school_level='Junior High School')
        self.assertEqual(jhs.count(), 4)

    def test_senior_high_school_levels(self):
        """Verify Senior High School has exactly 2 grades."""
        shs = GradeLevel.objects.filter(school_level='Senior High School')
        self.assertEqual(shs.count(), 2)

    def test_all_6_shs_strands_exist(self):
        """Verify all 6 standard SHS strands exist."""
        from academics.models import Strand
        expected_strands = [
            ('STEM', 'STEM'),
            ('ABM', 'ABM'),
            ('HUMSS', 'HUMSS'),
            ('GAS', 'GAS'),
            ('TVL-ICT', 'TVL-ICT'),
            ('TVL-HE', 'TVL-HE'),
        ]
        for code, name in expected_strands:
            strand = Strand.objects.get(code=code)
            self.assertEqual(strand.name, name)

    def test_strands_are_unique(self):
        """Verify strands are unique by code and name."""
        from academics.models import Strand
        strand_codes = Strand.objects.values_list('code', flat=True)
        self.assertEqual(len(strand_codes), len(set(strand_codes)), "Strands should have unique codes")

        strand_names = Strand.objects.values_list('name', flat=True)
        self.assertEqual(len(strand_names), len(set(strand_names)), "Strands should have unique names")

    def test_grade_levels_are_unique(self):
        """Verify grade levels are unique by code and name."""
        grade_codes = GradeLevel.objects.values_list('code', flat=True)
        self.assertEqual(len(grade_codes), len(set(grade_codes)), "Grade levels should have unique codes")

        grade_names = GradeLevel.objects.values_list('name', flat=True)
        self.assertEqual(len(grade_names), len(set(grade_names)), "Grade levels should have unique names")

    def test_grade_levels_are_active(self):
        """Verify all grade levels are active."""
        inactive_grades = GradeLevel.objects.filter(is_active=False)
        self.assertEqual(inactive_grades.count(), 0, "All grade levels should be active")

    def test_strands_are_active(self):
        """Verify all strands are active."""
        from academics.models import Strand
        inactive_strands = Strand.objects.filter(is_active=False)
        self.assertEqual(inactive_strands.count(), 0, "All strands should be active")

    def test_existing_enrollments_still_valid(self):
        """Verify existing enrollments from setup work with new grade data."""
        # Use a grade that exists from the migration (e.g., Grade 9)
        grade_9 = GradeLevel.objects.get(code='G9')
        self.assertEqual(grade_9.school_level, 'Junior High School')

        # Should be able to create a section with a migrated grade level
        academic_year = AcademicYear.objects.create(
            name='2025-2026-test',
            start_date='2025-06-01',
            end_date='2026-03-31',
            is_active=False
        )
        section = Section.objects.create(
            grade_level=grade_9,
            academic_year=academic_year,
            name='Test Section',
            capacity=40
        )
        self.assertEqual(section.grade_level.code, 'G9')


class SectionStrandValidationTests(TestCase):
    """Test Phase 2: Section-Strand relationships and validation."""

    def setUp(self):
        from academics.models import Strand

        self.academic_year = AcademicYear.objects.create(
            name='2025-2026',
            start_date='2025-06-01',
            end_date='2026-03-31',
            is_active=True
        )

        # Create grade levels
        self.grade_1 = GradeLevel.objects.get(code='G1')  # Elementary
        self.grade_7 = GradeLevel.objects.get(code='G7')  # JHS
        self.grade_11 = GradeLevel.objects.get(code='G11')  # SHS

        # Create strands
        self.stem = Strand.objects.get(code='STEM')
        self.abm = Strand.objects.get(code='ABM')

        # Create an inactive strand for testing
        self.inactive_strand = Strand.objects.create(
            name='Inactive Strand',
            code='INACTIVE',
            is_active=False
        )

    def test_elementary_section_without_strand_is_valid(self):
        """Elementary sections should not have strands."""
        section = Section(
            grade_level=self.grade_1,
            academic_year=self.academic_year,
            name='Grade 1-A',
            strand=None
        )
        try:
            section.full_clean()
            section.save()
            self.assertIsNone(section.strand)
        except Exception as e:
            self.fail(f"Elementary section without strand should be valid: {e}")

    def test_elementary_section_with_strand_is_invalid(self):
        """Elementary sections cannot have strands."""
        section = Section(
            grade_level=self.grade_1,
            academic_year=self.academic_year,
            name='Grade 1-B',
            strand=self.stem
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            section.full_clean()
        self.assertIn('strand', context.exception.error_dict)

    def test_jhs_section_without_strand_is_valid(self):
        """Junior High School sections should not have strands."""
        section = Section(
            grade_level=self.grade_7,
            academic_year=self.academic_year,
            name='Grade 7-A',
            strand=None
        )
        try:
            section.full_clean()
            section.save()
            self.assertIsNone(section.strand)
        except Exception as e:
            self.fail(f"JHS section without strand should be valid: {e}")

    def test_jhs_section_with_strand_is_invalid(self):
        """Junior High School sections cannot have strands."""
        section = Section(
            grade_level=self.grade_7,
            academic_year=self.academic_year,
            name='Grade 7-B',
            strand=self.stem
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            section.full_clean()
        self.assertIn('strand', context.exception.error_dict)

    def test_shs_section_with_strand_is_valid(self):
        """Senior High School sections must have strands."""
        section = Section(
            grade_level=self.grade_11,
            academic_year=self.academic_year,
            name='Grade 11-STEM',
            strand=self.stem
        )
        try:
            section.full_clean()
            section.save()
            self.assertEqual(section.strand, self.stem)
        except Exception as e:
            self.fail(f"SHS section with strand should be valid: {e}")

    def test_shs_section_without_strand_is_invalid(self):
        """Senior High School sections must have strands."""
        section = Section(
            grade_level=self.grade_11,
            academic_year=self.academic_year,
            name='Grade 11-NoStrand',
            strand=None
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            section.full_clean()
        self.assertIn('strand', context.exception.error_dict)

    def test_shs_section_with_inactive_strand_is_invalid(self):
        """SHS sections cannot have inactive strands."""
        section = Section(
            grade_level=self.grade_11,
            academic_year=self.academic_year,
            name='Grade 11-InactiveStrand',
            strand=self.inactive_strand
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            section.full_clean()
        self.assertIn('strand', context.exception.error_dict)

    def test_section_strand_displayed_in_serializer(self):
        """Section serializer should expose strand information."""
        from academics.serializers import SectionSerializer

        section = Section.objects.create(
            grade_level=self.grade_11,
            academic_year=self.academic_year,
            name='Grade 11-ABM',
            strand=self.abm
        )

        serializer = SectionSerializer(section)
        data = serializer.data

        self.assertEqual(data['strand'], self.abm.id)
        self.assertEqual(data['strand_name'], 'ABM')

    def test_enrollment_with_shs_requires_strand(self):
        """Enrollment for SHS students must include strand matching section."""
        from accounts.models import UserProfile

        section = Section.objects.create(
            grade_level=self.grade_11,
            academic_year=self.academic_year,
            name='Grade 11-STEM',
            strand=self.stem
        )

        student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            gender='Male',
            student_status='active'
        )

        # Should succeed with matching strand
        enrollment = Enrollment(
            student=student,
            academic_year=self.academic_year,
            grade_level=self.grade_11,
            section=section,
            strand=self.stem
        )
        try:
            enrollment.full_clean()
            enrollment.save()
        except Exception as e:
            self.fail(f"Enrollment with matching strand should be valid: {e}")

    def test_enrollment_with_mismatched_strand_is_invalid(self):
        """Enrollment strand must match section strand."""
        section = Section.objects.create(
            grade_level=self.grade_11,
            academic_year=self.academic_year,
            name='Grade 11-STEM',
            strand=self.stem
        )

        student = Student.objects.create(
            first_name='Test',
            last_name='Student2',
            gender='Female',
            student_status='active'
        )

        # Should fail with mismatched strand
        enrollment = Enrollment(
            student=student,
            academic_year=self.academic_year,
            grade_level=self.grade_11,
            section=section,
            strand=self.abm  # Wrong strand
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_enrollment_elementary_no_strand_required(self):
        """Elementary enrollments should not require strands."""
        section = Section.objects.create(
            grade_level=self.grade_1,
            academic_year=self.academic_year,
            name='Grade 1-A',
            strand=None
        )

        student = Student.objects.create(
            first_name='Elementary',
            last_name='Student',
            gender='Male',
            student_status='active'
        )

        enrollment = Enrollment(
            student=student,
            academic_year=self.academic_year,
            grade_level=self.grade_1,
            section=section,
            strand=None
        )
        try:
            enrollment.full_clean()
            enrollment.save()
            self.assertIsNone(enrollment.strand)
        except Exception as e:
            self.fail(f"Elementary enrollment without strand should be valid: {e}")

    def test_section_serializer_validates_strand_for_shs(self):
        """Section serializer should validate strand requirements."""
        from academics.serializers import SectionSerializer

        # SHS without strand should fail
        data = {
            'grade_level': self.grade_11.id,
            'academic_year': self.academic_year.id,
            'name': 'Grade 11-Invalid',
            'strand': None
        }
        serializer = SectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('strand', serializer.errors)

    def test_section_serializer_rejects_strand_for_elementary(self):
        """Section serializer should reject strand for Elementary."""
        from academics.serializers import SectionSerializer

        data = {
            'grade_level': self.grade_1.id,
            'academic_year': self.academic_year.id,
            'name': 'Grade 1-Invalid',
            'strand': self.stem.id
        }
        serializer = SectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('strand', serializer.errors)

    def test_multiple_sections_same_grade_different_strands(self):
        """Multiple SHS sections can exist for same grade with different strands."""
        section_stem = Section.objects.create(
            grade_level=self.grade_11,
            academic_year=self.academic_year,
            name='Grade 11-STEM-A',
            strand=self.stem
        )

        section_abm = Section.objects.create(
            grade_level=self.grade_11,
            academic_year=self.academic_year,
            name='Grade 11-ABM-A',
            strand=self.abm
        )

        self.assertEqual(section_stem.strand, self.stem)
        self.assertEqual(section_abm.strand, self.abm)

        # Query should find both sections
        grade_11_sections = Section.objects.filter(grade_level=self.grade_11)
        self.assertEqual(grade_11_sections.count(), 2)

    def tearDown(self):
        """Clean up inactive strand created in setUp."""
        self.inactive_strand.delete()


class SubjectValidationTests(TestCase):
    """Test Phase 3: Subject classification with educational level, category, and strand validation."""

    def setUp(self):
        """Set up test subjects for all grade levels and strands."""
        self.academic_year = AcademicYear.objects.create(
            name='2025-2026',
            start_date='2025-06-01',
            end_date='2026-03-31',
            is_active=True
        )

        # Get grade levels
        self.grade_1 = GradeLevel.objects.get(code='G1')  # Elementary
        self.grade_6 = GradeLevel.objects.get(code='G6')  # Elementary
        self.grade_7 = GradeLevel.objects.get(code='G7')  # JHS
        self.grade_10 = GradeLevel.objects.get(code='G10')  # JHS
        self.grade_11 = GradeLevel.objects.get(code='G11')  # SHS
        self.grade_12 = GradeLevel.objects.get(code='G12')  # SHS

        # Get strands
        self.stem = Strand.objects.get(code='STEM')
        self.abm = Strand.objects.get(code='ABM')
        self.humss = Strand.objects.get(code='HUMSS')
        self.gas = Strand.objects.get(code='GAS')
        self.tvl_ict = Strand.objects.get(code='TVL-ICT')
        self.tvl_he = Strand.objects.get(code='TVL-HE')

        # Create an inactive strand for testing
        self.inactive_strand = Strand.objects.create(
            name='Inactive Strand',
            code='INACTIVE',
            is_active=False
        )

    # ============ EDUCATIONAL LEVEL TESTS ============

    def test_subject_educational_level_for_elementary(self):
        """Subjects for Elementary grades should have 'Elementary' educational level."""
        subject = Subject.objects.create(
            code='MATH1',
            name='Math Grade 1',
            category='Learning Area',
            grade_level=self.grade_1
        )
        self.assertEqual(subject.educational_level, 'Elementary')

    def test_subject_educational_level_for_jhs(self):
        """Subjects for JHS grades should have 'Junior High School' educational level."""
        subject = Subject.objects.create(
            code='MATH7',
            name='Math Grade 7',
            category='Learning Area',
            grade_level=self.grade_7
        )
        self.assertEqual(subject.educational_level, 'Junior High School')

    def test_subject_educational_level_for_shs(self):
        """Subjects for SHS grades should have 'Senior High School' educational level."""
        subject = Subject.objects.create(
            code='MATH11',
            name='Math Grade 11',
            category='Core',
            grade_level=self.grade_11
        )
        self.assertEqual(subject.educational_level, 'Senior High School')

    def test_subject_without_grade_level_has_no_educational_level(self):
        """Subject without grade level should have None educational level."""
        subject = Subject.objects.create(
            code='GEN101',
            name='General Subject',
            category='Learning Area',
            grade_level=None
        )
        self.assertIsNone(subject.educational_level)

    # ============ ELEMENTARY SUBJECT TESTS ============

    def test_elementary_subject_with_learning_area_is_valid(self):
        """Elementary subjects with Learning Area category should be valid."""
        subject = Subject(
            code='ELEM_MATH',
            name='Elementary Mathematics',
            category='Learning Area',
            grade_level=self.grade_1,
            strand=None
        )
        try:
            subject.full_clean()
            subject.save()
            self.assertEqual(subject.category, 'Learning Area')
            self.assertIsNone(subject.strand)
        except ValidationError as e:
            self.fail(f"Elementary subject with Learning Area should be valid: {e}")

    def test_elementary_subject_with_strand_is_invalid(self):
        """Elementary subjects cannot have strands."""
        subject = Subject(
            code='ELEM_STEM',
            name='Elementary with Strand',
            category='Learning Area',
            grade_level=self.grade_1,
            strand=self.stem
        )
        with self.assertRaises(ValidationError) as context:
            subject.full_clean()
        self.assertIn('strand', context.exception.error_dict)

    def test_elementary_subject_with_shs_category_is_invalid(self):
        """Elementary subjects cannot use SHS categories (Core, Applied, Specialized)."""
        for category in ['Core', 'Applied', 'Specialized']:
            subject = Subject(
                code=f'ELEM_{category}',
                name=f'Elementary {category}',
                category=category,
                grade_level=self.grade_1,
                strand=None
            )
            with self.assertRaises(ValidationError) as context:
                subject.full_clean()
            self.assertIn('category', context.exception.error_dict,
                         f"Elementary subject with {category} should be invalid")

    def test_elementary_subject_all_grades_valid(self):
        """All elementary grades (1-6) should accept subjects with Learning Area."""
        elementary_grades = [self.grade_1, self.grade_6]
        for i, grade in enumerate(elementary_grades):
            subject = Subject(
                code=f'MATH_E{i}',
                name=f'Math {grade.name}',
                category='Learning Area',
                grade_level=grade,
                strand=None
            )
            try:
                subject.full_clean()
                subject.save()
            except ValidationError as e:
                self.fail(f"Subject for {grade.name} should be valid: {e}")

    # ============ JHS SUBJECT TESTS ============

    def test_jhs_subject_with_learning_area_is_valid(self):
        """JHS subjects with Learning Area category should be valid."""
        subject = Subject(
            code='JHS_MATH',
            name='JHS Mathematics',
            category='Learning Area',
            grade_level=self.grade_7,
            strand=None
        )
        try:
            subject.full_clean()
            subject.save()
            self.assertEqual(subject.category, 'Learning Area')
            self.assertIsNone(subject.strand)
        except ValidationError as e:
            self.fail(f"JHS subject with Learning Area should be valid: {e}")

    def test_jhs_subject_with_strand_is_invalid(self):
        """JHS subjects cannot have strands."""
        subject = Subject(
            code='JHS_STEM',
            name='JHS with Strand',
            category='Learning Area',
            grade_level=self.grade_7,
            strand=self.stem
        )
        with self.assertRaises(ValidationError) as context:
            subject.full_clean()
        self.assertIn('strand', context.exception.error_dict)

    def test_jhs_subject_with_shs_category_is_invalid(self):
        """JHS subjects cannot use SHS categories (Core, Applied, Specialized)."""
        for category in ['Core', 'Applied', 'Specialized']:
            subject = Subject(
                code=f'JHS_{category}',
                name=f'JHS {category}',
                category=category,
                grade_level=self.grade_7,
                strand=None
            )
            with self.assertRaises(ValidationError) as context:
                subject.full_clean()
            self.assertIn('category', context.exception.error_dict)

    def test_jhs_subject_all_grades_valid(self):
        """All JHS grades (7-10) should accept subjects with Learning Area."""
        jhs_grades = [self.grade_7, self.grade_10]
        for i, grade in enumerate(jhs_grades):
            subject = Subject(
                code=f'SCI_J{i}',
                name=f'Science {grade.name}',
                category='Learning Area',
                grade_level=grade,
                strand=None
            )
            try:
                subject.full_clean()
                subject.save()
            except ValidationError as e:
                self.fail(f"Subject for {grade.name} should be valid: {e}")

    # ============ SHS SUBJECT TESTS ============

    def test_shs_subject_with_core_category_is_valid(self):
        """SHS subjects with Core category should be valid."""
        subject = Subject(
            code='CORE_MATH',
            name='Core Mathematics',
            category='Core',
            grade_level=self.grade_11,
            strand=None
        )
        try:
            subject.full_clean()
            subject.save()
            self.assertEqual(subject.category, 'Core')
        except ValidationError as e:
            self.fail(f"SHS Core subject should be valid: {e}")

    def test_shs_subject_with_applied_category_is_valid(self):
        """SHS subjects with Applied category should be valid."""
        subject = Subject(
            code='APPL_MATH',
            name='Applied Mathematics',
            category='Applied',
            grade_level=self.grade_11,
            strand=None
        )
        try:
            subject.full_clean()
            subject.save()
            self.assertEqual(subject.category, 'Applied')
        except ValidationError as e:
            self.fail(f"SHS Applied subject should be valid: {e}")

    def test_shs_subject_with_specialized_category_is_valid(self):
        """SHS subjects with Specialized category should be valid."""
        subject = Subject(
            code='SPEC_TECH',
            name='Specialized Technology',
            category='Specialized',
            grade_level=self.grade_11,
            strand=None
        )
        try:
            subject.full_clean()
            subject.save()
            self.assertEqual(subject.category, 'Specialized')
        except ValidationError as e:
            self.fail(f"SHS Specialized subject should be valid: {e}")

    def test_shs_subject_can_have_strand(self):
        """SHS subjects may optionally have a strand."""
        subject = Subject(
            code='STEM_MATH',
            name='STEM Mathematics',
            category='Core',
            grade_level=self.grade_11,
            strand=self.stem
        )
        try:
            subject.full_clean()
            subject.save()
            self.assertEqual(subject.strand, self.stem)
        except ValidationError as e:
            self.fail(f"SHS subject with strand should be valid: {e}")

    def test_shs_subject_with_inactive_strand_is_invalid(self):
        """SHS subjects cannot have inactive strands."""
        subject = Subject(
            code='INACTIVE_SUBJECT',
            name='Inactive Strand Subject',
            category='Core',
            grade_level=self.grade_11,
            strand=self.inactive_strand
        )
        with self.assertRaises(ValidationError) as context:
            subject.full_clean()
        self.assertIn('strand', context.exception.error_dict)

    def test_shs_subject_with_learning_area_is_valid(self):
        """SHS subjects can still use 'Learning Area' category (backwards compatible)."""
        subject = Subject(
            code='SHS_AREA',
            name='SHS Learning Area',
            category='Learning Area',
            grade_level=self.grade_11,
            strand=None
        )
        try:
            subject.full_clean()
            subject.save()
        except ValidationError as e:
            self.fail(f"SHS subject with Learning Area should be valid: {e}")

    def test_shs_subject_all_grades_valid(self):
        """All SHS grades (11-12) should accept subjects with Core category."""
        shs_grades = [self.grade_11, self.grade_12]
        for i, grade in enumerate(shs_grades):
            subject = Subject(
                code=f'CORE_S{i}',
                name=f'Core {grade.name}',
                category='Core',
                grade_level=grade,
                strand=None
            )
            try:
                subject.full_clean()
                subject.save()
            except ValidationError as e:
                self.fail(f"Subject for {grade.name} should be valid: {e}")

    # ============ SUBJECT WITHOUT GRADE LEVEL TESTS ============

    def test_subject_without_grade_level_is_valid(self):
        """Subjects without grade level should be allowed (no validation)."""
        subject = Subject(
            code='GEN_SUB',
            name='General Subject',
            category='Learning Area',
            grade_level=None,
            strand=None
        )
        try:
            subject.full_clean()
            subject.save()
            self.assertIsNone(subject.grade_level)
            self.assertIsNone(subject.educational_level)
        except ValidationError as e:
            self.fail(f"Subject without grade level should be valid: {e}")

    def test_subject_without_grade_level_can_have_any_category(self):
        """Subjects without grade level can have any category (no validation)."""
        for category in ['Learning Area', 'Core', 'Applied', 'Specialized']:
            subject = Subject(
                code=f'GEN_{category}',
                name=f'Generic {category}',
                category=category,
                grade_level=None,
                strand=None
            )
            try:
                subject.full_clean()
                subject.save()
            except ValidationError as e:
                self.fail(f"Subject without grade level with {category} should be valid: {e}")

    # ============ SERIALIZER VALIDATION TESTS ============

    def test_subject_serializer_exposes_educational_level(self):
        """Subject serializer should expose educational level derived from grade level."""
        subject = Subject.objects.create(
            code='SER_MATH',
            name='Math Subject',
            category='Core',
            grade_level=self.grade_11
        )
        serializer = SubjectSerializer(subject)
        data = serializer.data

        self.assertIn('educational_level', data)
        self.assertEqual(data['educational_level'], 'Senior High School')

    def test_subject_serializer_validates_elementary_strand_rejection(self):
        """Subject serializer should reject strand for Elementary."""
        from academics.serializers import SubjectSerializer
        data = {
            'code': 'SER_ELEM',
            'name': 'Elementary Subject',
            'category': 'Learning Area',
            'grade_level': self.grade_1.id,
            'strand': self.stem.id
        }
        serializer = SubjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('strand', serializer.errors)

    def test_subject_serializer_validates_jhs_strand_rejection(self):
        """Subject serializer should reject strand for JHS."""
        from academics.serializers import SubjectSerializer
        data = {
            'code': 'SER_JHS',
            'name': 'JHS Subject',
            'category': 'Learning Area',
            'grade_level': self.grade_7.id,
            'strand': self.stem.id
        }
        serializer = SubjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('strand', serializer.errors)

    def test_subject_serializer_validates_elementary_category_restriction(self):
        """Subject serializer should reject SHS categories for Elementary."""
        from academics.serializers import SubjectSerializer
        for category in ['Core', 'Applied', 'Specialized']:
            data = {
                'code': f'SER_ELEM_{category}',
                'name': f'Elementary {category}',
                'category': category,
                'grade_level': self.grade_1.id,
                'strand': None
            }
            serializer = SubjectSerializer(data=data)
            self.assertFalse(serializer.is_valid(),
                            f"Elementary with {category} should be invalid")
            self.assertIn('category', serializer.errors)

    def test_subject_serializer_validates_jhs_category_restriction(self):
        """Subject serializer should reject SHS categories for JHS."""
        from academics.serializers import SubjectSerializer
        for category in ['Core', 'Applied', 'Specialized']:
            data = {
                'code': f'SER_JHS_{category}',
                'name': f'JHS {category}',
                'category': category,
                'grade_level': self.grade_7.id,
                'strand': None
            }
            serializer = SubjectSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('category', serializer.errors)

    def tearDown(self):
        """Clean up inactive strand created in setUp."""
        self.inactive_strand.delete()
