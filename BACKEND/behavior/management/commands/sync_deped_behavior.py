from django.core.management.base import BaseCommand
from django.db import transaction

from behavior.models import BehavioralRating, BehaviorIndicator, CoreValue
from behavior.reference_data import DEPED_CORE_VALUES, DEPED_RATINGS


class Command(BaseCommand):
    help = 'Synchronize active behavior references with the DepEd observed-values structure.'

    @transaction.atomic
    def handle(self, *args, **options):
        for rating_data in DEPED_RATINGS:
            BehavioralRating.objects.update_or_create(
                code=rating_data['code'],
                defaults={
                    'label': rating_data['label'],
                    'description': rating_data['description'],
                    'numeric_value': None,
                    'is_active': True,
                },
            )
            BehavioralRating.objects.exclude(code__in={item['code'] for item in DEPED_RATINGS}).update(is_active=False)

        source_core_value_names = {item['name'] for item in DEPED_CORE_VALUES}
        CoreValue.objects.exclude(name__in=source_core_value_names).update(is_active=False)
        BehaviorIndicator.objects.exclude(core_value__name__in=source_core_value_names).update(is_active=False)

        for core_value_data in DEPED_CORE_VALUES:
            core_value, _ = CoreValue.objects.update_or_create(
                name=core_value_data['name'],
                defaults={
                    'description': core_value_data['description'],
                    'is_active': True,
                },
            )
            BehaviorIndicator.objects.filter(core_value=core_value).exclude(
                name__in=core_value_data['indicators']
            ).update(is_active=False)
            for indicator_name in core_value_data['indicators']:
                BehaviorIndicator.objects.update_or_create(
                    core_value=core_value,
                    name=indicator_name,
                    defaults={
                        'description': '',
                        'is_active': True,
                    },
                )

        self.stdout.write(self.style.SUCCESS('DepEd behavior references synchronized.'))
