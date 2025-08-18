.PHONY: fmt lint test hooks

fmt:
	black .

lint:
	ruff check .

test:
	pytest -q

hooks:
	pre-commit install
