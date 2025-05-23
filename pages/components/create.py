# Module to display ui components for running analyses
from copy import copy
from pages.components.display import DataframeView
from pages.components.output import summarise_summary_level, summarise_summary_levels
import streamlit as st
from modules.settings import get_analyses_settings
from modules.validation import NameValidation, NotNoneValidation, ValidationError, ValidationGroup
import pandas as pd

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



class ModelSettingsFragment:
    '''Form fragment which sets categorical model settings.

    Currently handles the following settings:
        - `event_set`,
        - `event_occurrence_id`,
        - `footprint_set`,
        - `vulnerability_set`,
        - `pla_loss_factor_set`,

    Args:
        model_settings (dict) : model settings for form fragment
    '''
    def __init__(self, model_settings):
        self.model_settings = model_settings['model_settings']

    def display(self):
        '''
        Display the form fragment.

        Returns:
           (dict) selected options in a dict under the `model_settings` key.
        '''
        # Handle categorical settings
        valid_settings = [
            'event_set',
            'event_occurrence_id',
            'footprint_set',
            'vulnerability_set',
            'pla_loss_factor_set',
        ]

        model_settings = self.model_settings
        outputs = {'model_settings': {}}

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


class PerspectivesFragment:
    '''Form fragment to set the active perspectives.

    Args:
        model_settings (dict)
        default (list) : List of active perspectives.
    '''
    def __init__(self, model_settings={}, default=[]):
        self.valid_perspectives = ['gul', 'il', 'ri']
        if "valid_output_perspectives" in model_settings.get('model_settings', {}):
            self.valid_perspectives = model_settings["model_settings"]["valid_output_perspectives"]

        self.default = default

    def display(self):
        valid_outputs = self.valid_perspectives
        default = self.default

        outputs = {}
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

class NumberSamplesFragment:
    '''Form fragment to set the number of samples in the analysis settings.

    Args:
        model_settings (dict)
        analysis_settings (dict)

    Usage:
        Initialise and run `display()` to create form elements. Returns corresponding section of analysis settings.
    '''
    def __init__(self, model_settings={}, analysis_settings={}):
        self.model_settings = model_settings
        self.analysis_settings = analysis_settings


    def display(self):
        model_settings = self.model_settings
        analysis_settings = self.analysis_settings

        outputs = {}

        default_samples = model_settings.get("model_default_samples", 10)
        default_samples = analysis_settings.get("number_of_samples", default_samples)
        outputs["number_of_samples"] = st.number_input("Number of samples",
                                                                 min_value = 1,
                                                                 value = default_samples)

        return outputs


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

def extract_default_from_level_settings(level_settings):
    '''Extract default dict for output fragments from analysis settings.
    '''
    default = {'ord_outputs': {}, 'legacy_outputs': {}}
    summary = summarise_summary_level(level_settings)

    st.write(summary)

    summary_ord = summary.get('ord_output', [])

    # Handle ord output
    default['ord_outputs']['elt'] = [opt[4:] for opt in summary_ord if opt.startswith('elt')]
    default['ord_outputs']['plt'] = [opt[4:] for opt in summary_ord if opt.startswith('plt')]
    default['ord_outputs']['alt'] = [opt[4:] for opt in summary_ord if opt.startswith('alt')]
    default['ord_outputs']['alct_convergence'] = 'alct_convergence' in summary_ord
    default['ord_outputs']['alct_confidence'] = level_settings['ord_output'].get('alct_confidence', 0.95)
    default['ord_outputs']['ept'] = [opt[4:] for opt in summary_ord if opt.startswith('ept')]
    default['ord_outputs']['psept'] = [opt[6:] for opt in summary_ord if opt.startswith('psept')]

    # Handle legacy output
    default['legacy_outputs'] = summary.get('legacy_output', None)

    # oed field
    default['oed_fields'] = summary.get('oed_fields', [])

    return default


