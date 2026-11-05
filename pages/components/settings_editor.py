'''
Schema-driven analysis settings editor.

Controls are generated from the ODS-tools analysis settings schema (general
options and output flags) and from the selected model's settings (run options
and model parameters). `analysis_settings_editor` returns the assembled
settings dict on every rerun; the caller decides when to save it.
'''
import json
from copy import deepcopy

import streamlit as st

from modules import schemas
from modules.schemas import (CATEGORICAL_MODEL_SETTINGS, DEFAULT_GROUP_FIELDS, DEFAULT_ORD_OUTPUTS,
                             ORD_OUTPUT_GROUPS, PARAMETER_TYPES, PERSPECTIVE_LABELS, PERSPECTIVES)


##########################################################################################
# Helpers
##########################################################################################

def _label(entry, fallback):
    return schemas.title(entry, fallback).rstrip('.')


def _parse_number_list(text, cast):
    '''Parse "10, 50, 100" into a list of numbers. Returns (values, error).'''
    if not text or not text.strip():
        return None, None
    try:
        return [cast(v) for v in text.replace(';', ',').split(',') if v.strip()], None
    except ValueError:
        return None, f'Could not read "{text}" as a comma separated list of numbers.'


def _list_text(values):
    return ', '.join(str(v) for v in values) if values else ''


def _events_text(event_ids, event_ranges):
    parts = [str(e) for e in event_ids or []]
    if event_ranges:
        parts += [r.strip() for r in str(event_ranges).split(',') if r.strip()]
    return ', '.join(parts)


def _parse_events(text):
    '''Parse "1, 5, 100-120" into (event_ids, event_ranges, error).

    Single ids go to `event_ids` and hyphenated ranges to `event_ranges`;
    oasislmf combines the two.
    '''
    if not text or not text.strip():
        return None, None, None
    ids, ranges = [], []
    for part in text.replace(';', ',').split(','):
        part = part.strip()
        if not part:
            continue
        try:
            if '-' in part:
                lo, hi = (int(v) for v in part.split('-', 1))
                if lo < 1 or hi < lo:
                    raise ValueError
                ranges.append(f'{lo}-{hi}')
            else:
                value = int(part)
                if value < 1:
                    raise ValueError
                ids.append(value)
        except ValueError:
            return None, None, f'Could not read "{part}" as an event id (a whole number from 1) or range like 100-120.'
    return ids or None, ','.join(ranges) or None, None


def selected_option(model_settings, setting, option_id):
    '''The option dict chosen for a categorical model setting (e.g. the event set), or {}.'''
    options = model_settings.get('model_settings', {}).get(setting, {}).get('options', [])
    return next((o for o in options if o.get('id') == option_id), {})


def valid_metrics(model_settings, event_set=None):
    '''Output metrics the model supports (None = no restriction).

    An event set's `valid_metrics` overrides the model's `valid_output_metrics`.
    '''
    return (event_set or {}).get('valid_metrics') or \
        model_settings.get('model_settings', {}).get('valid_output_metrics') or None


def metric_allowed(flag, metrics):
    '''Whether an ORD output flag is allowed by a `valid_metrics` list.

    Entries may name a flag exactly (`elt_sample`), a table family (`elt`,
    `plt`, `alt`, `ept`, `psept`), or a loss type (`aep`, `oep`).
    '''
    if not metrics:
        return True
    family = flag.split('_')[0]
    if flag.startswith('alct'):
        family = 'alt'
    loss_type = flag.rsplit('_', 1)[-1]
    return flag in metrics or family in metrics or (loss_type in ('aep', 'oep') and loss_type in metrics)


def default_ord_outputs(metrics=None):
    return {o: True for o in DEFAULT_ORD_OUTPUTS if metric_allowed(o, metrics)}


