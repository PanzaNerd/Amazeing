# APPUNTI AMAZEING — generatore di labirinti

Questo file serve SOLO a capire. Segue **la cronologia del programma**:
si parte dall'input e si va avanti nell'ordine in cui il codice si
esegue. Ogni sezione risponde a: **cos'è → cosa viene preso → come viene
letto/elaborato → cosa ne deriva**. Niente codice, illustrazioni semplici.

## INDICE

1. La cronologia del programma (la mappa)
   - 1.1 L'INPUT: config.txt
   - 1.2 La griglia e i muri (decimale, binario, esadecimale)
   - 1.3 Il seed
   - 1.4 La generazione (backtracker, PERFECT=False, il "42")
   - 1.5 Il percorso più breve (BFS)
   - 1.6 L'OUTPUT: il file esadecimale
   - 1.7 Il display interattivo
   - 1.8 Il main e la gestione errori
2. I moduli: chi fa cosa
3. Glossario

---

# 1. La cronologia del programma (la mappa)

```
python3 a_maze_ing.py config.txt

1. INPUT        config.txt ──▶ Config
                (width, height, entry, exit, output_file, perfect, seed)

2. GENERAZIONE  Config ──▶ il generatore decide i muri ──▶ griglia di celle

3. SOLUZIONE    griglia ──▶ BFS ──▶ percorso entrata→uscita

4. OUTPUT       griglia + percorso ──▶ file esadecimale

5. DISPLAY      griglia + percorso ──▶ terminale interattivo
```

## 1.1 L'INPUT: config.txt

### Cos'è

`config.txt` è un **file di testo** con una riga `KEY=VALUE` per riga.
Le righe che iniziano con `#` sono commenti e vengono ignorate. Esempio
(il nostro config di default):

```
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
```

### Cosa viene preso

Nel file TUTTO è testo: anche "20" è la parola "20", non il numero 20.
Il parser (il pezzo che legge il file) converte ogni valore nel tipo
giusto:

| Riga del file | Cosa c'è scritto | In cosa viene convertito |
|---------------|------------------|--------------------------|
| WIDTH=20 | testo "20" | numero decimale 20 |
| HEIGHT=15 | testo "15" | numero decimale 15 |
| ENTRY=0,0 | testo "0,0" | coppia di numeri (0, 0) |
| EXIT=19,14 | testo "19,14" | coppia di numeri (19, 14) |
| OUTPUT_FILE=maze.txt | testo | resta testo |
| PERFECT=True | testo "True" | valore di verità True |
| SEED=42 | testo "42" | numero decimale 42 |

### Come viene letto

1. Si apre il file e si leggono le righe una a una
2. Righe vuote e commenti (`#`) vengono saltati
3. Ogni riga viene spezzata in due al segno `=`: chiave e valore
4. Ogni coppia finisce in una tabella chiave→valore (il dizionario)
5. Alla fine si controlla che ci siano TUTTE le chiavi obbligatorie:
   WIDTH, HEIGHT, ENTRY, EXIT, OUTPUT_FILE, PERFECT
6. Poi ogni valore viene convertito e CONTROLLATO:
   - WIDTH e HEIGHT devono essere numeri ≥ 2 (un labirinto 1x1 non ha senso)
   - ENTRY e EXIT devono essere dentro la griglia e diversi tra loro
   - PERFECT deve essere esattamente True o False
   - OUTPUT_FILE non può essere vuoto

Se qualcosa non va → messaggio d'errore chiaro e il programma si ferma
senza mai andare in crash.

### Cosa ne deriva (gli effetti dell'input)

L'oggetto `Config` (il risultato della lettura) viene passato al passo
successivo, e ogni campo produce un effetto preciso:

| Chiave del config | Effetto nel programma |
|-------------------|-----------------------|
| WIDTH | numero di colonne della griglia |
| HEIGHT | numero di righe della griglia |
| ENTRY | la "porta" d'ingresso del labirinto |
| EXIT | la "porta" d'uscita del labirinto |
| OUTPUT_FILE | il nome del file scritto al passo 4 |
| PERFECT | True = un solo percorso entrata→uscita |
| SEED | stesso seed = stesso labirinto (vedi 1.3) |

