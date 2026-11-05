'''
Render the outputs of a completed analysis, driven by its analysis settings.
'''
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
    '''(title, render-callable) for each output enabled in a summary level.'''
    ord_settings = summary.get('ord_output', {})
    sections = []

    def add(enabled, title, render):
        if enabled:
            sections.append((title, render))

    # ORD outputs
    add(ord_settings.get('elt_sample'), 'Sample event loss table (SELT)',
        lambda p, vis: generate_selt_fragment(p, vis, locations=locations))
    add(ord_settings.get('elt_moment'), 'Moment event loss table (MELT)',
        lambda p, vis: generate_melt_fragment(p, vis, locations=locations))
    add(ord_settings.get('elt_quantile'), 'Quantile event loss table (QELT)',
        lambda p, vis: generate_qelt_fragment(p, vis, locations=locations))
    add(ord_settings.get('plt_sample'), 'Sample period loss table (SPLT)', generate_splt_fragment)
    add(ord_settings.get('plt_moment'), 'Moment period loss table (MPLT)', generate_mplt_fragment)
    add(ord_settings.get('plt_quantile'), 'Quantile period loss table (QPLT)', generate_qplt_fragment)
    add(ord_settings.get('alt_meanonly'), 'Average loss table, mean only (ALT)',
        lambda p, vis: generate_alt_fragment(p, vis, 'alt_meanonly'))
    add(ord_settings.get('alt_period'), 'Period average loss table (PALT)',
        lambda p, vis: generate_alt_fragment(p, vis, 'alt_period'))
    add(ord_settings.get('alct_convergence'), 'Average loss convergence table (ALCT)', generate_alct_fragment)
    add(any(ord_settings.get(e) for e in EPT_FLAGS), 'Exceedance probability table (EPT)', generate_ept_fragment)
    add(any(ord_settings.get(e) for e in PSEPT_FLAGS), 'Per-sample EPT (PSEPT)', generate_psept_fragment)

    # Legacy ktools outputs
    add(summary.get('eltcalc'), 'ELT (legacy)',
        lambda p, vis: generate_eltcalc_fragment(p, vis, locations=locations, map=True))
    add(summary.get('aalcalc'), 'AAL (legacy)', generate_aalcalc_fragment)
    add(summary.get('lec_output'), 'Loss exceedance curve (legacy)',
        lambda p, vis: generate_leccalc_fragment(p, vis, summary.get('leccalc')))
    add(summary.get('pltcalc'), 'PLT (legacy)', generate_pltcalc_fragment)
    return sections


def render_results(settings, outputs, locations=None):
    '''Visualise analysis outputs.

    Args:
        settings: the analysis settings used for the run.
        outputs: `{filename: DataFrame}` from the analysis output file.
        locations: optional location DataFrame used for maps.
    '''
    if not outputs:
        st.info('No output files were found for this analysis.')
        return

    vis = OutputInterface(outputs)
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
            vis.set_oed_fields(p, summary.get('oed_fields') or None)

            sections = _sections(summary, locations)
            if not sections:
                st.info('No outputs were selected for this summary level.')
            for i, (title, render) in enumerate(sections):
                with st.expander(title, expanded=i == 0):
                    render(p, vis)


def level_label(level):
    fields = level.get('oed_fields') or []
    if isinstance(fields, str):
        fields = [fields]
    grouping = f"grouped by {', '.join(fields)}" if fields else 'portfolio total'
    return f"Level {level['id']}: {grouping}"
