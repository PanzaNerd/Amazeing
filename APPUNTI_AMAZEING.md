# APPUNTI AMAZEING — generatore di labirinti

Ogni pezzo è raccontato **nell'ordine in cui si esegue il codice**: si parte
dal main e si segue il flusso passo per passo. Poi codice, poi teoria.

---

# Il progetto in parole semplici

## Cosa facciamo

Il programma legge un file di configurazione (`config.txt`), genera un
labirinto casuale ma **riproducibile**, lo scrive in un file in formato
esadecimale e lo mostra nel terminale con colori e interazioni.

## Il labirinto è una griglia

Un labirinto di WIDTH=20 e HEIGHT=15 è una tabella di 20 colonne × 15 righe.
Ogni casella (cella) ha fino a 4 muri: NORD, EST, SUD, OVEST.
Due celle vicine sono collegate se il muro tra loro è **aperto** (tolto).

## I muri sono bit

Per ogni cella memorizziamo un numero da 0 a 15. In binario sono 4 bit,
uno per muro:

| Bit | Valore | Muro |
|-----|--------|------|
| 0   | 1      | NORD chiuso |
| 1   | 2      | EST chiuso |
| 2   | 4      | SUD chiuso |
| 3   | 8      | OVEST chiuso |

Esempio: cella = 5 (binario 0101) → NORD chiuso (1) + SUD chiuso (4) +
EST aperto + OVEST aperto. In esadecimale 0-15 si scrive con una sola
cifra: 10 = A, 15 = F. Per questo il file di output ha UNA cifra per cella.

È la stessa idea di `flags` bit-a-bit in C: `cell & 1` per il muro NORD.

## Il seed: la casualità riproducibile

"Casuale ma riproducibile" sembra una contraddizione: in realtà la
casualità del computer è una sequenza di numeri calcolata da un punto di
partenza. Se il punto di partenza (il **seed**) è lo stesso, la sequenza è
identica → stesso labirinto. `random.Random(42)` in Python = `srand(42)`
in C.

## Labirinto perfetto

"Perfetto" = tra due celle qualsiasi esiste UN SOLO percorso (è un albero,
in termini di grafi). L'algoritmo "recursive backtracker" (una DFS) lo
garantisce gratis: parte da una cella, visita un vicino mai visitato
togliendo il muro tra loro, e quando è bloccato torna indietro.

## Il "42"

Il subject vuole un "42" visibile nel labirinto, disegnato con celle
completamente chiuse (tutti e 4 i muri, valore F). Quelle celle sono
"isole" inaccessibili: la generazione non le tocca. Se il labirinto è
troppo piccolo si omette e si stampa un errore (il programma continua).

## Il percorso più breve: BFS

Il percorso entrata→uscita lo trova la BFS (Breadth-First Search): parto
dall'entrata, visito tutti i vicini raggiungibili (distanza 1), poi i
loro vicini (distanza 2), ecc. La prima volta che arrivo all'uscita ho il
percorso più breve. È come un'onda che si allarga.

## Il file di output

1. Una riga per riga del labirinto, una cifra esadecimale per cella
2. Una riga vuota
3. Tre righe: coordinate entrata, coordinate uscita, percorso NESW
   (es. `EESSWW` = Est, Est, Sud, Sud, Ovest, Ovest)

## Chi fa cosa

- **mpanzani:** config_parser.py (legge il config), output_writer.py
  (scrive il file), a_maze_ing.py (main), Makefile, README, test,
  pacchetto pip
- **roblomba:** mazegen.py (classe MazeGenerator + BFS), display.py
  (terminale interattivo)

## Glossario

- **nibble:** 4 bit = mezza byte = una cifra esadecimale
- **BFS:** visita in ampiezza, trova il percorso più corto
- **DFS:** visita in profondità, alla base del recursive backtracker
- **albero ricoprente:** grafo connesso senza cicli che tocca tutte le celle

---

# config_parser.py — leggere e validare il config

**Cosa chiede:** leggere `config.txt` (righe `KEY=VALUE`, `#` = commento),
validare tutto (chiavi obbligatorie, numeri, coordinate nei bordi,
entry ≠ exit, PERFECT bool) e restituire un oggetto `Config`.

**Esecuzione:** (dal main) `parse_config("config.txt")` →
1. `values = {}` — dizionario vuoto
2. `with open(...) as f:` apre il file (chiusura automatica a fine blocco,
   anche con errori — è il `finally` di p02 fatto dal linguaggio)
3. per ogni riga (`enumerate(f, start=1)` conta le righe da 1):
   - `strip()` toglie spazi e `\n`
   - salta righe vuote e commenti `#`
   - senza `=` → `raise ConfigError` con numero di riga
   - `split("=", 1)` → chiave e valore (diviso solo al PRIMO =)
   - chiave già vista → `raise ConfigError` (duplicato)
   - `values[key] = value`
4. `REQUIRED_KEYS - set(values)` → chiavi obbligatorie mancanti → errore
5. `_parse_int` su WIDTH/HEIGHT: `int(raw)` fallisce → `raise ... from None`
   (da ValueError a ConfigError con messaggio chiaro; `from None` toglie il
   doppio traceback)
6. WIDTH/HEIGHT < 2 → errore (1x1 non è un labirinto)
7. `_parse_coords` su ENTRY/EXIT: `"0,0"` → `(0, 0)` (split su `,` + int)
8. `_check_bounds`: le coordinate devono stare nella griglia
9. entry == exit → errore
10. `_parse_bool` su PERFECT: solo esattamente True/False
11. OUTPUT_FILE non vuoto
12. SEED opzionale: se manca → `None` (casuale a ogni run)
13. `return Config(...)` — il @dataclass ha già il costruttore pronto

**Codice:** in `python/AMAZEING/config_parser.py`

**Teoria:**
- `raise` sostituisce i return code del C: se nessuno cattura, il programma
  si ferma → impossibile ignorare l'errore per sbaglio
- `@dataclass(frozen=True)` = struct del C con `__init__`/`__eq__`/`__repr__`
  generati; frozen = immutabile come `const`
- `with` = context manager: chiusura automatica delle risorse
- `int | None` = Optional, serve per mypy --strict
- f-string = `printf` di Python
- `enumerate` = contatore automatico nel loop (niente `int i = 0; i++`)
- `split("=", 1)`: il secondo argomento limita le divisioni a 1

**Errori gestiti (tutti ConfigError):** chiave mancante, duplicata, int
invalido, coordinate malformate, fuori bordi, entry==exit, PERFECT non bool,
OUTPUT_FILE vuoto, riga senza `=`. File inesistente → OSError propaga al main.
