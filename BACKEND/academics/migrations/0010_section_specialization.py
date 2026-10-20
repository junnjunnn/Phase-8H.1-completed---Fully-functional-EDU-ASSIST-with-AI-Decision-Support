from django.db import migrations, models
import django.db.models.deletion


def create_required_shs_reference_data(apps, schema_editor):
    Strand = apps.get_model('academics', 'Strand')
    Specialization = apps.get_model('academics', 'Specialization')

    tvl, _ = Strand.objects.get_or_create(
        name='TVL',
        defaults={
            'code': 'TVL',
            'description': 'Technical-Vocational-Livelihood',
            'is_active': True,
        },
    )
    Specialization.objects.get_or_create(
        strand=tvl,
        name='Caregiving',
        defaults={'code': 'CAREGIVING', 'is_active': True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0009_remove_teacherassignment_academics_t_teacher_3f2cd1_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Specialization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('strand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='specializations', to='academics.strand')),
            ],
            options={
                'ordering': ['name'],
                'indexes': [models.Index(fields=['strand', 'is_active'], name='academics_s_strand__e6c3ef_idx')],
                'constraints': [models.UniqueConstraint(fields=('strand', 'name'), name='unique_specialization_per_strand')],
            },
        ),
        migrations.AddField(
            model_name='section',
            name='specialization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sections', to='academics.specialization'),
        ),
        migrations.RunPython(create_required_shs_reference_data, migrations.RunPython.noop),
    ]