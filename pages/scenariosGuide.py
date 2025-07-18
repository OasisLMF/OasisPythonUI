from modules.authorisation import quiet_login, validate_page, handle_login
from oasis_data_manager.errors import OasisException
import tarfile
from io import BytesIO
from pathlib import Path
from requests.exceptions import HTTPError
import streamlit as st
from modules.nav import SidebarNav
from modules.config import retrieve_ui_config
from modules.rerun import RefreshHandler
from modules.settings import get_analyses_settings
from pages.components.display import DataframeView, MapView
from pages.components.create import create_analysis_form
from pages.components.output import valid_locations
from modules.validation import KeyInValuesValidation, NotNoneValidation, ValidationGroup, IsNoneValidation
from modules.visualisation import OutputInterface
import time
from json import JSONDecodeError
import json
from modules.client import ClientInterface
import logging
import os

from pages.components.output import generate_eltcalc_fragment, generate_leccalc_fragment, generate_pltcalc_fragment, model_summary, summarise_inputs, generate_aalcalc_fragment
from pages.components.process import enrich_analyses, enrich_portfolios

logger = logging.getLogger(__name__)

##########################################################################################
# Header
##########################################################################################

ui_config = retrieve_ui_config()

validate_page("User Guide")

st.set_page_config(
    page_title = "User Guide",
    layout = "centered"
)

cols = st.columns([0.1, 0.8, 0.1])
with cols[1]:
    st.image("images/oasis_logo.png")

##########################################################################################
# Page
##########################################################################################

SidebarNav(no_client=ui_config.skip_login)

# Title
st.title("User Guide: Scenario analysis and comparison")

# Table of Contents
st.header("Table of Contents")
st.markdown("""
[1. Introduction](#1-introduction)\\
[2. Getting Started](#2-getting-started)\\
[3. Understanding the Interface](#3-understanding-the-interface)\\
[4. Working with Scenarios](#4-working-with-scenarios)\\
[5. Interpreting Results](#5-interpreting-results)\\
[6. Scenario Comparison](#6-scenario-comparison)\\
[7. Troubleshooting](#7-troubleshooting)\\
[8. Limitations](#8-limitations)\\
[9. Attributions](#9-attributions)\\
[10. Disclaimer](#10-disclaimer)
""")

# Introduction
st.header("1. Introduction")
st.markdown("*[back to top](#table-of-contents)*")
st.markdown("""
The Oasis Loss Modelling Framework (LMF) Scenarios Tool is a web-based application designed for catastrophe (or disaster) scenario impact analysis. 
As part of the open-source Oasis platform, it provides accessible tools to evaluate potential loss from selected disaster event scenarios.
It can be used for demonstrating and conducting stress-testing for insurance regulatory or rating agency purposes, 'what-if' modelling of historical events, or
worst-case scenario modelling of hypothetical events for (re)insurance, government, and academic use.
This tool uses hazard scenarios, or hazard footprints, as well as exposure data and physical vulnerability curves in Oasis formats.
""")

st.subheader("Key Features")
st.markdown("""
- Uses the [Oasis LMF](https://oasislmf.org/) open-source platform analytical engine, with no installation or download required and with full transparency of methods
- Web-based interface: Accessible through any modern web browser, free to use 
- Standardized data formats: Uses [Open Exposure Data (OED) and Open Results Data (ORD) standards](https://oasislmf.org/open-data-standards)
- Comprehensive modelling: Supports multiple perils and modelling approaches
- Flexible analysis: Monte Carlo simulation with customizable parameters
- Visualization tools: Interactive maps, charts, and reporting capabilities
""")

st.subheader("Target Users")
st.markdown("""
- Insurance and reinsurance professionals
- Risk analysts and catastrophe modellers
- Government agencies and public sector organizations
- Academic researchers and students
- Consultants and third-party risk assessment providers
""")

# Getting Started
st.header("2. Getting Started")
st.markdown("*[back to top](#table-of-contents)*")
st.subheader("System Requirements")
st.markdown("""
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Stable internet connection
""")

