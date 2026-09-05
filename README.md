*This project has been created as part of the 42 curriculum by mpanzani, roblomba.*

# A-Maze-ing

## Description

AMAZEING is a maze generator written in Python 3.10+. Given a configuration
file, it generates a random but reproducible maze, writes it to a file using
a hexadecimal wall representation, and displays it in an interactive ASCII
terminal view. The generation logic lives in a standalone, reusable class
(`MazeGenerator`) packaged as `mazegen`.

## Instructions

Requirements: Python 3.10 or later. Install the development tools with:

	make install

Generate a maze (writes the output file, then opens the interactive display):

	python3 a_maze_ing.py config.txt

Interactive display keys:

| Key | Action                    |
|-----|---------------------------|
| r   | regenerate a new maze     |
| p   | show/hide shortest path   |
| c   | change wall colours       |
| q   | quit                      |

Development targets:

	make run          # run with the default config
	make debug        # run under pdb
	make test         # run the pytest suite
	make lint         # flake8 + mypy (subject flags)
	make lint-strict  # flake8 + mypy --strict
	make clean        # remove caches and build artifacts
	make build        # build the mazegen package in dist/

Reusable module: build and install it (in a virtualenv or equivalent):

	make build
	python3 -m pip install dist/mazegen-1.0.0-py3-none-any.whl

Basic usage:

```python
from mazegen import MazeGenerator

gen = MazeGenerator(width=20, height=15, seed=42)  # custom size and seed
gen.generate(perfect=True, entry=(0, 0), exit=(19, 14))
maze = gen.grid     # grid[y][x] = 0-15, bits 0-3 = walls N/E/S/W
path = gen.solve()  # shortest path entry -> exit as list of (x, y) cells
```

## Configuration file format

One `KEY=VALUE` pair per line; lines starting with `#` are comments.

| Key          | Mandatory | Description                  | Example              |
|--------------|-----------|------------------------------|----------------------|
| WIDTH        | yes       | maze width in cells          | WIDTH=20             |
| HEIGHT       | yes       | maze height in cells         | HEIGHT=15            |
| ENTRY        | yes       | entry coordinates (x,y)      | ENTRY=0,0            |
| EXIT         | yes       | exit coordinates (x,y)       | EXIT=19,14           |
| OUTPUT_FILE  | yes       | output filename              | OUTPUT_FILE=maze.txt |
| PERFECT      | yes       | perfect maze (True/False)    | PERFECT=True         |
| SEED         | no        | random seed for reproducibility | SEED=42           |

## Output file format

One hexadecimal digit per cell: bit 0 = North wall, bit 1 = East, bit 2 =
South, bit 3 = West (1 = closed). Rows are written one per line, then an
empty line, then entry coordinates, exit coordinates and the shortest path
using the letters N, E, S, W.

## Algorithm

The perfect maze is generated with the recursive backtracker (depth-first
search): starting from a cell, it visits unvisited neighbours by carving the
wall between them, and backtracks when stuck. The result is a spanning tree,
i.e. a perfect maze with exactly one path between any two cells.

We chose it because it is simple to implement, produces long corridors with
good visual quality, and its tree property guarantees the "perfect"
constraint for free.

For PERFECT=False, a few extra internal walls are carved after the perfect
generation, each checked so that no open area wider than 2 cells appears.

The "42" pattern is drawn with fully closed cells (all four walls), placed
where it does not disconnect the maze, and omitted with a console error
message when the maze is too small.

## Reusable part

The `MazeGenerator` class in `mazegen.py` is a standalone, documented
module, packaged as `mazegen` (see Instructions above). It generates,
holds and solves a maze without knowing anything about the configuration
file or the output format, and can be imported in any future project.

## Team and project management

This project was carried out entirely together by mpanzani and roblomba:
both worked on every part (parsing, generation, output, display) and
studied the code step by step as a pair.

Anticipated planning and how it evolved: we started with a split of
responsibilities, then switched to working on everything together so that
both of us understand every part of the code.

What worked well: studying each module one by one, following the
execution order of the program. To improve: start earlier.

Tools: flake8, mypy, pytest, build, git.

## Resources

- [Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Depth-first search](https://en.wikipedia.org/wiki/Depth-first_search)
- [Breadth-first search](https://en.wikipedia.org/wiki/Breadth-first_search)

AI was used for: structuring the project into modules, writing and
reviewing the code, drafting this README. All AI-generated content was
reviewed and understood before inclusion.
