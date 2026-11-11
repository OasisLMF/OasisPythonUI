"""Guide: what the Scenarios tool is and how to use it."""
import streamlit as st

from modules.scenarios import scenario_models, vulnerability_info
from pages.components.data import cached_model_settings
from scenarios_ui.common import Context, footer

ctx = Context()
limits = ctx.limits

st.title('Guide')

st.markdown("""
The **Oasis Scenarios** tool lets you see how catastrophe loss modelling works, using the open-source
[Oasis Loss Modelling Framework](https://oasislmf.org/). It runs real historical events and realistic
disaster scenarios - floods, windstorms, earthquakes, hail - against pre-loaded portfolios of buildings,
and shows you the losses they would cause.

It is free to use and needs no account. You cannot upload your own data: every scenario and portfolio has
been prepared in advance, so you can focus on running models and understanding their results.
""")

st.header('How a loss model works')
st.markdown("""
Every Oasis model combines three parts:

- **Hazard** - how severe the event is at each place, for example flood depth or wind speed. In this tool
  each scenario provides a *hazard footprint* for one or a few events.
- **Vulnerability** - how much damage that severity causes to a building, as a share of its value.
- **Exposure** - the buildings at risk: where they are, what they are built from and what they are worth,
  in the [Open Exposure Data (OED)](https://oasislmf.org/open-data-standards) format.

Oasis combines them to estimate the loss to each building, then adds the losses up.
""")

st.header('Vulnerability functions')
st.markdown("""
A vulnerability function gives the damage to a building, as a share of its value, for each level of hazard -
for example how much a house is damaged by one metre of flood water. Functions usually depend on what the
building is used for (its *occupancy*) and sometimes on how it is built, and they can include uncertainty: a
spread of possible damage at each hazard level, which is what the samples draw from.

The same hazard footprint can give very different losses with different vulnerability functions, so they are
as important to the result as the event itself. The scenarios here use these functions:
""")
ci = ctx.ci
by_source = {}
for model in scenario_models(ci.models.get(), ci.portfolios.get(), ctx.ui_config):
    info = vulnerability_info(cached_model_settings(ci, model)) or {'source': 'Not documented'}
    entry = by_source.setdefault(info['source'], {'url': info.get('url'), 'scenarios': []})
    entry['scenarios'].append(ctx.scenario_name(model))
lines = []
for source, entry in sorted(by_source.items()):
    label = f"[{source}]({entry['url']})" if entry['url'] else source
    lines.append(f"- **{label}**: {', '.join(sorted(entry['scenarios']))}")
st.markdown('\n'.join(lines))
st.markdown("""
Each scenario's functions are described in full when you choose it. They are part of the scenario's model
data and cannot be changed in this tool. To run a scenario with different functions, download it from the
[Oasis Scenarios repository](https://github.com/OasisLMF/Scenarios) and replace its vulnerability files - for
example with functions from the [Oasis Vulnerability Library](https://github.com/OasisLMF/VulnerabilityLibrary) -
then run it with the [Oasis MDK](https://github.com/OasisLMF/OasisLMF).
""")

st.header('Running a scenario')
st.markdown(f"""
1. **Choose a scenario** on the *Run a scenario* page. Filter the list by peril, country or provider; the
   chosen scenario shows what it represents, who provided it and which vulnerability functions it uses.
2. **Check the exposure.** The map and figures show the buildings the scenario will be run against.
3. **Run it.** Choose:
   - **Number of samples** (up to {limits.max_samples}) - damage is uncertain, so Oasis draws several
     possible outcomes (samples) and averages them. More samples give a steadier average but take longer.
   - **Break losses down by** - portfolio, country or location, to see where losses come from.
4. **Watch it run.** A progress bar shows the current step and how many events have been processed.
   Most scenarios finish within a few minutes.
5. **Explore the results** under *Your runs*, and download them as a zip file.

You can have up to {limits.max_active_runs_per_visitor} runs in progress at a time. Your runs are linked to
this browser address (the `?v=` part of the URL): bookmark it to come back to them. Runs are kept for a few
days.
""")

st.header('Reading the results')
st.markdown("""
Results follow the [Open Results Data (ORD)](https://oasislmf.org/open-data-standards) standard. Which tables
you see depends on the scenario, but the most common are:

- **Event loss tables (ELT)** - the loss from each event. *Sample* ELTs (SELT) give the loss in each sample;
  *moment* ELTs (MELT) give the mean and standard deviation.
- **Average loss tables (ALT)** - the average loss across the events in the scenario.
- **Exceedance probability tables (EPT)** - for scenarios with many events, how likely losses are to exceed
  each level. With one or a few events these are less meaningful.

**Mean of samples vs analytical mean.** Sample tables can show the *mean of samples* - the average of the
sampled losses - or the model's *analytical mean*, calculated exactly from the damage distribution without
sampling. With few samples the two can differ noticeably; as you add samples, the mean of samples gets closer
to the analytical mean.

**Loss perspectives.** *Ground up loss* is the cost of the damage before any insurance. Some scenarios also
show *insured loss*, after policy terms such as deductibles and limits.
""")

st.header('Comparing runs')
st.markdown("""
The *Compare* page puts two runs side by side - for example the same flood with and without flood defences,
or two different scenarios against the same buildings. Choose from the showcase runs and your own runs.
""")

st.header('Where the data comes from')
st.markdown("""
The scenarios are contributed by model providers and are published in the
[Oasis Scenarios repository](https://github.com/OasisLMF/Scenarios). They may use simplified hazard,
vulnerability or exposure compared with the providers' full commercial models, so treat the results as
illustrative.

To suggest a scenario or report a problem, open an issue on
[GitHub](https://github.com/OasisLMF/OasisPythonUI/issues).
""")

footer(ctx.ui_config)
