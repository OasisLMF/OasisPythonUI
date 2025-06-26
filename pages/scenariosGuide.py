import streamlit as st
import os

cols = st.columns([0.1, 0.8, 0.1])

# Title
st.title("Oasis Loss Modelling Framework Scenarios Tool - User Guide")

# Table of Contents
st.header("Table of Contents")
st.markdown("""
1. Introduction  
2. Getting Started  
3. Understanding the Interface  
4. Working with Scenario  
5. Data Input and Management  
6. Running Model Analyses  
7. Interpreting Results  
8. Advanced Features  
9. Troubleshooting  
10. Best Practices  
""")

# Introduction
st.header("Introduction")
st.markdown("""
The Oasis Loss Modelling Framework (LMF) Scenarios Tool is a web-based application designed for catastrophe risk modelling and analysis. As part of the open-source Oasis platform, it provides insurance and reinsurance professionals, government agencies, and academic researchers with powerful tools to evaluate catastrophic risk exposure and potential losses.
""")

st.subheader("Key Features")
st.markdown("""
- Open-source platform: Free to use with full transparency  
- Web-based interface: Accessible through any modern web browser  
- Comprehensive modelling: Supports multiple perils and modelling approaches  
- Standardized data formats: Uses Open Exposure Data (OED) and Open Results Data (ORD) standards  
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
st.header("Getting Started")
st.subheader("System Requirements")
st.markdown("""
- Modern web browser (Chrome, Firefox, Safari, Edge)  
- Stable internet connection  
""")

st.subheader("Accessing the Platform")
st.markdown("""
1. Navigate to [Oasis LMF Scenarios](https://ui.oasislmf-scenarios.com/scenarios in your browser  
3. No installation or download required  
""")

st.subheader("First Time Setup")
st.markdown("""
Upon first access, you'll be presented with the main dashboard. The interface is designed to be intuitive, but familiarizing yourself with the key components will enhance your experience.
""")

# Understanding the Interface
st.header("Understanding the Interface")
st.subheader("Main Dashboard")
st.markdown("""
The main dashboard provides an overview of your current scenarios and quick access to key functions:  
- Scenarios: Summary of existing scenarios and their status  
- Comparison: Compare outputs from multiple analyses  
""")

st.subheader("Key Interface Elements")
st.markdown("""
- Scenario Management Panel: Create, edit, and organise scenarios  
- Model Configuration: Select and configure scenarios  
- Analysis Controls: Set parameters for model runs  
- Results Viewer: Display and analyse output data  
- Export Functions: Download results in various formats  
""")

# Working with Scenarios
st.header("Working with Scenarios")
st.subheader("Creating a New Scenario")
st.markdown("""
**Step-by-Step Instructions:**  

1. Access the Main Dashboard  
   - Navigate to [Oasis LMF Scenarios](https://ui.oasislmf-scenarios.com/scenarios) 
   - Wait for the application  to load completely  
""")

# Check if the image file exists
if os.path.exists("STguide_1_createAnalysis.png"):
    # Display the image
    st.image("STguide_1_createAnalysis.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_1_createAnalysis.png"}' not found. Please check the file path and try again.")

   
st.markdown("""
2. Start a New Scenario  
   - Select a scenario by checking the box next to the model/supplier table  
   - Select the portfolio from the list of available exposures for the scenario  
   - Click the "Create Analysis" button (typically located in the bottom-right corner)  
""")

if os.path.exists("STguide_2_createAnalysis.png"):
    # Display the image
    st.image("STguide_2_createAnalysis.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_2_createAnalysis.png"}' not found. Please check the file path and try again.")

   
st.markdown("""
3. Configure Scenario Details  
   - Scenario Name: Enter a descriptive name (e.g., "Ghana Flood 61")  
   - Portfolio: Select from the available exposure sets for the scenario  
   - Model: Select from the available model variants  
   - Click on “Create Analysis”  
""")

if os.path.exists("STguide_3_createAnalysis.png"):
    # Display the image
    st.image("STguide_3_createAnalysis.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_3_createAnalysis.png"}' not found. Please check the file path and try again.")

   
st.markdown("""
4. Run Analysis  
   - Selection: Choose from available analyses. The one that has just been created should have a green “Ready” as its status. Click the check-box next to this.  
   - Select the level you would like the output losses grouped by  
     - Portfolio: all locations combined  
     - Country: split by country  
     - Location: split by individual location  
   - Click the “Run” button to execute the analysis  
   - When running, your analysis will show the status “Running”  
   - When Complete, the status will switch to “Run Completed” 
""")

if os.path.exists("STguide_4_runAnalysis.png"):
    # Display the image
    st.image("STguide_4_runAnalysis.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_4_runAnalysis.png"}' not found. Please check the file path and try again.")

   
st.markdown("""
5. Viewing Results
  - Once the analysis is in the “Run Completed” status, when selecting the analysis, you will be able to click the “Show Output” button
""")

if os.path.exists("STguide_5_runAnalysis_showOutput.png"):
    # Display the image
    st.image("STguide_5_runAnalysis_showOutput.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_5_runAnalysis_showOutput.png"}' not found. Please check the file path and try again.")

st.markdown("""
  - The output data will then be available in the pop up screen, including a summary of the analysis inputs and the modelled results
""")



if os.path.exists("STguide_6_Output.png"):
    # Display the image
    st.image("STguide_6_Output.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_6_Output.png"}' not found. Please check the file path and try again.")

if os.path.exists("STguide_7_ResultsSummary.png"):
    # Display the image
    st.image("STguide_7_ResultsSummary.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_7_ResultsSummary.png"}' not found. Please check the file path and try again.")

   

st.markdown("""
  - There is also an option to download the results as a compressed tar file at the bottom of the screen
""")

if os.path.exists("STguide_8_downloadOption.png"):
    # Display the image
    st.image("STguide_8_downloadOption.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_8_downloadOption.png"}' not found. Please check the file path and try again.")



st.subheader("Accessing the Platform")
st.markdown("""
Deterministic Scenarios: Analyse specific events with known parameters
  - Historical events 
  - Hypothetical "what-if" scenarios 
  - Regulatory or rating agency scenarios 
Stochastic Scenarios: Analyse probabilistic risk using event sets
  - Annual aggregate losses 
  - Portfolio optimization studies 
""")


st.header("Interpreting Results")
st.subheader("Result Categories")
st.markdown("""
  - Ground-Up Losses (GUL): Losses before application of insurance terms 
  - Insured Losses (IL): Losses after policy terms but before reinsurance 
  - Reinsured Losses (RIL): Net losses after reinsurance arrangements
""")

st.subheader("Statistical Outputs")
st.markdown("""
Summary Statistics:
  - Mean annual loss 
  - Standard deviation 
  - Coefficient of variation 
  - Maximum simulated loss 

Percentile Measures:
  - 90th, 95th, 99th percentiles 
  - Value at Risk (VaR)
  - Tail Value at Risk (TVaR)
""")


st.header("Interpreting Results")
st.markdown("""
Summary Statistics:
  - Mean annual loss 
  - Standard deviation 
  - Coefficient of variation 
  - Maximum simulated loss 

Percentile Measures:
  - 90th, 95th, 99th percentiles 
  - Value at Risk (VaR)
  - Tail Value at Risk (TVaR)
""")

st.subheader("Accessing and Viewing Results - Step by Step")
st.markdown("""
Step 1: Navigate to Results
1.	Follow the steps as laid out above to run an analysis and view the results

Step 2: Understanding Statistical Outputs
1.	Summary Statistics Panel
- Mean Annual Loss: Average expected loss per year 
- Standard Deviation: Measure of loss variability 
- Coefficient of Variation: Risk-adjusted measure 
- Maximum Simulated Loss: Highest loss in simulation set 

Step 3: Interactive Visualizations
1.	Geographic Loss Maps
- Click "Maps" tab to view spatial results 
- Use zoom controls to focus on specific areas 
- Click locations for detailed loss information 
""")

if os.path.exists("STguide_9_outputMap.png"):
    # Display the image
    st.image("STguide_9_outputMap.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_9_outputMap.png"}' not found. Please check the file path and try again.")


st.markdown("""
Step 4: Detailed Tabular Results
1.	Results Tables
- Click "Tables" or "Data" tab 
- Switch between different summary levels: 
- Portfolio Level: Overall results 
- Location Level: Individual property results 
- Account Level: Policy-specific results 
""")

if os.path.exists("STguide_10_outputTbl.png"):
    # Display the image
    st.image("STguide_10_outputTbl.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_10_outputTbl.png"}' not found. Please check the file path and try again.")


st.markdown("""
2.	Table Features
- Sort: Click column headers to sort data 
""")

if os.path.exists("STguide_11_outputTbloption.png"):
    # Display the image
    st.image("STguide_11_outputTbloption.png")
else:
    # Display a warning message
    st.warning(f"Image file '{"STguide_11_outputTbloption.png"}' not found. Please check the file path and try again.")



st.markdown("""
Step 5: Interpreting Key Results
1.	Risk Metrics Understanding
- Value at Risk (VaR): Loss level not exceeded with specified confidence 
- Tail Value at Risk (TVaR): Average loss above VaR threshold 
- Return Period Losses: Expected loss for specific return periods 

2.	Comparing Scenarios
- Use "Compare" function to analyse multiple scenarios 
- Side-by-side result comparison 
- Difference calculations and visualization 

Troubleshooting Results Issues
Common Display Problems:
- Blank Charts: Refresh browser or check data filters 
- Slow Loading: Large datasets may take time to render 
- Export Failures: Check file permissions and browser settings 

Advanced Features
Sensitivity Analysis
Test how changes in key parameters affect results:
- Model Parameters: Adjust hazard or vulnerability settings 
- Exposure Values: Modify replacement costs or coverage limits 
- Financial Terms: Change deductibles or policy limits 
- Geographic Factors: Analyse sub-regions or specific areas 
Scenario Comparison
Compare multiple scenarios side-by-side:
- Baseline vs. Alternative: Assess impact of changes 
- Before vs. After: Evaluate risk reduction measures 
- Multiple Models: Compare results across different models 
- Time Series: Analyse trends over multiple time periods 
Custom Analytics
Develop specialized analyses:
- Portfolio Optimization: Identify optimal risk transfer strategies 
- Capital modelling: Support regulatory capital calculations 
- Pricing Analysis: Inform insurance pricing decisions 
- Risk Ranking: Prioritize locations or portfolios by risk 
Troubleshooting
Common Issues and Solutions

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
Performance Optimization

Analysis Efficiency:
- Start with smaller sample sizes for testing 
- Use appropriate model resolution 
- Monitor resource usage during analysis 
Getting Help
Getting Help

Documentation Resources:
- Official Oasis LMF documentation: https://oasislmf.github.io/ 
- Model-specific user guides and technical documentation 
- Open Exposure Data (OED) format specifications 
- API documentation for advanced integrations 
Community and Support:
- Email support: support@oasislmf.org 
- GitHub repositories with example code and issues: https://github.com/OasisLMF 
- Community forums and user discussions 
- Professional training sessions and webinars 
Example Data and Models:
- PiWind demonstration model with example OED files available 
- Sample data files like SourceLocOEDPiWind10.csv for testing 
- Multiple example models available in the “OasisModels” repository 
Best Practices
Model Usage
- Understand Limitations: Be aware of model scope and assumptions 
- Validate Results: Compare with independent estimates where possible 
- Document Assumptions: Record all analysis assumptions and parameters 
- Regular Review: Periodically review and update model selections 
Analysis Workflow
- Start Simple: Begin with basic analyses before complex scenarios 
- Test Thoroughly: Validate results with known benchmarks 
- Document Process: Maintain detailed records of analysis steps 
- Review Results: Have analyses reviewed by qualified professionals 
Result Interpretation
- Consider Uncertainty: Understand confidence intervals and limitations 
- Compare Multiple Sources: Use multiple models where appropriate 
- Communicate Clearly: Present results in appropriate format for audience 
- Update Regularly: Refresh analyses as new data becomes available 
Security and Compliance
- Data Protection: Follow data privacy and security protocols 
- Access Control: Implement appropriate user access restrictions 
- Audit Trails: Maintain records of data access and analysis history 
- Regulatory Compliance: Ensure analyses meet regulatory requirements 
Collaboration
- Share Scenarios: Use collaboration features for team projects 
- Version Control: Maintain clear versioning of scenarios and data 
- Peer Review: Implement review processes for critical analyses 
- Knowledge Transfer: Document processes for team continuity 



\*This user guide provides a comprehensive overview of the Oasis Loss Modelling Framework Scenarios Tool. The demonstration videos on the Oasis LMF YouTube and the example files from the PiWind model can help supplement this written guide. For the most current information and detailed technical documentation, please refer to the official Oasis LMF documentation at https://oasislmf.github.io/*
""")



