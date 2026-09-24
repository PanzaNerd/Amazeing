# Ordine cronologico di utilizzo (tutto gira DENTRO il venv di 'make env',
# niente da attivare):  make env -> make install -> make lint -> ...
# NOTA: le ricette iniziano SEMPRE con un TAB, non con gli spazi.

NAME = a_maze_ing.py
CONFIG = config.txt

.PHONY: all env install run debug test lint lint-strict build wheel clean

# il bersaglio di default (bare 'make'): i controlli severi
all: lint-strict

# 1) la CUCINA: crea l'ambiente virtuale 'venv' (una volta sola per macchina)
env:
	python3 -m venv venv

# 2) il CORRIERE: porta i 4 strumenti dentro la cucina (una volta sola)
install:
	venv/bin/python -m pip install flake8 mypy pytest build

# 3) il programma: genera maze.txt e apre il display interattivo
run:
	venv/bin/python $(NAME) $(CONFIG)

# 3) il debugger (pdb, come gdb)
debug:
	venv/bin/python -m pdb $(NAME) $(CONFIG)

# 3) il vigile: i 22 test
test:
	venv/bin/python -m pytest tests/ -v

# 3) i controlli richiesti dal subject (flake8 + mypy coi flag esatti)
lint:
	venv/bin/python -m flake8 .
	venv/bin/python -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

# 3) la versione piu' severa dei controlli
lint-strict:
	venv/bin/python -m flake8 .
	venv/bin/python -m mypy . --strict

# 4) la SCATOLA: costruisce la wheel in dist/ (dalla ricetta pyproject.toml)
build:
	venv/bin/python -m build

# 4) la scatola PRONTA alla radice (quella che il subject VI vuole committata)
wheel:
	venv/bin/python -m build
	cp dist/mazegen-1.0.0-py3-none-any.whl ./mazegen-1.0.0-py3-none-any.whl

# pulizia: cache e artefatti (NON tocca la cucina 'venv')
clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache build dist *.egg-info

# --------------------------------------------------------------
# SEZIONE 6 (difesa): i comandi da digitare A MANO davanti
# all'evaluator — sono la dimostrazione, NON bersagli di make.
#   python3 -m venv /tmp/venv1             # 1) la FABBRICA
#   /tmp/venv1/bin/pip install build       # 2) il tool nella fabbrica
#   /tmp/venv1/bin/python -m build         # 3) RICOSTRUISCI la scatola
#   python3 -m venv /tmp/venv2             # 4) il CLIENTE
#   /tmp/venv2/bin/pip install dist/mazegen-1.0.0-py3-none-any.whl
#                                          # 5) il cliente riceve la scatola
#   cd /tmp                                # 6) esci dal progetto
#   /tmp/venv2/bin/python -c "from mazegen import MazeGenerator; print('funziona')"
#                                          #    la prova FUORI dal progetto
# --------------------------------------------------------------
