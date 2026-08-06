from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('behavior', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='behavioralrating',
            name='numeric_value',
            field=models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='behavioralassessment',
            name='numeric_score',
            field=models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=2),
        ),
    ]
