<img src="https://oasislmf.org/packages/oasis_theme_package/themes/oasis_theme/assets/src/oasis-lmf-colour.png" alt="Oasis LMF logo" width="250"/>

# Oasis Python UI

A web-based UI utilising [Streamlit](https://github.com/streamlit/streamlit) to
manage exposure data and run modeling workflows on the OasisLMF platform.

The current version of the UI contains the following pages:

- `/analyses` - View and create portfolios and analyses.
- `/dashboard` - View the output of completed analyses.
- `/simplified` - Simplified UI which allows for the running of analyses using previously loaded portfolios & models.

## Installation

We include a demo docker installation to run the UI. The pre-requisites for
this installation is `git`, `docker` and `docker-compose`. To run the
deployment clone this repo and run the `./install.sh` script.

This installation is based on the
[OasisEvaluation](https://github.com/OasisLMF/OasisEvaluation) repo. It will
initialise the [Oasis Platform](https://github.com/OasisLMF/OasisPlatform) with
the test [PiWind](https://github.com/OasisLMF/OasisPiWind) model.

The UI can then be accessed at
[http://localhost:8501/](http://localhost:8501/). A single default user will be
initialised with the following credentials:

```
Username: admin
Password: password
```

Note that if previous Oasis docker installations are present they will be
removed during this installation.