def perspective_availability(model_settings, portfolio, event_set=None):
    '''Which perspectives can be run, with a reason for those that can't.

    An event set's `valid_perspectives` overrides the model's `valid_output_perspectives`.
    '''
    valid = list((event_set or {}).get('valid_perspectives')
                 or model_settings.get('model_settings', {}).get('valid_output_perspectives') or PERSPECTIVES)
    # The model settings schema has no 'rl': ceded reinsurance follows 'ri'
    if 'ri' in valid and 'rl' not in valid:
        valid.append('rl')
    has = {f: bool((portfolio.get(f) or {}).get('stored')) for f in
           ['accounts_file', 'reinsurance_info_file', 'reinsurance_scope_file']}

    reasons = {}
    for p in PERSPECTIVES:
        if p not in valid:
            reasons[p] = ('Not supported by the selected event set.' if (event_set or {}).get('valid_perspectives')
                          else 'Not supported by this model.')
        elif p in ('il', 'ri', 'rl') and not has['accounts_file']:
            reasons[p] = 'The portfolio has no accounts file.'
        elif p in ('ri', 'rl') and not (has['reinsurance_info_file'] and has['reinsurance_scope_file']):
            reasons[p] = 'The portfolio has no reinsurance info and scope files.'
    return reasons


def default_settings(model, model_settings):
    '''Minimal starting settings for a model when no template is used.'''
    return {
        'model_supplier_id': model['supplier_id'],
        'model_name_id': model['model_id'],
        'number_of_samples': model_settings.get('model_default_samples',
                                                schemas.analysis_property('number_of_samples').get('default', 10)),
        'gul_output': True,
        'gul_summaries': [{'id': 1, 'ord_output': default_ord_outputs(valid_metrics(model_settings))}],
    }


def group_field_options(model_settings, extra=(), portfolio_fields=()):
    '''OED fields offered for grouping losses.

    Common grouping fields and those the model suggests come first, followed
    by every other column in the portfolio's OED files (alphabetically).
    '''
    data_settings = model_settings.get('data_settings', {})
    fields = list(DEFAULT_GROUP_FIELDS)
    for f in [*data_settings.get('damage_group_fields', []), *data_settings.get('hazard_group_fields', []),
              *model_settings.get('model_settings', {}).get('summary_report_fields', []), *extra,
              *sorted(portfolio_fields, key=str.lower)]:
        # OED field names are case-insensitive: keep the first spelling seen
        if f.lower() not in {x.lower() for x in fields}:
            fields.append(f)
    return fields


##########################################################################################
# Sections
##########################################################################################

