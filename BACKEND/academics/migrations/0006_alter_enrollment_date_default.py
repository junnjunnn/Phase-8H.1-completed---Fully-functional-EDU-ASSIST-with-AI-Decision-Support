# Generated migration for the enrollment date default fix.

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0005_add_section_strand'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enrollment',
            name='enrollment_date',
            field=models.DateField(default=timezone.localdate),
        ),
    ]
