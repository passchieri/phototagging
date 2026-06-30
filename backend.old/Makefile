.PHONY: init install run clean container container-run container-shell container-push test

SERVER=app.api:app
IMAGE=phototagging-backend
REGISTRY=igorprivate
VERSION := $(shell git rev-parse --short HEAD)


init:
	poetry --version || (echo "Please install poetry first " && false)
	poetry config virtualenvs.in-project true
	poetry env use python3.14
	poetry install --all-groups

test:
	poetry run pytest -v test

install: test
	poetry install --with=dev

run: test
	poetry run uvicorn $(SERVER) --reload --log-level debug --port 8000

clean:
	rm -rf .venv __pycache__ */__pycache__ .pytest_cache .mypy_cache


container:
	podman build \
		-f container/Dockerfile \
		-t $(IMAGE) .

container-run:
	podman run \
		-it \
		--rm \
		-p 0.0.0.0:8000:8000 \
		--env-file .env \
		$(IMAGE)

container-shell:
	podman run \
		-it \
		--rm \
		--env-file .env \
		$(IMAGE) \
		/bin/bash

container-push:
	az acr login --name $(REGISTRY)
	podman tag $(IMAGE) $(REGISTRY).azurecr.io/$(IMAGE):$(VERSION)
	podman push $(REGISTRY).azurecr.io/$(IMAGE):$(VERSION)

