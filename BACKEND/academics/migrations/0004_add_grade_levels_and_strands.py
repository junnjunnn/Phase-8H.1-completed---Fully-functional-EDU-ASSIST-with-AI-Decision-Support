# Generated data migration for Phase 1: Academic Master Data

from django.db import migrations


def create_grade_levels_and_strands(apps, schema_editor):
    """
    Create complete academic master data:
    - All 12 expected grade levels (Elementary 1-6, JHS 7-10, SHS 11-12)
    - All 6 standard SHS strands (STEM, ABM, HUMSS, GAS, TVL-ICT, TVL-HE)

    This function is idempotent: safe to run multiple times without creating duplicates.
    """
    GradeLevel = apps.get_model('academics', 'GradeLevel')
    Strand = apps.get_model('academics', 'Strand')

    # Grade level data: (name, code, school_level, order)
    grade_levels_data = [
        # Elementary (1-6)
        ('Grade 1', 'G1', 'Elementary', 1),
        ('Grade 2', 'G2', 'Elementary', 2),
        ('Grade 3', 'G3', 'Elementary', 3),
        ('Grade 4', 'G4', 'Elementary', 4),
        ('Grade 5', 'G5', 'Elementary', 5),
        ('Grade 6', 'G6', 'Elementary', 6),
        # Junior High School (7-10)
        ('Grade 7', 'G7', 'Junior High School', 7),
        ('Grade 8', 'G8', 'Junior High School', 8),
        ('Grade 9', 'G9', 'Junior High School', 9),
        ('Grade 10', 'G10', 'Junior High School', 10),
        # Senior High School (11-12)
        ('Grade 11', 'G11', 'Senior High School', 11),
        ('Grade 12', 'G12', 'Senior High School', 12),
    ]

    # Create or update grade levels (using code as unique identifier)
    for name, code, school_level, order in grade_levels_data:
        grade, created = GradeLevel.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'school_level': school_level,
                'order': order,
                'is_active': True,
            }
        )
        # Update existing records if they have wrong school_level or order
        if not created and (grade.school_level != school_level or grade.order != order or grade.name != name):
            grade.name = name
            grade.school_level = school_level
            grade.order = order
            grade.save(update_fields=['name', 'school_level', 'order'])

    # Strand data (SHS only): (name, code, description)
    strands_data = [
        ('STEM', 'STEM', 'Science, Technology, Engineering, Mathematics'),
        ('ABM', 'ABM', 'Accountancy, Business, Management'),
        ('HUMSS', 'HUMSS', 'Humanities and Social Sciences'),
        ('GAS', 'GAS', 'General Academic Strand'),
        ('TVL-ICT', 'TVL-ICT', 'Technical-Vocational-Livelihood - Information and Communications Technology'),
        ('TVL-HE', 'TVL-HE', 'Technical-Vocational-Livelihood - Home Economics'),
    ]

    # Create strands (using code as unique identifier)
    for name, code, description in strands_data:
        strand, created = Strand.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'is_active': True,
            }
        )
        # Update existing records if they have wrong name or description
        if not created and (strand.name != name or strand.description != description):
            strand.name = name
            strand.description = description
            strand.save(update_fields=['name', 'description'])


def reverse_grade_levels_and_strands(apps, schema_editor):
    """
    Reverse function: Delete only the newly created grade levels and strands.
    Preserve any existing data that was already in the database.
    """
    GradeLevel = apps.get_model('academics', 'GradeLevel')
    Strand = apps.get_model('academics', 'Strand')

    # Delete the specific grade levels and strands created by this migration
    grade_codes = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12']
    GradeLevel.objects.filter(code__in=grade_codes).delete()

    strand_codes = ['STEM', 'ABM', 'HUMSS', 'GAS', 'TVL-ICT', 'TVL-HE']
    Strand.objects.filter(code__in=strand_codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0003_subject_description_teacherassignment'),
    ]

    operations = [
        migrations.RunPython(create_grade_levels_and_strands, reverse_grade_levels_and_strands),
    ]
