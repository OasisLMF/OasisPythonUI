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


def test_selt_fragment_mean_view_uses_special_sidx_row_not_a_recomputed_average():
    '''
    Regression test: `generate_selt_fragment`'s default "Mean (All
    Samples)" view used to recompute the mean itself via a pandas
    groupby over the file's positive-SampleId rows. SELT's SampleId
    column is ORD's reserved "sidx": -1 is ktools' own
    analytically-integrated mean (not a recomputed average of the
    positive-sidx rows in the same file), so the fragment should read
    that row directly instead. The fixture's -1 rows are deliberately
    not the arithmetic average of their samples, so this fails if the
    fragment goes back to recomputing.
    '''
    at = AppTest.from_file("tests/fixtures/selt_fragment_app.py").run()

    assert len(at.exception) == 0
    assert at.selectbox(key="selt_gul_sample_filter").value == "Mean (All Samples)"
    # Sample filter options must not expose the special sidx rows as if
    # they were selectable individual samples.
    assert at.selectbox(key="selt_gul_sample_filter").options == ["Mean (All Samples)", "1", "2"]
    # sorted descending by Loss: the fixture's -1 rows are [150, 90, 25, 15],
    # not the samples' naive averages [200, 100, 30, 20].
    assert list(at.dataframe[0].value["Loss"]) == [150.0, 90.0, 25.0, 15.0]


def test_splt_fragment_renders_bar_chart():
    at = AppTest.from_file("tests/fixtures/splt_fragment_app.py").run()

    assert len(at.exception) == 0
    assert len(at.get("plotly_chart")) == 1


def test_splt_fragment_mean_view_uses_special_sidx_row_not_a_recomputed_average():
    '''
    Regression test: `generate_splt_fragment`'s default "Mean (All
    Samples)" view used to recompute the mean itself via a pandas
    groupby over the file's positive-SampleId rows, same bug as SELT's.
    SPLT's SampleId column is ORD's reserved "sidx": -1 is ktools' own
    analytically-integrated mean, so the fragment should read that row
    directly instead. The fixture's -1 rows per (SummaryId, date) are
    deliberately not the arithmetic average of their samples (12 not
    15, 17 not 20, 6 not 6.5, 7 not 7.5); `pltcalc_bar` then sums
    across SummaryId per date, giving 12+17=29 for 2020-01-01 and
    6+7=13 for 2021-06-15 - not the naive-average equivalents (35, 14),
    so this fails if the fragment goes back to recomputing.
    '''
    at = AppTest.from_file("tests/fixtures/splt_fragment_app.py").run()

    assert len(at.exception) == 0
    assert at.selectbox(key="splt_gul_sample_filter").value == "Mean (All Samples)"
    # Sample filter options must not expose the special sidx row as if
    # it were a selectable individual sample.
    assert at.selectbox(key="splt_gul_sample_filter").options == ["Mean (All Samples)", "1", "2"]

    spec = _plotly_spec(at.get("plotly_chart")[0])
    losses = []
    for trace in spec['data']:
        losses.extend(_decode_plotly_array(trace.get('y')))
    assert sorted(losses) == [13.0, 29.0]


def test_alct_fragment_renders_table():
    at = AppTest.from_file("tests/fixtures/alct_fragment_app.py").run()

    assert len(at.exception) == 0
    assert len(at.dataframe) == 1
    assert set(at.dataframe[0].value["SummaryId"]) == {1, 2}


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
