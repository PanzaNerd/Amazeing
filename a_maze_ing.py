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
	"""Il direttore d'orchestra: chiama i moduli nell'ordine delle tappe."""
	# tappa 0: servono ESATTAMENTE il nome del programma e il config
	if len(sys.argv) != 2:
		print(f"Usage: python3 {sys.argv[0]} config.txt")
		sys.exit(1)

	# TAPPA A: parse del config, protetto dalle reti di sicurezza
	try:
		config = config_parser.parse_config(sys.argv[1])
	except config_parser.ConfigError as e:
		print(f"Error: {e}")
		sys.exit(1)
	# la seconda rete: il file non esiste (open fallisce in parse_config)
	except OSError:
		print(f"Error: cannot read config file '{sys.argv[1]}'")
		sys.exit(1)

	# TAPPA B: la talpa, il piccone e il 42 lavorano qui
	gen = mazegen.MazeGenerator(config.width, config.height, config.seed)
	gen.generate(perfect=config.perfect, entry=config.entry,
	             exit=config.exit)

	# TAPPA C: il FUOCO trova il percorso piu' breve
	path = gen.solve()
	# TAPPA D: il file esadecimale
	output_writer.write_output_file(gen.grid, config.entry, config.exit,
	                                path, config.output_file)

	# il resoconto del 42: se manca, il messaggio richiesto dal subject
	if not gen.has_42:
		print("Error: maze too small, '42' pattern omitted")

	# TAPPA E: il terminale interattivo
	display.run(gen)


# il pulsante di avvio: parte solo se il file viene ESEGUITO
if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		# Ctrl+C: l'utente ha chiuso lui, non e' un errore
		print()
		sys.exit(0)
	except Exception as e:
		# l'ultima rete: mai traceback sullo schermo
		print(f"Unexpected error: {e}")
		sys.exit(1)