st.subheader("Accessing the Platform")
st.markdown("""
1. Navigate to [Oasis LMF Scenarios](https://ui.oasislmf-scenarios.com/scenarios) in your browser
2. No installation or download required
3. Upon first access, you'll be presented with the main dashboard. The interface is designed to be intuitive, but familiarizing yourself 
with the key components will enhance your experience.
""")

# Understanding the Interface
st.header("3. Understanding the Interface")
st.markdown("*[back to top](#table-of-contents)*")

st.subheader("Scenarios: Analyse individual disaster scenarios")
st.markdown("""
The Scenarios dashboard provides an overview of your current scenarios and quick access to key functions:
- Scenario Selection: Select scenarios from a default list maintained by Oasis. New scenarios can be added [on request](https://github.com/OasisLMF/Scenarios/issues)
- Portfolio Selection: Select a portfolio of exposure to assess the disaster scenario against. The tool supports built asset data in OED format. THese may be 'flat file' where each location has the same value, or data derived from an exposure model. 
- Create analysis: Give the analysis a name, view the distribution of hazard intensity and exposure value.
- Run analysis: Select granularity of loss to analyse: total scenario loss (whole portfolio), per-country breakdown of loss, or per-location loss.
- Output Viewer: Show a summary of the input scenario and exposure and a summary of ground up or economic loss in the form of a table, chart or map.
- Export results: Download the full results.
""")

st.subheader("Comparison: Compare losses from disaster scenarios")
st.markdown("""
- Select scenario analyses to compare: Select two analyses that have been run in the [Scenarios](https://ui.oasislmf-scenarios.com/scenarios) page.
- View results: Display and analyse the ground up (economic) loss of the two scenarios side-by-side in table and chart form - for the scenario total and per location.
""")


# Working with Scenarios
st.header("4. Working with Scenarios")
st.markdown("*[back to top](#table-of-contents)*")

st.subheader("Creating a New Scenario")

st.markdown("""
**1. Access the Main Dashboard**
   - Navigate to [Oasis LMF Scenarios](https://ui.oasislmf-scenarios.com/scenarios)
   - Wait for the application  to load completely
""")

# Check if the image file exists
if os.path.exists("images/STguide_1_createAnalysis.png"):
    # Display the image
    st.image("images/STguide_1_createAnalysis.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_1_createAnalysis.png"}' not found. Please check the file path and try again.")


st.markdown("""
**2. Start a New Scenario**
   - Select a scenario by checking the box next to the model/supplier table
   - Select the portfolio from the list of available exposures for the scenario
   - Click the "Create Analysis" button (typically located in the bottom-right corner)
""")

if os.path.exists("images/STguide_2_createAnalysis.png"):
    # Display the image
    st.image("images/STguide_2_createAnalysis.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_2_createAnalysis.png"}' not found. Please check the file path and try again.")


st.markdown("""
**3. Configure Scenario Details**
   - Scenario Name: Enter a descriptive name (e.g., "Ghana Flood 61")
   - Portfolio: Select from the available exposure sets for the scenario
   - Model: Select from the available model variants
   - Vulnerability: In future versions of the tool, the vulnerability functions being applied in the analysis will be shown here (and could be selected).
   - Click on “Create Analysis”
""")

if os.path.exists("images/STguide_3_createAnalysis.png"):
    # Display the image
    st.image("images/STguide_3_createAnalysis.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_3_createAnalysis.png"}' not found. Please check the file path and try again.")


st.markdown("""
**4. Run Analysis**
   - Selection: Choose from available analyses. The one that has just been created should have a green “Ready” as its status. Click the check-box next to this.
   - Select the level you would like the output losses grouped by
     - Portfolio: all locations combined
     - Country: split by country
     - Location: split by individual location
   - Click the “Run” button to execute the analysis
   - When running, your analysis will show the status “Running”
   - When Complete, the status will switch to “Run Completed”

The analysis run will include 'analytical' and 'sample' options. 
Under 'analytical', 1 version of the scenario analysis will be run. 
Under 'sample', 10 samples will be run, to account for the effect of modelling uncertainty on the estimated loss. This value cannot be changed in this version of the tool.
""")