def general_section(base, model_settings, key):
    out = {}
    errors = []

    entry = schemas.analysis_property('number_of_samples')
    default_samples = base.get('number_of_samples',
                               model_settings.get('model_default_samples', entry.get('default', 10)))
    left, _ = st.columns(2)
    out['number_of_samples'] = left.number_input(
        _label(entry, 'Number of samples'), min_value=entry.get('minimum', 0), step=1,
        value=int(default_samples), help=entry.get('description'), key=f'{key}_samples')

    with st.expander('Advanced'):
        entry = schemas.analysis_property('gul_threshold')
        out['gul_threshold'] = st.number_input(
            _label(entry, 'Ground-up loss threshold'), min_value=float(entry.get('minimum', 0)),
            value=float(base.get('gul_threshold', entry.get('default', 0))),
            help=entry.get('description'), key=f'{key}_gul_threshold')

        text = st.text_input(
            'Events', value=_events_text(base.get('event_ids'), base.get('event_ranges')),
            placeholder='e.g. 1, 5, 100-120',
            help='Run only these event ids. Use commas between ids and hyphens for ranges. '
                 'Leave blank to run every event in the event set.',
            key=f'{key}_events')
        event_ids, event_ranges, error = _parse_events(text)
        if error:
            errors.append(error)
        if event_ids:
            out['event_ids'] = event_ids
        if event_ranges:
            out['event_ranges'] = event_ranges

        entry = schemas.analysis_property('return_periods')
        text = st.text_input(_label(entry, 'Return periods'), value=_list_text(base.get('return_periods')),
                             placeholder='e.g. 10, 50, 100, 250, 500, 1000',
                             help=f"{entry.get('description', '')} Leave blank to use the model's defaults.",
                             key=f'{key}_return_periods')
        values, error = _parse_number_list(text, int)
        if error:
            errors.append(error)
        elif values:
            out['return_periods'] = values

        entry = schemas.analysis_property('quantiles')
        text = st.text_input(_label(entry, 'Quantiles'), value=_list_text(base.get('quantiles')),
                             placeholder='e.g. 0.05, 0.5, 0.95',
                             help=f"{entry.get('description', '')} Used by quantile (Q) outputs.",
                             key=f'{key}_quantiles')
        values, error = _parse_number_list(text, float)
        if error:
            errors.append(error)
        elif values:
            out['quantiles'] = values

        perils = model_settings.get('lookup_settings', {}).get('supported_perils', [])
        if perils:
            entry = schemas.analysis_property('peril_filter')
            peril_desc = {p['id']: p.get('desc', '') for p in perils}
            out['peril_filter'] = st.multiselect(
                _label(entry, 'Peril filter'), options=list(peril_desc),
                default=[p for p in base.get('peril_filter', []) if p in peril_desc],
                format_func=lambda p: f'{p} – {peril_desc[p]}' if peril_desc[p] else p,
                help=f"{entry.get('description', '')} Leave empty to include all perils.",
                key=f'{key}_peril_filter') or None

        entry = schemas.analysis_property('join_summary_info')
        out['join_summary_info'] = st.toggle(
            _label(entry, 'Join summary info'), value=bool(base.get('join_summary_info', True)),
            help=f"{entry.get('description', '')} Writes the group-by fields into each output file, "
                 "so results can be broken down without a separate summary-info lookup. On by default.",
            key=f'{key}_join_summary_info')

    return {k: v for k, v in out.items() if v is not None}, errors


def _parameter_control(param, kind, current, key):
    name = param['name']
    label = param.get('desc') or name
    help_text = param.get('tooltip') or (f'`{name}`' if param.get('desc') else None)
    disabled = param.get('editable') is False
    value = current.get(name, param.get('default'))
    wkey = f'{key}_param_{name}'

    if kind == 'bool':
        return st.toggle(label, value=bool(value), help=help_text, disabled=disabled, key=wkey), None
    if kind == 'float':
        lo, hi = float(param['min']), float(param['max'])
        step = float(param.get('stepsize') or (hi - lo) / 100 or 0.01)
        return st.slider(label, min_value=lo, max_value=hi, value=float(value), step=step,
                         help=help_text, disabled=disabled, key=wkey), None
    if kind == 'int':
        return st.number_input(label, value=int(value), step=1, help=help_text,
                               disabled=disabled, key=wkey), None
    if kind == 'number':
        return st.number_input(label, value=float(value), help=help_text,
                               disabled=disabled, key=wkey), None
    if kind == 'dropdown':
        options = param.get('options', [])
        ids = [o['id'] for o in options]
        descs = {o['id']: o.get('desc', '') for o in options}
        return st.selectbox(label, ids, index=ids.index(value) if value in ids else 0,
                            format_func=lambda i: f'{i} – {descs[i]}' if descs[i] else str(i),
                            help=help_text, disabled=disabled, key=wkey), None
    if kind in ('list', 'dict'):
        text = st.text_area(label, value=json.dumps(value), help=f"{help_text or ''} (JSON)".strip(),
                            disabled=disabled, key=wkey, height=68)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            return value, f'{label}: invalid JSON ({e.msg}).'
        expected = list if kind == 'list' else dict
        if not isinstance(parsed, expected):
            return value, f'{label}: expected a JSON {expected.__name__}.'
        return parsed, None
    return st.text_input(label, value='' if value is None else str(value), help=help_text,
                         disabled=disabled, key=wkey), None


