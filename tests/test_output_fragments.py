'''
AppTest-based coverage for the ORD render fragments in
`pages/components/output.py`. Each fragment is exercised via a small
standalone script under `tests/fixtures/` (rather than the full
app/login stack), built around a synthetic output DataFrame using the
PascalCase column names the fragments assume ktools produces (see
`OutputInterface`'s docstring and the "Important caveat" in the
project's ORD visualisation plan: there are no sample ktools output
fixtures checked into this repo, so these assumptions are not yet
validated against a real analysis run).
'''
import base64
import json
import struct

from streamlit.testing.v1 import AppTest

# Plotly figures rendered via `AppTest` encode numeric trace arrays as
# base64 binary rather than plain JSON lists, tagged with a dtype code.
# This decodes them so a test can assert on exact chart values.
_DTYPE_STRUCT_CODES = {
    'i1': 'b', 'i2': 'h', 'i4': 'i', 'i8': 'q',
    'u1': 'B', 'u2': 'H', 'u4': 'I', 'u8': 'Q',
    'f4': 'f', 'f8': 'd',
}


def _decode_plotly_array(value):
    if isinstance(value, dict) and 'bdata' in value:
        raw = base64.b64decode(value['bdata'])
        code = _DTYPE_STRUCT_CODES[value['dtype']]
        count = len(raw) // struct.calcsize(code)
        return list(struct.unpack(f'<{count}{code}', raw))
    return value


def _plotly_spec(chart_element):
    return json.loads(chart_element.proto.spec)


def test_selt_fragment_renders_table_and_map():
    at = AppTest.from_file("tests/fixtures/selt_fragment_app.py").run()

    assert len(at.exception) == 0
    assert [t.label for t in at.tabs] == ["Table", "Map"]
    assert len(at.dataframe) == 1
    assert len(at.get("plotly_chart")) == 1


SAMPLE_OPTIONS = ["Mean of samples", "Analytical mean (sidx -1)", "Sample 1", "Sample 2"]


def test_selt_fragment_mean_of_samples_and_analytical_mean():
    '''
    SELT's SampleId column uses ORD's reserved "sidx" values: -1 is the
    model's analytically integrated mean, which is not the mean of the
    sampled losses. The default view is the true mean of the samples; the
    analytical mean is offered separately and labelled as such. The
    fixture's -1 rows are deliberately not the average of their samples.
    '''
    at = AppTest.from_file("tests/fixtures/selt_fragment_app.py").run()

    assert len(at.exception) == 0
    select = at.selectbox(key="selt_gul_sample_filter")
    assert select.options == SAMPLE_OPTIONS
    assert select.value == "Mean of samples"
    # sorted descending by Loss: averages of the two samples
    assert list(at.dataframe[0].value["Loss"]) == [200.0, 100.0, 30.0, 20.0]

    select.set_value("Analytical mean (sidx -1)").run()
    assert list(at.dataframe[0].value["Loss"]) == [150.0, 90.0, 25.0, 15.0]

    select.set_value(2).run()
    assert list(at.dataframe[0].value["Loss"]) == [300.0, 150.0, 40.0, 30.0]


def test_sample_mean_counts_samples_without_rows():
    '''Samples with zero loss have no row, so divide by the number of samples.'''
    import pandas as pd
    from pages.components.output import sample_mean

    df = pd.DataFrame({'EventId': [1, 1, 1], 'SummaryId': [1, 1, 1],
                       'SampleId': [-1, 1, 3], 'Loss': [5.0, 10.0, 20.0]})
    result = sample_mean(df, n_samples=4)
    assert list(result['Loss']) == [7.5]  # (10 + 20 + 0 + 0) / 4
    assert list(result.columns) == ['EventId', 'SummaryId', 'SampleId', 'Loss']


def test_splt_fragment_renders_bar_chart():
    at = AppTest.from_file("tests/fixtures/splt_fragment_app.py").run()

    assert len(at.exception) == 0
    assert len(at.get("plotly_chart")) == 1


