.PHONY: install test lint format typecheck clean docker-up docker-down dev demo docs

install:
	pip install -e .[dev]

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

typecheck:
	pyright

docker-up:
	docker compose up -d

docker-down:
	docker compose down

dev:
	python examples/run_demo.py

demo:
	python examples/run_demo.py

docs:
	mkdocs build

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; shutil.rmtree('.pytest_cache', ignore_errors=True); shutil.rmtree('.ruff_cache', ignore_errors=True)"
