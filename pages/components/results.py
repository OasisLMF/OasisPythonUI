"""Render the outputs of a completed analysis, driven by its analysis settings."""
import re

import streamlit as st

from modules.schemas import PERSPECTIVE_LABELS, PERSPECTIVES
from modules.visualisation import OutputInterface
from pages.components.output import (generate_aalcalc_fragment, generate_alct_fragment,
                                     generate_alt_fragment, generate_eltcalc_fragment,
                                     generate_ept_fragment, generate_leccalc_fragment,
                                     generate_melt_fragment, generate_mplt_fragment,
                                     generate_pltcalc_fragment, generate_psept_fragment,
                                     generate_qelt_fragment, generate_qplt_fragment,
                                     generate_selt_fragment, generate_splt_fragment)

EPT_FLAGS = ['ept_full_uncertainty_aep', 'ept_full_uncertainty_oep',
             'ept_mean_sample_aep', 'ept_mean_sample_oep',
             'ept_per_sample_mean_aep', 'ept_per_sample_mean_oep']
PSEPT_FLAGS = ['psept_aep', 'psept_oep']


def _sections(summary, locations):
    """(title, render-callable) for each output enabled in a summary level."""
    ord_settings = summary.get('ord_output', {})
    sections = []

    def add(enabled, title, render, output_type=None):
        if enabled:
            sections.append((title, render, output_type))

    # ORD outputs
    add(ord_settings.get('elt_sample'), 'Sample event loss table (SELT)',
        lambda p, vis: generate_selt_fragment(p, vis, locations=locations), output_type='elt_sample')
    add(ord_settings.get('elt_moment'), 'Moment event loss table (MELT)',
        lambda p, vis: generate_melt_fragment(p, vis, locations=locations), output_type='elt_moment')
    add(ord_settings.get('elt_quantile'), 'Quantile event loss table (QELT)',
        lambda p, vis: generate_qelt_fragment(p, vis, locations=locations), output_type='elt_quantile')
    add(ord_settings.get('plt_sample'), 'Sample period loss table (SPLT)', generate_splt_fragment, output_type='plt_sample')
    add(ord_settings.get('plt_moment'), 'Moment period loss table (MPLT)', generate_mplt_fragment, output_type='plt_moment')
    add(ord_settings.get('plt_quantile'), 'Quantile period loss table (QPLT)', generate_qplt_fragment, output_type='plt_quantile')
    add(ord_settings.get('alt_meanonly'), 'Average loss table, mean only (ALT)',
        lambda p, vis: generate_alt_fragment(p, vis, 'alt_meanonly'), output_type='alt_meanonly')
    add(ord_settings.get('alt_period'), 'Period average loss table (PALT)',
        lambda p, vis: generate_alt_fragment(p, vis, 'alt_period'), output_type='alt_period')
    add(ord_settings.get('alct_convergence'), 'Average loss convergence table (ALCT)', generate_alct_fragment, output_type='alct_convergence')
    add(any(ord_settings.get(e) for e in EPT_FLAGS), 'Exceedance probability table (EPT)', generate_ept_fragment, output_type='ept')
    add(any(ord_settings.get(e) for e in PSEPT_FLAGS), 'Per-sample EPT (PSEPT)', generate_psept_fragment, output_type='psept')

    # Legacy ktools outputs
    add(summary.get('eltcalc'), 'ELT (legacy)',
        lambda p, vis: generate_eltcalc_fragment(p, vis, locations=locations, map=True), output_type='eltcalc')
    add(summary.get('aalcalc'), 'AAL (legacy)', generate_aalcalc_fragment, output_type='aalcalc')
    add(summary.get('lec_output'), 'Loss exceedance curve (legacy)',
        lambda p, vis: generate_leccalc_fragment(p, vis, summary.get('leccalc')), output_type=None)
    add(summary.get('pltcalc'), 'PLT (legacy)', generate_pltcalc_fragment, output_type='pltcalc')
    return sections


def render_results(settings, outputs, locations=None):
    """Visualise analysis outputs.

    Args:
        settings: the analysis settings used for the run.
        outputs: `{filename: DataFrame}` from the analysis output file.
        locations: optional location DataFrame used for maps.
    """
    if not outputs:
        st.info('No output files were found for this analysis.')
        return

    vis = OutputInterface(outputs)
    vis.number_of_samples = settings.get('number_of_samples')
    perspectives = [p for p in PERSPECTIVES if settings.get(f'{p}_output')]
    if not perspectives:
        st.info('No loss perspectives were enabled in the analysis settings.')
        return

    tabs = st.tabs([PERSPECTIVE_LABELS[p] for p in perspectives])
    for p, tab in zip(perspectives, tabs):
        with tab:
            levels = {lv['id']: lv for lv in settings.get(f'{p}_summaries') or [] if 'id' in lv}
            if not levels:
                st.info('No summary levels were configured for this perspective.')
                continue

            level_id = next(iter(levels))
            if len(levels) > 1:
                level_id = st.selectbox(
                    'Summary level', list(levels), format_func=lambda i: level_label(levels[i]),
                    key=f'results_level_{p}',
                    help='Each summary level groups losses differently. Choose which one to view.')
            else:
                st.caption(level_label(levels[level_id]))

            summary = levels[level_id]
            vis.set_summary_level(p, level_id)

            # Reinsurance outputs can be split by inuring priority (rl_IP1_S1_..., ri_S1_...)
            priorities = inuring_priorities(outputs, p, level_id)
            prefix = priorities[0] if priorities else ''
            if len(priorities) > 1:
                prefix = st.selectbox('Inuring priority', priorities, format_func=priority_label,
                                      key=f'results_priority_{p}_{level_id}')
            vis.set_file_prefix(p, prefix)

            oed_fields = summary.get('oed_fields') or None
            if oed_fields and not vis.fields_available(p, oed_fields, level_id):
                st.caption(f"Breakdown by {', '.join(oed_fields)} isn't available here: the run produced "
                           "no summary-info file for this perspective, so results are shown by SummaryId.")
                oed_fields = None
            vis.set_oed_fields(p, oed_fields)

            sections = _sections(summary, locations)
            if not sections:
                st.info('No outputs were selected for this summary level.')
            for i, (title, render, output_type) in enumerate(sections):
                with st.expander(title, expanded=i == 0):
                    # Check first: the views are fragments, which show their own errors
                    if output_type and not vis.has_output(p, output_type):
                        st.info('This output was requested in the settings but the run did not produce it.')
                    else:
                        render(p, vis)


def level_label(level):
    fields = level.get('oed_fields') or []
    if isinstance(fields, str):
        fields = [fields]
    grouping = f"grouped by {', '.join(fields)}" if fields else 'portfolio total'
    return f"Level {level['id']}: {grouping}"


def inuring_priorities(outputs, perspective, level_id):
    """File prefixes for the inuring priorities present, final ('') first.

    e.g. `['', 'IP1_']` for ri_S1_* and ri_IP1_S1_*, or `['IP1_']` for rl_IP1_S1_*.
    """
    pattern = re.compile(rf'^{perspective}_(IP\d+_)?S{level_id}_')
    found = {m.group(1) or '' for name in outputs if (m := pattern.match(name))}
    return sorted(found, key=lambda pre: (pre != '', int(pre[2:-1]) if pre else 0))


def priority_label(prefix):
    return 'Final' if not prefix else f'Inuring priority {prefix[2:-1]}'
