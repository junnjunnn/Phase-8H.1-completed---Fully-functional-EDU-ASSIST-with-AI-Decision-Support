from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0011_subject_subject_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='official_subject_code',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
