.PHONY: all init test srcs clean docs publish publish_bin publish_docs lint docker docker_image publish_image install uninstall sync


EXIV2_VERSION:=$(shell brew info --json exiv2 |jq -r '.[0].installed[0].version')
BOOST_VERSION:=$(shell brew info --json boost |jq -r '.[0].installed[0].version')

export CPLUS_INCLUDE_PATH :=$(HOMEBREW_CELLAR)/exiv2/$(EXIV2_VERSION)/include/:$(HOMEBREW_CELLAR)/boost/$(BOOST_VERSION)/include/
export LIBRARY_PATH :=$(HOMEBREW_CELLAR)/exiv2/$(EXIV2_VERSION)/lib:$(HOMEBREW_CELLAR)/boost-python3/$(BOOST_VERSION)/lib/:$(HOMEBREW_CELLAR)/boost/$(BOOST_VERSION)/lib/

print:
	@echo "CPLUS_INCLUDE_PATH='$$CPLUS_INCLUDE_PATH'"
	@echo "LIBRARY_PATH=$(LIBRARY_PATH)"

PACKAGE_NAME        := $(shell project_info name)
PROJECT_SCRIPTS     := $(shell project_info scripts)
VERSION             := $(shell project_info version)
BUMP_VERSION		:= $(shell project_info next_version)
NORMALIZED_VERSION  := $(shell echo $(VERSION) | sed -e 's/+/_/g')

SRCS           =$(wildcard src/*.py) \
				$(wildcard src/*/*.py) \
				$(wildcard src/*/*/*.py) \
				$(wildcard src/*/*/*/*.py)
INSTALL_SCRIPTS=$(addprefix $(bindir)/,$(PROJECT_SCRIPTS))
VENV_SCRIPTS   =$(addprefix $(datadir)/venv/bin/,$(PROJECT_SCRIPTS))
WHEEL          =$(addprefix dist/, $(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl)
SRCS_TAR       :=$(addprefix dist/,$(PACKAGE_NAME)-$(VERSION).tar.gz)

NOTEBOOKS      =$(wildcard *.ipynb)

REPO			= simpartnerregistry.azurecr.io
TAG				= simulytic/ps360metrics

DOCS := dist/doc/usage.md

prefix = /opt
datarootdir = $(prefix)
datadir = $(datarootdir)/$(PACKAGE_NAME)
exec_prefix=/usr/local
bindir=$(exec_prefix)/bin

sync: #picks up the exported CPLUS_INCLUDE_PATH and LIBRARY_PATH from the environment
	uv sync

all: $(WHEEL)

build: lint test
	uv build

$(WHEEL) $(SRCS_TAR): $(SRCS) test
	uv build

test:
	uv run pytest -v --cov=src --cov-report=xml test

lint: $(SRCS)
	uv run ruff check --fix .
	uv run ruff format .
	uv run mypy .

run: backend

backend: test
	uv run uvicorn --reload --port 8000 server.api:app

init:
	uv init --package


clean:
	find . -name site-packages -prune -exec rm -Rf '{}' \+
	find . -name __pycache__  -exec rm -Rf '{}' \+
	find . -name '*.egg-info' -exec rm -Rf '{}' \+
	rm -Rf dist build coverage.xml .coverage .pytest_cache docker/*.whl
# 	uv run jupyter nbconvert --clear-output --inplace $(NOTEBOOKS) || true

docker: publish_image

docker/$(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl: $(WHEEL)
	cp $< $@

docker_image: docker/$(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl
	docker build \
    	--platform=linux/amd64 \
    	-t $(TAG):$(NORMALIZED_VERSION) \
    	-t $(REPO)/$(TAG):$(NORMALIZED_VERSION) \
    	-t $(TAG):latest \
    	-t $(REPO)/$(TAG):latest \
    	--build-arg PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL \
    	-f docker/Dockerfile docker

publish_image: docker_image
	docker push $(REPO)/$(TAG):latest
	docker push $(REPO)/$(TAG):$(NORMALIZED_VERSION)


install: $(WHEEL)
	uv tool install $(WHEEL)

check-clean:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "❌ You have uncommitted changes!"; \
		exit 1; \
	else \
		echo "✅ Working directory is clean."; \
	fi

bump: check-clean test
	@echo "Current version: $(VERSION)"
	@echo "Bumping to next version: $(BUMP_VERSION)"
	git tag v$(BUMP_VERSION)


docs: $(DOCS)

$(DOCS): $(WHEEL)
	./utils/create_usage.sh

$(bindir)/%: $(datadir)/venv/bin/%
	ln -fs $< $@
	$@ -h &>/dev/null

$(datadir)/venv:
	mkdir -p $(datadir)
	python3 -m venv $(datadir)/venv
	source $(datadir)/venv/bin/activate && pip install --upgrade pip

$(VENV_SCRIPTS): $(WHEEL) $(datadir)/venv
	source $(datadir)/venv/bin/activate && pip install --force-reinstall $<

uninstall:
	@echo "Uninstalling $(PACKAGE_NAME)"
	@uv tool uninstall $(PACKAGE_NAME) || true
