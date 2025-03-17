# Module to display ui components for running analyses
import streamlit as st
from modules.settings import get_analyses_settings
from modules.validation import NameValidation, NotNoneValidation, ValidationError, ValidationGroup
import json

class FormFragment():
    def __init__(self, params={}):
        self.params = params

    def display(self):
        return {}

def create_analysis_form(portfolios, models):
    """Analysis creation form ui component."""

    def list_empty(lst):
        if len(lst) == 0:
            return True
        if all(e is None for e in lst):
            return True
        return False

    if list_empty(portfolios) or list_empty(models):
        st.write("Ensure portfolios and models are loaded")
        return None

    def format_portfolio(portfolio):
        return f"{portfolio['name']}"

    def format_model(model):
        return f"{model['model_id']} {model['run_mode']} {model['supplier_id']}"

    with st.form("create_analysis_form", clear_on_submit=True, enter_to_submit=False):
        name = st.text_input("Analysis Name")

        selected_port = 0 if len(portfolios) == 1 else None
        portfolio = st.selectbox('Select Portfolio', options=portfolios,
                                 index=selected_port, format_func=format_portfolio)

        selected_model = 0 if len(models) == 1 else None
        model = st.selectbox('Select Model', options=models,
                             index=selected_model, format_func=format_model)

        submitted = st.form_submit_button("Create Analysis")

    if submitted:
        val_group = ValidationGroup()
        val_group.add_validation(NameValidation('Name'), name)
        val_group.add_validation(NotNoneValidation('Portfolio'), portfolio)
        val_group.add_validation(NotNoneValidation('Model'), model)

        try:
            val_group.validate()
            return {'name': name, 'model_id': int(model['id']), 'portfolio_id': int(portfolio['id'])}
        except ValidationError as e:
            st.error(e)
    return None

class PortfolioFilesFragment(FormFragment):
    def display(self):
        options = self.params.get('options', [])

        name = st.text_input('Portfolio Name', value=None, key='portfolio_name')
        loc_file = st.selectbox('Select Location File', options, index=None)
        acc_file = st.selectbox('Select Accounts File', options, index=None)
        ri_file = st.selectbox('Select Reinsurance Info File', options, index=None)
        rs_file = st.selectbox('Select Reinsurance Scope File', options, index=None)

        return {
                'name': name,
                'location_file': loc_file,
                'accounts_file': acc_file,
                'reinsurance_info_file': ri_file,
                'reinsurance_scope_file': rs_file
        }

def create_portfolio_form():
    files = st.file_uploader("Upload portfolio files", accept_multiple_files=True)
    filesDict = { f.name: f for f in files}

    options = [f.name for f in files]

    with st.form("create_portfolio_form", clear_on_submit=True, enter_to_submit=False):
        name = st.text_input('Portfolio Name', value=None, key='portfolio_name')
        loc_file = st.selectbox('Select Location File', options, index=None)
        acc_file = st.selectbox('Select Accounts File', options, index=None)
        ri_file = st.selectbox('Select Reinsurance Info File', options, index=None)
        rs_file = st.selectbox('Select Reinsurance Scope File', options, index=None)

        submitted = st.form_submit_button("Create Portfolio")


    if submitted:
        validation = NameValidation("Name")
        if not validation.is_valid(name):
            st.error(validation.message)
            return None

        return {
                'name': name,
                'location_file': filesDict.get(loc_file),
                'accounts_file': filesDict.get(acc_file),
                'reinsurance_info_file': filesDict.get(ri_file),
                'reinsurance_scope_file': filesDict.get(rs_file)
        }



class ModelSettingsFragment(FormFragment):
    def display(self):
        # Handle categorical settings
        valid_settings = [
            'event_set',
            'event_occurrence_id',
            'footprint_set',
            'vulnerability_set',
            'pla_loss_factor_set',
        ]

        model_settings = self.params.get('model_settings', {}).get('model_settings', {})
        outputs = {'model_settings': {}}

        if not model_settings:
            return outputs

        for k, v in model_settings.items():
            if k in valid_settings:
                default = v.get('default', None)
                options = v['options']
                default_index = self._get_default_index(options, default)
                selected = st.selectbox(f"Set {v['name']}", options=v['options'], format_func=self._format_option, index=default_index)
                outputs['model_settings'][k] = selected["id"]
        return outputs

    @staticmethod
    def _format_option(opt):
        return f'{opt["id"]} : {opt["desc"]}'

    @staticmethod
    def _get_default_index(options, default=None):
        if default is None:
            return None
        return [i for i in range(len(options)) if options[i]['id'] == default][0]


