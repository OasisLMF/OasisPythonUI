'''
Test file for `pages/components/create.py`
'''
import json
from pages.components.output import pltcalc_bar
import pytest
from streamlit.testing.v1 import AppTest
import functools
from pandas.testing import assert_frame_equal
import pandas as pd

# Test plan
# - produce analysis settings
# - [x] ModelSettingsFragment
# - [x] NumberSamplesFragment
# - [x] PerspectivesFragment
# - [ ] summaries settings fragment
#   - [x] ViewSummarySettings
#   - [x] SummarySettingsFragment
#       - [x] ORDOutputFragment
#       - [x] OutputFragment
#       - [x] OEDGroupFragment
# - [ ] Mock response from each fragment output and confirm the save settings button works
# - consume analysis settings
# - [ ] set `created_analysis_settings` to None and test dict and confirm output

def assert_list_equal_noorder(list1, list2):
    assert len(list1) == len(list2)
    assert all([el in list2 for el in list1])

def test_ModelSettingsFragment():
    mock_settings = {
        "model_settings": {
            "event_set": {
                "name": "Event Set",
                "desc": "Custom Event Set selection",
                "default": "h",
                "options": [
                    {
                        "id": "h",
                        "desc": "Historical",
                        "number_of_events": 982
                    },
                    {
                        "id": "s",
                        "desc": "Synthetic",
                        "number_of_events": 2034
                    }
                ]
            },
            "event_occurrence_id": {
                "name": "Occurrence Set",
                "desc": "Custom Occurrence selection",
                "default": "st",
                "options": [
                    {
                        "id": "st",
                        "desc": "Short Term"
                    },
                    {
                        "id": "mt",
                        "desc": "Medium Term"
                    }
                ]
            }
        }
    }

    def test_script(model_settings):
        import streamlit as st
        from pages.components.create import ModelSettingsFragment

        output = ModelSettingsFragment(model_settings).display()

        st.write(output)

    at = AppTest.from_function(test_script, args=[mock_settings,])
    at.run()

    assert not at.exception

    assert at.selectbox[0].label == 'Set Event Set'
    assert at.selectbox[0].options == ['h : Historical', 's : Synthetic']
    assert at.selectbox[0].value['id'] == 'h'

    assert at.selectbox[1].label == 'Set Occurrence Set'
    assert at.selectbox[1].options == ['st : Short Term', 'mt : Medium Term']
    assert at.selectbox[1].value['id'] == 'st'

    output = json.loads(at.json[0].value)
    assert output == {"model_settings": {
                          "event_set": "h",
                          "event_occurrence_id": "st"
                        }
                     }

test_data = [
    (1, 2, 2),
    (1, None, 1),
    (None, 2, 2),
    (None, None, 10)
]
@pytest.mark.parametrize("model_settings_no,analysis_settings_no,initial", test_data)
def test_NumberSamplesFragment(model_settings_no, analysis_settings_no, initial):

    model_settings = {}
    analysis_settings = {}

    if model_settings_no is not None:
        model_settings = {
            "model_default_samples": model_settings_no
        }

    if analysis_settings_no is not None:
        analysis_settings = {
            "number_of_samples": analysis_settings_no
        }

    def test_script(model_settings, analysis_settings):
        import streamlit as st
        from pages.components.create import NumberSamplesFragment

        output = NumberSamplesFragment(model_settings=model_settings,
                                       analysis_settings=analysis_settings).display()

        st.write(output)

    at = AppTest.from_function(test_script, args=[model_settings, analysis_settings])
    at.run()

    assert not at.exception

    input_widget = at.number_input[0]
    assert input_widget.label == 'Number of samples'
    assert input_widget.step == 1.0
    assert input_widget.min == 1.0
    assert input_widget.value == initial

    output = json.loads(at.json[0].value)
    assert output == {"number_of_samples" : initial}


