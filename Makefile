.PHONY: install test lint run-stage3 run-tests

install:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

test:
	pytest -q

lint:
	flake8 .

run-stage3:
	python stages/stage3_vfs.py --vfs vfs_examples/deep_nested.csv --script scripts/start_full_test.txt

run-tests-linux:
	./scripts/run_tests_linux.sh