.PHONY: init install run clean container container-run container-shell container-push api

IMAGE=phototagging-frontend
REGISTRY=igorprivate
VERSION := $(shell git rev-parse --short HEAD)

init:
	nvm install v22

install:
	npm install

build:
	npm run build

run:
	npm run dev

api:
	echo creating the api in src/api from the backend running at localhost:8000
	curl -sf http://localhost:8000/openapi.json |\
	npx openapi-typescript-codegen -i /dev/stdin -o src/api --useUnionTypes --name PhotoTaggingClient
# 	npm run openapi-ts

container:
	podman build \
		-f container/Dockerfile \
		-t $(IMAGE) .

container-run:
	podman run \
	-it \
	--rm \
	-p 3000:80 \
	$(IMAGE)

container-shell:
	podman run \
	-it \
	--rm \
	-p 3000:80 \
	$(IMAGE) /bin/sh

container-push: container
	az acr login --name $(REGISTRY)
	podman tag $(IMAGE) $(REGISTRY).azurecr.io/$(IMAGE):$(VERSION)
	podman push $(REGISTRY).azurecr.io/$(IMAGE):$(VERSION)