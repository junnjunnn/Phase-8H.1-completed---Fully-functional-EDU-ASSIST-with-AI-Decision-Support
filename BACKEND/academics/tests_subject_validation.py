"""
Subject Validation Tests - Phase 3
Tests for Subject academic level classification, category validation, and strand rules
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Subject, Strand
from academics.serializers import SubjectSerializer


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
            strand=None  # Core subjects often don't require strand
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
        """SHS subjects can still use 'Learning Area' category (for backwards compatibility)."""
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

    def test_subject_serializer_allows_all_categories_for_shs(self):
        """Subject serializer should accept all categories for SHS."""
        for category in ['Learning Area', 'Core', 'Applied', 'Specialized']:
            data = {
                'code': f'SER_SHS_{category}',
                'name': f'SHS {category}',
                'category': category,
                'grade_level': self.grade_11.id,
                'strand': None
            }
            serializer = SubjectSerializer(data=data)
            self.assertTrue(serializer.is_valid(),
                           f"SHS with {category} should be valid: {serializer.errors}")

    def test_subject_serializer_exposes_grade_level_info(self):
        """Subject serializer should expose grade level name and school level."""
        subject = Subject.objects.create(
            code='SER_INFO',
            name='Info Subject',
            category='Learning Area',
            grade_level=self.grade_7
        )
        serializer = SubjectSerializer(subject)
        data = serializer.data

        self.assertIn('grade_level_name', data)
        self.assertEqual(data['grade_level_name'], 'Grade 7')
        self.assertIn('grade_level_school_level', data)
        self.assertEqual(data['grade_level_school_level'], 'Junior High School')

    def test_subject_serializer_exposes_strand_info(self):
        """Subject serializer should expose strand name."""
        subject = Subject.objects.create(
            code='SER_STRAND',
            name='Strand Subject',
            category='Core',
            grade_level=self.grade_11,
            strand=self.stem
        )
        serializer = SubjectSerializer(subject)
        data = serializer.data

        self.assertIn('strand_name', data)
        self.assertEqual(data['strand_name'], 'STEM')

    # ============ API INTEGRATION TESTS ============

    def test_create_elementary_subject_via_api(self):
        """Create Elementary subject via API should be valid."""
        client = APIClient()
        user = get_user_model().objects.create_user(username='admin_test', password='AdminPass1!')
        UserProfile.objects.create(user=user, role_name='SCHOOL_ADMIN')
        client.force_authenticate(user=user)

        response = client.post('/api/subjects/', {
            'code': 'API_ELEM_MATH',
            'name': 'API Elementary Math',
            'category': 'Learning Area',
            'grade_level': self.grade_1.id,
            'is_active': True
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['code'], 'API_ELEM_MATH')
        self.assertEqual(response.data['educational_level'], 'Elementary')

    def test_create_shs_core_subject_via_api(self):
        """Create SHS Core subject via API should be valid."""
        client = APIClient()
        user = get_user_model().objects.create_user(username='admin_test2', password='AdminPass2!')
        UserProfile.objects.create(user=user, role_name='SCHOOL_ADMIN')
        client.force_authenticate(user=user)

        response = client.post('/api/subjects/', {
            'code': 'API_SHS_CORE',
            'name': 'API SHS Core Subject',
            'category': 'Core',
            'grade_level': self.grade_11.id,
            'is_active': True
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['category'], 'Core')
        self.assertEqual(response.data['educational_level'], 'Senior High School')

    def test_create_shs_strand_subject_via_api(self):
        """Create SHS subject with strand via API should be valid."""
        client = APIClient()
        user = get_user_model().objects.create_user(username='admin_test3', password='AdminPass3!')
        UserProfile.objects.create(user=user, role_name='SCHOOL_ADMIN')
        client.force_authenticate(user=user)

        response = client.post('/api/subjects/', {
            'code': 'API_SHS_STRAND',
            'name': 'API SHS Strand Subject',
            'category': 'Specialized',
            'grade_level': self.grade_11.id,
            'strand': self.stem.id,
            'is_active': True
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['strand_name'], 'STEM')

    def test_invalid_elementary_with_strand_rejected_by_api(self):
        """API should reject Elementary subject with strand."""
        client = APIClient()
        user = get_user_model().objects.create_user(username='admin_test4', password='AdminPass4!')
        UserProfile.objects.create(user=user, role_name='SCHOOL_ADMIN')
        client.force_authenticate(user=user)

        response = client.post('/api/subjects/', {
            'code': 'API_INVALID_ELEM',
            'name': 'Invalid Elementary',
            'category': 'Learning Area',
            'grade_level': self.grade_1.id,
            'strand': self.stem.id,
            'is_active': True
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('strand', str(response.data))

    def test_invalid_jhs_with_core_category_rejected_by_api(self):
        """API should reject JHS subject with Core category."""
        client = APIClient()
        user = get_user_model().objects.create_user(username='admin_test5', password='AdminPass5!')
        UserProfile.objects.create(user=user, role_name='SCHOOL_ADMIN')
        client.force_authenticate(user=user)

        response = client.post('/api/subjects/', {
            'code': 'API_INVALID_JHS',
            'name': 'Invalid JHS',
            'category': 'Core',
            'grade_level': self.grade_7.id,
            'is_active': True
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('category', str(response.data))

    def tearDown(self):
        """Clean up inactive strand created in setUp."""
        self.inactive_strand.delete()
