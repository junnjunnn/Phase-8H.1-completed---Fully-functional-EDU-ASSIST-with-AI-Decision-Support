from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0012_schoolcalendarday_approval_notes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='excused_absences',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
