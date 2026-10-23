from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0010_section_specialization'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='subject_type',
            field=models.CharField(
                choices=[('STANDARD', 'Standard curriculum'), ('SCHOOL_SPECIFIC', 'School-specific')],
                default='STANDARD',
                max_length=20,
            ),
        ),
    ]
