.PHONY: install test run demo docker

install:
	python -m pip install -e .[dev]

test:
	pytest -q

run:
	uvicorn intelligence_router.main:app --host 0.0.0.0 --port 8000

demo:
	python scripts/demo_benchmark.py --output MVP_VALIDATION.md --json benchmark_results.json

docker:
	docker compose up --build
