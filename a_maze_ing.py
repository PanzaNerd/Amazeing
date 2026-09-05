# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    a_maze_ing.py                                      :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: mpanzani <mpanzani@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/05 10:00:00 by mpanzani         #+#    #+#              #
#    Updated: 2026/09/05 10:00:00 by mpanzani        ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

"""Programma principale del generatore di labirinti AMAZEING.

Uso: python3 a_maze_ing.py config.txt
"""

import sys

import config_parser
import display
import mazegen
import output_writer


def main() -> None:
	"""Esegue il flusso completo: parse, generazione, output, display."""
	if len(sys.argv) != 2:
		print(f"Usage: python3 {sys.argv[0]} config.txt")
		sys.exit(1)

	try:
		config = config_parser.parse_config(sys.argv[1])
	except config_parser.ConfigError as e:
		print(f"Error: {e}")
		sys.exit(1)
	except OSError:
		print(f"Error: cannot read config file '{sys.argv[1]}'")
		sys.exit(1)

	gen = mazegen.MazeGenerator(config.width, config.height, config.seed)
	gen.generate(perfect=config.perfect, entry=config.entry,
	             exit=config.exit)

	path = gen.solve()
	output_writer.write_output_file(gen.grid, config.entry, config.exit,
	                                path, config.output_file)

	if not gen.has_42:
		print("Error: maze too small, '42' pattern omitted")

	display.run(gen)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print()
		sys.exit(0)
	except Exception as e:
		print(f"Unexpected error: {e}")
		sys.exit(1)