@st.fragment
def summary_settings_fragment(oed_fields, perspective):
    if f'{perspective}_summaries' not in st.session_state:
        st.session_state[f'{perspective}_summaries'] = []
    original_summaries = st.session_state[f'{perspective}_summaries']
    curr_summaries = copy(original_summaries)

    selected = ViewSummarySettings(original_summaries, key=f'{perspective}_summaries_view')

    col1, col2, col3, *_ = st.columns(5)

    level_container = st.container(border=True)

    if f'adding_level_{perspective}' not in st.session_state:
        st.session_state[f'adding_level_{perspective}'] = False
    if f'editing_level_{perspective}' not in st.session_state:
        st.session_state[f'editing_level_{perspective}'] = False

    if col1.button('Add Level', key=f'{perspective}_summary_add_button',
                   use_container_width=True):
        st.session_state[f'adding_level_{perspective}'] = not st.session_state[f'adding_level_{perspective}']
        st.session_state[f'{perspective}_summaries'] = original_summaries

    if st.session_state[f'adding_level_{perspective}']:
        with level_container:
            curr_summary_settings = SummarySettingsFragment(oed_fields, perspective)
            curr_summary_settings['id'] = max([s['id'] for s in curr_summaries] + [0]) + 1
            submitted = st.button('Create Level')

        if submitted:
            st.session_state[f'adding_level_{perspective}'] = False
            curr_summaries.append(curr_summary_settings)
            st.session_state[f'{perspective}_summaries'] = curr_summaries
            st.rerun(scope='fragment')

    if col2.button('Delete Level', key=f'{perspective}_summary_delete_button',
                   use_container_width=True, disabled=selected is None):
        pos = [i for i, el in enumerate(curr_summaries) if el['id'] == selected][0]
        curr_summaries.pop(pos)
        st.session_state[f'{perspective}_summaries'] = curr_summaries
        st.rerun(scope='fragment')

    if col3.button('Edit Level', key=f'{perspective}_summary_edit_button',
                   use_container_width=True, disabled=selected is None):
        st.session_state[f'editing_level_{perspective}'] = not st.session_state[f'editing_level_{perspective}']
        st.session_state[f'{perspective}_summaries'] = original_summaries

    if st.session_state[f'editing_level_{perspective}']:
        if selected is None:
            st.session_state[f'editing_level_{perspective}'] = False
            st.rerun(scope='fragment')

        st.info('Editing level')
        pos = [i for i, el in enumerate(curr_summaries) if el['id'] == selected][0]
        selected_summary = curr_summaries[pos]
        defaults = extract_default_from_level_settings(selected_summary)

        with level_container:
            updated_summary_settings = SummarySettingsFragment(oed_fields, perspective, defaults)
            submit_edit = st.button('Save Edit')

        if submit_edit:
            curr_summaries.pop(pos)
            updated_summary_settings['id'] = selected_summary['id']
            st.session_state[f'editing_level_{perspective}'] = False
            curr_summaries.append(updated_summary_settings)
            st.session_state[f'{perspective}_summaries'] = curr_summaries
            st.rerun(scope='fragment')

def ViewSummarySettings(summary_settings, key=None):
    '''
    Display the summary settings for a single perspective as a selectable dataframe.

    Args:
        summary_settings (list[dict]): List of summary settings to display.

    Returns:
        (int) `id` for selected summary settings.

    '''
    summaries = summarise_summary_levels(summary_settings)
    summaries = pd.DataFrame(summaries)
    cols = ['level_id', 'ord_output', 'legacy_output', 'oed_fields']
    summaries = DataframeView(summaries, display_cols=cols, selectable=True)
    summaries.column_config['ord_output'] = st.column_config.ListColumn('ORD Output')
    summaries.column_config['legacy_output'] = st.column_config.ListColumn('Legacy Output')
    summaries.column_config['oed_fields'] = st.column_config.ListColumn('OED Fields')

    selected = summaries.display(key=key)
    return selected['level_id'].iloc[0] if selected is not None else None

