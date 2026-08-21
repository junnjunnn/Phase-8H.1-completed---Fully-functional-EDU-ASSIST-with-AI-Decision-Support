from django.db import migrations, models
import django.db.models.deletion


def copy_primary_grade_to_applicability(apps, schema_editor):
    Subject = apps.get_model('academics', 'Subject')
    for subject in Subject.objects.exclude(grade_level__isnull=True).iterator():
        subject.grade_levels.add(subject.grade_level_id)


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0006_alter_enrollment_date_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='grade_levels',
            field=models.ManyToManyField(blank=True, related_name='applicable_subjects', to='academics.gradelevel'),
        ),
        migrations.RunPython(copy_primary_grade_to_applicability, migrations.RunPython.noop),
    ]
