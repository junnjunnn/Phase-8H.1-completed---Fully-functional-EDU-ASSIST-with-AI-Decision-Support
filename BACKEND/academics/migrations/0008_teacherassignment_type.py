from django.db import migrations, models


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
        migrations.AlterField(
            model_name='teacherassignment',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='teacher_assignments', to='academics.subject'),
        ),
        migrations.AddConstraint(
            model_name='teacherassignment',
            constraint=models.UniqueConstraint(fields=('teacher', 'academic_year', 'grade_level', 'section', 'subject'), name='unique_active_subject_teacher_assignment'),
        ),
        migrations.AddConstraint(
            model_name='teacherassignment',
            constraint=models.UniqueConstraint(fields=('academic_year', 'section', 'assignment_type'), name='unique_active_section_adviser_assignment'),
        ),
    ]