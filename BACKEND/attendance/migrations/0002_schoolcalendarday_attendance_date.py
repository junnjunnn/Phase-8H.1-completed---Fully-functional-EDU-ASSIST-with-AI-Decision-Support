import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
        ('academics', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolCalendarDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('calendar_date', models.DateField()),
                ('day_type', models.CharField(choices=[('SCHOOL_DAY', 'School Day'), ('WEEKEND', 'Weekend'), ('HOLIDAY', 'Holiday'), ('SUSPENSION', 'Suspension'), ('SPECIAL_NON_CLASS_DAY', 'Special Non-Class Day')], default='SCHOOL_DAY', max_length=30)),
                ('title', models.CharField(max_length=150)),
                ('remarks', models.TextField(blank=True, default='')),
                ('attendance_expected', models.BooleanField(default=True)),
                ('classes_suspended', models.BooleanField(default=False)),
                ('scope_type', models.CharField(choices=[('SCHOOL_WIDE', 'School-wide'), ('SECTION_SPECIFIC', 'Section-specific')], default='SCHOOL_WIDE', max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academic_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='school_calendar_days', to='academics.academicyear')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='school_calendar_days', to=settings.AUTH_USER_MODEL)),
                ('section', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='school_calendar_days', to='academics.section')),
            ],
            options={
                'ordering': ['calendar_date'],
                'indexes': [models.Index(fields=['academic_year', 'calendar_date'], name='attendance_scho_academic_5125b0_idx'), models.Index(fields=['attendance_expected', 'calendar_date'], name='attendance_scho_attend_5e27fe_idx'), models.Index(fields=['day_type', 'calendar_date'], name='attendance_scho_day_typ_5a2d02_idx')],
                'unique_together': {('academic_year', 'calendar_date')},
            },
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='attendance_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='attendancerecord',
            index=models.Index(fields=['enrollment', 'attendance_date'], name='attendance_att_enrollm_4f6f7a_idx'),
        ),
    ]
