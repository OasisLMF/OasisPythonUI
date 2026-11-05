'''
Access to the ODS-tools analysis / model settings JSON schemas.

The schemas are the source of truth for labels, descriptions, defaults and
the available output options, so the UI follows ods_tools upgrades rather
than hard-coding them.
'''
import json
from functools import lru_cache
from pathlib import Path

import ods_tools
from ods_tools.oed.settings import AnalysisSettingHandler

SCHEMA_DIR = Path(ods_tools.__file__).parent / 'data'

PERSPECTIVES = ['gul', 'il', 'ri', 'rl']
PERSPECTIVE_LABELS = {
    'gul': 'Ground up loss (GUL)',
    'il': 'Insured loss (IL)',
    'ri': 'Net of reinsurance (RI)',
    'rl': 'Ceded to reinsurance (RL)',
}

# Model settings keys that select one option from a list of `{id, desc}` options
CATEGORICAL_MODEL_SETTINGS = [
    'event_set',
    'event_occurrence_id',
    'footprint_set',
    'vulnerability_set',
    'pla_loss_factors_set',
]

# Model settings keys holding lists of user-settable parameters, mapped to the
# kind of control used to edit them.
PARAMETER_TYPES = {
    'string_parameters': 'string',
    'list_parameters': 'list',
    'dictionary_parameters': 'dict',
    'boolean_parameters': 'bool',
    'float_parameters': 'float',
    'numeric_parameters': 'number',
    'integer_parameters': 'int',
    'dropdown_parameters': 'dropdown',
}

# OED fields that can always be used to group outputs, in addition to any the
# model declares in `data_settings`.
DEFAULT_GROUP_FIELDS = ['PortNumber', 'AccNumber', 'LocNumber', 'CountryCode', 'LocPeril']


@lru_cache
def analysis_settings_schema():
    with open(SCHEMA_DIR / 'analysis_settings_schema.json') as f:
        return json.load(f)


@lru_cache
def model_settings_schema():
    with open(SCHEMA_DIR / 'model_settings_schema.json') as f:
        return json.load(f)


def analysis_property(key):
    '''Schema entry for a top-level analysis settings key (`{}` if unknown).'''
    return analysis_settings_schema()['properties'].get(key, {})


def model_settings_property(key):
    '''Schema entry for a key under the model settings `model_settings` section.'''
    props = model_settings_schema()['properties']['model_settings'].get('properties', {})
    return props.get(key, {})


def model_property(key):
    '''Schema entry for a top-level model settings key.'''
    return model_settings_schema()['properties'].get(key, {})


def title(schema_entry, fallback):
    return schema_entry.get('title') or fallback


def ord_output_options():
    '''Boolean ORD output flags from the schema as `{key: (title, description)}`.

    Excludes the non-table flags (`parquet_format`, `alct_confidence`,
    `return_period_file`), which are handled separately.
    '''
    props = (analysis_settings_schema()['definitions']['output_summaries']
             ['items']['properties']['ord_output']['properties'])
    skip = {'parquet_format', 'alct_confidence', 'return_period_file'}
    return {k: (v.get('title', k), v.get('description', ''))
            for k, v in props.items()
            if v.get('type') == 'boolean' and k not in skip}


# Groupings of the ORD output flags for presentation
ORD_OUTPUT_GROUPS = {
    'Event loss tables (ELT)': ['elt_sample', 'elt_quantile', 'elt_moment'],
    'Period loss tables (PLT)': ['plt_sample', 'plt_quantile', 'plt_moment'],
    'Average loss tables (ALT)': ['alt_period', 'alt_meanonly', 'alct_convergence'],
    'Exceedance probability tables (EPT)': [
        'ept_full_uncertainty_aep', 'ept_full_uncertainty_oep',
        'ept_mean_sample_aep', 'ept_mean_sample_oep',
        'ept_per_sample_mean_aep', 'ept_per_sample_mean_oep',
    ],
    'Per-sample EPT (PSEPT)': ['psept_aep', 'psept_oep'],
}

# A sensible starting set of outputs for a new summary level
DEFAULT_ORD_OUTPUTS = ['elt_moment', 'alt_meanonly', 'ept_full_uncertainty_aep', 'ept_full_uncertainty_oep']


def validate_analysis_settings(settings):
    '''Validate analysis settings against the ODS analysis settings schema.

    The model-derived schema (`AnalysisSettingHandler.make(model_setting_json=...)`)
    isn't used: in ods_tools 5.0.x it rejects the event/footprint set selectors
    whenever a model defines parameters, and its dropdown `oneOf` never
    validates. Model options are instead constrained by the editor's controls.

    Returns:
        (bool, dict): validity and `{field: [messages]}`.
    '''
    return AnalysisSettingHandler.make().validate(settings, raise_error=False)