class PerspectivesFragment(FormFragment):
    def display(self):
        model_settings = self.params.get('model_settings', {}).get('model_settings', {})
        # Select perspectives
        valid_outputs = ['gul', 'il', 'ri']
        if "valid_output_perspectives" in model_settings:
            valid_outputs = model_settings["model_settings"]["valid_output_perspectives"]

        outputs = {}

        default = self.params.get('default', [])

        perspectives = {'gul': 'Ground up loss',
                        'il': 'Insured loss',
                        'ri': 'Reinsurance net loss'}
        opt_cols = st.columns(3)

        for col, p in zip(opt_cols, perspectives.keys()):
            with col:
                opt = st.checkbox(p.upper(), help=perspectives[p],
                                  value = p in default,
                                  disabled = (p not in valid_outputs)
                                  )
                outputs[f'{p}_output'] = opt

        return outputs

class NumberSamplesFragment(FormFragment):
    def display(self):
        model_settings = self.params.get('model_settings')
        analysis_settings = self.params.get('analysis_settings')

        outputs = {}

        default_samples = model_settings.get("model_default_samples", 10)
        default_samples = analysis_settings.get("number_of_samples", default_samples)
        outputs["number_of_samples"] = st.number_input("Number of samples",
                                                                 min_value = 1,
                                                                 value = default_samples)

        return outputs

class OEDGroupFragment(FormFragment):
    EXCLUDED_FIELDS = [ "BuildingTIV", "ContentsTIV", "OtherTIV", "BITIV", "OEDVersion" ]

    def display(self):
        perspective = self.params.get('perspective', 'gul')
        oed_options = self.params.get('oed_fields', None)
        if oed_options is None:
            oed_options = ['PortNumber', 'CountryCode', 'LocNumber']

        oed_options = sorted(filter(self.valid_field_filter, oed_options))

        oed_fields = st.multiselect(f"{perspective.upper()} OED grouping:",
                             oed_options,
                             key=f'{id}_{perspective}_oed')

        output = {'oed_fields': oed_fields}

        return output

    @staticmethod
    def valid_field_filter(field):
        if field in OEDGroupFragment.EXCLUDED_FIELDS:
            return False
        return True



class OutputFragment(FormFragment):
    def display(self):
        perspective = self.params.get('perspective', 'gul')
        default = self.params.get('default', [])

        options = [
            'eltcalc',
            'aalcalc',
            'aalcalcmeanonly',
            'pltcalc',
            'summarycalc',
            'leccalc-full_uncertainty_aep',
            'leccalc-full_uncertainty_oep',
            'leccalc-persample_aep',
            'leccalc-persample_oep',
            'leccalc-persample_mean_aep',
            'leccalc-persample_mean_oep',
            'leccalc-sample_mean_aep',
            'leccalc-sample_mean_oep'
        ]

        selected = st.multiselect(f"{perspective.upper()} Outputs",
                                 options, key=f'{id}_{perspective}_output',
                                 default=default)

        output_dict = {
            'eltcalc': False,
            'aalcalc': False,
            'aalcalcmeanonly': False,
            'pltcalc': False,
            'summarycalc': False,
            'lec_output': False,
            'leccalc': {
                'full_uncertainty_aep': False,
                'full_uncertainty_oep': False,
                'wheatsheaf_aep': False,
                'wheatsheaf_oep': False,
                'wheatsheaf_mean_aep': False,
                'wheatsheaf_mean_oep': False,
                'sample_mean_aep': False,
                'sample_mean_oep': False
            }

        }

        for output_option in selected:
            if output_option[:7] == 'leccalc':
                output_dict['lec_output'] = True
                lec_option = output_option[8:]
                lec_option = lec_option.replace('persample', 'wheatsheaf')
                output_dict['leccalc'][lec_option] = True
            else:
                output_dict[output_option] = True

        return output_dict


def merge_settings(settings1, settings2):
    from copy import copy
    settings1 = copy(settings1)

    for key, value in settings2.items():
        if key in settings1 and isinstance(settings1[key], dict) and isinstance(value, dict):
            settings1[key] = merge_settings(settings1[key], value)
        elif key in settings1 and isinstance(settings1[key], list) and isinstance(value, list):
            settings1[key] += value
        else:
            settings1[key] = value
    return settings1

