import base64
import io
import json
import tarfile
import zipfile

import numpy as np

from streamlit.testing.v1 import AppTest

from modules.client import tar_to_zip
from pages.components.common import analysis_progress
from pages.components.output import order_ep_calcs
from pages.components.results import level_label

APP = 'tests/fixtures/results_levels_app.py'


def _values(arr):
    '''Plotly figure arrays may be plain lists or base64 typed arrays.'''
    if isinstance(arr, dict) and 'bdata' in arr:
        return np.frombuffer(base64.b64decode(arr['bdata']), dtype=arr['dtype']).tolist()
    return list(arr)


def chart_losses(at):
    '''Loss values plotted in the first plotly chart.'''
    spec = json.loads(at.get('plotly_chart')[0].proto.spec)
    return sorted(y for trace in spec['data'] for y in _values(trace['y']))


def test_summary_level_selector():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception

    select = at.selectbox(key='results_level_gul')
    assert select.options == ['Level 1: portfolio total', 'Level 2: grouped by LocNumber']
    # Level 1, full uncertainty (EPCalc 2) shown by default
    assert chart_losses(at) == [101, 102]

    select.set_value(2).run()
    assert not at.exception
    assert chart_losses(at) == [201, 202]


def test_ep_defaults_to_full_uncertainty_then_meandr():
    at = AppTest.from_file(APP, default_timeout=30).run()
    calc = at.radio(key='ept_gul_calc_filter')
    assert calc.options == ['Full uncertainty', 'Mean damage ratio (MeanDR)']
    assert calc.value == 2

    calc.set_value(1).run()
    assert chart_losses(at) == [103, 104]


def test_ep_axis_is_linear():
    at = AppTest.from_file(APP, default_timeout=30).run()
    layout = json.loads(at.get('plotly_chart')[0].proto.spec)['layout']
    assert layout.get('xaxis', {}).get('type') != 'log'


def test_order_ep_calcs():
    assert order_ep_calcs([1, 3, 2, 4]) == [2, 1, 4, 3]
    assert order_ep_calcs([1]) == [1]


def test_level_label():
    assert level_label({'id': 3}) == 'Level 3: portfolio total'
    assert level_label({'id': 1, 'oed_fields': ['CountryCode', 'LocNumber']}) == \
        'Level 1: grouped by CountryCode, LocNumber'


def test_tar_to_zip_keeps_files_and_paths():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        for name, data in [('output/gul_S1_ept.csv', b'a\n1\n'), ('./output/il_S1_ept.csv', b'b\n')]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

    with zipfile.ZipFile(io.BytesIO(tar_to_zip(buf.getvalue()))) as zf:
        assert sorted(zf.namelist()) == ['output/gul_S1_ept.csv', 'output/il_S1_ept.csv']
        assert zf.read('output/gul_S1_ept.csv') == b'a\n1\n'


def test_progress_uses_events_while_running():
    running = {'status': 'RUN_STARTED', 'num_events_complete': 963, 'num_events_total': 1447,
               'status_count': {'COMPLETED': 2, 'TOTAL': 6}}
    fraction, text = analysis_progress(running)
    assert text == '963 of 1,447 events'
    assert round(fraction, 3) == round(963 / 1447, 3)


def test_progress_falls_back_to_tasks():
    queued = {'status': 'RUN_STARTED', 'num_events_complete': 0, 'num_events_total': 0,
              'status_count': {'COMPLETED': 1, 'TOTAL': 4}}
    assert analysis_progress(queued) == (0.25, '1 of 4 tasks')
    assert analysis_progress({'status': 'RUN_QUEUED'}) == (None, '')
