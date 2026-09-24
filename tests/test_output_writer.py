
"""Test per output_writer."""

import os
import tempfile

from output_writer import path_to_nesw, write_output_file


def test_path_to_nesw_simple() -> None:
    """Le celle diventano le lettere N/E/S/W giuste: 'ESW'."""
    path = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert path_to_nesw(path) == "ESW"


def test_path_to_nesw_empty() -> None:
    """Lista vuota: stringa vuota (nessun passo)."""
    assert path_to_nesw([]) == ""


def test_path_to_nesw_single_cell() -> None:
    """Una cella sola: nessun passo, stringa vuota."""
    assert path_to_nesw([(1, 1)]) == ""


def test_write_output_file_format() -> None:
    """Il file esce nel formato del subject:
    griglia esadecimale, riga vuota, entry, exit, percorso."""
    grid = [[3, 10], [12, 5]]
    path = [(0, 0), (1, 0), (1, 1)]
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "maze.txt")
        write_output_file(grid, (0, 0), (1, 1), path, out)
        with open(out, "r", encoding="utf-8") as f:
            lines = f.readlines()
    assert lines[0] == "3A\n"
    assert lines[1] == "C5\n"
    assert lines[2] == "\n"
    assert lines[3] == "0,0\n"
    assert lines[4] == "1,1\n"
    assert lines[5] == "ES\n"
