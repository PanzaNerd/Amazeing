# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    output_writer.py                                   :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: mpanzani <mpanzani@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/05 10:00:00 by mpanzani         #+#    #+#              #
#    Updated: 2026/09/05 10:00:00 by mpanzani        ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

"""Scrittura del labirinto nel file di output in formato esadecimale."""

HEX_DIGITS: str = "0123456789ABCDEF"


def path_to_nesw(path: list[tuple[int, int]]) -> str:
	"""Converte una lista di celle in una stringa di direzioni NESW.

	Args:
		path: lista di coordinate (x, y) consecutive, da entry a exit.

	Returns:
		Stringa con una lettera N/E/S/W per ogni passo.
	"""
	result = ""
	for i in range(len(path) - 1):
		x1, y1 = path[i]
		x2, y2 = path[i + 1]
		if x2 == x1 + 1:
			result = result + "E"
		elif x2 == x1 - 1:
			result = result + "W"
		elif y2 == y1 - 1:
			result = result + "N"
		elif y2 == y1 + 1:
			result = result + "S"
		else:
			raise ValueError("non-adjacent cells in path")
	return result


def write_output_file(grid: list[list[int]], entry: tuple[int, int],
                      exit_: tuple[int, int], path: list[tuple[int, int]],
                      filename: str) -> None:
	"""Scrive il labirinto nel file di output richiesto dal subject.

	Formato: una riga per riga della griglia, ogni cella come cifra
	esadecimale (bit 0-3 = muri N/E/S/W); riga vuota; poi su tre righe
	entry, exit e percorso NESW. Ogni riga termina con newline.

	Args:
		grid: griglia del labirinto (grid[y][x] = 0-15).
		entry: coordinate (x, y) dell'entrata.
		exit_: coordinate (x, y) dell'uscita.
		path: percorso piu' breve come lista di celle.
		filename: nome del file da scrivere.
	"""
	with open(filename, "w", encoding="utf-8") as f:
		for row in grid:
			line = ""
			for cell in row:
				line = line + HEX_DIGITS[cell]
			f.write(line + "\n")
		f.write("\n")
		f.write(f"{entry[0]},{entry[1]}\n")
		f.write(f"{exit_[0]},{exit_[1]}\n")
		f.write(path_to_nesw(path) + "\n")