def test_splt_fragment_mean_of_samples_and_analytical_mean():
    '''
    As for SELT: the default view averages the samples, and ORD's -1
    analytical mean is a separate option. `pltcalc_bar` sums across
    SummaryId per date: sample means give 15+20=35 and 6.5+7.5=14; the
    fixture's -1 rows give 12+17=29 and 6+7=13.
    '''
    at = AppTest.from_file("tests/fixtures/splt_fragment_app.py").run()

    assert len(at.exception) == 0
    select = at.selectbox(key="splt_gul_sample_filter")
    assert select.options == SAMPLE_OPTIONS
    assert select.value == "Mean of samples"

    def losses():
        spec = _plotly_spec(at.get("plotly_chart")[0])
        return sorted(v for trace in spec['data'] for v in _decode_plotly_array(trace.get('y')))

    assert losses() == [14.0, 35.0]

    # Fresh run with the choice preset: AppTest can't rerun this fragment
    # interactively while its (unselected) single-select pills are present.
    at = AppTest.from_file("tests/fixtures/splt_fragment_app.py")
    at.session_state["splt_gul_sample_filter"] = "Analytical mean (sidx -1)"
    at.run()
    assert losses() == [13.0, 29.0]


def test_alct_fragment_renders_convergence_chart_and_table():
    at = AppTest.from_file("tests/fixtures/alct_fragment_app.py").run()

    assert len(at.exception) == 0
    # One confidence band and one mean line per summary id
    spec = _plotly_spec(at.get("plotly_chart")[0])
    assert len(spec['data']) == 4
    assert spec['layout']['xaxis']['title']['text'] == 'Number of samples'
    table = at.dataframe[0].value
    assert set(table["SummaryId"]) == {"1", "2"}
    assert list(table.columns) == ['SummaryId', 'SampleSize', 'MeanLoss', 'LowerCI', 'UpperCI',
                                   'StandardError', 'RelativeError']


def test_palt_breakdown_by_numeric_field_labels_each_bar():
    '''
    A numeric OED field such as PiWind's LocNumber gets one labelled bar
    per value, in numeric order, rather than a continuous axis.
    '''
    at = AppTest.from_file("tests/fixtures/palt_fragment_app.py")
    at.session_state["alt_period_gul_oed_filter"] = "LocNumber"
    at.run()

    assert len(at.exception) == 0
    spec = _plotly_spec(at.get("plotly_chart")[0])
    assert spec['layout']['xaxis']['type'] == 'category'
    assert [x for trace in spec['data'] for x in trace['x']] == ['1', '2', '10']


def test_psept_fragment_renders_ep_curve():
    at = AppTest.from_file("tests/fixtures/psept_fragment_app.py").run()

    assert len(at.exception) == 0
    assert len(at.get("plotly_chart")) == 1


def test_psept_fragment_excludes_special_sidx_rows_from_sample_stats():
    '''
    Regression test: `generate_psept_fragment`'s min/mean/max error-bar
    stats are meant to be computed across real Monte Carlo samples
    only, but previously never excluded ORD's reserved negative
    SampleId ("sidx") rows first - so ktools' -1 (analytically
    integrated mean) row would get silently averaged in alongside the
    real samples as if it were just another one of them. The fixture's
    -1 rows are huge outliers (999/9999), so this fails if they leak
    into the plotted mean/min/max.
    '''
    at = AppTest.from_file("tests/fixtures/psept_fragment_app.py").run()

    assert len(at.exception) == 0

    spec = _plotly_spec(at.get("plotly_chart")[0])
    traces_by_name = {trace.get('name'): trace for trace in spec['data']}
    assert set(traces_by_name) == {'1', '2'}

    trace_1 = traces_by_name['1']
    assert _decode_plotly_array(trace_1['x']) == [10, 100]
    assert _decode_plotly_array(trace_1['y']) == [55.0, 550.0]
    assert _decode_plotly_array(trace_1['error_y']['array']) == [5.0, 50.0]
    assert _decode_plotly_array(trace_1['error_y']['arrayminus']) == [5.0, 50.0]

    trace_2 = traces_by_name['2']
    assert _decode_plotly_array(trace_2['x']) == [10, 100]
    assert _decode_plotly_array(trace_2['y']) == [42.5, 425.0]
    assert _decode_plotly_array(trace_2['error_y']['array']) == [2.5, 25.0]
    assert _decode_plotly_array(trace_2['error_y']['arrayminus']) == [2.5, 25.0]


