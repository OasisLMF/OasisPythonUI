'''
Test file for `pages/components/create.py`
'''
import json
import pytest
from streamlit.testing.v1 import AppTest

# Test plan
# - produce analysis settings
# - [x] ModelSettingsFragment
# - [x] NumberSamplesFragment
# - [ ] PerspectivesFragment
# - [ ] summaries settings fragment
# - [ ] Mock response from each fragment output and confirm the save settings button works
# - consume analysis settings
# - [ ] set `created_analysis_settings` to None and test dict and confirm output

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
