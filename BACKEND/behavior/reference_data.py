import re

DEPED_RATINGS = [
    {
        'code': 'AO',
        'label': 'Always Observed',
        'description': 'Behavior is always observed.',
    },
    {
        'code': 'SO',
        'label': 'Sometimes Observed',
        'description': 'Behavior is sometimes observed.',
    },
    {
        'code': 'RO',
        'label': 'Rarely Observed',
        'description': 'Behavior is rarely observed.',
    },
    {
        'code': 'NO',
        'label': 'Not Observed',
        'description': 'Behavior is not observed.',
    },
]

LEGACY_CORE_VALUE_ALIASES = {
    'Maka-Diyos (Love for God)': 'Maka-Diyos',
    'Maka-Diyos': 'Maka-Diyos',
    'Makatao (Love for Fellowmen)': 'Makatao',
    'Makatao': 'Makatao',
    'Maka-Kalikasan (Love for Nature)': 'Makakalikasan',
    'Maka-Kalikasan': 'Makakalikasan',
    'Makakalikasan (Love for Nature)': 'Makakalikasan',
    'Makakalikasan': 'Makakalikasan',
    'Makabansa (Love for Country)': 'Makabansa',
    'Makabansa': 'Makabansa',
}

CORE_VALUE_CANONICAL_INDICATORS = {
    'Maka-Diyos': [
        'Expresses one\'s spiritual beliefs while respecting the spiritual beliefs of others',
        'Shows adherence to ethical principles by upholding truth',
    ],
    'Makatao': [
        'Is sensitive to individual, social, and cultural differences',
        'Demonstrate contributions toward solidarity',
    ],
    'Makakalikasan': [
        'Cares for the environment and utilizes resources wisely, judiciously, and economically',
    ],
    'Makabansa': [
        'Demonstrates pride in being a Filipino; exercises the rights and responsibilities of a Filipino Citizen',
        'Demonstrates appropriate behavior in carrying out activities in the school, community, and country',
    ],
}

LEGACY_INDICATOR_ALIASES = {
    'Expresses one\'s spiritual beliefs while respecting the spiritual beliefs of others': 'Expresses one\'s spiritual beliefs while respecting the spiritual beliefs of others',
    'Shows adherence to ethical principles by upholding truth': 'Shows adherence to ethical principles by upholding truth',
    'Is sensitive to individual, social, and cultural differences': 'Is sensitive to individual, social, and cultural differences',
    'Demonstrate contributions toward solidarity': 'Demonstrate contributions toward solidarity',
    'Cares for the environment and utilizes resources wisely, judiciously, and economically': 'Cares for the environment and utilizes resources wisely, judiciously, and economically',
    'Demonstrates pride in being a Filipino; exercises the rights and responsibilities of a Filipino Citizen': 'Demonstrates pride in being a Filipino; exercises the rights and responsibilities of a Filipino Citizen',
    'Demonstrates appropriate behavior in carrying out activities in the school, community, and country': 'Demonstrates appropriate behavior in carrying out activities in the school, community, and country',
}

DEPED_CORE_VALUES = [
    {
        'name': 'Maka-Diyos',
        'description': 'DepEd Core Value',
        'indicators': CORE_VALUE_CANONICAL_INDICATORS['Maka-Diyos'],
    },
    {
        'name': 'Makatao',
        'description': 'DepEd Core Value',
        'indicators': CORE_VALUE_CANONICAL_INDICATORS['Makatao'],
    },
    {
        'name': 'Makakalikasan',
        'description': 'DepEd Core Value',
        'indicators': CORE_VALUE_CANONICAL_INDICATORS['Makakalikasan'],
    },
    {
        'name': 'Makabansa',
        'description': 'DepEd Core Value',
        'indicators': CORE_VALUE_CANONICAL_INDICATORS['Makabansa'],
    },
]


def canonicalize_core_value_name(value):
    if value is None:
        return value
    normalized = str(value).strip()
    if not normalized:
        return normalized
    normalized = re.sub(r'\s*\(.*?\)', '', normalized)
    normalized = normalized.strip()
    if normalized in LEGACY_CORE_VALUE_ALIASES:
        return LEGACY_CORE_VALUE_ALIASES[normalized]
    normalized_casefold = normalized.casefold()
    for legacy_name, canonical_name in LEGACY_CORE_VALUE_ALIASES.items():
        if legacy_name.casefold() == normalized_casefold:
            return canonical_name
    return normalized


def canonicalize_indicator_name(value):
    if value is None:
        return value
    normalized = str(value).strip()
    if not normalized:
        return normalized
    for legacy_name, canonical_name in LEGACY_INDICATOR_ALIASES.items():
        if normalized.casefold() == legacy_name.casefold():
            return canonical_name
    return normalized