## 1.2 La griglia e i muri (dove entrano decimale, binario, esadecimale)

### I tre sistemi di numeri e dove compaiono

| Sistema | Dove compare nel progetto |
|---------|---------------------------|
| DECIMALE (i numeri normali, cifre 0-9) | nel config (WIDTH=20) e nelle somme dei muri (12) |
| BINARIO (solo 0 e 1) | nei 4 muri di ogni cella: 0 = aperto, 1 = chiuso |
| ESADECIMALE (cifre 0-9 + lettere A-F) | nel file di output: una cifra per cella |

### Come si contano i numeri (le colonne)

Il numero normale `352` è fatto di **colonne**: 3 centinaia, 5 decine,
2 unità. Ogni colonna vale **10 volte** quella alla sua destra (1 → 10
→ 100) perché abbiamo 10 cifre. `352` = 3×100 + 5×10 + 2×1.

Nel **binario** ci sono solo 2 cifre (0 e 1), quindi ogni colonna vale
**2 volte** quella alla sua destra:

```
  1     0     1     0
  8     4     2     1      <- il valore di ogni colonna
```

`1010` = 1×8 + 0×4 + 1×2 + 0×1 = 10.

**1, 2, 4, 8 non sono altro che le colonne di un numero binario di 4
cifre.** Stessa regola dei numeri normali, ma ×2 invece di ×10.

### Il trucco delle monete

Con 4 monete da **1€, 2€, 4€, 8€** puoi pagare qualsiasi cifra esatta da
0 a 15 euro, e ogni cifra in **un solo modo**: 5€ = 4+1, 10€ = 8+2,
14€ = 8+4+2. Funziona perché ogni moneta è più grande della somma di
tutte quelle più piccole (8 > 1+2+4; 4 > 1+2; 2 > 1).

**Decodificare** = partire dalla moneta più grande e chiedersi "ci sta?":
11 → l'8 ci sta (resta 3) → il 4 no → il 2 sì (resta 1) → l'1 sì →
11 = 8+2+1. Sempre senza ambiguità.

### I muri sono le monete

| Muro  | Moneta |
|-------|--------|
| NORD  | 1€     |
| EST   | 2€     |
| SUD   | 4€     |
| OVEST | 8€     |

**Muro CHIUSO = 1 = prendi la moneta. Muro APERTO = 0 = non la prendi.**
Il numero della cella = la somma delle monete prese.

Esempio: NORD chiuso + SUD chiuso, EST e OVEST aperti → 1 + 4 = **5**.
Altro esempio: EST e OVEST chiusi → 2 + 8 = **10**.

### Perché esadecimale (il problema dei due caratteri)

Nel file le celle sono scritte una di fila all'altra, senza spazi. Se i
numeri 10-15 si scrivessero in decimale (DUE caratteri), il file
diventerebbe ambiguo: `1103` è 11-0-3? O 1-10-3? Non si sa dove finisce
una cella e inizia l'altra.

Soluzione: ogni cella deve occupare ESATTAMENTE un carattere. Ma i valori
sono 16 (0-15) e le cifre normali sono solo 10. Ai 6 numeri mancanti si
dà una lettera:

| 10 | 11 | 12 | 13 | 14 | 15 |
|----|----|----|----|----|----|
| A  | B  | C  | D  | E  | F  |

Esempio chiave: cella con TUTTI i muri chiusi = 8+4+2+1 = 15 → nel file
si scrive **F** (perché "15" occuperebbe due caratteri).

### ATTENZIONE: perché 0-15? (non è la HEIGHT del config!)

Il 0-15 viene dai **4 muri** della cella, non dalla dimensione del
labirinto: minimo = nessuna moneta (tutti aperti) = 0; massimo = tutte
le monete (tutti chiusi) = 1+2+4+8 = 15. Una cella ha sempre e solo 4
muri → il suo numero va SEMPRE da 0 a 15, in qualsiasi labirinto.

`WIDTH=20` e `HEIGHT=15` del config sono un'altra cosa: la grandezza
della GRIGLIA (20 celle per riga, 15 righe = 300 celle). Nel file di
output: 15 righe di 20 cifre. Che "15" compaia in entrambi i posti è
una COINCIDENZA. Due mondi separati: la dimensione del labirinto
(config) e i muri di una singola cella (0-15).

