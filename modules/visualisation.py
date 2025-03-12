from oasis_data_manager.errors import OasisException
import plotly.express as px
import logging
import streamlit as st

logger = logging.getLogger(__name__)

TYPE_MAP = {
    1: 'Analytical',
    2: 'Sample'
}

class OutputVisualisationInterface:
    def __init__(self, output_file_dict):
        '''
        Parameters
        ----------
        output_file_dict : dict
                           Dictionary of output files as pd.DataFrames with the
                           key as the output file name.
        '''
        self.output_file_dict = output_file_dict
        self.oed_fields = {}

    def set_oed_fields(self, perspective, oed_fields):
        self.oed_fields[perspective] = oed_fields

    def get(self, summary_level, perspective, output_type, **kwargs):
        '''
        Generate graph from the output file.

        Parameters
        ----------
        summary_level : int
        perspective : str
                      One of the following
                      - `gul` : ground up loss
                      - `il` : insured loss
                      - `ri` : losses net of reinsurance
        output_type : str
                      Output type requested in the analysis settings.
                      Currently supported output types:
                      - `eltcalc`
                      - `aalcalc`
                      - `leccalc`
                      - `pltcalc`
        **kwargs : Additional options `output_type`.
                   For `leccalc`the following keys and options are expected:
                       `analysis_type`: `full_uncertainty`, `sample_mean`, `wheatsheaf`, `wheatsheaf_mean`
                       `loss_type`: `aep`, `oep`

                   For `eltcalc` the following optional arguments are accepted:
                        `group_fields`: Columns to group by. By default `type` will be first groupby column.

        Returns
        -------
        plotly.Figure
        '''
        assert output_type in ['eltcalc', 'aalcalc', 'leccalc', 'pltcalc'], 'Output type not supported'
        assert perspective in ['gul', 'il', 'ri'], 'Perspective not valid'

        if output_type == "leccalc":
            assert kwargs.get("analysis_type") in ["full_uncertainty", "sample_mean", "wheatsheaf", "wheatsheaf_mean"], "Analysis type not supported."
            assert kwargs.get("loss_type") in ["aep", "oep"], "Loss type not supported."

        fname = self._request_to_fname(summary_level, perspective, output_type,
                                           **kwargs)
        results = self.output_file_dict.get(fname)
        if results is None:
            logger.error(f'Failed to find output file: {fname}')
            raise OasisException('Output file not found.')

        oed_fields = self.oed_fields.get(perspective, None)
        if oed_fields:
            summary_info = self.output_file_dict.get(self._request_to_summary_info_fname(summary_level, perspective))
            results = self.add_oed_fields(results, summary_info, oed_fields)
            kwargs['oed_fields'] = oed_fields

        fig = getattr(self, f'generate_{output_type}')(results, **kwargs)
        return fig

    @staticmethod
    def _request_to_fname(summary_level, perspective, output_type, **kwargs):
        fname = f'{perspective}_S{summary_level}_{output_type}'
        if output_type == 'leccalc':
            fname += f'_{kwargs.get("analysis_type")}_{kwargs.get("loss_type")}'
        fname += '.csv'
        return fname

    @staticmethod
    def _request_to_summary_info_fname(summary_level, perspective):
        return f'{perspective}_S{summary_level}_summary-info.csv'

    @staticmethod
    def add_oed_fields(results, summary_info, oed_fields):
        summary_info = summary_info.set_index('summary_id')
        summary_info = summary_info[oed_fields]
        return results.join(summary_info, on='summary_id', rsuffix='_')

    @staticmethod
    def generate_eltcalc(results, categorical_cols=[], **kwargs):
        '''
        Create graphs from eltcalc results.
        '''
        cols = kwargs.get('columns', ['type'])
        cols += kwargs.get('oed_fields', [])
        cols += ['mean']

        filter_type = kwargs.get('filter_type', None)

        if filter_type:
            assert filter_type in TYPE_MAP.keys(), 'filter_type is not valid.'
            results = results[results['type'] == filter_type]

        group_fields = kwargs.get('group_fields', [])
        if group_fields:
            if 'type' not in group_fields:
                group_fields = ['type'] + group_fields

            ungrouped_cols = results.columns.difference(group_fields)
            numeric_cols = results.select_dtypes(include='number').columns
            numeric_cols = numeric_cols.difference(categorical_cols)
            numeric_cols = numeric_cols.intersection(ungrouped_cols)
            non_numeric_cols = ungrouped_cols.difference(numeric_cols)

            agg_dict = {}
            for c in numeric_cols:
                agg_dict[c] = 'sum'
            for c in non_numeric_cols:
                agg_dict[c] = 'unique'

            @st.cache_data(show_spinner=False, max_entries=1000)
            def eltcalc_transform(results, group_fields, agg_dict):
                return results.groupby(group_fields, as_index=False).agg(agg_dict)

            results = eltcalc_transform(results, group_fields, agg_dict)

        vis = results[cols]
        vis.loc[:, 'type'] = vis['type'].replace(TYPE_MAP)

        return vis

    @staticmethod
    def generate_aalcalc(results, **kwargs):
        results['type'] = results['type'].replace(TYPE_MAP)
        return results

    @staticmethod
    def generate_leccalc(results, **kwargs):
        results['type'] = results['type'].replace(TYPE_MAP)
        title = ''
        if kwargs.get('analysis_type'):
            a_type = kwargs['analysis_type'].replace('_', ' ').title()
            o_type = kwargs['loss_type'].upper()
            title = f'{a_type} {o_type}'
        fig = px.line(results, x='return_period', y='loss', color='type', markers=False, log_x=True,
                      labels={'loss': 'Loss', 'return_period': 'Return Period', 'type': 'Type'}, title=title)


        return fig

    @staticmethod
    def generate_pltcalc(results, **kwargs):
        results['type'] = results['type'].replace(TYPE_MAP)

        fig = px.scatter(results, x='period_no', y='mean', color='type', marginal_y='histogram',
                         labels = {'period_no': 'Period No.',
                                   'mean': 'Mean Loss',
                                   'type': 'Type'
                                  })
        return fig
