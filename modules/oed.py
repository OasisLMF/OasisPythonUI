"""OED reference data (peril and country names) from the ods_tools OED spec."""
import json
import re
from functools import lru_cache
from pathlib import Path

import ods_tools

# Broad peril families used to filter scenarios, by the first letter of the OED peril code
PERIL_FAMILIES = {
    'Q': 'Earthquake',
    'W': 'Windstorm',
    'O': 'Flood',
    'X': 'Convective storm',
    'Z': 'Winter storm',
    'B': 'Wildfire',
    'V': 'Volcano',
}
# Codes whose family differs from their first letter
PERIL_FAMILY_OVERRIDES = {'XHL': 'Hail', 'XCH': 'Hail', 'ZST': 'Windstorm'}


@lru_cache
def oed_spec():
    """The newest OED spec bundled with ods_tools."""
    data = Path(ods_tools.__file__).parent / 'data'

    def version(path):
        return tuple(int(v) for v in re.findall(r'\d+', path.stem))

    latest = max(data.glob('OpenExposureData_*Spec.json'), key=version)
    return json.loads(latest.read_text())


def country_name(code):
    entry = oed_spec().get('country', {}).get(str(code).upper(), {})
    return entry.get('Name') or str(code)


def peril_description(code):
    entry = oed_spec().get('perils', {}).get('info', {}).get(str(code).upper(), {})
    return entry.get('Peril Description') or str(code)


def peril_family(code):
    code = str(code).upper()
    return PERIL_FAMILY_OVERRIDES.get(code) or PERIL_FAMILIES.get(code[:1], peril_description(code))
