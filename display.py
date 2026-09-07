# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    display.py                                         :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: mpanzani <mpanzani@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/05 10:00:00 by mpanzani         #+#    #+#              #
#    Updated: 2026/09/05 10:00:00 by mpanzani        ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

"""Visualizzazione del labirinto nel terminale (ASCII minimale, interattivo).

Ogni cella occupa UN carattere e ogni muro UN carattere: '─'
orizzontali, '│' verticali, incroci '┼'. Un labirinto 20x15 e' largo
41 caratteri.
"""

from mazegen import N, S, W, MazeGenerator

RED: str = "\033[31m"
GREEN: str = "\033[32m"
BLUE: str = "\033[34m"
MAGENTA: str = "\033[35m"
CYAN: str = "\033[36m"
NORMAL: str = ""
DOT: str = "·"
NO_BG: str = "\033[49m"
RESET: str = "\033[0m"
CLEAR: str = "\033[2J\033[H"

# colori dei muri ciclabili con '3' (visibili su sfondo chiaro e scuro;
# il verde NON c'e': e' riservato alla catena del percorso)
WALL_COLORS: list[str] = [RED, BLUE, MAGENTA, CYAN]

# stessi colori come SFONDI: riempiono le celle del pattern "42",
# cosi' il 42 e' un blocco uniforme dello stesso colore dei muri
WALL_BGS: list[str] = ["\033[41m", "\033[44m", "\033[45m", "\033[46m"]


def run(gen: MazeGenerator) -> None:
	"""Mostra il labirinto con un menu numerato.

	1 = regenerate maze, 2 = show/hide path, 3 = change wall colour,
	q = quit.
	"""
	show_path = False
	color_index = 0
	while True:
		print(CLEAR)
		print("===== A-MAZE-ING =====")
		print()
		_print_maze(gen, show_path, WALL_COLORS[color_index],
		            WALL_BGS[color_index])
		print("+--------------------------------------+")
		print("| 1) Regenerate maze                   |")
		print("| 2) Show/hide path                    |")
		print("| 3) Change wall colour                |")
		print("| q) Quit                              |")
		print("+--------------------------------------+")
		cmd = input("Choice > ").strip().lower()
		if cmd == "1":
			gen.generate(perfect=gen.perfect, entry=gen.entry,
			             exit=gen.exit, with_42=True)
			show_path = False
		elif cmd == "2":
			show_path = not show_path
		elif cmd == "3":
			color_index = (color_index + 1) % len(WALL_COLORS)
		elif cmd == "q":
			break


def _print_maze(gen: MazeGenerator, show_path: bool, wall_color: str,
                wall_bg: str) -> None:
	"""Disegna il labirinto minimale: 1 cella = 1 carattere.

	Muri '─' e '│' con incroci giusti ('┼', '┬', '┴', '├', '┤', '┌',
	'┐', '└', '┘'). Le celle del pattern "42" sono quadratini PIENI
	dello stesso colore dei muri: con i muri interni dello stesso
	colore il 42 appare come un blocco unico e uniforme. I = entrata,
	O = uscita, percorso = catena di punti '·' verdi.
	"""
	path: list[tuple[int, int]] = []
	if show_path:
		path = gen.solve()

	path_n: list[tuple[int, int]] = []
	path_w: list[tuple[int, int]] = []
	for i in range(len(path) - 1):
		x1, y1 = path[i]
		x2, y2 = path[i + 1]
		if y2 == y1 - 1:
			path_n.append((x1, y1))
		elif y2 == y1 + 1:
			path_n.append((x2, y2))
		elif x2 == x1 + 1:
			path_w.append((x2, y2))
		else:
			path_w.append((x1, y1))

	for y in range(gen.height):
		wall = ""
		for x in range(gen.width):
			wall = wall + _junction(gen, x, y)
			if (gen.grid[y][x] & N) != 0:
				wall = wall + "─"
			else:
				if (x, y) in path_n:
					wall = wall + GREEN + DOT + wall_color
				else:
					wall = wall + " "
		wall = wall + _junction(gen, gen.width, y)
		print(wall_color + wall)

		line = ""
		for x in range(gen.width):
			if (gen.grid[y][x] & W) != 0:
				line = line + "│"
			else:
				if (x, y) in path_w:
					line = line + GREEN + DOT + wall_color
				else:
					line = line + " "
			if (x, y) in gen.forty_two:
				line = line + wall_bg + " " + NO_BG + wall_color
			elif (x, y) == gen.entry:
				line = line + NORMAL + "I" + wall_color
			elif (x, y) == gen.exit:
				line = line + NORMAL + "O" + wall_color
			elif (x, y) in path:
				line = line + GREEN + DOT + wall_color
			else:
				line = line + " "
		line = line + "│"
		print(wall_color + line)

	bottom = ""
	for x in range(gen.width):
		bottom = bottom + _junction(gen, x, gen.height)
		if (gen.grid[gen.height - 1][x] & S) != 0:
			bottom = bottom + "─"
		else:
			bottom = bottom + " "
	bottom = bottom + _junction(gen, gen.width, gen.height)
	print(wall_color + bottom)
	print(RESET)


def _junction(gen: MazeGenerator, x: int, y: int) -> str:
	"""Carattere del nodo della griglia alla colonna x della linea di muro y.

	Guarda se dal nodo partono muri verso sinistra, destra, sopra e
	sotto e sceglie il glifo giusto ('┼', '┬', '┴', '├', '┤', '┌',
	'┐', '└', '┘', '─', '│'). Per la linea di fondo (y == height)
	guarda i muri S dell'ultima riga.
	"""
	if y < gen.height:
		left = x > 0 and (gen.grid[y][x - 1] & N) != 0
		right = x < gen.width and (gen.grid[y][x] & N) != 0
		if x < gen.width:
			up = y > 0 and (gen.grid[y - 1][x] & W) != 0
			down = (gen.grid[y][x] & W) != 0
		else:
			up = y > 0
			down = True
	else:
		left = x > 0 and (gen.grid[gen.height - 1][x - 1] & S) != 0
		right = x < gen.width and (gen.grid[gen.height - 1][x] & S) != 0
		if x < gen.width:
			up = (gen.grid[gen.height - 1][x] & W) != 0
		else:
			up = True
		down = False

	if up and down and left and right:
		return "┼"
	if up and down and left:
		return "┤"
	if up and down and right:
		return "├"
	if left and right and up:
		return "┴"
	if left and right and down:
		return "┬"
	if left and right:
		return "─"
	if up and down:
		return "│"
	if left and up:
		return "┘"
	if left and down:
		return "┐"
	if right and up:
		return "└"
	if right and down:
		return "┌"
	if left or right:
		return "─"
	if up or down:
		return "│"
	return " "
