.PHONY: help bootstrap build verify lint

help:            ## List targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ —/'

bootstrap:       ## Install Python deps (pyyaml, jsonschema, requests)
	pip3 install -r requirements.txt

build:           ## Compile deliverables/**/*.md -> dist/ (json + html)
	python3 scripts/compile.py

verify: build    ## build, then validate output against output_schema.json. Exit 0 = healthy.
	python3 scripts/compile.py --check

lint:            ## Static schema check only (no URL resolution, no network)
	python3 scripts/compile.py --lint
