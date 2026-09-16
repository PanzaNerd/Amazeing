# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    test_mazegen.py                                    :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: mpanzani <mpanzani@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/16 10:00:00 by mpanzani         #+#    #+#              #
#    Updated: 2026/09/16 10:00:00 by mpanzani        ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

"""Test per mazegen."""

from collections import deque

from mazegen import E, N, S, W, MazeGenerator


def _reachable_cells(gen: MazeGenerator) -> set[tuple[int, int]]:
	"""Tutte le celle raggiungibili da entry passando da muri aperti."""
	reachable: set[tuple[int, int]] = {gen.entry}
	queue: deque[tuple[int, int]] = deque([gen.entry])
	while len(queue) > 0:
		x, y = queue.popleft()
		if not gen._has_wall(x, y, N) and (x, y - 1) not in reachable:
			reachable.add((x, y - 1))
			queue.append((x, y - 1))
		if not gen._has_wall(x, y, E) and (x + 1, y) not in reachable:
			reachable.add((x + 1, y))
			queue.append((x + 1, y))
		if not gen._has_wall(x, y, S) and (x, y + 1) not in reachable:
			reachable.add((x, y + 1))
			queue.append((x, y + 1))
		if not gen._has_wall(x, y, W) and (x - 1, y) not in reachable:
			reachable.add((x - 1, y))
			queue.append((x - 1, y))
	return reachable


def _free_cells(gen: MazeGenerator) -> set[tuple[int, int]]:
	"""Tutte le celle che non sono mattoncini del pattern 42."""
	free: set[tuple[int, int]] = set()
	for y in range(gen.height):
		for x in range(gen.width):
			if (x, y) not in gen.forty_two:
				free.add((x, y))
	return free


def test_full_connectivity_with_42() -> None:
	"""Ogni cella libera e' raggiungibile da entry, e il percorso esiste.

	Le misure basse coprono il bug del 42: con 5 righe il labirinto si
	spezzava in parti non collegate, con 6 righe due celle restavano
	isolate nel "buco" del 4 contro il bordo.
	"""
	for width, height in [(9, 5), (10, 5), (20, 5), (9, 6), (10, 6),
	                      (20, 6), (9, 7), (10, 7), (20, 15)]:
		gen = MazeGenerator(width, height, seed=42)
		gen.generate(perfect=True)
		assert len(gen.solve()) > 0
		unreachable = _free_cells(gen) - _reachable_cells(gen)
		assert len(unreachable) == 0


def test_full_connectivity_not_perfect() -> None:
	"""Le aperture extra non devono scollegare nulla nemmeno a 9x6."""
	for width, height in [(9, 6), (20, 15)]:
		gen = MazeGenerator(width, height, seed=42)
		gen.generate(perfect=False)
		assert len(gen.solve()) > 0
		unreachable = _free_cells(gen) - _reachable_cells(gen)
		assert len(unreachable) == 0


def test_42_placement_threshold() -> None:
	"""Il 42 si disegna solo da 9x6 in su (una riga libera sopra le cifre)."""
	for width, height, expected in [(8, 7, False), (9, 5, False),
	                                (9, 6, True), (9, 7, True),
	                                (20, 15, True)]:
		gen = MazeGenerator(width, height, seed=42)
		gen.generate(perfect=True)
		assert gen.has_42 is expected


def test_42_bricks_fully_closed() -> None:
	"""Ogni mattoncino del 42 ha tutti e 4 i muri chiusi (valore 15)."""
	gen = MazeGenerator(20, 15, seed=42)
	gen.generate(perfect=True)
	assert gen.has_42 is True
	for x, y in gen.forty_two:
		assert gen.grid[y][x] == N + E + S + W
