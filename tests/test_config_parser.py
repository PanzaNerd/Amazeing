
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
    """Il config completo: il parser restituisce ogni campo giusto."""
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
    """Senza PERFECT: ConfigError che nomina la chiave mancante."""
    content = VALID.replace("PERFECT=True\n", "")
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ConfigError, match="PERFECT"):
            parse_config(_write(tmpdir, content))


def test_duplicate_key() -> None:
    """Chiave ripetuta: ConfigError duplicate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ConfigError, match="duplicate"):
            parse_config(_write(tmpdir, VALID + "WIDTH=10\n"))


def test_bad_integer() -> None:
    """WIDTH=abc non e' un numero: ConfigError su WIDTH."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad = VALID.replace("WIDTH=20", "WIDTH=abc")
        with pytest.raises(ConfigError, match="WIDTH"):
            parse_config(_write(tmpdir, bad))


def test_bad_coords() -> None:
    """ENTRY senza virgola: ConfigError su ENTRY."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad = VALID.replace("ENTRY=0,0", "ENTRY=abc")
        with pytest.raises(ConfigError, match="ENTRY"):
            parse_config(_write(tmpdir, bad))


def test_out_of_bounds() -> None:
    """EXIT fuori dalla griglia: ConfigError outside."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad = VALID.replace("EXIT=19,14", "EXIT=99,99")
        with pytest.raises(ConfigError, match="outside"):
            parse_config(_write(tmpdir, bad))


def test_entry_equals_exit() -> None:
    """ENTRY ed EXIT uguali: ConfigError different."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad = VALID.replace("EXIT=19,14", "EXIT=0,0")
        with pytest.raises(ConfigError, match="different"):
            parse_config(_write(tmpdir, bad))


def test_bad_perfect() -> None:
    """PERFECT=maybe: ConfigError su PERFECT."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad = VALID.replace("PERFECT=True", "PERFECT=maybe")
        with pytest.raises(ConfigError, match="PERFECT"):
            parse_config(_write(tmpdir, bad))


def test_lowercase_keys_ok() -> None:
    """Le chiavi minuscole vanno bene (il subject le ammette)."""
    content = "\n".join([
        "width=20",
        "height=15",
        "entry=0,0",
        "exit=19,14",
        "output_file=maze.txt",
        "perfect=true",
        "seed=42",
    ])
    with tempfile.TemporaryDirectory() as tmpdir:
        config = parse_config(_write(tmpdir, content + "\n"))
    assert config.width == 20
    assert config.height == 15
    assert config.perfect is True
    assert config.seed == 42


def test_duplicate_key_case_insensitive() -> None:
    """Doppione anche in minuscolo: duplicate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ConfigError, match="duplicate"):
            parse_config(_write(tmpdir, VALID + "width=10\n"))


def test_unknown_keys_ignored() -> None:
    """Chiavi sconosciute: ignorate senza errori."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = parse_config(_write(tmpdir, VALID + "ALGORITHM=dfs\n"))
    assert config.perfect is True


def test_no_seed_is_none() -> None:
    """Senza SEED il campo resta None (labirinto casuale)."""
    content = VALID.replace("SEED=42\n", "")
    with tempfile.TemporaryDirectory() as tmpdir:
        config = parse_config(_write(tmpdir, content))
    assert config.seed is None


def test_small_size_rejected() -> None:
    """WIDTH=1: rifiutato, serve almeno 2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ConfigError, match="at least 2"):
            parse_config(_write(tmpdir, VALID.replace("WIDTH=20", "WIDTH=1")))


def test_syntax_error_line() -> None:
    """Riga senza '=': ConfigError KEY=VALUE."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ConfigError, match="KEY=VALUE"):
            parse_config(_write(tmpdir, VALID + "no_equals_here\n"))
