import plotly.express as px


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

    def get(self, summary_level, perspective, output_type):
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

        Returns
        -------
        plotly.Figure
        '''
        assert output_type in ['eltcalc'], 'Output type not supported'
        assert perspective in ['gul', 'il', 'ri'], 'Perspective not valid'

        fname = self._request_to_fname(summary_level, perspective, output_type)
        results = self.output_file_dict.get(fname)

        fig = getattr(self, f'generate_{output_type}')(results)
        return fig

    @staticmethod
    def _request_to_fname(summary_level, perspective, output_type):
        return f'{perspective}_S{summary_level}_{output_type}.csv'

    @staticmethod
    def generate_eltcalc(results):
        '''
        Create graphs from eltcalc results.
        '''
        cols = ['type', 'mean']
        vis = results[cols].groupby('type').mean()
        vis = vis.reset_index()
        vis['type'] = vis['type'].map({1: "Analytical", 2: "Sample"})

        return vis

    @staticmethod
    def generate_aalcalc(results):
        results['type'] = results['type'].map({1: "Analytical", 2 : "Sample"})
        fig = px.bar(results, x='type', y='mean')
        return fig

    @staticmethod
    def generate_leccalc(results):
        pass

    @staticmethod
    def generate_pltcalc(results):
        pass