def model_options_section(base, model_settings, key):
    ms = model_settings.get('model_settings', {})
    current = base.get('model_settings', {})
    out, errors = {}, []

    selectors = [k for k in CATEGORICAL_MODEL_SETTINGS if ms.get(k, {}).get('options')]
    if selectors:
        cols = st.columns(min(len(selectors), 2))
        for i, k in enumerate(selectors):
            option = ms[k]
            ids = [o['id'] for o in option['options']]
            descs = {o['id']: o.get('desc', '') for o in option['options']}
            default = current.get(k, option.get('default'))
            entry = schemas.model_settings_property(k)
            out[k] = cols[i % len(cols)].selectbox(
                option.get('name') or _label(entry, k), ids,
                index=ids.index(default) if default in ids else 0,
                format_func=lambda i, d=descs: f'{i} – {d[i]}' if d[i] else str(i),
                help=option.get('tooltip') or option.get('desc') or entry.get('description'),
                key=f'{key}_ms_{k}')

    params = {}
    for type_key, kind in PARAMETER_TYPES.items():
        for p in ms.get(type_key, []):
            if p.get('visible') is False:
                if p['name'] in current:
                    out[p['name']] = current[p['name']]
                continue
            params[p['name']] = (p, kind)

    groups = sorted(ms.get('parameter_groups', []), key=lambda g: g.get('priority_id', 0))
    rendered = set()

    def render(names):
        for n in names:
            p, kind = params[n]
            value, error = _parameter_control(p, kind, current, key)
            out[n] = value
            if error:
                errors.append(error)
            rendered.add(n)

    for g in groups:
        names = [n for n in g.get('presentation_order', []) if n in params and n not in rendered]
        if not names:
            continue
        title = g.get('desc') or g.get('name')
        if g.get('collapsible'):
            with st.expander(title, expanded=not g.get('default_collapsed', False)):
                render(names)
        else:
            st.markdown(f'**{title}**', help=g.get('tooltip'))
            render(names)

    rest = [n for n in params if n not in rendered]
    if rest:
        if rendered:
            st.markdown('**Other parameters**')
        render(rest)

    if not selectors and not params:
        st.caption('This model has no run options to set.')

    # Keep any model settings from the template that the model doesn't describe
    for k, v in current.items():
        out.setdefault(k, v)
    return out, errors


def _levels_state_key(key, scope):
    return f'{key}_levels_{scope}'


def _init_levels(key, scope, summaries, metrics=None):
    '''Track summary levels for `scope` ('all' or a perspective) in session state.'''
    state_key = _levels_state_key(key, scope)
    if state_key not in st.session_state:
        levels = [deepcopy(s) for s in (summaries or [])]
        if not levels:
            levels = [{'id': 1, 'ord_output': default_ord_outputs(metrics)}]
        st.session_state[state_key] = levels
    return st.session_state[state_key]


