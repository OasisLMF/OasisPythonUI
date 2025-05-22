'''
Test file for `pages/components/create.py`
'''
import json
from requests import options
import streamlit as st
from streamlit.testing.v1 import AppTest

# Test plan
# - produce analysis settings
# - [x] ModelSettingsFragment
# - [ ] NumberSamplesFragment
# - [ ] PerspectivesFragment
# - [ ] summaries settings fragment
# - [ ] Mock response from each fragment output and confirm the save settings button works
# - consume analysis settings
# - [ ] set `created_analysis_settings` to None and test dict and confirm output

def test_ModelSettingsFragment():
    mock_model_settings = {
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

    def test_script(model_settings, *args):
        import streamlit as st
        from pages.components.create import ModelSettingsFragment

        output = ModelSettingsFragment(model_settings).display()

        st.write(output)


    at = AppTest.from_function(test_script, args=[mock_model_settings,])
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
