# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    mazegen.py                                         :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: mpanzani <mpanzani@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/05 10:00:00 by mpanzani         #+#    #+#              #
#    Updated: 2026/09/05 10:00:00 by mpanzani        ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

"""Generatore di labirinti riusabile (progetto AMAZEING, 42).

Modulo autonomo: contiene la classe MazeGenerator, che genera un
labirinto casuale ma riproducibile e ne trova il percorso piu' breve.

Esempio di utilizzo:

	from mazegen import MazeGenerator

	gen = MazeGenerator(width=20, height=15, seed=42)
	gen.generate(perfect=True, entry=(0, 0), exit=(19, 14))
	maze = gen.grid       # grid[y][x] = 0-15, bit 0-3 = muri N/E/S/W
	path = gen.solve()    # percorso piu' breve come lista di celle (x, y)
"""

import random
from collections import deque

N: int = 1   # moneta del muro NORD
E: int = 2   # moneta del muro EST
S: int = 4   # moneta del muro SUD
W: int = 8   # moneta del muro OVEST

# Disegno della cifra "4" (3 colonne x 4 righe):
#   # . #
#   # . #
#   # # #
#   . . #
FOUR: list[tuple[int, int]] = [
	(0, 0), (2, 0),
	(0, 1), (2, 1),
	(0, 2), (1, 2), (2, 2),
	(2, 3),
]

# Disegno della cifra "2" (3 colonne x 4 righe):
#   # # #
#   . . #
#   # # #
#   # . .
TWO: list[tuple[int, int]] = [
	(0, 0), (1, 0), (2, 0),
	(2, 1),
	(0, 2), (1, 2), (2, 2),
	(0, 3),
]


