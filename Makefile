#!make
include .env

build:
	docker build -f oasisui_st_app.Dockerfile . -t ${PYTHONUI_IMG}:${VERS_UI}

push:
	docker push ${PYTHONUI_IMG}:${VERS_UI}

build_and_push: build push