test_data = [
    (None, None, (False, False, False), (False, False, False)),
    (None, ['gul', 'ri'], (False, False, False), (True, False, True)),
    (['il', 'ri'], 'ri', (True, False, False), (False, False, True))
]
@pytest.mark.parametrize("valid_perspectives,default_perspectives,disabled,expected_output", test_data)
def test_PerspectivesFragment(valid_perspectives, default_perspectives, disabled, expected_output):
    kwargs = {}

    if valid_perspectives is not None:
        model_settings = {"model_settings": {"valid_output_perspectives": valid_perspectives}}
        kwargs["model_settings"] = model_settings

    if default_perspectives is not None:
        kwargs["default"] = default_perspectives

    def test_script(kwargs):
        import streamlit as st
        from pages.components.create import PerspectivesFragment

        output = PerspectivesFragment(**kwargs).display()

        st.write(output)

    at = AppTest.from_function(test_script, args=(kwargs,))
    at.run()

    assert not at.exception

    perspectives = ["GUL", "IL", "RI"]
    for i in range(3):
        checkbox = at.checkbox[i]
        assert checkbox.label == perspectives[i]
        assert checkbox.disabled == disabled[i]
        assert checkbox.value == expected_output[i]

    output = json.loads(at.json[0].value)

    assert output == {'gul_output': expected_output[0],
                      'il_output': expected_output[1],
                      'ri_output': expected_output[2]}



test_data_viewsummarysettings = [
        ([], True, {'level_id': [], 'ord_output': [], 'legacy_output': [], 'oed_fields': []}) ,
        ([{
          "eltcalc": True,
          "id": 1
        },
        {
          "ord_output": {
            "elt_sample": True,
            "elt_quantile": False,
            "elt_moment": False,
            "plt_sample": False,
            "plt_quantile": False,
            "plt_moment": False,
            "alt_period": False,
            "alt_meanonly": False,
            "ept_full_uncertainty_aep": False,
            "ept_full_uncertainty_oep": False,
            "ept_mean_sample_aep": False,
            "ept_mean_sample_oep": False,
            "ept_per_sample_mean_aep": False,
            "ept_per_sample_mean_oep": False,
            "psept_aep": False,
            "psept_oep": False
          },
          "oed_fields": [
            "CountryCode"
          ],
          "id": 2
        }], False, {'ord_output': [[], ['elt_sample']],
                    'legacy_output': [['eltcalc'],[]],
                    'oed_fields': [[], ['CountryCode']],
                    'level_id': [1, 2]})

]
@pytest.mark.parametrize("settings,empty,df_dict", test_data_viewsummarysettings)
def test_ViewSummarySettings(settings, empty, df_dict):
    def app_view_summary_script(settings):
        import streamlit as st
        from pages.components.create import ViewSummarySettings

        output = ViewSummarySettings(settings)

        st.write(output)

    at = AppTest.from_function(app_view_summary_script, args=[settings,])
    at.run()

    assert not at.exception

    df = at.dataframe[0].value
    assert df.empty == empty
    expected_cols = ['level_id', 'ord_output', 'legacy_output', 'oed_fields']
    df_cols = df.columns.to_list()
    assert_list_equal_noorder(expected_cols, df_cols)
    assert_frame_equal(df, pd.DataFrame(df_dict), check_dtype=False)

test_data = [
    ('gul', {}, {'elt_sample': False, 'elt_quantile': False, 'elt_moment': False, 'plt_sample': False, 'plt_quantile': False, 'plt_moment': False, 'alt_period': False, 'alt_meanonly': False, 'ept_full_uncertainty_aep': False, 'ept_full_uncertainty_oep': False, 'ept_mean_sample_aep': False, 'ept_mean_sample_oep': False, 'ept_per_sample_mean_aep': False, 'ept_per_sample_mean_oep': False, 'psept_aep': False, 'psept_oep': False}),
    ('ri', {
        'elt': ['sample', 'quantile'],
        'plt': ['quantile'],
        'alt': ['period'],
        'ept': ['full_uncertainty_aep', 'per_sample_mean_oep', 'mean_sample_aep'],
        'psep': ['oep']
    }, {'elt_sample': True, 'elt_quantile': True, 'elt_moment': False, 'plt_sample': False, 'plt_quantile': True, 'plt_moment': False, 'alt_period': True, 'alt_meanonly': False, 'alct_convergence': False, 'alct_confidence': 0.95, 'ept_full_uncertainty_aep': True, 'ept_full_uncertainty_oep': False, 'ept_mean_sample_aep': True, 'ept_mean_sample_oep': False, 'ept_per_sample_mean_aep': False, 'ept_per_sample_mean_oep': True, 'psept_aep': False, 'psept_oep': True})
]

