from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('attendance', '0012_schoolcalendarday_approval_notes_and_more'),
    ]
    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('APPROVAL_PENDING', 'Pending approval'), ('CALENDAR_EVENT', 'Calendar event'), ('EXAMINATION', 'Examination'), ('ENROLLMENT_DEADLINE', 'Enrollment deadline'), ('ACADEMIC_DEADLINE', 'Academic deadline'), ('SUSPENSION', 'Suspension or event')], max_length=30)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('scheduled_for', models.DateTimeField()),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('idempotency_key', models.CharField(max_length=180, unique=True)),
                ('calendar_entry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='attendance.schoolcalendarday')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('recurring_event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='attendance.recurringschoolcalendarevent')),
            ],
            options={'ordering': ['read_at', '-scheduled_for', '-created_at']},
        ),
        migrations.AddIndex(model_name='notification', index=models.Index(fields=['recipient', 'read_at'], name='notificatio_recipie_564b1f_idx')),
        migrations.AddIndex(model_name='notification', index=models.Index(fields=['scheduled_for'], name='notificatio_schedul_cf7340_idx')),
    ]