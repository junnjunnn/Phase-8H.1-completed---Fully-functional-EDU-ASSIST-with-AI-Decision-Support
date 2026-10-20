from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0002_alter_auditlog_action'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('CREATE', 'CREATE'),
                    ('UPDATE', 'UPDATE'),
                    ('DELETE', 'DELETE'),
                    ('LOGIN_SUCCESS', 'LOGIN_SUCCESS'),
                    ('LOGIN_FAILED', 'LOGIN_FAILED'),
                    ('LOGOUT', 'LOGOUT'),
                    ('ACCOUNT_ACTIVATED', 'ACCOUNT_ACTIVATED'),
                    ('ACCOUNT_DEACTIVATED', 'ACCOUNT_DEACTIVATED'),
                    ('PASSWORD_CHANGED', 'PASSWORD_CHANGED'),
                    ('USER_CREATED', 'USER_CREATED'),
                    ('VIEW_SENSITIVE_RECORD', 'VIEW_SENSITIVE_RECORD'),
                    ('EXPORT_REPORT', 'EXPORT_REPORT'),
                    ('PREDICTION_GENERATED', 'PREDICTION_GENERATED'),
                    ('INTERVENTION_CREATED', 'INTERVENTION_CREATED'),
                    ('SUBMITTED_FOR_APPROVAL', 'SUBMITTED_FOR_APPROVAL'),
                    ('APPROVED', 'APPROVED'),
                    ('REJECTED', 'REJECTED'),
                    ('REAPPROVAL_REQUIRED', 'REAPPROVAL_REQUIRED'),
                    ('PUBLISHED', 'PUBLISHED'),
                    ('CANCELLED', 'CANCELLED'),
                ],
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='details',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='new_status',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='object_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='object_name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='previous_status',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='reason',
            field=models.TextField(blank=True, default=''),
        ),
    ]