def merge_summaries(summaries1, summaries2):
    summaries1 = list(sorted(summaries1, key= lambda x: x['id']))
    summaries2 = list(sorted(summaries2, key= lambda x: x['id']))

    i1, i2, output_summaries = 0, 0, []

    while i1 < len(summaries1) and i2 < len(summaries2):
        if summaries1[i1]['id'] == summaries2[i2]['id']:
            output_summaries.append(summaries1[i1] | summaries2[i2])
            i1 += 1
            i2 += 1
        elif summaries1[i1]['id'] < summaries2[i2]['id']:
            output_summaries.append(summaries1[i1])
            i1 += 1
        else:
            output_summaries.append(summaries2[i2])
            i2 += 1

    output_summaries.extend(summaries1[i1:])
    output_summaries.extend(summaries2[i2:])

    return output_summaries


def create_analysis_settings(model, model_settings, oed_fields=None):
    '''
    Create a form to get user input for setting analysis settings.

    Parameters
    ----------
    model : dict
            Information about the model, particularly `model_id` and `supplier_id`.
    model_settings : dict
            Model settings dictionary for given model.
    oed_fields : list[str]
                 List of OED Fields to allow user to group by.

    Returns
    -------
    dict : Dictionary of settings for analysis, can be used in `client.upload_settings`
    '''
    default = get_analyses_settings(model_name_id=model["model_id"], supplier_id=model["supplier_id"])

    if default:
        with open(default[0], 'r') as f:
            analysis_settings = json.load(f)
    else:
        analysis_settings = {
                    'model_settings': {},
                    'model_supplier_id': model["supplier_id"],
                    'model_name_id': model["model_id"],
                    'gul_output': True,
                    'gul_summaries': [{
                        'id': 1,
                    }],
        }

    perspectives = ['gul', 'il', 'ri']

    with st.form("create_analysis_settings_form", enter_to_submit=False, clear_on_submit=True):
        selected_settings = {}

        selected_settings |= ModelSettingsFragment(params={'model_settings': model_settings}).display()
        selected_settings |= NumberSamplesFragment(params={'model_settings': model_settings,
                                                           'analysis_settings': analysis_settings}).display()
        default_perspectives = [p for p in perspectives if analysis_settings.get(f'{p}_output', False)]
        selected_settings |= PerspectivesFragment(params={'model_settings': model_settings,
                                                          'default': default_perspectives}).display()

        # Generate summaries
        summaries = {f'{p}_summaries': [{'id': 1}] for p in perspectives}

        # Load default outputs
        default_dict = {}
        supported_outputs = set([
            'eltcalc', 'aalcalc', 'pltcalc', 'summarycalc'
        ])
        for p in perspectives:
            settings_name = f'{p}_summaries'
            default_summaries = analysis_settings.get(settings_name, None)

            if default_summaries:
                default_summaries = default_summaries[0]
                default_outputs = supported_outputs & set(default_summaries.keys())
                default_dict[p] = [output for output in default_outputs if default_summaries[output]]


        for p in perspectives:
            p_summaries = OutputFragment(params={'perspective': p, 'default': default_dict.get(p, [])}).display()
            summaries[f'{p}_summaries'][0] |= p_summaries

        with st.popover('OED Fields', use_container_width=True):
            for p in perspectives:
                if isinstance(oed_fields, dict):
                    if oed_fields.get(p, None):
                        p_summaries = OEDGroupFragment(params={'perspective': p,
                                                               'oed_fields': oed_fields[p]}).display()
                else:
                    p_summaries = OEDGroupFragment(params={'perspective': p,
                                                           'oed_fields': oed_fields}).display()

                summaries[f'{p}_summaries'][0] |= p_summaries

        submitted = st.form_submit_button('Submit')

    if submitted:
        # Merge summaries settings
        for p in perspectives:
            settings_name = f'{p}_summaries'
            default_summaries = analysis_settings.pop(settings_name, None)
            if default_summaries is None:
                selected_settings[settings_name] = summaries[settings_name]
            else:
                selected_settings[settings_name] = merge_summaries(default_summaries, summaries[settings_name])

        settings = merge_settings(analysis_settings, selected_settings)
        return settings
    else:
        return None
