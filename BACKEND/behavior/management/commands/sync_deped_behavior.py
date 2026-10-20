from django.core.management.base import BaseCommand
from django.db import transaction

from behavior.models import BehavioralRating, BehaviorIndicator, CoreValue
from behavior.reference_data import (
    DEPED_CORE_VALUES,
    DEPED_RATINGS,
    canonicalize_core_value_name,
    canonicalize_indicator_name,
)

LEGACY_CORE_VALUE_ALIASES = {
    'Maka-Diyos': ['Maka-Diyos (Love for God)'],
    'Makatao': ['Makatao (Love for Fellowmen)'],
    'Makakalikasan': ['Maka-Kalikasan (Love for Nature)', 'Makakalikasan (Love for Nature)'],
    'Makabansa': ['Makabansa (Love for Country)'],
}


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

        # Preserve historical rows while standardizing the canonical names used for new records.
        legacy_names = list(CoreValue.objects.values_list('name', flat=True).distinct())
        for legacy_name in legacy_names:
            canonical_name = canonicalize_core_value_name(legacy_name)
            if canonical_name and canonical_name != legacy_name:
                CoreValue.objects.filter(name=legacy_name).update(name=canonical_name)

        # Keep legacy aliases visible in the data model without letting them remain the active contract.
        for canonical_name, aliases in LEGACY_CORE_VALUE_ALIASES.items():
            for alias in aliases:
                CoreValue.objects.filter(name=alias).update(name=canonical_name)

        source_core_value_names = {item['name'] for item in DEPED_CORE_VALUES}
        CoreValue.objects.filter(name__in=source_core_value_names).update(is_active=True)
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

            canonical_indicator_names = {canonicalize_indicator_name(name) for name in core_value_data['indicators']}
            all_indicators = list(BehaviorIndicator.objects.filter(core_value=core_value).order_by('id'))
            for indicator in all_indicators:
                canonical_name = canonicalize_indicator_name(indicator.name)
                if canonical_name in canonical_indicator_names:
                    indicator.name = canonical_name
                    indicator.description = ''
                    indicator.is_active = True
                    indicator.save(update_fields=['name', 'description', 'is_active'])
                else:
                    indicator.is_active = False
                    indicator.save(update_fields=['is_active'])

            for canonical_indicator_name in sorted(canonical_indicator_names):
                BehaviorIndicator.objects.update_or_create(
                    core_value=core_value,
                    name=canonical_indicator_name,
                    defaults={'description': '', 'is_active': True},
                )

            # Ensure no canonical indicator remains hidden after the sync.
            BehaviorIndicator.objects.filter(core_value=core_value, name__in=sorted(canonical_indicator_names)).update(is_active=True)

        self.stdout.write(self.style.SUCCESS('DepEd behavior references synchronized.'))
