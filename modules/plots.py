import plotly.graph_objects as go


class OutputPlotInterface:
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

        fig = getattr(self, f'generate_{output_type}_fig')(results)
        return fig

    @staticmethod
    def _request_to_fname(summary_level, perspective, output_type):
        return f'{perspective}_S{summary_level}_{output_type}.csv'

    @staticmethod
    def generate_eltcalc_fig(results):
        '''
        Create graphs from eltcalc results.
        '''
        cols = ['type', 'event_id', 'mean']
        results = results[cols]
        analytical_results = results.loc[results['type'] == 1]
        sample_results = results.loc[results['type'] == 2]

        analytical_results["cum_mean"] = analytical_results['mean'].cumsum()
        sample_results["cum_mean"] = sample_results['mean'].cumsum()

        fig = go.Figure()
        fig.add_trace(go.Scatter(name="Analytical", x=analytical_results["event_id"], y=analytical_results["cum_mean"]))
        fig.add_trace(go.Scatter(name="Sample", x=sample_results["event_id"], y=sample_results["cum_mean"]))
        fig.update_xaxes(title_text = 'Return Period')
        fig.update_yaxes(title_text = 'Cumulative Loss')


        return fig

    @staticmethod
    def generate_aalcalc_fig(results):
        pass

    @staticmethod
    def generate_leccalc_fig(results):
        pass

    @staticmethod
    def generate_pltcalc_fig(results):
        pass