def summary_levels_editor(key, scope, summaries, field_options, metrics=None):
    '''Edit a list of summary levels (group-by fields + ORD outputs).

    `metrics` (from `valid_metrics`) disables outputs the model doesn't support.
    '''
    levels = _init_levels(key, scope, summaries, metrics)
    flags = schemas.ord_output_options()
    result = []

    for level in list(levels):
        lid = level['id']
        wkey = f'{key}_{scope}_{lid}'
        ord_output = level.get('ord_output', {})
        with st.container(border=True):
            head, remove = st.columns([0.85, 0.15], vertical_alignment='center')
            head.markdown(f'**Summary level {lid}**')
            if remove.button('Remove', key=f'{wkey}_remove', disabled=len(levels) == 1, width='stretch'):
                levels.remove(level)
                st.rerun()

            existing = level.get('oed_fields') or []
            if isinstance(existing, str):
                existing = [existing]
            fields = st.multiselect(
                'Group losses by', options=list(dict.fromkeys([*field_options, *existing])),
                default=existing, placeholder='Portfolio total (no grouping)',
                help='OED fields to break losses down by. Leave empty for a single portfolio-level total.',
                key=f'{wkey}_fields')

            selected = []
            cols = st.columns(len(ORD_OUTPUT_GROUPS))
            for col, (group, keys) in zip(cols, ORD_OUTPUT_GROUPS.items()):
                with col:
                    st.markdown(f'<small>**{group}**</small>', unsafe_allow_html=True)
                    for k in keys:
                        unsupported = not metric_allowed(k, metrics)
                        # oasislmf only writes the ALCT alongside the period ALT (PALT)
                        needs_palt = k == 'alct_convergence' and 'alt_period' not in selected
                        blocked = unsupported or needs_palt
                        help_text = flags[k][1] + (' Not supported by this model.' if unsupported else
                                                   ' Requires PALT.' if needs_palt else '')
                        if col.checkbox(flags[k][0], value=bool(ord_output.get(k)) and not blocked,
                                        help=help_text, disabled=blocked, key=f'{wkey}_{k}') \
                                and not blocked:
                            selected.append(k)

            new_level = {k: v for k, v in level.items() if k not in ('ord_output', 'oed_fields')}
            new_ord = {k: v for k, v in ord_output.items() if k not in flags}
            new_ord.update({k: True for k in selected})
            if 'alct_convergence' in selected:
                new_ord['alct_confidence'] = st.number_input(
                    'ALCT confidence level', min_value=0.0, max_value=1.0,
                    value=float(ord_output.get('alct_confidence', 0.95)), key=f'{wkey}_alct_conf')
            new_level['ord_output'] = new_ord
            if fields:
                new_level['oed_fields'] = fields

            legacy = [k for k in ['eltcalc', 'aalcalc', 'aalcalcmeanonly', 'pltcalc', 'summarycalc', 'lec_output']
                      if level.get(k)]
            if legacy:
                st.caption(f"Also keeps legacy ktools outputs from the template: {', '.join(legacy)}")
            if not selected and not legacy:
                st.caption(':orange[No outputs selected for this level.]')
            result.append(new_level)

    if st.button('Add summary level', icon=':material/add:', key=f'{key}_{scope}_add'):
        next_id = max([lv['id'] for lv in levels] + [0]) + 1
        levels.append({'id': next_id, 'ord_output': default_ord_outputs(metrics)})
        st.rerun()

    return result


