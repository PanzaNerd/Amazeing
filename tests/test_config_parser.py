# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    test_config_parser.py                              :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: mpanzani <mpanzani@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/05 10:00:00 by mpanzani         #+#    #+#              #
#    Updated: 2026/09/05 10:00:00 by mpanzani        ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

"""Test per config_parser."""

import os
import tempfile

import pytest

from config_parser import ConfigError, parse_config

VALID = (
	"# maze config\n"
	"WIDTH=20\n"
	"HEIGHT=15\n"
	"ENTRY=0,0\n"
	"EXIT=19,14\n"
	"OUTPUT_FILE=maze.txt\n"
	"PERFECT=True\n"
	"SEED=42\n"
)


def _write(tmpdir: str, content: str) -> str:
	"""Scrive content in un file temporaneo e ne restituisce il percorso."""
	path = os.path.join(tmpdir, "config.txt")
	with open(path, "w", encoding="utf-8") as f:
		f.write(content)
	return path


def test_valid_config() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		config = parse_config(_write(tmpdir, VALID))
	assert config.width == 20
	assert config.height == 15
	assert config.entry == (0, 0)
	assert config.exit == (19, 14)
	assert config.output_file == "maze.txt"
	assert config.perfect is True
	assert config.seed == 42


def test_missing_key() -> None:
	content = VALID.replace("PERFECT=True\n", "")
	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(ConfigError, match="PERFECT"):
			parse_config(_write(tmpdir, content))


def test_duplicate_key() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(ConfigError, match="duplicate"):
			parse_config(_write(tmpdir, VALID + "WIDTH=10\n"))


def test_bad_integer() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(ConfigError, match="WIDTH"):
			parse_config(_write(tmpdir, VALID.replace("WIDTH=20", "WIDTH=abc")))


def test_bad_coords() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(ConfigError, match="ENTRY"):
			parse_config(_write(tmpdir, VALID.replace("ENTRY=0,0", "ENTRY=abc")))


def test_out_of_bounds() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(ConfigError, match="outside"):
			parse_config(_write(tmpdir, VALID.replace("EXIT=19,14", "EXIT=99,99")))


def test_entry_equals_exit() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(ConfigError, match="different"):
			parse_config(_write(tmpdir, VALID.replace("EXIT=19,14", "EXIT=0,0")))


def test_bad_perfect() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(ConfigError, match="PERFECT"):
			parse_config(_write(tmpdir, VALID.replace("PERFECT=True", "PERFECT=maybe")))


def test_unknown_keys_ignored() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		config = parse_config(_write(tmpdir, VALID + "ALGORITHM=dfs\n"))
	assert config.perfect is True


def test_no_seed_is_none() -> None:
	content = VALID.replace("SEED=42\n", "")
	with tempfile.TemporaryDirectory() as tmpdir:
		config = parse_config(_write(tmpdir, content))
	assert config.seed is None


def test_small_size_rejected() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(ConfigError, match="at least 2"):
			parse_config(_write(tmpdir, VALID.replace("WIDTH=20", "WIDTH=1")))


def test_syntax_error_line() -> None:
	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(ConfigError, match="KEY=VALUE"):
			parse_config(_write(tmpdir, VALID + "no_equals_here\n"))
