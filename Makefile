.PHONY: install test check serve docker

install:
	pip install -e ".[dev]"

test:
	pytest -q

check:
	python scripts/check_m5_benchmark.py
	python scripts/check_policy_corpus.py
	python scripts/check_m6_product.py

serve:
	python run_api.py

docker:
	docker compose up --build