@pytest.mark.parametrize("perspective,default,expected_output", test_data)
def test_ORDOutputFragment(perspective, default, expected_output):

    def test_script(perspective, default):
        import streamlit as st
        from pages.components.create import ORDOutputFragment

        output = ORDOutputFragment(perspective, default).display()

        st.write(output)

    at = AppTest.from_function(test_script, args=(perspective, default))
    at.run()

    assert not at.exception
    assert json.loads(at.json[0].value) == expected_output

def test_select_ORDOutputFragment():
    def test_script():
        import streamlit as st
        from pages.components.create import ORDOutputFragment

        output = ORDOutputFragment('gul',).display()

        st.json(output)

    at = AppTest.from_function(test_script)
    at.run()

    assert not at.exception

    select_options = (
        ('elt', 'moment'),
        ('plt', 'sample'),
        ('plt', 'quantile'),
        ('alt', 'period'),
        ('ept', 'full_uncertainty_aep'),
        ('psep', 'aep')
    )

    for opt in select_options:
        at.multiselect(key=f"gul_{opt[0]}_multiselect").select(opt[1])
        at.run()

    expected_output = {'elt_sample': False, 'elt_quantile': False,
                       'elt_moment': True, 'plt_sample': True, 'plt_quantile':
                       True, 'plt_moment': False, 'alt_period': True,
                       'alt_meanonly': False, 'alct_convergence': False,
                       'alct_confidence': 0.95, 'ept_full_uncertainty_aep':
                       True, 'ept_full_uncertainty_oep': False,
                       'ept_mean_sample_aep': False, 'ept_mean_sample_oep':
                       False, 'ept_per_sample_mean_aep': False,
                       'ept_per_sample_mean_oep': False, 'psept_aep': True,
                       'psept_oep': False}
    assert not at.exception
    assert json.loads(at.json[0].value) == expected_output

test_data = [
    ([], [], {'eltcalc': False, 'aalcalc': False, 'aalcalcmeanonly': False,
              'pltcalc': False, 'summarycalc': False, 'lec_output': False,
              'leccalc': {'full_uncertainty_aep': False,
                          'full_uncertainty_oep': False, 'wheatsheaf_aep':
                          False, 'wheatsheaf_oep': False,
                          'wheatsheaf_mean_aep': False, 'wheatsheaf_mean_oep':
                          False, 'sample_mean_aep': False, 'sample_mean_oep':
                          False}}),
    ([],
    ['eltcalc', 'pltcalc', 'leccalc-full_uncertainty_aep',
      'leccalc-persample_aep', 'leccalc-persample_mean_oep'],
    {'eltcalc': True, 'aalcalc': False, 'aalcalcmeanonly': False,
     'pltcalc': True, 'summarycalc': False, 'lec_output': True,
     'leccalc': {'full_uncertainty_aep': True, 'full_uncertainty_oep': False,
                 'wheatsheaf_aep': True, 'wheatsheaf_oep': False,
                 'wheatsheaf_mean_aep': False, 'wheatsheaf_mean_oep': True,
                 'sample_mean_aep': False, 'sample_mean_oep': False}})
]
@pytest.mark.parametrize("default,selected,expected_output", test_data)
def test_OutputFragment(default, selected, expected_output):

    def test_script(default):
        import streamlit as st
        from pages.components.create import OutputFragment

        output = OutputFragment('gul', default).display()

        st.json(output)

    at = AppTest.from_function(test_script, args=(default,))
    at.run()

    assert not at.exception

    for option in selected:
        at.multiselect(key="gul_legacy_output_select").select(option)
    at.run()

    assert json.loads(at.json[0].value) == expected_output

def create_app_test(func, *args, **kwargs):
    def wrapper(func, *args, **kwargs):
        import streamlit as st
        output = func(*args, **kwargs)

        st.json(output)

    at = AppTest.from_function(wrapper, args=(func, *args), kwargs=kwargs)
    return at