def SummarySettingsFragment(oed_fields, perspective, default_outputs={}):
    '''
    Fragment to generate UI which creates summary settings.

    Args:
        oed_fields: List of OED Fields to group by.
        perspective: perspective name (`gul`, `il`, `ri`)
        default_outputs : dict with default options to preload form.

    Returns:
        dict: single summary setting instance.
    '''
    ord_output = ORDOutputFragment(perspective, default_outputs.get('ord_outputs', {})).display()
    summaries_settings = {'ord_output' : ord_output}

    legacy_outputs = False
    if len(default_outputs.get('legacy_outputs', [])) > 0:
        legacy_outputs = True
    if st.checkbox("Enable legacy outputs", key=f'{perspective}_enable_legacy_check', value=legacy_outputs):
        p_summaries = OutputFragment(params={'perspective': perspective, 'default': default_outputs.get('legacy_outputs', [])}).display()
        summaries_settings |= p_summaries

    if oed_fields:
        p_summaries = OEDGroupFragment(params={'perspective': perspective,
                                               'oed_fields': oed_fields,
                                               'default': default_outputs.get('oed_fields', [])}).display()
        summaries_settings |= p_summaries
    return summaries_settings


class ORDOutputFragment:
    '''
    Generate selectboxes to select ORD output settings.

    Args:
        perspective: perspective name (`gul`, `il`, `ri`)
        default : dictionary containing the default options.
    '''
    def __init__(self, perspective, default={}):
        self.perspective = perspective
        self.default = default

    def display(self):
        ord_options = {}
        perspective = self.perspective
        defaults = self.default

        def output_type_multiselect(label, options, prefix, key=None, default=None):
            selected_options = st.multiselect(label, options=options, key=key, default=default)

            output_dict = {}
            for opt in options:
                output_dict[f'{prefix}_{opt}'] = opt in selected_options
            return output_dict

        elt_plt_options = ['sample', 'quantile', 'moment']

        ord_options |= output_type_multiselect(label='Event Loss Table (ELT) Output', prefix='elt',
                                               options=elt_plt_options,
                                               default=defaults.get('elt', None),
                                               key=f'{perspective}_elt_multiselect')

        ord_options |= output_type_multiselect(label='Period Loss Table (ELT) Output', prefix='plt',
                                               options=elt_plt_options,
                                               default=defaults.get('plt', None),
                                               key=f'{perspective}_plt_multiselect')

        ord_options |= output_type_multiselect(label='Average Loss Table (ALT) Output', prefix='alt',
                                               options=['period', 'meanonly'],
                                               default=defaults.get('alt', None),
                                               key=f'{perspective}_alt_multiselect')

        alct_enabled = ord_options.get('alt_period', False)
        if alct_enabled:
            alct_container = st.container(border=True)
            alct_container.write('Average Loss Convergence Table (ALCT) Options')
            ord_options['alct_convergence'] = alct_container.checkbox('Generate Convergence Table',
                                                          key=f'{perspective}_alct_conv_check',
                                                          value=defaults.get('alct_convergence', False))
            ord_options['alct_confidence'] = alct_container.number_input('Confidence Level',
                                                             min_value=0.0, max_value=1.0,
                                                             key=f'{perspective}_alct_conf_numeric',
                                                             value=defaults.get('alct_confidence', 0.95))

        ept_output_options = [
            'full_uncertainty_aep',
            'full_uncertainty_oep',
            'mean_sample_aep',
            'mean_sample_oep',
            'per_sample_mean_aep',
            'per_sample_mean_oep'
        ]
        ord_options |= output_type_multiselect(label='Exceedance Probability Table (EPT) Output: ', prefix='ept',
                                               options=ept_output_options,
                                               default=defaults.get('ept', None),
                                               key=f'{perspective}_ept_multiselect')

        ord_options |= output_type_multiselect(label='Per Sample Exceedance Probability Table (PS EPT) Output:', prefix='psept',
                                               options=['aep', 'oep'],
                                               default=defaults.get('psep', None),
                                               key=f'{perspective}_psep_multiselect')

        return ord_options


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
                                 options, key=f'{perspective}_legacy_output_select',
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