if os.path.exists("images/STguide_4_runAnalysis.png"):
    # Display the image
    st.image("images/STguide_4_runAnalysis.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_4_runAnalysis.png"}' not found. Please check the file path and try again.")


st.markdown("""
*5. Viewing Results*
  - Once the analysis is in the “Run Completed” status, when selecting the analysis, you will be able to click the “Show Output” button
""")

if os.path.exists("images/STguide_5_runAnalysis_showOutput.png"):
    # Display the image
    st.image("images/STguide_5_runAnalysis_showOutput.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_5_runAnalysis_showOutput.png"}' not found. Please check the file path and try again.")

st.markdown("""
  - The output data will then be available in the pop up screen, including a summary of the analysis inputs and the modelled results
""")



if os.path.exists("images/STguide_6_Output.png"):
    # Display the image
    st.image("images/STguide_6_Output.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_6_Output.png"}' not found. Please check the file path and try again.")

if os.path.exists("images/STguide_7_ResultsSummary.png"):
    # Display the image
    st.image("images/STguide_7_ResultsSummary.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_7_ResultsSummary.png"}' not found. Please check the file path and try again.")



st.markdown("""
  - There is also an option to download the results as a compressed tar file at the bottom of the screen
""")

if os.path.exists("images/STguide_8_downloadOption.png"):
    # Display the image
    st.image("images/STguide_8_downloadOption.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_8_downloadOption.png"}' not found. Please check the file path and try again.")



# Interpreting Results
st.header("5. Interpreting Results")
st.markdown("*[back to top](#table-of-contents)*")

st.subheader("Available Results")

st.markdown("""
The scenarios workflow results present the mean loss of the selected scenario. This can be shown per-location, 
per-country (for trans-boundary / cross-border scenarios) and as a scenario total loss.

The 'analytical' and 'sample' results will be shown, to view the difference between single- and multiple-sample runs. 

The following loss perspectives can be run:
  - Ground-Up Loss (GUL): Losses before application of insurance terms - requires no (re)insurance terms in the portfolio.
  - Insured Loss (IL): Losses after policy terms but before reinsurance - requires (re)insurance terms in the portfolio.
  - Reinsured Loss (RIL): Net losses after reinsurance arrangements - requires (re)insurance terms in the portfolio.
""")

st.subheader("Viewing Results")

st.markdown("""
Geographic Loss Maps:
- Click "Maps" tab to view spatial distribution of scenario loss 
- Use zoom controls to focus on specific areas
- Click locations for detailed loss information
""")

if os.path.exists("images/STguide_9_outputMap.png"):
    # Display the image
    st.image("images/STguide_9_outputMap.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_9_outputMap.png"}' not found. Please check the file path and try again.")


st.markdown("""
Detailed Tabular Results:
- Click "Table" tab
- Switch between different summary levels: portfolio, country, location
- Click column headers to sort data
""")

if os.path.exists("images/STguide_10_outputTbl.png"):
    # Display the image
    st.image("images/STguide_10_outputTbl.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_10_outputTbl.png"}' not found. Please check the file path and try again.")

if os.path.exists("images/STguide_11_outputTbloption.png"):
    # Display the image
    st.image("images/STguide_11_outputTbloption.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_11_outputTbloption.png"}' not found. Please check the file path and try again.")




# Scenario Comparison
st.header("6. Scenario Comparison")
st.markdown("*[back to top](#table-of-contents)*")