### Esempio completo (labirinto 2x2)

Un labirinto di 2 celle di larghezza × 2 di altezza. Ingresso in alto a
sinistra, uscita in basso a destra.

**Il disegno** (legenda: `-` o `|` = muro CHIUSO, spazio vuoto = APERTO):

```
       INGRESSO (N di (0,0) aperto)
               |
               v
    +----------+--------+
    |                   |
    |   (0,0)    (1,0)  |
    |                   |
    +----------         |   <- sotto (0,0): muro | sotto (1,0): aperto
    |                   |
    |   (0,1)    (1,1)  |
    |                   |
    +----------         |   <- sotto (0,1): muro | sotto (1,1): aperto
               ^
               |
       USCITA (S di (1,1) aperto)
```

**Le 4 celle, una per una, in parole:**

```
Cella (0,0):  NORD aperto (ingresso)  EST aperto   SUD chiuso   OVEST chiuso
Cella (1,0):  NORD chiuso (bordo)     EST chiuso   SUD aperto   OVEST aperto
Cella (0,1):  NORD chiuso (muro)      EST aperto   SUD chiuso   OVEST chiuso
Cella (1,1):  NORD aperto             EST chiuso   SUD aperto (uscita)  OVEST aperto
```

**Le monete prese (solo i muri CHIUSI):**

```
(0,0): SUD+OVEST        = 4+8     = 12  →  nel file: C
(1,0): NORD+EST         = 1+2     = 3   →  nel file: 3
(0,1): NORD+SUD+OVEST   = 1+4+8   = 13  →  nel file: D
(1,1): EST              = 2       = 2   →  nel file: 2
```

**Il file di output completo:**

```
C3          <- riga 0: le due celle in alto
D2          <- riga 1: le due celle in basso
            <- riga vuota
0,0         <- entrata
1,1         <- uscita
ES          <- percorso: Est poi Sud
```

**Decodifica (leggere il file):** trovi `C` → numero 12 → moneta più
grande che ci sta: 8 (OVEST chiuso), resta 4 → 4 (SUD chiuso), resta 0
→ NORD e EST aperti. Confronta col disegno: torna.

**Coerenza tra vicini:** il muro condiviso deve avere la stessa risposta
da entrambi i lati — (0,0) EST aperto ↔ (1,0) OVEST aperto ✓; (0,0) SUD
chiuso ↔ (0,1) NORD chiuso ✓. Se un lato dice sì e l'altro no → il
validator segnala "Wrong encoding".

### Riepilogo: le due direzioni

**Scrittura (quello che fa il programma):**

```
il generatore decide i muri
      ↓
per ogni cella: CHIUSO = 1 (prendo la moneta), APERTO = 0
monete: N=1  E=2  S=4  W=8
      ↓
somma delle monete = numero decimale della cella (0-15)
      ↓
se serve, soprannome esadecimale: 10=A ... 15=F
      ↓
FILE: una cifra per cella
```

**Lettura (quello che fanno display e validator):**

```
FILE: una cifra (es. "C")
      ↓
C = 12 (decimale)
      ↓
scomposizione con le monete, dalla più grande:
  8 ci sta? sì → OVEST chiuso, resta 4
  4 ci sta? sì → SUD chiuso, resta 0
  2 no → EST aperto, 1 no → NORD aperto
      ↓
ecco i muri della cella
```