class MazeGenerator:
	"""Genera labirinti casuali riproducibili e ne trova il percorso.

	Attributes:
		width: larghezza del labirinto in celle.
		height: altezza del labirinto in celle.
		rng: generatore di numeri casuali (parte dal seed).
		grid: griglia del labirinto, grid[y][x] = 0-15 (bit 0-3 = muri N/E/S/W).
		forty_two: celle del pattern "42" (vuota se assente).
		has_42: True se il pattern "42" e' presente.
		entry: coordinate (x, y) dell'entrata.
		exit: coordinate (x, y) dell'uscita.
		perfect: True se l'ultimo labirinto generato e' perfetto.
	"""

	def __init__(self, width: int, height: int, seed: int | None = None) -> None:
		self.width = width
		self.height = height
		self.rng = random.Random(seed)
		self.grid: list[list[int]] = []
		self.forty_two: list[tuple[int, int]] = []
		self.has_42 = False
		self.entry = (0, 0)
		self.exit = (width - 1, height - 1)
		self.perfect = True

	def _in_bounds(self, x: int, y: int) -> bool:
		"""True se (x, y) sta dentro la griglia."""
		if x < 0 or x >= self.width or y < 0 or y >= self.height:
			return False
		return True

	def _has_wall(self, x: int, y: int, mask: int) -> bool:
		"""True se la cella (x, y) ha la moneta 'mask' (muro chiuso)."""
		return (self.grid[y][x] & mask) != 0

	def _remove_wall(self, x: int, y: int, mask: int) -> None:
		"""Toglie la moneta 'mask' dalla cella (x, y): il muro si apre."""
		self.grid[y][x] = self.grid[y][x] - mask

	def _add_wall(self, x: int, y: int, mask: int) -> None:
		"""Rimette la moneta 'mask' nella cella (x, y): il muro si chiude."""
		self.grid[y][x] = self.grid[y][x] + mask

	def generate(self, perfect: bool = True, entry: tuple[int, int] = (0, 0),
	             exit: tuple[int, int] | None = None,
	             with_42: bool = True) -> None:
		"""Genera un nuovo labirinto.

		Args:
			perfect: True per un labirinto perfetto (un solo percorso).
			entry: coordinate (x, y) dell'entrata.
			exit: coordinate (x, y) dell'uscita (None = angolo in basso a destra).
			with_42: True per disegnare il pattern "42" (se c'e' spazio).

		Raises:
			ValueError: entry o exit fuori dai bordi, o uguali tra loro.
		"""
		self.perfect = perfect
		self.entry = entry
		if exit is None:
			self.exit = (self.width - 1, self.height - 1)
		else:
			self.exit = exit

		if not self._in_bounds(self.entry[0], self.entry[1]):
			raise ValueError("entry is outside the maze")
		if not self._in_bounds(self.exit[0], self.exit[1]):
			raise ValueError("exit is outside the maze")
		if self.entry == self.exit:
			raise ValueError("entry and exit must be different")

		self.grid = []
		for y in range(self.height):
			row: list[int] = []
			for x in range(self.width):
				row.append(N + E + S + W)
			self.grid.append(row)

		self._carve_doors()
		self._carve_42(with_42)
		self._carve_maze()
		if not perfect:
			self._carve_extra_walls()

	def _carve_doors(self) -> None:
		"""Apre i muri di confine di entry ed exit rivolti verso l'esterno."""
		for x, y in (self.entry, self.exit):
			if y == 0:
				self._remove_wall(x, y, N)
			if x == self.width - 1:
				self._remove_wall(x, y, E)
			if y == self.height - 1:
				self._remove_wall(x, y, S)
			if x == 0:
				self._remove_wall(x, y, W)

	def _carve_42(self, with_42: bool) -> None:
		"""Disegna il pattern "42" come celle completamente chiuse.

		Le celle del pattern restano chiuse e verranno marcate come gia'
		visitate, cosi' la generazione non le attraversa mai. Se il
		labirinto e' troppo piccolo o il pattern coprirebbe entry/exit,
		si salta e has_42 resta False.
		"""
		self.forty_two = []
		self.has_42 = False
		if not with_42:
			return
		if self.width < 9 or self.height < 6:
			return
		start_x = 1
		start_y = self.height - 6
		pattern: list[tuple[int, int]] = []
		for dx, dy in FOUR:
			pattern.append((start_x + dx, start_y + dy))
		for dx, dy in TWO:
			pattern.append((start_x + 4 + dx, start_y + dy))
		for cell in pattern:
			if cell == self.entry or cell == self.exit:
				return
		self.forty_two = pattern
		self.has_42 = True

	def _carve_maze(self) -> None:
		"""Genera il labirinto perfetto (recursive backtracker iterativo).

		Parte da entry, visita i vicini non ancora visitati togliendo il
		muro tra le due celle (da entrambi i lati), e torna indietro
		quando non ha piu' vicini disponibili.
		"""
		visited: list[list[bool]] = []
		for y in range(self.height):
			row: list[bool] = []
			for x in range(self.width):
				row.append(False)
			visited.append(row)

		for x, y in self.forty_two:
			visited[y][x] = True

		stack: list[tuple[int, int]] = [self.entry]
		visited[self.entry[1]][self.entry[0]] = True

		while len(stack) > 0:
			x, y = stack[len(stack) - 1]
			neighbors = self._unvisited_neighbors(x, y, visited)
			if len(neighbors) == 0:
				stack.pop()
			else:
				nx, ny, mask_here, mask_there = self.rng.choice(neighbors)
				self._remove_wall(x, y, mask_here)
				self._remove_wall(nx, ny, mask_there)
				visited[ny][nx] = True
				stack.append((nx, ny))

	def _unvisited_neighbors(self, x: int, y: int,
	                         visited: list[list[bool]]) -> list[tuple[int, int, int, int]]:
		"""Vicini non ancora visitati di (x, y).

		Per ogni vicino restituisce anche la moneta del muro dal lato di
		(x, y) e la moneta speculare dal lato del vicino.
		"""
		neighbors: list[tuple[int, int, int, int]] = []
		if y > 0 and not visited[y - 1][x]:
			neighbors.append((x, y - 1, N, S))
		if x < self.width - 1 and not visited[y][x + 1]:
			neighbors.append((x + 1, y, E, W))
		if y < self.height - 1 and not visited[y + 1][x]:
			neighbors.append((x, y + 1, S, N))
		if x > 0 and not visited[y][x - 1]:
			neighbors.append((x - 1, y, W, E))
		return neighbors

	def _carve_extra_walls(self) -> None:
		"""Apre muri interni extra per creare cicli (labirinto non perfetto).

		Ogni apertura viene controllata: non deve creare un'area aperta
		3x3 (corridoi larghi al massimo 2 celle), e non deve toccare il
		pattern "42".
		"""
		for _ in range(20):
			x = self.rng.randrange(self.width)
			y = self.rng.randrange(self.height)
			mask = self.rng.choice([N, E, S, W])
			nx = x
			ny = y
			mask_here = mask
			mask_there = mask
			if mask == N and y > 0:
				ny = y - 1
				mask_there = S
			elif mask == E and x < self.width - 1:
				nx = x + 1
				mask_there = W
			elif mask == S and y < self.height - 1:
				ny = y + 1
				mask_there = N
			elif mask == W and x > 0:
				nx = x - 1
				mask_there = E
			else:
				continue
			if (x, y) in self.forty_two or (nx, ny) in self.forty_two:
				continue
			if not self._has_wall(x, y, mask_here):
				continue
			self._remove_wall(x, y, mask_here)
			self._remove_wall(nx, ny, mask_there)
			if self._has_3x3_open():
				self._add_wall(x, y, mask_here)
				self._add_wall(nx, ny, mask_there)

	def _has_3x3_open(self) -> bool:
		"""True se esiste una zona aperta di 3x3 celle (12 muri interni aperti)."""
		for y in range(self.height - 2):
			for x in range(self.width - 2):
				if self._window_3x3_open(x, y):
					return True
		return False

	def _window_3x3_open(self, x: int, y: int) -> bool:
		"""True se la finestra 3x3 con angolo in alto a sinistra (x, y) e' tutta aperta."""
		for wy in range(y, y + 2):
			for wx in range(x, x + 3):
				if self._has_wall(wx, wy, S):
					return False
		for wy in range(y, y + 3):
			for wx in range(x, x + 2):
				if self._has_wall(wx, wy, E):
					return False
		return True

	def solve(self) -> list[tuple[int, int]]:
		"""Trova il percorso piu' breve da entry a exit (BFS).

		Returns:
			Lista di celle da entry a exit incluse, o lista vuota se
			l'uscita non e' raggiungibile.
		"""
		queue: deque[tuple[int, int]] = deque()
		queue.append(self.entry)
		came_from: dict[tuple[int, int], tuple[int, int] | None] = {}
		came_from[self.entry] = None

		while len(queue) > 0:
			x, y = queue.popleft()
			if (x, y) == self.exit:
				break
			if y > 0 and not self._has_wall(x, y, N):
				self._add_neighbor(queue, came_from, x, y - 1, x, y)
			if x < self.width - 1 and not self._has_wall(x, y, E):
				self._add_neighbor(queue, came_from, x + 1, y, x, y)
			if y < self.height - 1 and not self._has_wall(x, y, S):
				self._add_neighbor(queue, came_from, x, y + 1, x, y)
			if x > 0 and not self._has_wall(x, y, W):
				self._add_neighbor(queue, came_from, x - 1, y, x, y)

		if self.exit not in came_from:
			return []

		path: list[tuple[int, int]] = []
		cell: tuple[int, int] | None = self.exit
		while cell is not None:
			path.append(cell)
			cell = came_from[cell]
		path.reverse()
		return path

	def _add_neighbor(self, queue: deque[tuple[int, int]],
	                  came_from: dict[tuple[int, int], tuple[int, int] | None],
	                  nx: int, ny: int, x: int, y: int) -> None:
		"""Aggiunge il vicino (nx, ny) alla coda se non e' mai stato visto."""
		if (nx, ny) not in came_from:
			came_from[(nx, ny)] = (x, y)
			queue.append((nx, ny))