class OEDGroupFragment(FormFragment):
    EXCLUDED_FIELDS = [ "BuildingTIV", "ContentsTIV", "OtherTIV", "BITIV", "OEDVersion" ]

    def display(self):
        perspective = self.params.get('perspective', 'gul')
        oed_options = self.params.get('oed_fields', None)
        defaults = self.params.get('default', [])
        if oed_options is None:
            oed_options = ['PortNumber', 'CountryCode', 'LocNumber']

        oed_options = sorted(filter(self.valid_field_filter, oed_options))

        oed_fields = st.multiselect(f"{perspective.upper()} OED grouping:",
                             oed_options,
                             default=defaults,
                             key=f'{id}_{perspective}_oed')

        output = {'oed_fields': oed_fields}

        return output

    @staticmethod
    def valid_field_filter(field):
        if field in OEDGroupFragment.EXCLUDED_FIELDS:
            return False
        return True


def clear_summaries_settings():
    """Remove summaries settings from session state.
    """
    perspectives = ['gul', 'il', 'ri']
    # Reset form if previously rendered
    for p in perspectives:
        setting_name = f'{p}_summaries'
        if setting_name in st.session_state:
            del st.session_state[setting_name]


def save_settings(initial_settings, selected_settings):
    perspectives = ['gul', 'il', 'ri']
    for p in perspectives:
        settings_name = f'{p}_summaries'

        # Remove default summaries
        if settings_name in initial_settings.keys():
            initial_settings.pop(settings_name)

        selected_settings[settings_name] = st.session_state[settings_name]

    settings = merge_settings(initial_settings, selected_settings)
    clear_summaries_settings() # Remove settings from session state
    st.write('Saving settings')
    st.session_state['created_analysis_settings'] = settings

def produce_analysis_settings(model, model_settings, oed_fields=None, initial_settings=None):
    '''
    Create a form to get user input for setting analysis settings.

    Parameters
    ----------
    model : dict
            Information about the model, particularly `model_id` and `supplier_id`.
    model_settings : dict
            Model settings dictionary for given model.
    oed_fields : list[str]
                 List of OED Fields to allow user to group by. If `None`,
                 attempt to infer the `oed_fields` from the `data_settings` in
                 `model_settings`.
    initial_settings : dict
            Analysis settings to initialise the form with.

    Returns
    -------
    dict : Dictionary of the new analysis settings.
    '''
    clear_summaries_settings() # Run this once prior to loading fragment
    create_analysis_settings_fragment(model, model_settings, oed_fields, initial_settings)


def consume_analysis_settings():
    if 'created_analysis_settings' in st.session_state:
        output = copy(st.session_state['created_analysis_settings'])
        del st.session_state['created_analysis_settings']
    else:
        output = None
    return output

@st.fragment
def create_analysis_settings_fragment(model, model_settings, oed_fields=None, initial_settings=None):
    perspectives = ['gul', 'il', 'ri']

    if oed_fields is None:
        oed_fields = model_settings.get('data_settings', {}).get('damage_group_fields', [])
        oed_fields.extend(model_settings.get('data_settings', {}).get('hazard_group_fields', []))
        oed_fields = list(set(oed_fields))

    if initial_settings is not None:
        analysis_settings = copy(initial_settings)
    else:
        analysis_settings = {
                    'model_settings': {},
                    'model_supplier_id': model["supplier_id"],
                    'model_name_id': model["model_id"],
                    'gul_output': True,
                    'gul_summaries': [],
        }


    form_container = st.container(border=True)
    with form_container:
        selected_settings = {}

        selected_settings |= ModelSettingsFragment(model_settings=model_settings).display()
        selected_settings |= NumberSamplesFragment(model_settings=model_settings,
                                                   analysis_settings=analysis_settings).display()
        default_perspectives = [p for p in perspectives if analysis_settings.get(f'{p}_output', False)]
        selected_settings |= PerspectivesFragment(model_settings=model_settings,
                                                  default=default_perspectives).display()

        p_tabs = st.tabs([p.upper() for p in perspectives])
        for p, tab in zip(perspectives, p_tabs):
            with tab:
                st.write(f'### {p.upper()} Output Settings')

                if f'{p}_summaries' not in st.session_state:
                    st.session_state[f'{p}_summaries'] = analysis_settings.get(f'{p}_summaries', [])
                summary_settings_fragment(oed_fields, p)

        if st.button('Save Settings', on_click=save_settings, args=[analysis_settings, selected_settings]):
            st.rerun()