options_full = [
    "AccCurrency", "AccNumber", "BuildingID", "BuildingTIV",
    "ConstructionCode", "CountryCode", "IsTenant", "Latitude",
    "LayerAttachment", "LayerLimit", "LayerNumber", "LayerParticipation",
    "LocCurrency", "LocNumber", "LocPerilsCovered", "Longitude",
    "NumberOfBuildings", "OEDVersion", "OccupancyCode", "PolExpiryDate",
    "PolInceptionDate", "PolNumber", "PolPeril", "PolPerilsCovered",
    "PortNumber", "PostalCode", "StreetAddress"
    ]
test_data = [
        (None, [], [], {'oed_fields': []}),
        (options_full, ['AccNumber', 'PostalCode', 'LocNumber'], [],
         {'oed_fields': ['AccNumber', 'PostalCode', 'LocNumber']}),
        (options_full, ['AccNumber', 'PostalCode', 'LocNumber'],
         ['AccCurrency', 'CountryCode'], {'oed_fields': ['AccNumber',
                                                         'PostalCode',
                                                         'LocNumber',
                                                         'AccCurrency',
                                                         'CountryCode']})
]
@pytest.mark.parametrize("options,default,selected,expected_output", test_data)
def test_OEDGroupFragment(options, default, selected, expected_output):
    EXCLUDED_FIELDS = [ "BuildingTIV", "ContentsTIV", "OtherTIV", "BITIV", "OEDVersion" ]
    def test_script(options, default):
        from pages.components.create import OEDGroupFragment
        return OEDGroupFragment('gul', options, default).display()

    at = create_app_test(test_script, options, default)
    at.run()

    assert not at.exception

    expected_options = options
    if expected_options is None:
        expected_options = ["PortNumber", "CountryCode", "LocNumber"] # default options
    expected_options = [opt for opt in expected_options if opt not in EXCLUDED_FIELDS]

    selectbox = at.multiselect(key="gul_oed_select")
    assert_list_equal_noorder(selectbox.options, expected_options)

    for option in selected:
        selectbox.select(option)
    at.run()

    assert json.loads(at.json[0].value) == expected_output

def test_SummarySettingsFragment():
    oed_fields = options_full

    default = {
        'ord_outputs': {
            'elt': ['sample', 'quantile']
        },
        'legacy_outputs': ['eltcalc', 'leccalc-persample_aep'],
        'oed_fields': ['CountryCode', 'LocNumber']
    }

    expected_output = {'ord_output': {'elt_sample': True, 'elt_quantile': True,
                                      'elt_moment': False, 'plt_sample': False,
                                      'plt_quantile': False, 'plt_moment':
                                      False, 'alt_period': False,
                                      'alt_meanonly': False,
                                      'ept_full_uncertainty_aep': False,
                                      'ept_full_uncertainty_oep': False,
                                      'ept_mean_sample_aep': False,
                                      'ept_mean_sample_oep': False,
                                      'ept_per_sample_mean_aep': False,
                                      'ept_per_sample_mean_oep': False,
                                      'psept_aep': False, 'psept_oep': False},
                       'eltcalc': True, 'aalcalc': False, 'aalcalcmeanonly':
                       False, 'pltcalc': False, 'summarycalc': False,
                       'lec_output': True,
                       'leccalc': {'full_uncertainty_aep': False,
                                   'full_uncertainty_oep': False,
                                   'wheatsheaf_aep': True, 'wheatsheaf_oep':
                                   False, 'wheatsheaf_mean_aep': False,
                                   'wheatsheaf_mean_oep': False,
                                   'sample_mean_aep': False, 'sample_mean_oep':
                                   False},
                       'oed_fields': ['CountryCode', 'LocNumber']}

    def test_script(oed_fields, default):
        from pages.components.create import SummarySettingsFragment
        return SummarySettingsFragment(oed_fields, 'gul', default)

    at = create_app_test(test_script, oed_fields, default)
    at.run()

    assert not at.exception
    assert json.loads(at.json[0].value) == expected_output

