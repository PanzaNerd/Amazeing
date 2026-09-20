
NAME = a_maze_ing.py
CONFIG = config.txt

.PHONY: all install run debug clean lint lint-strict test build

all: lint-strict

install:
	python3 -m pip install flake8 mypy pytest build

run:
	python3 $(NAME) $(CONFIG)

debug:
	python3 -m pdb $(NAME) $(CONFIG)

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache build dist *.egg-info

lint:
	flake8 a_maze_ing.py config_parser.py display.py mazegen.py output_writer.py tests/
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 a_maze_ing.py config_parser.py display.py mazegen.py output_writer.py tests/
	mypy . --strict

test:
	python3 -m pytest tests/ -v

build:
	python3 -m build
