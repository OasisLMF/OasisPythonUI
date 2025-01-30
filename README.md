<img src="https://oasislmf.org/packages/oasis_theme_package/themes/oasis_theme/assets/src/oasis-lmf-colour.png" alt="Oasis LMF logo" width="250"/>

# Oasis Streamlit UI

A web-based UI utilising [Streamlit](https://github.com/streamlit/streamlit) to
manage exposure data and run modelling workflows on the OasisLMF Platform.

The current version of the UI contains the following pages:

- `/analyses` - View and create portfolios and analyses.
- `/dashboard` - View the output of completed analyses.
- `/simplified` - Simplified UI which allows for the running of analyses using preloaded portfolios & models.

## Installation

We include a demo docker installation to run the UI. The pre-requisites for
this installation is `git`, `docker` and `docker-compose`. To run the
deployment clone this repo and run the `./install.sh` script.

The UI can then be accessed at [http://localhost:8501/](http://localhost:8501/).
