# Generated schema migration for Phase 2: Add Strand to Section

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0004_add_grade_levels_and_strands'),
    ]

    operations = [
        migrations.AddField(
            model_name='section',
            name='strand',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sections', to='academics.strand'),
        ),
        migrations.AlterUniqueTogether(
            name='section',
            unique_together={('grade_level', 'academic_year', 'name')},
        ),
    ]
