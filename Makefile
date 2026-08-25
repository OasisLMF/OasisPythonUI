#!make
include .env

build:
	docker build -f oasisui_st_app.Dockerfile . -t ${PYTHONUI_IMG}:${VERS_UI}

push:
	docker push ${PYTHONUI_IMG}:${VERS_UI}

scenarios_portfolios:
	python ./scripts/add_test_portfolios.py -c ./scenarios/portfolios.json

scenarios_settings:
	python ./scripts/add_settings_template.py -c ./scenarios/a_settings.json

scenarios: scenarios_portfolios scenarios_settings

build_and_push: build push