st.markdown("""
Compare multiple scenarios side-by-side in the [Comparisons](https://ui.oasislmf-scenarios.com/comparison) tab, by following the instructions in the tab.

Scenario comparisons could include:
- Loss due to change in hazard such as flood inundation under two different levels of flood protection.
- Loss due to change in exposure distribution or value over time.
- Loss under different asset building code / retrofit conditions, i.e., change in property vulnerability.
- Loss under two representations of the same (e.g., historical) event, from two versions of a model or two different model providers

Note: this version of the workflow requires that the scenarios being compared are added to the [scenarios list](https://github.com/OasisLMF/scenario)
and run through the Scenarios tab first. Changes directly to the hazard footprint, exposure, or vulnerability are not yet possible in this tool. 

**Analysis Summary** provides a side-by-side review of the input data and analysis settings in the two analyses.

**Loss Estimates** enables side-by-side visualisation of the loss estimates from both scenarios in chart, table and map form.  
""")


# Troubleshooting
st.header("7. Troubleshooting")
st.markdown("*[back to top](#table-of-contents)*")

st.subheader("Common Issues and Solutions")
st.markdown("""
Analysis Failures:
- Insufficient Data: Verify all required fields are populated
- Model Compatibility: Confirm model supports your data characteristics
- Resource Limits: Check computational resource availability
- Parameter Conflicts: Review analysis configuration settings

Result Display Issues:
- Browser Compatibility: Update to latest browser version
- JavaScript Errors: Enable JavaScript and clear browser cache
- Memory Issues: Close other applications to free up resources
- Network Timeout: Refresh page and try again
- Blank Charts: Refresh browser or check data filters
- Slow Loading: Large datasets may take time to render
- Export Failures: Check file permissions and browser settings
""")

st.subheader("Performance Optimization")
st.markdown("""
Analysis Efficiency:
- Start with smaller sample sizes for testing
- Use appropriate model resolution
- Monitor resource usage during analysis
""")

st.subheader("Getting Help")
st.markdown("""
- Open an issue in GitHub: https://github.com/OasisLMF/OasisPythonUI/issues
- Email support: support@oasislmf.org
- Official Oasis LMF documentation: https://oasislmf.github.io/
- Open Exposure Data (OED) format specifications: https://github.com/OasisLMF/OpenDataStandards/
- Oasis LMF Information Library: https://oasislmf.org/oasis-information-library
- GitHub repositories with example code and issues: https://github.com/OasisLMF
""")


# Limitations
st.header("7. Limitations")
st.markdown("*[back to top](#table-of-contents)*")

st.markdown("""
Limitations of this tool include:

- Users cannot directly upload or adjust their own scenarios, exposure portfolios or vulnerability functions in this version of the tool. 
New files can be shared with Oasis and uploaded by the admin team if they are needed for demonstration purposes, for example (see [7. Troubleshooting](#7-troubleshooting)). 
Adjustments to scenario already included can be made by obtaining the hazard footprint from the Scenarios GitHub repository and sharing it back to Oasis for upload.
- This version of the tool enables analysis using ground up exposure only - no re/insurance policy terms are handled in the tool. 
- The number of simulations that can be run on a scenario are limited to prevent excessive computational burden. 
""")

# Attributions
st.header("8. Attributions")
st.markdown("*[back to top](#table-of-contents)*")

st.markdown("""
Many thanks to the following model vendors who have participated in this project and made their scenarios footprint files available:

- Applied Research Associates (ARA)
- Impact Forecasting
- Insurance Partners Europe (IPE)
- JBA Risk Management
""")

# Disclaimer
st.header("8. Disclaimer")
st.markdown("*[back to top](#table-of-contents)*")

st.markdown("""
All data and information within this repository fall under the BSD 3-Clause License.

DISCLAIMER: No contributors to this repository, namely the third-party model providers, brokers, insurers or reinsurers take any 
responsibility for the outputs produced from these scenarios or deterministic models. Although the providers of the scenarios have 
ensured the hazard data captured within the footprint files is as accurate as possible, the event losses produced may vary from those 
in the full stochastic model from the same vendor. These scenarios may also be accompanied by different (or simplified) vulnerability 
functions which will produce different losses and so do not reflect the company's "true" view of risk for these events.
""")

if ui_config.skip_login:
    quiet_login()
