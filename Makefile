.PHONY: bootstrap test lint check doctor

bootstrap:
	./scripts/bootstrap.sh

test:
	.venv/bin/pytest -m "not model"

lint:
	.venv/bin/ruff check local_inference scripts tests benchmarks

check: lint test
	bash -n scripts/*.sh
	.venv/bin/python scripts/check_no_model_artifacts.py

doctor:
	.venv/bin/python scripts/doctor.py
