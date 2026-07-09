.PHONY: help install install-dev scrape ingest index query eval test lint format clean

help:           ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:        ## Install the package
	pip install -e .

install-dev:    ## Install with dev dependencies (test, lint, format)
	pip install -e ".[dev]"

scrape:         ## Run the scraper (usage: make scrape DOMAIN=giao_thong)
	python scripts/scrape.py $(DOMAIN)

ingest:         ## Run the ingestion pipeline (usage: make ingest DOMAIN=giao_thong)
	python scripts/ingest.py $(DOMAIN)

index:          ## Build the ChromaDB index
	python scripts/build_index.py

query:          ## Interactive query (usage: make query Q="...")
	python scripts/query.py "$(Q)"

eval:           ## Run evaluation on the eval set
	python scripts/eval.py

test:           ## Run the test suite
	pytest

lint:           ## Run ruff + mypy
	ruff check src tests
	mypy src

format:         ## Auto-format with ruff
	ruff format src tests
	ruff check --fix src tests

clean:          ## Remove caches and local indexes
	rm -rf .pytest_cache .mypy_cache .ruff_cache data/index
	find . -type d -name __pycache__ -exec rm -rf {} +
