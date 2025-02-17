from oasis_data_manager.errors import OasisException
import plotly.express as px
import logging

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

    def get(self, summary_level, perspective, output_type, opts={}):
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
        opts : dict
               Additional options depending on `output_type`.
               For `leccalc`the following keys and options are expected:
                   `opts`: {`analysis_type`: `full_uncertainty`, `sample_mean`, `wheatsheaf`, `wheatsheaf_mean`
                            `loss_type`: `aep`, `oep`
                           }

        Returns
        -------
        plotly.Figure
        '''
        assert output_type in ['eltcalc', 'aalcalc', 'leccalc'], 'Output type not supported'
        assert perspective in ['gul', 'il', 'ri'], 'Perspective not valid'

        if output_type == "leccalc":
            assert opts.get("analysis_type") in ["full_uncertainty", "sample_mean", "wheatsheaf", "wheatsheaf_mean"], "Analysis type not supported."
            assert opts.get("loss_type") in ["aep", "oep"], "Loss type not supported."


        fname = self._request_to_fname(summary_level, perspective, output_type,
                                           opts=opts)
        results = self.output_file_dict.get(fname)
        if results is None:
            logger.error(f'Failed to find output file: {fname}')
            raise OasisException('Output file not found.')

        fig = getattr(self, f'generate_{output_type}')(results, opts=opts)
        return fig


    @staticmethod
    def _request_to_fname(summary_level, perspective, output_type, opts={}):
        fname = f'{perspective}_S{summary_level}_{output_type}'
        if output_type == 'leccalc':
            fname += f'_{opts.get("analysis_type")}_{opts.get("loss_type")}'
        fname += '.csv'
        return fname

    @staticmethod
    def generate_eltcalc(results, opts={}):
        '''
        Create graphs from eltcalc results.
        '''
        cols = ['type', 'mean']
        vis = results[cols].groupby('type').mean()
        vis = vis.reset_index()
        vis['type'] = vis['type'].replace(TYPE_MAP)

        return vis

    @staticmethod
    def generate_aalcalc(results, opts={}):
        results['type'] = results['type'].replace(TYPE_MAP)
        fig = px.bar(results, x='type', y='mean', labels={'type': 'Type', 'mean': 'Average Annual Loss'})
        return fig

    @staticmethod
    def generate_leccalc(results, opts={}):
        results['type'] = results['type'].replace(TYPE_MAP)
        title = ''
        if opts:
            a_type = opts['analysis_type'].replace('_', ' ').title()
            o_type = opts['loss_type'].upper()
            title = f'{a_type} {o_type}'
        fig = px.line(results, x='return_period', y='loss', color='type', markers=False, log_x=True,
                      labels={'loss': 'Loss', 'return_period': 'Return Period', 'type': 'Type'}, title=title)


        return fig

    @staticmethod
    def generate_pltcalc(results, opts={}):
        pass