def outputs_section(base, model_settings, portfolio, key, portfolio_fields=(), event_set=None):
    out, errors = {}, []
    unavailable = perspective_availability(model_settings, portfolio, event_set)
    metrics = valid_metrics(model_settings, event_set)
    if metrics:
        st.caption(f"This model {'event set ' if (event_set or {}).get('valid_metrics') else ''}"
                   f"supports these outputs only: {', '.join(metrics)}.")

    st.markdown('**Loss perspectives**')
    cols = st.columns(len(PERSPECTIVES))
    enabled = []
    for col, p in zip(cols, PERSPECTIVES):
        reason = unavailable.get(p)
        default = bool(base.get(f'{p}_output', p == 'gul')) and not reason
        if col.checkbox(PERSPECTIVE_LABELS[p], value=default, disabled=bool(reason),
                        help=reason or schemas.analysis_property(f'{p}_output').get('description'),
                        key=f'{key}_{p}_output'):
            enabled.append(p)
        out[f'{p}_output'] = p in enabled

    if not enabled:
        errors.append('Select at least one loss perspective.')
        return out, errors

    existing = {p: base.get(f'{p}_summaries') for p in PERSPECTIVES}
    first = next((existing[p] for p in PERSPECTIVES if existing[p]), None)
    same_default = all(existing[p] in (None, first) for p in PERSPECTIVES)
    extra_fields = [f for s in (first or []) for f in (s.get('oed_fields') or [])]
    field_options = group_field_options(model_settings, extra_fields, portfolio_fields)

    same = st.toggle('Use the same outputs for every perspective', value=same_default,
                     key=f'{key}_same_outputs')
    if same:
        levels = summary_levels_editor(key, 'all', first, field_options, metrics)
        for p in enabled:
            out[f'{p}_summaries'] = deepcopy(levels)
    else:
        tabs = st.tabs([PERSPECTIVE_LABELS[p] for p in enabled])
        for p, tab in zip(enabled, tabs):
            with tab:
                out[f'{p}_summaries'] = summary_levels_editor(key, p, existing[p] or first, field_options, metrics)

    with st.expander('Advanced output options'):
        flag = (schemas.analysis_settings_schema()['definitions']['output_summaries']['items']
                ['properties']['ord_output']['properties']['parquet_format'])
        parquet = st.toggle(_label(flag, 'Parquet output'), help=flag.get('description'),
                            value=any(s.get('ord_output', {}).get('parquet_format')
                                      for s in (first or [])), key=f'{key}_parquet')
    for p in enabled:
        for level in out[f'{p}_summaries']:
            level['ord_output']['parquet_format'] = parquet
    return out, errors


##########################################################################################
# Editor
##########################################################################################

def analysis_settings_editor(model, model_settings, portfolio, base_settings, key, portfolio_fields=()):
    '''Render the editor and return `(settings, valid, problems)`.

    Args:
        model: model record from the API.
        model_settings: the model's settings (may be `{}`).
        portfolio: portfolio record, used to decide which perspectives are possible.
        base_settings: settings to start from (template / existing settings).
        key: unique widget key prefix. Change it to reset the editor.
        portfolio_fields: columns in the portfolio's OED files, offered for grouping.
    '''
    base = deepcopy(base_settings) if base_settings else default_settings(model, model_settings)

    general_tab, model_tab, outputs_tab, review_tab = st.tabs(
        ['General', 'Model options', 'Outputs', 'Review'])

    with general_tab:
        general, general_errors = general_section(base, model_settings, key)
    with model_tab:
        ms, ms_errors = model_options_section(base, model_settings, key)
    with outputs_tab:
        event_set = selected_option(model_settings, 'event_set', ms.get('event_set'))
        outputs, output_errors = outputs_section(base, model_settings, portfolio, key, portfolio_fields, event_set)

    # Start from the template so keys the editor doesn't manage are kept
    settings = {k: v for k, v in base.items()
                if k not in ('return_periods', 'quantiles', 'peril_filter', 'model_settings',
                             'event_ids', 'event_ranges')
                and not any(k.startswith(f'{p}_') for p in PERSPECTIVES)}
    settings.update(general)
    settings['model_supplier_id'] = model['supplier_id']
    settings['model_name_id'] = model['model_id']
    settings['model_settings'] = ms
    settings.update(outputs)

    problems = general_errors + ms_errors + output_errors
    if not problems:
        valid, messages = schemas.validate_analysis_settings(settings)
        problems += [f'{field}: {"; ".join(msgs)}' for field, msgs in messages.items()]

    with review_tab:
        if problems:
            st.error('These settings need attention before they can be used:\n\n' +
                     '\n'.join(f'- {p}' for p in problems))
        else:
            st.success('Settings are valid.')
        st.json(settings, expanded=3)
        st.download_button('Download analysis_settings.json', json.dumps(settings, indent=2),
                           file_name='analysis_settings.json', key=f'{key}_download')

    return settings, not problems, problems


def reset_editor(key):
    '''Clear editor state stored under `key` (e.g. after saving).'''
    for k in [k for k in st.session_state if str(k).startswith(f'{key}_')]:
        del st.session_state[k]
