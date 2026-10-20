from django.db import migrations, models


def set_assignment_types(apps, schema_editor):
    TeacherAssignment = apps.get_model('academics', 'TeacherAssignment')
    Section = apps.get_model('academics', 'Section')
    for assignment in TeacherAssignment.objects.select_related('section').all():
        section = assignment.section
        assignment.assignment_type = 'ADVISER' if section and section.adviser_id == assignment.teacher_id else 'SUBJECT'
        assignment.save(update_fields=['assignment_type'])


def normalize_active_adviser_assignments(apps, schema_editor):
    TeacherAssignment = apps.get_model('academics', 'TeacherAssignment')
    seen = set()
    for assignment in TeacherAssignment.objects.filter(is_active=True, assignment_type='ADVISER').order_by('academic_year_id', 'section_id', '-updated_at', '-created_at', '-id'):
        key = (assignment.academic_year_id, assignment.section_id)
        if key in seen:
            assignment.is_active = False
            assignment.save(update_fields=['is_active'])
        else:
            seen.add(key)


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0007_subject_grade_levels'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacherassignment',
            name='assignment_type',
            field=models.CharField(choices=[('SUBJECT', 'Subject Teacher'), ('ADVISER', 'Class Adviser')], default='SUBJECT', max_length=20),
        ),
        migrations.RunPython(set_assignment_types, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(normalize_active_adviser_assignments, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='teacherassignment',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='teacher_assignments', to='academics.subject'),
        ),
        migrations.AddConstraint(
            model_name='teacherassignment',
            constraint=models.UniqueConstraint(fields=('teacher', 'academic_year', 'grade_level', 'section', 'subject'), condition=models.Q(is_active=True), name='unique_active_subject_teacher_assignment'),
        ),
        migrations.AddConstraint(
            model_name='teacherassignment',
            constraint=models.UniqueConstraint(fields=('academic_year', 'section'), condition=models.Q(is_active=True, assignment_type='ADVISER'), name='unique_active_section_adviser_assignment'),
        ),
    ]