@pytest.fixture
def at_summary_settings():
    summaries = {"gul_summaries": [
        {
          "eltcalc": True,
          "id": 1
        },
        {
          "ord_output": {
            "elt_sample": True,
            "elt_quantile": False,
            "elt_moment": False,
            "plt_sample": False,
            "plt_quantile": False,
            "plt_moment": False,
            "alt_period": False,
            "alt_meanonly": False,
            "ept_full_uncertainty_aep": False,
            "ept_full_uncertainty_oep": False,
            "ept_mean_sample_aep": False,
            "ept_mean_sample_oep": False,
            "ept_per_sample_mean_aep": False,
            "ept_per_sample_mean_oep": False,
            "psept_aep": False,
            "psept_oep": False
          },
          "oed_fields": [
            "CountryCode"
          ],
          "id": 2
        }
    ],
    "il_summaries": [
        {
          "eltcalc": True,
          "id": 1
        }
    ],
    "ri_summaries": []}

    def test_script(oed_fields):
        from pages.components.create import summary_settings_fragment

        summary_settings_fragment(oed_fields, 'gul')

    oed_fields = {"gul" : {opt: "test_desc" for opt in options_full}}

    at =  AppTest.from_function(test_script, args=(oed_fields,))

    for k, v in summaries.items():
        at.session_state[k] = v

    return at

def test_summary_settings_fragment(at_summary_settings):
    at = at_summary_settings
    at.run()

    assert not at.exception
    expected_view = pd.DataFrame({'ord_output': [[], ['elt_sample']],
                    'legacy_output': [['eltcalc'],[]],
                    'oed_fields': [[], ['CountryCode']],
                    'level_id': [1, 2]})
    assert_frame_equal(at.dataframe[0].value, expected_view)
    assert at.button(key="gul_summary_edit_button").disabled == True
    assert at.button(key="gul_summary_delete_button").disabled == True

def test_summary_settings_fragment_delete(at_summary_settings, mocker):
    # Test selecting
    mocker.patch("pages.components.create.ViewSummarySettings", return_value = 1)
    at = at_summary_settings
    at.run()

    assert not at.exception
    assert at.button(key="gul_summary_edit_button").disabled == False
    assert at.button(key="gul_summary_delete_button").disabled == False

    at.button(key="gul_summary_delete_button").click().run()

    assert at.session_state["gul_summaries"] == [
        {
          "ord_output": {
            "elt_sample": True,
            "elt_quantile": False,
            "elt_moment": False,
            "plt_sample": False,
            "plt_quantile": False,
            "plt_moment": False,
            "alt_period": False,
            "alt_meanonly": False,
            "ept_full_uncertainty_aep": False,
            "ept_full_uncertainty_oep": False,
            "ept_mean_sample_aep": False,
            "ept_mean_sample_oep": False,
            "ept_per_sample_mean_aep": False,
            "ept_per_sample_mean_oep": False,
            "psept_aep": False,
            "psept_oep": False
          },
          "oed_fields": [
            "CountryCode"
          ],
          "id": 2
        }
    ]

def test_summary_settings_fragment_edit(at_summary_settings, mocker):
    # Test selecting
    mocker.patch("pages.components.create.ViewSummarySettings", return_value = 1)
    at = at_summary_settings
    at.session_state["editing_level_gul"] = True

    from pages.components import create
    spy_summarysettingsfragment = mocker.spy(create, "SummarySettingsFragment")

    at.run()

    assert not at.exception
    expected_default = {'ord_outputs': {'elt': [], 'plt': [], 'alt': [],
                                        'alct_convergence': False,
                                        'alct_confidence': 0.95, 'ept': [],
                                        'psept': []}, 'legacy_outputs':
                        ['eltcalc'], 'oed_fields': []}
    spy_summarysettingsfragment.assert_called_once_with(options_full, 'gul',
                                                        expected_default)

def test_summary_settings_fragment_add(at_summary_settings, mocker):
    # Test selecting
    at = at_summary_settings
    at.session_state["adding_level_gul"] = True

    from pages.components import create
    spy_summarysettingsfragment = mocker.spy(create, "SummarySettingsFragment")

    at.run()

    assert not at.exception
    expected_default = {'ord_outputs': {'elt': [], 'plt': [], 'alt': [],
                                        'alct_convergence': False,
                                        'alct_confidence': 0.95, 'ept': [],
                                        'psept': []}, 'legacy_outputs':
                        ['eltcalc'], 'oed_fields': []}
    spy_summarysettingsfragment.assert_called_once_with(options_full, 'gul')
