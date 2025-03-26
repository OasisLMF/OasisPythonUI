from oasis_data_manager.errors import OasisException
import plotly.express as px
import logging
import streamlit as st

logger = logging.getLogger(__name__)

TYPE_MAP = {
    1: 'Analytical',
    2: 'Sample'
}

class OutputInterface:
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
                      Currently supported legacy output types:
                      - `eltcalc`
                      - `aalcalc`
                      - `leccalc`
                      - `pltcalc`
                      Currently supported ORD output types:
                      - elt_sample, elt_quantile, elt_moment
                      - alt_meanonly, alt_period, alct_convergence
                      - ept (all ept outputs)
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
        supported_outputs = ['eltcalc', 'aalcalc', 'leccalc', 'pltcalc',
                             'elt_sample', 'elt_moment', 'elt_quantile',
                             'plt_sample', 'plt_moment', 'plt_quantile',
                             'alt_meanonly', 'alt_period', 'alct_convergence',
                             'ept'
                             ]
        assert output_type in supported_outputs, 'Output type not supported'
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

        result = getattr(self, f'generate_{output_type}')(results, **kwargs)
        return result

    @staticmethod
    def _request_to_fname(summary_level, perspective, output_type, **kwargs):
        if output_type[:4] in ['elt_', 'plt_']:
            output_type = output_type[4] + output_type[:3]

        alt_map = {
            'alt_meanonly': 'altmeanonly',
            'alt_period': 'palt'
        }

        if output_type[:4] == 'alt_':
            output_type = alt_map[output_type]

        if output_type[:4] == 'alct':
            output_type = 'alct'

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
        if 'summary_id' in results.columns:
            return results.join(summary_info, on='summary_id', rsuffix='_')

        return results.join(summary_info, on='SummaryId', rsuffix='_')

    @staticmethod
    def generate_eltcalc(results, **kwargs):
        results['type'] = results['type'].replace(TYPE_MAP)
        return results

    @staticmethod
    def generate_aalcalc(results, **kwargs):
        results['type'] = results['type'].replace(TYPE_MAP)
        return results

    @staticmethod
    def generate_leccalc(results, **kwargs):
        if 'type' in results.columns:
            results['type'] = results['type'].replace(TYPE_MAP)
        return results

    @staticmethod
    def generate_pltcalc(results, **kwargs):
        results['type'] = results['type'].replace(TYPE_MAP)
        return results

    @staticmethod
    def generate_elt_moment(results, **kwargs):
        results['SampleType'] = results['SampleType'].replace(TYPE_MAP)
        return results

    @staticmethod
    def generate_elt_quantile(results, **kwargs):
        return results

    @staticmethod
    def generate_elt_sample(results, **kwargs):
        return results

    @staticmethod
    def generate_plt_sample(results, **kwargs):
        return results

    @staticmethod
    def generate_plt_moment(results, **kwargs):
        results['SampleType'] = results['SampleType'].replace(TYPE_MAP)
        return results

    @staticmethod
    def generate_plt_quantile(results, **kwargs):
        return results

    @staticmethod
    def generate_alt_meanonly(results, **kwargs):
        results['SampleType'] = results['SampleType'].replace(TYPE_MAP)
        return results

    @staticmethod
    def generate_alt_period(results, **kwargs):
        results['SampleType'] = results['SampleType'].replace(TYPE_MAP)
        return results

    @staticmethod
    def generate_alct_convergence(results, **kwargs):
        return results

    @staticmethod
    def generate_ept(results, **kwargs):
        return results