**Il programma NON riceve numeri di muri come input: riceve il config e
PRODUCE quei numeri.** La scomposizione numero→muri è la lettura del
file (l'altra direzione).

**Frase pronta per l'evaluation:** "Il generatore decide i muri; per ogni
cella si sommano i valori dei muri chiusi (N=1, E=2, S=4, W=8) ottenendo
un numero 0-15 che nel file si scrive con una sola cifra esadecimale. Chi
legge il file fa l'inverso: sottrae le monete più grandi per capire quali
muri sono chiusi."

## 1.3 Il seed: la casualità riproducibile

Nel passo 2 il generatore riceve il seed. "Casuale ma riproducibile"
sembra una contraddizione: in realtà la casualità del computer è una
sequenza di numeri calcolata da un punto di partenza. Se il punto di
partenza (il **seed**) è lo stesso, la sequenza è identica → stesso
labirinto. `random.Random(42)` in Python = `srand(42)` in C. Se il
config non ha SEED → ogni run produce un labirinto diverso.

## 1.4 La generazione (recursive backtracker)

**Labirinto perfetto** = tra due celle qualsiasi esiste UN SOLO percorso
(è un albero, in termini di grafi). L'algoritmo "recursive backtracker"
(una DFS) lo garantisce gratis: parte da una cella, visita un vicino mai
visitato togliendo il muro tra loro (sempre a specchio, da entrambi i
lati), e quando è bloccato torna indietro.

**PERFECT=False:** dopo la generazione perfetta si aprono alcuni muri
interni extra (creano cicli = più percorsi), controllando di non creare
mai un'area aperta 3x3 (corridoi larghi max 2 celle).

**Il "42":** disegnato con celle completamente chiuse (tutti e 4 i muri,
valore F) — isole inaccessibili che la generazione non tocca. Se il
labirinto è troppo piccolo il 42 si omette e il main stampa un messaggio
d'errore, poi il programma CONTINUA (il subject lo permette).

## 1.5 Il percorso più breve: BFS

La BFS (Breadth-First Search) parte dall'entrata, visita tutti i vicini
raggiungibili (distanza 1), poi i loro vicini (distanza 2), ecc. — come
un'onda che si allarga. La prima volta che arriva all'uscita ha il
percorso più breve. Il risultato è una lista di celle da entry a exit
incluse: [(0,0), (1,0), (1,1), ...].

## 1.6 L'OUTPUT: il file esadecimale

Il formato è imposto dal subject:

1. Una riga per riga della griglia, una cifra esadecimale per cella
2. Una riga vuota
3. Tre righe: coordinate entrata (`x,y`), coordinate uscita (`x,y`),
   percorso NESW (es. `ES` = Est poi Sud)
4. Ogni riga termina con un "a capo"

Il percorso in lettere si ottiene confrontando ogni cella con la
successiva: se x aumenta → E, se x diminuisce → W, se y diminuisce → N,
se y aumenta → S.

## 1.7 Il display interattivo

Il labirinto si mostra nel terminale con colori (codici ANSI: sequenze
di caratteri speciali che il terminale interpreta come colori). Tasti:
`r` rigenera (richiama generate con gli stessi parametri), `p`
mostra/nascondi percorso, `c` cambia colore muri, `q` esce. Disegno
ASCII `+---+` con due for annidati: I = entrata, O = uscita, . =
percorso.

## 1.8 Il main e la gestione errori

`a_maze_ing.py` è il direttore d'orchestra: controlla gli argomenti,
chiama le tappe A→E nell'ordine della mappa, gestisce gli errori senza
mai crashare (messaggio chiaro + uscita con codice 1). Tre livelli di
protezione: ConfigError (config sbagliato), OSError (file illeggibile),
un except finale di sicurezza (mai traceback sullo schermo).

---

# 2. I moduli: chi fa cosa

| File | Chi | Cosa fa | Spiegato in |
|------|-----|---------|-------------|
| config_parser.py | mpanzani | legge e valida config.txt → Config | 1.1 |
| mazegen.py | roblomba | genera il labirinto + BFS | 1.4, 1.5 |
| output_writer.py | mpanzani | scrive il file esadecimale | 1.6 |
| display.py | roblomba | terminale interattivo | 1.7 |
| a_maze_ing.py | mpanzani | orchestrazione + errori | 1.8 |
| pacchetto mazegen | roblomba | modulo riusabile installabile con pip | README |

# 3. Glossario

- **nibble:** 4 bit = mezza byte = una cifra esadecimale
- **BFS:** visita in ampiezza, trova il percorso più corto
- **DFS:** visita in profondità, alla base del recursive backtracker
- **albero ricoprente:** grafo connesso senza cicli che tocca tutte le celle
- **Config:** oggetto che contiene i parametri validati del labirinto
- **grid:** la griglia del labirinto, grid[y][x] = numero 0-15 della cella
- **seed:** punto di partenza della sequenza casuale (riproducibilità)
