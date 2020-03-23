all: poetry.lock requirements.txt
.PHONY: all

poetry.lock: pyproject.toml
	poetry lock

requirements.txt: poetry.lock
	poetry export --format requirements.txt -o $@