def test_qplt_and_ept_fragments_coexist_without_widget_key_collision():
    '''
    Regression test: `generate_ept_fragment` used to reuse
    `generate_qplt_fragment`'s OED-field pills key
    (`qplt_{p}_group_field_pills`) and had no key at all on its EP
    Curve Type / Calculation Method radios, so rendering both QPLT and
    EPT for the same perspective raised a Streamlit
    duplicate-widget-key error.
    '''
    at = AppTest.from_file("tests/fixtures/qplt_ept_regression_app.py").run()

    assert len(at.exception) == 0
    assert len(at.get("plotly_chart")) == 2


def test_eltcalc_map_heatmap_survives_locnumber_dtype_mismatch():
    '''
    Regression test: `eltcalc_map`'s heatmap branch merged the ORD
    output's `LocNumber` (joined in from the ktools summary-info file)
    against the location file's `LocNumber` without normalising
    either side's dtype first. A str-vs-int mismatch between the two
    (same values, different dtype) used to merge to all-NaN
    Longitude/Latitude silently, rendering a map with nothing visible
    on it - the exact "map view isn't working" symptom this pins.
    '''
    at = AppTest.from_file("tests/fixtures/eltcalc_map_locnumber_mismatch_app.py").run()

    assert len(at.exception) == 0
    assert len(at.warning) == 0
    assert len(at.get("plotly_chart")) == 1


def test_eltcalc_map_heatmap_warns_when_no_locations_match():
    '''
    When the output's LocNumber values have no overlap at all with the
    location file (a real data problem, not a dtype mismatch), warn
    instead of silently rendering a map with every point at NaN.
    '''
    at = AppTest.from_file("tests/fixtures/eltcalc_map_no_match_app.py").run()

    assert len(at.exception) == 0
    assert len(at.warning) == 1
    assert len(at.get("plotly_chart")) == 0


def test_choropleth_survives_countrycode_case_mismatch():
    '''
    Regression test: `MapView.generate_choropleth` merged the output's
    `CountryCode` against the geojson's `iso_a2` without normalising
    either side first. A case mismatch between the two ('fr' vs 'FR' -
    same country, different formatting) used to merge to no rows
    silently, same failure class as the LocNumber/heatmap one above.
    '''
    at = AppTest.from_file("tests/fixtures/choropleth_countrycode_mismatch_app.py").run()

    assert len(at.exception) == 0
    assert len(at.warning) == 0
    assert len(at.get("plotly_chart")) == 1


def test_choropleth_warns_when_no_countries_match():
    '''
    When the output's CountryCode values don't correspond to any
    country in the geojson (a real data problem), warn instead of
    silently computing a NaN center from an empty geometry join.
    '''
    at = AppTest.from_file("tests/fixtures/choropleth_no_match_app.py").run()

    assert len(at.exception) == 0
    assert len(at.warning) == 1
    assert len(at.get("plotly_chart")) == 0


def test_melt_defaults_to_sample_and_filters_events():
    at = AppTest.from_file("tests/fixtures/melt_events_app.py").run()
    assert len(at.exception) == 0, [e.value for e in at.exception]

    results = at.radio(key='melt_gul_type_filter')
    assert results.options == ['Sample', 'Analytical']
    assert results.value == 'Sample'

    events = at.selectbox(key='melt_gul_event_filter')
    # All events first, then events by loss (largest first)
    assert events.options == ['All events', 'Event 2 (loss 420)', 'Event 1 (loss 110)']
    assert sorted(at.dataframe[0].value['MeanLoss']) == [110.0, 420.0]

    events.set_value(2).run()
    assert list(at.dataframe[0].value['MeanLoss']) == [420.0]
    # Not grouped by location or country, so there is nothing to map and no Map tab
    assert [t.label for t in at.tabs] == ['Table']


def test_map_type_for():
    import pandas as pd
    from pages.components.output import map_type_for
    located = pd.DataFrame({'LocNumber': [1, 2], 'Latitude': [51.5, 48.8], 'Longitude': [-0.1, 2.3]})
    not_geocoded = located.assign(Latitude=0.0, Longitude=0.0)
    assert map_type_for(['LocNumber'], located) == 'heatmap'
    assert map_type_for(['LocNumber'], not_geocoded) is None
    assert map_type_for(['LocNumber'], None) is None
    assert map_type_for(['CountryCode'], None) == 'choropleth'
    assert map_type_for([], located) is None


def test_order_sample_types():
    from pages.components.output import order_sample_types
    assert order_sample_types(['Analytical', 'Sample']) == ['Sample', 'Analytical']
    assert order_sample_types(['Sample']) == ['Sample']
