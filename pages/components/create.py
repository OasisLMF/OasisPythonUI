# Module to display ui components for running analyses
import streamlit as st
from modules.settings import get_analyses_settings
from modules.validation import NameValidation, NotNoneValidation, ValidationError, ValidationGroup

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
                             index=selected_port, format_func=format_model)

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

def create_analysis_settings(model, model_settings):
    # Load default todo
    default = get_analyses_settings(model_name_id=model["model_id"], supplier_id=model["supplier_id"])

    if default:
        analysis_settings = default[0]
    else:
        analysis_settings = {
                    'model_settings': {},
                    'model_supplier_id': model["model_supplier_id"],
                    'model_name_id': model["model_name_id"]
        }

    with st.form("create_analysis_settings_form", enter_to_submit=False, clear_on_submit=True):
        # Handle categorical settings
        valid_settings = [
            'event_set',
            'event_occurrence_id',
            'footprint_set',
            'vulnerability_set',
            'pla_loss_factor_set',
        ]

        def format_option(opt):
            return f'{opt["id"]} : {opt["desc"]}'

        def get_default_index(options, default=None):
            if default is None:
                return None
            return [i for i in range(len(options)) if options[i]['id'] == default][0]

        for k, v in model_settings["model_settings"].items():
            if k in valid_settings:
                default = v.get('default', None)
                options = v['options']
                default_index = get_default_index(options, default)
                selected = st.selectbox(f"Set {v['name']}", options=v['options'], format_func=format_option, index=default_index)
                analysis_settings['model_settings'][k] = selected["id"]

        # Select perspectives
        valid_outputs = ['gul', 'il', 'ri']
        if "valid_output_perspectives" in model_settings["model_settings"]:
            valid_outputs = model_settings["model_settings"]["valid_output_perspectives"]

        opt_cols = st.columns(5)
        with opt_cols[0]:
            gul_opt = st.checkbox("GUL", help="Ground up loss", value=True, disabled=("gul" not in valid_outputs))
            analysis_settings["gul_output"] = gul_opt
        with opt_cols[1]:
            il_opt = st.checkbox("IL", help="Insured loss", disabled=("il" not in valid_outputs))
            analysis_settings["il_output"] = il_opt
        with opt_cols[2]:
            ri_opt = st.checkbox("RI", help="Reinsurance net loss", disabled=("ri" not in valid_outputs))
            analysis_settings["ri_otuput"] = ri_opt

        # Set number of sampled
        default_samples = model_settings["model_settings"].get("model_default_samples", 10)
        default_samples = analysis_settings.get("number_of_samples", default_samples)
        analysis_settings["number_of_samples"] = st.number_input("Number of samples",
                                                                 min_value = 1,
                                                                 value = default_samples)

        submitted = st.form_submit_button("Submit")

    if submitted:
        return analysis_settings

    return None
