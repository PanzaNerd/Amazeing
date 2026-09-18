# APPUNTI AMAZEING — generatore di labirinti

Questo file serve SOLO a capire. Segue **la cronologia del programma**:
si parte dall'input e si va avanti nell'ordine in cui il codice si
esegue. Ogni sezione risponde a: **cos'è → cosa viene preso → come viene
letto/elaborato → cosa ne deriva**. Niente codice, illustrazioni semplici.

## INDICE

1. La cronologia del programma (la mappa)
   - Come eseguire e testare il programma (comandi da terminale)
   - 1.1 L'INPUT: config.txt
   - 1.2 La griglia e i muri (decimale, binario, esadecimale)
   - 1.3 Il seed (la casualità riproducibile)
   - 1.4 La generazione (la talpa che scava tunnel)
   - 1.5 Il percorso più breve (BFS)
   - 1.6 L'OUTPUT: il file esadecimale
   - 1.7 Il display interattivo
   - 1.8 Il main e la gestione errori
2. I moduli
3. Studio del codice (in ordine di esecuzione)
   - L'ordine di studio (perché questo)
   - 3.1 a_maze_ing.py — il direttore d'orchestra
   - 3.2 config_parser.py — nasce il Config (base pronta)
   - 3.3 mazegen.py — il cuore (base pronta)
   - 3.4 output_writer.py — il file di output (base pronta)
   - 3.5 display.py — il terminale interattivo (base pronta)
4. Glossario

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

## Come eseguire e testare il programma (comandi da terminale)

Tutto parte dalla cartella del progetto:

```bash
cd "~/Desktop/python repo/Common_Core_2/python/AMAZEING"
source .venv/bin/activate        # attiva il venv (pip di sistema e' bloccato)
```

**Eseguire il programma** (genera `maze.txt` e apre il display interattivo):

```bash
make run
# oppure direttamente:
python3 a_maze_ing.py config.txt
```

Nel display: `1` = rigenera, `2` = mostra/nascondi percorso, `3` = cambia
colore muri, `q` = esci. Uscita con codice 0 = tutto ok, 1 = errore.

**Test automatici** (16 test):

```bash
make test                                                # tutta la suite
python3 -m pytest tests/test_config_parser.py -v         # solo il parser
python3 -m pytest tests/test_output_writer.py::test_path_to_nesw_simple -v   # un singolo test
```

**Controlli di qualita'** (richiesti dal subject):

```bash
make lint          # flake8 + mypy (flag del subject)
make lint-strict   # flake8 + mypy --strict (piu' severo)
make debug         # esegue dentro pdb (il debugger, come gdb)
```

**Validatore del subject** (sul file appena generato; MAI pushato):

```bash
python3 output_validator.py maze.txt
# se non stampa nulla: i muri delle celle vicine sono coerenti (OK)
```

**Verifiche manuali veloci**:

```bash
python3 a_maze_ing.py                    # senza argomento → Usage + exit 1
python3 a_maze_ing.py file_che_non_esiste.txt   # → errore chiaro + exit 1
make run && make run                     # due volte: maze.txt identico (SEED=42 = riproducibilita')
```

**Pacchetto riusabile** (per l'evaluation):

```bash
make build    # crea dist/mazegen-1.0.0-py3-none-any.whl
make clean    # rimuove cache e artefatti (__pycache__, dist, ...)
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

### Le dimensioni NON sono fisse

WIDTH e HEIGHT vengono dal config: il codice non ha nessuna taglia
cucita dentro e funziona con qualunque misura (minimo 2x2, imposto dal
parser; massimo nessuno). WIDTH = larghezza (colonne), HEIGHT =
altezza (righe). All'evaluation il config sarà diverso dal nostro:
dimensioni, ENTRY, EXIT e PERFECT possono cambiare e il programma deve
gestirli tutti. Il "42" invece richiede spazio (almeno 9 colonne x 6
righe): sotto quella taglia viene omesso (messaggio + programma
continua, il subject lo ammette).

Per allenarsi: modificare config.txt con altre misure (es. WIDTH=5
HEIGHT=5, WIDTH=40 HEIGHT=20, PERFECT=False) e rilanciare il
programma.

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

### Il dubbio frequente: il seed è il punto di partenza I?

NO. Sono due cose di due mondi diversi:

- **ENTRY** (la I nel display) = **DOVE** entri nel labirinto: una
  posizione, una cella (es. 0,0).
- **SEED** = **QUALE** labirinto ottieni: un numero che sceglie le
  "estrazioni a sorte" del generatore.

Il seed non c'entra nulla con la I: la I viene da ENTRY nel config, il
seed viene da SEED nel config.

### Cos'è la casualità del computer

Il computer non sa tirare dadi veri. Immagina che ogni computer abbia
lo stesso librone di tiri di dado (milioni di tiri da 1 a 6, scritti
in fila). "Dammi un numero a caso" = "leggi il prossimo tiro della
pagina". Il **seed** = **la pagina da cui inizi a leggere**:

- SEED=42 → si parte sempre da pagina 42 → stessi tiri → il generatore
  fa le stesse scelte → stesso labirinto.
- Niente SEED → si parte da una pagina scelta dall'orologio del
  momento → ogni run un labirinto diverso.

"Casuale ma riproducibile" = le scelte sono a sorte, ma ripartendo
dalla stessa pagina sono sempre le stesse. `random.Random(42)` in
Python = `srand(42)` in C. Nei videogiochi è il seed del mondo
(Minecraft).

### Perché serve

Per rifare lo stesso labirinto a comando: testare, dimostrare,
confrontare. Con SEED=42: `make run` due volte → maze.txt identico.

**Frase pronta per l'evaluation:** "Il computer genera numeri
pseudo-casuali da una sequenza calcolata a partire da un numero
iniziale chiamato seed. Stesso seed → stessa sequenza → stesso
labirinto. L'entrata invece è una posizione decisa da ENTRY nel
config: non c'entra col seed."

## 1.4 La generazione (la talpa che scava tunnel)

### Il punto di partenza: tutte scatole chiuse

Prima di generare, ogni cella ha TUTTI i muri chiusi (valore F = 15).
Non è ancora un labirinto: è un blocco di scatole senza passaggi.

```
+---+---+---+
|   |   |   |
+---+---+---+
|   |   |   |
+---+---+---+
|   |   |   |
+---+---+---+
```

### La talpa e le sue 3 regole

Immagina una TALPA che parte dalla cella d'entrata e scava tunnel.

**Regola 1 — si scava solo nel nuovo.** La talpa entra SOLO in celle
dove non è mai stato nessuno. Mai scavare verso una cella già
visitata. Questo garantisce che tra due celle qualsiasi ci sia UN SOLO
percorso (mai scorciatoie) = labirinto perfetto.

**Regola 2 — il muro si apre da TUTTI E DUE i lati.** Quando la talpa
passa dalla cella A alla cella B, il muro tra loro va tolto sia dalla
scatola A sia dalla scatola B: il muro è condiviso, le monete si
tolgono da entrambe le celle.

**Regola 3 — la corda.** La talpa si trascina dietro una corda (la
memoria dei passi fatti). Se in una cella tutti i vicini sono già
visitati è BLOCCATA: ripercorre la corda ALL'INDIETRO finché trova una
cella con un vicino mai scavato e riparte da lì. Questo "tornare
indietro" è il backtracking.

**La scelta a caso:** quando ha più vicini nuovi ne sceglie uno A CASO
— qui entra il seed di 1.3: i tiri di dado decidono la strada → stesso
seed = stessa strada = stesso labirinto.

**La fine:** quando la talpa torna indietro fino all'entrata e non c'è
più nessun vicino nuovo → tutte le celle sono state scavate → fatto.
Tutti connessi, un solo percorso tra due celle qualsiasi = labirinto
PERFETTO (in termini di grafi: un albero).

### La traccia vera, passo per passo (labirinto 4x4, seed 42)

Ecco le mosse ESATTE del programma su un labirinto 4x4 con seed 42 (il
dado è quello vero del generatore). Prima di tutto, il rituale della
talpa ad ogni cella — sempre lo stesso, 5 passi:

1. Guarda i 4 vicini in ordine fisso: NORD, EST, SUD, OVEST.
2. Tiene solo quelli MAI visitati (la lista dei candidati).
3. Tira il dado e ne sceglie uno (il dado esce dal librone del seed).
4. Apre il muro DA TUTTI E DUE i lati (le due monete dello stesso muro).
5. Marca visitata la nuova cella, ci entra e allunga la corda.

Se la lista dei candidati è VUOTA → bloccata → torna indietro di una
cella lungo la corda e ripete il rituale da lì. La corda (lo stack) è
la memoria: in cima c'è SEMPRE la cella attuale.

Stato iniziale (tutte le celle chiuse):

```
+---+---+---+---+
|   |   |   |   |
+---+---+---+---+
|   |   |   |   |
+---+---+---+---+
|   |   |   |   |
+---+---+---+---+
|   |   |   |   |
+---+---+---+---+
```

Le mosse (per ogni passo: dove sei, chi sono i candidati, cosa esce
dal dado):

```
 1   (0,0)  candidati Est, Sud              dado: Est   → scava (1,0)
 2   (1,0)  candidati Est, Sud              dado: Est   → scava (2,0)
 3   (2,0)  candidati Est, Sud              dado: Sud   → scava (2,1)
 4   (2,1)  candidati Est, Sud, Ovest       dado: Est   → scava (3,1)
 5   (3,1)  candidati Nord, Sud             dado: Nord  → scava (3,0)
 6   (3,0)  candidati: NESSUNO → TORNA INDIETRO (si torna a (3,1))
 7   (3,1)  candidato Sud                   dado: Sud   → scava (3,2)
 8   (3,2)  candidati Sud, Ovest            dado: Sud   → scava (3,3)
 9   (3,3)  candidato Ovest                 dado: Ovest→ scava (2,3)
10   (2,3)  candidati Nord, Ovest           dado: Ovest→ scava (1,3)
11   (1,3)  candidati Nord, Ovest           dado: Nord  → scava (1,2)
12   (1,2)  candidati Nord, Est, Ovest      dado: Nord  → scava (1,1)
13   (1,1)  candidato Ovest                 dado: Ovest→ scava (0,1)
14   (0,1)  candidato Sud                   dado: Sud   → scava (0,2)
15   (0,2)  candidato Sud                   dado: Sud   → scava (0,3)
16   (0,3)  candidati: NESSUNO → TORNA INDIETRO
17-19     (0,2), (0,1), (1,1): NESSUNO → si riavvolge la corda
20   (1,2)  candidato Est (è rimasto nuovo!) dado: Est → scava (2,2)
21   (2,2)  candidati: NESSUNO → TORNA INDIETRO
22-31     tutti NESSUNO: la corda si riavvolge fino a (0,0) e poi si
          svuota → FINE
```

Risultato finale (16 celle, 15 tunnel aperti: in un albero i rami sono
sempre uno in meno dei nodi; con il 42 presente i nodi da contare sono
le celle scavate = celle totali meno i mattoncini, che restano isole
fuori dall'albero):

```
+---+---+---+---+
|           |   |
+---+---+   +   +
|       |       |
+   +   +---+   +
|   |       |   |
+   +   +---+   +
|   |           |
+---+---+---+---+
```

### Attenzione: due errori da NON dire all'evaluation

- "La talpa non torna mai indietro" → SBAGLIATO. Torna indietro
  continuamente: è il backtracking (mossa 6 della traccia). Senza,
  al primo vicolo cieco si fermerebbe per sempre con quasi tutte le
  celle ancora chiuse.
- "La generazione finisce all'uscita" → SBAGLIATO. La talpa non sa
  nemmeno che l'uscita esiste: scava TUTTE le celle e finisce quando
  la corda è vuota. Nella traccia l'uscita (3,3) è scavata alla mossa
  8 ma la generazione continua fino alla 31. Il percorso
  entrata→uscita lo trova DOPO la BFS (1.5).
- "Il percorso della talpa è il percorso del labirinto" → SBAGLIATO.
  La talpa fa deviazioni nei vicoli ciechi (es. (3,0)) che nel
  labirinto finale non contano. La generazione produce i MURI, non un
  percorso. Il percorso nasce dopo, dalla BFS sui muri aperti: nella
  traccia è (0,0)→(1,0)→(2,0)→(2,1)→(3,1)→(3,2)→(3,3), senza
  deviazioni.

Cose da notare:

- I muri NON "sorgono" dove la talpa non passa: c'erano GIÀ tutti
  all'inizio (ogni cella nasce con le 4 monete). La talpa ne RIMUOVE
  alcuni (i passaggi): i muri finali sono quelli rimasti, cioè
  esattamente dove non è mai passata. (In PERFECT=False può anche
  richiuderne uno, se l'apertura creerebbe una zona 3x3.)
- (3,0) alla mossa 6 è un VICOLO CIECO: Nord e Est sono bordo, Ovest è
  (2,0) già visitata, Sud è (3,1) da cui è venuta. Il backtracking è
  semplicemente: riavvolgi la corda finché trovi una cella con un
  candidato rimasto (alla mossa 20: (1,2) aveva ancora Est, il vicino
  (2,2) che alla mossa 12 il dado NON aveva scelto).
- Il muro si apre da TUTTI E DUE i lati perché è scritto due volte: la
  moneta Est di A e la moneta Ovest di B sono lo STESSO muro. Se
  aprissi un lato solo, le due celle non sarebbero d'accordo e il
  validatore direbbe "Wrong encoding".
- Mai scavare verso una cella già visitata: si creerebbe una
  scorciatoia, cioè un secondo percorso → il labirinto non sarebbe più
  perfetto.
- "In base a cosa decide dove andare": non decide con un criterio.
  Costruisce la lista dei candidati in ordine Nord, Est, Sud, Ovest e
  tira il dado. Con SEED=42 il dado esce sempre uguale → stesse mosse
  → stesso labirinto.

**Frase pronta per l'evaluation:** "Parto da una griglia di celle tutte
chiuse. Da ogni cella raccolgo i vicini mai visitati, ne scelgo uno a
caso con un generatore pilotato dal seed, apro il muro da entrambi i
lati e tengo la strada fatta su uno stack. Quando non ci sono più
vicini nuovi torno indietro finché trovo una cella con un vicino
nuovo. Quando lo stack è vuoto tutte le celle sono state visitate: il
risultato è un albero ricoprente, cioè un labirinto perfetto."

### PERFECT=False: le scorciatoie

La talpa scava SEMPRE il labirinto perfetto (fase 1). Le scorciatoie
NON le scava la talpa: sono una SECONDA passata separata del programma
(fase 2), che parte solo se PERFECT=False. Con PERFECT=True (il nostro
config.txt) la fase 2 non parte mai e non ci sono scorciatoie.

Quando si ha PERFECT=False? Lo decide il CONFIG: la riga
PERFECT=True/False di config.txt (vedi 1.1). Il nostro config dice
True; un config con False (come può portarlo l'evaluator) fa partire
la fase 2. Il programma non sceglie: obbedisce al config, e nel menu
del display "1" rigenera con lo stesso valore.

### Il rituale del piccone (5 passi, ripetuti 20 volte)

1. Dado 1: una cella a caso.
2. Dado 2: una direzione a caso (Nord, Est, Sud, Ovest).
3. Tre controlli preliminari: la cella è un mattoncino del 42? →
   salta. Il muro è sul bordo? → salta (il bordo non si tocca mai).
   Il muro è già aperto? → salta.
4. Altrimenti: apri dai due lati (le due monete, come fa la talpa).
5. Controllo finale: è nata una piazzetta 3x3? Se sì → richiudi
   subito (si rimette indietro); se no → resta aperta: è una
   SCORCIATOIA.

### La traccia vera dei 20 colpi (stesso 4x4, seed 42)

```
 1. cella (1,3)  direzione EST    muro già aperto (scavato dalla talpa) → salta
 2. cella (3,2)  direzione NORD   muro già aperto (scavato dalla talpa) → salta
 3. cella (1,3)  direzione SUD    è il bordo in basso → salta
 4. cella (2,1)  direzione EST    muro già aperto (scavato dalla talpa) → salta
 5. cella (2,0)  direzione NORD   è il bordo in alto → salta
 6. cella (3,0)  direzione SUD    muro già aperto (scavato dalla talpa) → salta
 7. cella (2,2)  direzione NORD   chiuso, niente 3x3 → APERTO (scorciatoia)
 8. cella (3,0)  direzione OVEST  chiuso, niente 3x3 → APERTO (scorciatoia)
 9. cella (0,2)  direzione SUD    muro già aperto (scavato dalla talpa) → salta
10. cella (1,0)  direzione NORD   è il bordo in alto → salta
11. cella (1,2)  direzione NORD   muro già aperto (scavato dalla talpa) → salta
12. cella (1,0)  direzione OVEST  muro già aperto (scavato dalla talpa) → salta
13. cella (2,3)  direzione SUD    è il bordo in basso → salta
14. cella (1,2)  direzione SUD    muro già aperto (scavato dalla talpa) → salta
15. cella (1,2)  direzione NORD   muro già aperto (DI NUOVO!) → salta
16. cella (1,1)  direzione EST    chiuso, niente 3x3 → APERTO (scorciatoia)
17. cella (3,3)  direzione SUD    è il bordo in basso → salta
18. cella (1,2)  direzione NORD   muro già aperto (DI NUOVO!) → salta
19. cella (1,0)  direzione SUD    chiuso, niente 3x3 → APERTO (scorciatoia)
20. cella (3,2)  direzione NORD   muro già aperto (scavato dalla talpa) → salta
```

Bilancio: 5 bordi + 11 già aperti + 4 a segno = 20. La talpa aveva
aperto 15 muri su 24 interni: circa metà dei colpi becca un muro già
aperto.

### I dadi del piccone: quante facce?

Il piccone fa tre lanci per tentativo:

- Dado della colonna x: tante facce quante sono le colonne, numerate
  da 0: con WIDTH=20 → 20 facce (0, 1, ..., 19) — come un d20 dei
  giochi di ruolo, ma che parte da 0.
- Dado della riga y: tante facce quante sono le righe: con HEIGHT=15
  → 15 facce (0, ..., 14).
- Dado della direzione: 4 facce: NORD, EST, SUD, OVEST (le 4 monete).

Le facce sono i NOMI delle celle: la griglia ha colonne da 0 a 19 e
righe da 0 a 14 (come gli indici degli array in C, che partono da 0).
Il dado esce sempre un nome di cella valido.

ATTENZIONE a non confondere con l'esadecimale 0-F di 1.2: quelle sono
le 16 etichette per scrivere il numero dei muri di una cella nel FILE
DI OUTPUT. I dadi del piccone escono coordinate e direzioni, non
cifre esadecimali: due mondi separati.

### Il piccone non ha memoria (e non gli serve)

Il dado può ricapitare sulla stessa cella — anzi capita di continuo:
nella traccia dei 20 colpi, cella (1,2) direzione NORD esce 3 volte
(tentativi 11, 15, 18) e cella (3,2) direzione NORD 2 volte (2 e 20).
Il piccone NON tiene nessuna lista di "celle già viste": ogni
tentativo è indipendente.

Come se la cava? Ricontrolla e basta: il muro è già aperto → salta.
Riaprire un muro già aperto non cambia nulla, quindi non serve
ricordare nulla. È una differenza voluta rispetto alla talpa: la
talpa HA memoria (la griglia visited + la corda) perché la sua regola
è "mai verso una cella già visitata"; il piccone non ha regole del
genere e può permettersi di non ricordare nulla. Le ripetizioni sono
anche il motivo per cui i colpi a segno sono pochi: 11 su 20 beccano
muri già aperti.

Le 4 scorciatoie aperte (creano i 4 cicli):
  (2,2)-(2,1)  tentativo 7
  (3,0)-(2,0)  tentativo 8
  (1,1)-(2,1)  tentativo 16
  (1,0)-(1,1)  tentativo 19

Il labirinto NON perfetto (confronta con quello perfetto: i passaggi
extra sono su due righe nuove):

```
+---+---+---+---+
|               |
+---+   +   +   +
|               |
+   +   +   +   +
|   |       |   |
+   +   +---+   +
|   |           |
+---+---+---+---+
```

Prima (perfetto) da (1,0) a (1,1) c'era UNA sola strada: un giro
lunghissimo di 9 passi intorno a tutto il labirinto. Ora c'è il
passaggio diretto (1,0)-(1,1), e si è formato un CICLO di 4 celle:

```
(1,0) ---- (2,0)
  |          |
(1,1) ---- (2,1)
```

Due strade diverse entrata→uscita (entrambe 6 passi):
  (0,0)→(1,0)→(1,1)→(2,1)→(3,1)→(3,2)→(3,3)
  (0,0)→(1,0)→(2,0)→(2,1)→(3,1)→(3,2)→(3,3)

Come contare i cicli: perfetto = tunnel aperti = celle - 1 (15 su 16,
zero cicli). Ogni tunnel in più = un ciclo in più: qui 19 tunnel = 4
cicli. La BFS (1.5) trova comunque il percorso più corto, anche con
le scorciatoie.

La zona 3x3 VIETATA (il controllo che fa richiudere il muro):

```
+---+---+---+
|           |
|           |
|           |
+---+---+---+
  3 righe x 3 colonne di CELLE = 9 celle tutte aperte = piazzetta:
  vietata dal subject (i corridoi restano larghi al massimo 2 celle)
```

### Come fa il controllo della piazzetta 3x3

Un blocco di 3x3 celle ha 12 muri INTERNI: 6 orizzontali (2 piani x 3
segmenti) e 6 verticali (2 colonne x 3 segmenti). Qui sotto la
finestra con tutti e 12 i muri interni CHIUSI (il bordo esterno non
conta):

```
+---+---+---+
| a | b | c |
+---+---+---+
| d | e | f |
+---+---+---+
| g | h | i |
+---+---+---+

6 muri orizzontali interni: SUD di a,b,c e SUD di d,e,f
6 muri verticali interni:   EST di a,d,g e EST di b,e,h
piazzetta = tutti e 12 i segmenti interni tolti
```

Controllare una finestra con le monete: si guardano le monete SUD
delle 6 celle in alto e le monete EST delle 6 celle a sinistra. Se
anche UNA SOLA moneta è ancora lì, c'è un muro → non è una piazzetta.
Se mancano tutte e 12 → piazzetta.

Quando controlla: dopo OGNI colpo di piccone andato a segno, il
programma fa il giro completo della griglia e prova tutte le finestre
3x3 possibili (su un 20x15 sono 18x13 = 234 finestre × 12 monete
ciascuna). Se anche una sola finestra è una piazzetta → il muro
appena aperto si rimette subito indietro. Si controlla tutto il
labirinto (non solo la zona del colpo) perché è più semplice: per il
computer 234×12 controlli sono un istante.

ATTENZIONE: "3x3" si conta in CELLE: 3 colonne x 3 righe = 9 celle
con i 12 muri interni aperti. Un quadrato 2x2 tutto aperto (4 celle,
come il ciclo dell'esempio del piccone) è LEGALE: i corridoi possono
essere larghi fino a 2 celle, il subject vieta le zone aperte da 3 in
su. Per questo il controllo non segnala il ciclo del 4x4: non è una
piazzetta.

### La traccia vera del controllo (4x4 finale, dopo le scorciatoie)

Il giro parte dalla finestra con angolo in alto a sinistra (0,0) e
procede in ordine. Per ogni finestra: prima le 6 monete SUD (i muri
orizzontali interni), poi le 6 monete EST (i muri verticali interni).
Al PRIMO muro trovato si ferma subito: la finestra non è una
piazzetta, si passa alla successiva.

```
Finestra (0,0) - celle (0,0)..(2,2):
  1. SUD di (0,0): PRESENTE -> STOP -> non piazzetta

Finestra (1,0) - celle (1,0)..(3,2):
  1-6.  SUD di (1,0),(2,0),(3,0),(1,1),(2,1),(3,1): assenti
  7-11. EST di (1,0),(2,0),(1,1),(2,1),(1,2): assenti
  12.   EST di (2,2): PRESENTE -> STOP -> non piazzetta
  (11 controlli su 12 passati! Il ciclo 2x2 era quasi una piazzetta:
  a salvare la finestra è l'ultimo muro, EST di (2,2))

Finestra (0,1) - celle (0,1)..(2,3):
  1-5. SUD di (0,1),(1,1),(2,1),(0,2),(1,2): assenti
  6.   SUD di (2,2): PRESENTE -> STOP -> non piazzetta

Finestra (1,1) - celle (1,1)..(3,3):
  1-4. SUD di (1,1),(2,1),(3,1),(1,2): assenti
  5.   SUD di (2,2): PRESENTE -> STOP -> non piazzetta

Risultato: nessuna piazzetta -> le 4 scorciatoie restano aperte.
```

Questo giro completo viene fatto dopo OGNI apertura andata a segno
(4 volte, una per scorciatoia), sempre con la stessa risposta:
nessuna piazzetta. Guarda la finestra (1,0): il ciclo 2x2 è tutto
aperto, ma la finestra 3x3 che lo contiene comprende anche la cella
(2,2), che ha ancora il muro EST chiuso: è quel muro che rende il
ciclo legale. Un solo muro può salvare più finestre: il SUD di (2,2)
blocca sia la (0,1) sia la (1,1).

### Il "42"

OBBLIGATORIO (subject: "the maze must contain a visible '42'"). Le
celle dei MATTONCINI del disegno "42" sono scatole COMPLETAMENTE chiuse
(F = tutti i muri) piazzate al CENTRO della griglia, ma sempre con
ALMENO UNA RIGA interamente libera SOPRA le cifre. Prima che la talpa
parta vengono marcate come "già visitate": per la talpa sono cemento
armato → non ci scava mai dentro → i mattoncini restano isole chiuse, e
anche il risolutore (1.5) non ci passa mai. Le celle VUOTE delle cifre
invece sono celle normali: la generazione ci scava dentro e il percorso
può passarci — il 42 resta leggibile perché i mattoncini sono blocchi
pieni. Nel display i mattoncini sono quadratini pieni del colore dei
muri: il 42 appare come un blocco compatto e le cifre si leggono bene.

Il disegno è 7 colonne x 5 righe, e il codice lo piazza solo se la
griglia è almeno 9x6, con almeno una riga libera sopra le cifre:

- con SOLO 5 righe le cifre occuperebbero tutta l'altezza: il lato
  destro del 4 è una colonna piena di mattoncini che andrebbe da bordo
  a bordo e taglierebbe il labirinto in due parti che non si toccano
  (se entrata e uscita stanno nelle due parti, il percorso NON esiste);
- il "buco" in alto del 4 deve toccare celle libere: appiccicato al
  bordo resterebbe sigillato dai mattoncini e due celle non sarebbero
  mai raggiunte da nessuno (il subject vieta le celle isolate).

Se il labirinto è troppo piccolo (sotto 9x6) il 42 si omette: il main
stampa un messaggio e il programma CONTINUA.

### Il 42 deve essere perfettamente centrato?

Il subject NON lo chiede: chiede solo che il 42 sia VISIBILE e fatto
di celle completamente chiuse ("the maze must contain a visible '42'
drawn by several fully closed cells"). Nessuna regola sulla posizione:
il centro è una NOSTRA scelta estetica (staccato dai bordi si legge
meglio).

E comunque il centro perfetto spesso NON esiste: le celle sono intere,
la mezza cella non esiste. Il 42 è largo 7 colonne: in un labirinto
largo 12 restano 12 - 7 = 5 colonne libere, che è DISPARI → si
dividono in 2 a sinistra e 3 a destra (la divisione intera // arrotonda
per difetto e la cella in più va a destra). In verticale con 9 righe
invece torna pari: 9 - 5 = 4 → 2 sopra e 2 sotto, centrato esatto.
Griglia REALE 12x9 generata dal codice (# = mattoncino, . = cella
libera):

```
............
............
..#.#.###...
..#.#...#...
..###.###...
....#.#.....
....#.###...
............
............
```

L'unica regola di posizione che conta davvero è quella del bug
corretto: ALMENO UNA RIGA interamente libera sopra le cifre
(connettività), più il non coprire entry/exit.

### Attenzione a come si contano le celle (indici da 0)

WIDTH=12 significa 12 CELLE: gli indici delle colonne vanno da 0 a 11.
L'indice 0 è la PRIMA cella, non una cella in più: l'ultimo indice è
sempre il numero meno 1 (come in C: int tab[12] va da tab[0] a
tab[11]). Per avere 13 colonne bisogna scrivere WIDTH=13. Stessa cosa
per HEIGHT: HEIGHT=9 sono 9 righe, indici da 0 a 8.

### Quando il centro esatto È possibile

Il centro esatto esiste solo se lo spazio libero è PARI. Con WIDTH=13:
13 - 7 = 6 → 3 a sinistra e 3 a destra, centrato perfetto; con
HEIGHT=9: 9 - 5 = 4 → 2 sopra e 2 sotto: un 13x9 è centrato in
entrambe le direzioni (il codice piazza start_x=3 e start_y=2). Con
12 colonne lo spazio libero è 5, dispari: 2/3 è il meglio possibile.
Con HEIGHT=10: 10 - 5 = 5, dispari → 2 sopra e 3 sotto: un 13x10 è
centrato solo in orizzontale. Regola: il centro perfetto in ENTRAMBE
le direzioni richiede che sia (WIDTH - 7) che (HEIGHT - 5) siano
PARI. Nel display la differenza sembra più grande di quella che è,
perché ogni cella diventa 2 caratteri + i muri, ma nel conteggio
delle CELLE (quello che conta per il subject) lo scarto è sempre al
massimo 1.

Risposta da evaluation: "Il subject chiede solo un 42 visibile di
celle chiuse, non centrato; lo centriamo con la divisione intera, e
quando lo spazio libero è dispari la cella in più va a destra/sotto
(il centro perfetto richiederebbe la mezza cella)."

### Riepilogo in 4 passi

1. Tutte le celle chiuse (scatole).
2. Si marcano i mattoncini del 42 come cemento: mai scavati.
3. La talpa scava il labirinto perfetto con le 3 regole.
4. Se PERFECT=False si aprono scorciatoie extra (controllo 3x3).

## 1.5 Il percorso più breve: BFS

### Cos'è

La BFS è il PASSO 3 della mappa: quando parte, il labirinto è GIÀ
finito (la talpa ha scavato tutto al passo 2). Il suo unico compito:
trovare il percorso più corto dall'entrata all'uscita. Nel codice è
la funzione solve().

### L'idea: il fuoco sull'erba secca

Il fuoco parte dall'entrata e si propaga di una cella al minuto, in
TUTTE le direzioni contemporaneamente. Su ogni cella che raggiunge
scrive il MINUTO in cui l'ha toccata. Il minuto scritto sull'uscita è
la lunghezza della strada più corta.

Nel 4x4 di sempre (numeri generati dal programma vero; il punto = le
celle mai toccate, il fuoco si ferma appena tocca l'uscita):

```
+---+---+---+---+
| 0   1   2 | 5 |
+---+---+   +   +
| .   . | 3   4 |
+   +   +---+   +
| . | .   . | 5 |
+   +   +---+   +
| . | .   .   6 |
+---+---+---+---+
```

### Come fa a sapere che è il più corto? Non lo scopre: lo costruisce

Il fuoco avanza UN passo al minuto, ovunque: al minuto 0 brucia solo
l'entrata; al minuto 1 tutte le celle a 1 passo; al minuto 2 tutte
quelle a 2 passi... Una cella prende fuoco un minuto dopo la PRIMA
delle sue vicine che brucia: non può prendere fuoco prima (prima non
brucia nessuna sua vicina), e appena una vicina brucia, prende fuoco
il minuto dopo. Quindi il minuto scritto su ogni cella è SEMPRE il
minimo possibile: nessuna strada più corta poteva arrivarci prima.

La catena di "chi ha acceso chi", dall'uscita all'indietro:

```
(3,3) acceso da (3,2) <- da (3,1) <- da (2,1) <- da (2,0) <- da (1,0) <- da (0,0)
```

Ogni passaggio scende di UN minuto esatto: 6, 5, 4, 3, 2, 1, 0. Il
percorso, capovolto: (0,0),(1,0),(2,0),(2,1),(3,1),(3,2),(3,3) — 6
passi. Se esistesse una strada da 5, il fuoco sarebbe arrivato
all'uscita al minuto 5: impossibile, perché l'uscita ha due sole
vicine, (3,2) (minuto 5) e (2,3) (che il fuoco non ha nemmeno fatto
in tempo a toccare).

### Come lo fa il programma

Prima cosa: per ricostruire la strada alla fine, il programma tiene
un QUADERNO: su ogni cella scrive CHI l'ha accesa. Finito il fuoco,
parte dall'uscita, risale il quaderno ("chi ha acceso chi") fino
all'entrata e capovolge la lista: è il percorso. Nel codice il
quaderno è un dizionario chiamato came_from: un dizionario è la
tabella chiave→valore già vista in 1.1, e qui la chiave è la cella,
il valore è chi l'ha accesa (l'entrata ha scritto "nessuno").

Seconda cosa: per far avanzare il fuoco minuto per minuto, il
programma tiene una PILA DI FOGLI: ogni foglio è una cella toccata
che deve ancora propagare il fuoco ai vicini. Quando una cella
prende fuoco, il suo foglio viene messo in CIMA alla pila. Il
programma prende sempre il foglio in FONDO, cioè il più vecchio:
così le celle propagano il fuoco nell'ordine in cui sono state
toccate — prima tutte quelle del minuto 1, poi quelle del minuto 2,
e via. Prendere dal fondo si chiama FIFO: il primo foglio entrato è
il primo che esce.

(La talpa usava la stessa pila al contrario: prendeva la CIMA — LIFO,
l'ultimo entrato è il primo che esce — ma solo per tornare indietro
lungo la corda quando era bloccata, non per trovare strade corte.)

Attenzione: il fuoco non è una cosa separata dalla pila — prendere
sempre il foglio più vecchio È il fuoco. I minuti non si conoscono
all'inizio: li scrive il programma cella per cella, e la pila presa
dal fondo li fa uscire nell'ordine giusto (0, 1, 2...). Senza
quell'ordine i minuti uscirebbero sbagliati e il percorso
ricostruito sarebbe più lungo del necessario. Due pile, due mestieri:
quella della talpa RICORDA la strada già fatta (per tornare
indietro); quella della BFS PRODUCE i minuti nell'ordine giusto
mentre calcola la strada corta.

### Nel codice

- la pila di fogli = una deque di collections ("via il foglio in
  fondo" = popleft(), "foglio nuovo in cima" = append())
- chi ha acceso chi = il dizionario came_from (l'entrata ha None)
- i 4 lati = i 4 controlli con _has_wall (le monete)
- la ricostruzione = il while che risale came_from e poi reverse

**Frase pronta per l'evaluation:** "La BFS è come un fuoco che parte
dall'entrata e brucia una cella al minuto in tutte le direzioni: ogni
cella prende fuoco al minuto minimo possibile e annota chi l'ha
accesa. Quando il fuoco tocca l'uscita, risalgo la catena di chi ha
acceso chi fino all'entrata e la capovolgo: è il percorso più corto,
perché il fuoco raggiunge ogni cella nel minor numero di passi
possibile."

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

Il labirinto si mostra nel terminale in **stile minimale pulito: 1
cella = 1 carattere**, muri `─` orizzontali e `│` verticali con **gli
incroci giusti** (`┼`, `┬`, `┴`, `├`, `┤`, `┌`, `┐`, `└`, `┘`): la
struttura si legge come un labirinto vero. Un labirinto 20x15 è largo
41 caratteri. Lo sfondo NON viene forzato: vale il tema del
terminale. Sotto il labirinto c'è un **menu numerato in INGLESE**
dentro una cornice (tutto il programma è in inglese, come il subject):
`1) Regenerate maze` (richiama generate con gli stessi parametri),
`2) Show/hide path`, `3) Change wall colour`, `q) Quit`. I = entrata,
O = uscita, **percorso = catena di punti `·` verdi** (si vede a colpo
d'occhio dove si passa), **"42" = blocco unico e uniforme: ogni
mattoncino del pattern è un quadratino PIENO dello stesso colore dei
muri, e i muri interni delle cifre sono dello stesso colore → il 42
appare come un blocco compatto senza linee interne, in qualsiasi
colore scelto con `3` — cifre 3x5 celle, il 2 ha lati di 3 caselle
che si incrociano a 90 gradi** (le celle vuote delle cifre sono celle
NORMALI: il labirinto ci scava dentro e il percorso ci passa; i
mattoncini restano isole chiuse, quindi 4 e 2 si leggono lo stesso).
**Il muro esterno del labirinto è completamente chiuso**: entry ed
exit sono celle marcate dentro il bordo, non aperture.

### Perché il labirinto sembra alto e stretto?

Il labirinto 20x15 è più LARGO che alto in celle (20 colonne, 15
righe), ma a schermo sembra il contrario. Il motivo: i caratteri del
terminale non sono quadrati — un carattere è circa 2 volte più ALTO
che largo. Con 1 cella = 1 carattere, 20 caratteri in orizzontale
occupano meno spazio visivo di 15 righe in verticale → il labirinto
appare alto e stretto.

Non è un bug: è l'effetto ottico della griglia di caratteri. Per
farlo sembrare "sdraiato" basta aumentare WIDTH nel config (es.
WIDTH=40 HEIGHT=15): nel codice non cambia nulla.

## 1.8 Il main e la gestione errori

`a_maze_ing.py` è il direttore d'orchestra: controlla gli argomenti,
chiama le tappe A→E nell'ordine della mappa, gestisce gli errori senza
mai crashare (messaggio chiaro + uscita con codice 1). Tre livelli di
protezione: ConfigError (config sbagliato), OSError (file illeggibile),
un except finale di sicurezza (mai traceback sullo schermo).

---

# 2. I moduli

Tutto è stato fatto e studiato INSIEME da mpanzani e roblomba: ogni
file è di tutti e due.

| File | Cosa fa | Spiegato in |
|------|---------|-------------|
| config_parser.py | legge e valida config.txt → Config | 1.1 |
| mazegen.py | genera il labirinto + BFS | 1.4, 1.5 |
| output_writer.py | scrive il file esadecimale | 1.6 |
| display.py | terminale interattivo | 1.7 |
| a_maze_ing.py | orchestrazione + errori | 1.8 |
| pacchetto mazegen | modulo riusabile installabile con pip | README |

# 3. Studio del codice (in ordine di esecuzione)

La teoria (parte 1) dice COSA fa il programma. Questa parte dice COME
lo fa: riga per riga, nell'ORDINE DI ESECUZIONE (lo stesso della
mappa: input → generazione → percorso → output → display). Si seguono
le CHIAMATE: quando una riga chiama una funzione di un altro file, ci
si sposta lì e si resta finché l'esecuzione non torna indietro. Per
questo 3.1 copre il main solo fino alla tappa A, e 3.2 parte dalla
chiamata a parse_config. Ogni sezione è la BASE completa del file; gli
approfondimenti nascono dalle domande fatte in chat e vengono aggiunti
man mano come sotto-sezioni.

## L'ordine di studio (perché questo)

1. **a_maze_ing.py** — il direttore d'orchestra: piccolo, fa solo
   chiamare gli altri file nell'ordine giusto. Studiandolo per primo
   si vede TUTTA la mappa del programma in miniatura.
2. **config_parser.py** — la PRIMA cosa che il main chiama: nasce il
   Config.
3. **mazegen.py** — il cuore: griglia, talpa, piccone, 42, BFS.
4. **output_writer.py** — scrive il file esadecimale.
5. **display.py** — il display interattivo.

Per ogni file si risponde a: cos'è → cosa fa nel flusso → esecuzione
riga per riga (in ordine!) → chi è cosa (predefinito di Python o
nostro) → analogie col C → risposte pronte per l'evaluation.

---

## 3.1 a_maze_ing.py — il direttore d'orchestra

### Cos'è

Il file principale: quello che si esegue con
`python3 a_maze_ing.py config.txt`. Fa SOLO il direttore d'orchestra:
non genera, non scrive, non disegna niente da solo — chiama gli altri
file (i "musicisti") nell'ordine giusto e protegge tutto dagli errori.
È l'unico file che si esegue direttamente; gli altri si importano.

### Il flusso in miniatura (le tappe)

1. controlla gli argomenti da terminale (righe 28-30)
2. tappa A: parse del config, dentro un try (righe 32-39)
3. tappa B: crea il generatore e genera il labirinto (righe 41-43)
4. tappa C: trova il percorso (riga 45)
5. tappa D: scrive il file di output (righe 46-47)
6. se il 42 manca, avvisa con un messaggio (righe 49-50)
7. tappa E: apre il display (riga 52)
8. in fondo: il "pulsante di avvio" (righe 55-63)

### Esecuzione riga per riga

**Righe 1-11: l'header 42.** Solo un commento obbligatorio della
scuola (login, data): Python lo salta, come /* ... */ in C.

**Righe 13-16: la docstring.** Il primo `"""..."""` dentro un file o
una funzione non è un semplice commento: è la DOCUMENTAZIONE ufficiale
di quel file o funzione (si può leggere con help()). Qui dice a cosa
serve il programma e come si usa.

**Riga 18: `import sys`.** sys è un MODULO PREDEFINITO di Python: una
libreria già pronta dentro Python, come le librerie standard del C
(#include <stdlib.h>). Porta con sé due strumenti che servono qui:
sys.argv (gli argomenti da terminale) e sys.exit (spegnere il
programma con un codice d'uscita).

**Righe 20-23: gli import dei NOSTRI file.** config_parser, display,
mazegen, output_writer sono i NOSTRI moduli: gli altri file .py della
cartella del progetto. `import` = "aggancia quel file: da ora posso
usare le sue funzioni e classi". In C si fa con #include + compilazione
di più file .c; in Python basta scrivere il nome del file senza .py.

**Riga 26: `def main():`** NOSTRA funzione. Il nome main è una
convenzione (non è obbligatorio come in C). `-> None` è il type hint:
la funzione non restituisce niente (come void in C), serve a mypy e al
lettore.

**Righe 28-30: il controllo degli argomenti.**
- `len(sys.argv)` — sys.argv è la LISTA di tutto ciò che è stato
  scritto da terminale: argv[0] = nome del programma, argv[1] = primo
  argomento (il config). È l'argc/argv del C. len() è una funzione
  predefinita che conta gli elementi di una lista.
- `!= 2` — devono esserci ESATTAMENTE 2 elementi: nome del programma
  + file di config. Se l'utente scrive solo `python3 a_maze_ing.py`
  (1 elemento) o troppa roba (3+), si entra nell'if.
- `print(...)` — predefinita, come printf. La f davanti alla stringa
  (f-string) è la "stringa coi buchi": le parti tra { } vengono
  riempite coi valori al momento dell'esecuzione (in C: printf("%s"),
  ma qui si scrive il nome della variabile direttamente nel buco).
- `sys.exit(1)` — spegne il programma SUBITO. Il numero è il codice
  d'uscita: 0 = tutto ok, 1 = errore (come return 1 dal main in C).

**Righe 32-39: tappa A protetta dal try.**
- `try:` apre la RETE DI SICUREZZA: esegui quello che segue, e se
  salta fuori un errore non crashare, vai alla rete giusta. In C non
  esiste: gli errori si controllavano a mano con if e return.
- `config = config_parser.parse_config(sys.argv[1])` — chiama la
  NOSTRA funzione parse_config (file 2, prossimo studio) passandole il
  percorso del config; lei restituisce un oggetto Config: la scatola
  coi parametri validati (width, height, entry, ...).
- `except config_parser.ConfigError as e:` — la PRIMA rete: se
  parse_config alza ConfigError (NOSTRA eccezione = "il config ha un
  contenuto sbagliato"), si cattura qui. `as e` dà un nome all'errore
  per poterlo stampare. Messaggio chiaro + uscita con codice 1.
- `except OSError:` — la SECONDA rete: OSError è un'eccezione
  PREDEFINITA di Python per i problemi di sistema, come "il file non
  esiste" (open fallisce dentro parse_config). Messaggio + uscita 1.
  Il subject chiede esattamente questo: mai crashare, sempre un
  messaggio chiaro.

**Righe 41-43: tappa B (in breve, studiata nel file 3).**
- `gen = mazegen.MazeGenerator(...)` — crea un oggetto della NOSTRA
  classe MazeGenerator: il "laboratorio" con larghezza, altezza e
  seed. `config.width` = il campo width della scatola Config (il
  punto è l'accesso ai campi, come struct.field in C).
- `gen.generate(perfect=..., entry=..., exit=...)` — genera il
  labirinto. I nomi con = sono gli ARGOMENTI CHIAVE: i valori si
  passano per nome e l'ordine non conta (in C non esistono). Al
  ritorno, gen.grid contiene la griglia.

**Riga 45: tappa C.** `path = gen.solve()` — il BFS (capitolo 1.5)
trova il percorso più corto e lo restituisce come lista di celle.

**Righe 46-47: tappa D.** `output_writer.write_output_file(...)` —
scrive il file di output (capitolo 1.6, file 4).

**Righe 49-50: il messaggio del 42.** Se `gen.has_42` è False (maze
troppo piccolo, sotto 9x6), il main stampa il messaggio richiesto dal
subject e il programma CONTINUA lo stesso.

**Riga 52: tappa E.** `display.run(gen)` — apre il display
interattivo (capitolo 1.7, file 5).

**Righe 55-63: il pulsante di avvio e l'ultima rete.**
- `if __name__ == "__main__":` — il trucco più famoso di Python.
  __name__ è una variabile PREDEFINITA che Python riempie da solo con
  il nome del file. Quando il file viene ESEGUITO da terminale,
  Python la riempie con la stringa "__main__" → la condizione è vera
  → main() parte. Quando invece il file viene IMPORTATO da un altro
  file, contiene "a_maze_ing" → main() NON parte. Serve per poter
  riusare il file senza eseguirlo per sbaglio. In C il problema non
  esiste: main() è l'unico punto d'ingresso per costruzione del
  linguaggio.
- `try: main()` con `except KeyboardInterrupt:` — il Ctrl+C (il
  SIGINT del C): stampa una riga vuota ed esce con codice 0 (l'utente
  ha chiuso lui: non è un errore). Senza questa rete, Ctrl+C
  lascerebbe il traceback brutto sullo schermo.
- `except Exception:` — l'ULTIMA rete: qualunque errore non previsto
  viene comunque catturato: messaggio chiaro e uscita 1. Mai crash,
  mai traceback, come chiede il subject.

### Chi è cosa

| Nome | Predefinito o nostro |
|------|----------------------|
| sys | predefinito (modulo della libreria standard) |
| len, print | predefinite (funzioni built-in) |
| __name__ | predefinita (variabile speciale di Python) |
| KeyboardInterrupt, OSError, Exception | predefinite (eccezioni) |
| ConfigError | NOSTRA (definita in config_parser.py) |
| parse_config, write_output_file, run | NOSTRE funzioni |
| MazeGenerator, Config | NOSTRE classi |
| main, gen, config, path, e | NOSTRI (funzione, oggetti, variabili) |

### Analogie col C

| Python | C |
|--------|---|
| import sys | #include <stdlib.h> |
| sys.argv | argv |
| len(sys.argv) != 2 | argc != 2 |
| print(f"...{x}...") | printf |
| sys.exit(1) | exit(1) / return 1 |
| try/except | non esiste (errori a mano con if) |
| config.width | struct.field |
| if __name__ == "__main__" | non serve: main() è già l'ingresso |

### Risposte pronte per l'evaluation

- "Da dove parte il programma?" Dal fondo: il blocco
  if __name__ == "__main__" chiama main().
- "Perché controlli len(sys.argv) != 2?" Perché servono esattamente
  il nome del programma + il file di config: con un numero diverso di
  argomenti si stampa l'uso corretto e si esce con codice 1.
- "Perché try/except?" Il subject vieta i crash: ogni errore
  prevedibile ha la sua rete con messaggio chiaro, e l'ultimo except
  Exception copre tutto il resto. Ctrl+C è trattato a parte con
  codice 0.
- "Il main genera il labirinto?" No: chiama solo i moduli
  nell'ordine giusto (parse → generate → solve → write → display).

---

## 3.2 config_parser.py — dalla chiamata del main alla nascita del Config

### Cos'è

Il modulo che il main chiama per PRIMO (tappa A, riga 33): legge
config.txt (righe KEY=VALUE), lo valida e restituisce l'oggetto Config
coi parametri del labirinto. Studio in ordine di CHIAMATE: entriamo
qui dalla riga 33 del main e ci restiamo finché parse_config non
ritorna al main col Config in mano.

### Prima della chiamata: cosa è successo all'import (righe 13-86)

Il file config_parser.py NON nasce alla riga 33 del main: nasce alla
riga 20, all'import. In quel momento Python ha eseguito il file
dall'alto in basso e ha PREPARATO le definizioni:

- REQUIRED_KEYS: la lista delle chiavi obbligatorie
- class ConfigError: la NOSTRA eccezione (la prima rete del main)
- class Config: la scatola che nascerà alla fine
- le 4 funzioni di servizio: _parse_int, _parse_bool, _parse_coords,
  _check_bounds (il trattino basso = convenzione "uso interno del
  file")

Preparare non è fare: niente di visibile è successo (come dichiarare
le funzioni in C prima del main). Le funzioni di servizio verranno
spiegate quando verranno CHIAMATE, nell'ordine di esecuzione.

### Dentro parse_config (righe 88-101)

- La docstring è il contratto: "mi dai il percorso, ti restituisco
  Config; contenuto sbagliato → ConfigError; file illeggibile → OSError
  che PROPAGA al chiamante".
- Riga 101: values, la scatola vuota — chiavi stringhe (WIDTH,
  HEIGHT...) e valori stringhe (ancora grezzi: "20" come parola, non
  come numero). Ci finiscono le righe del config NON ancora
  interpretate.

### Riga 102: ★ PRIMA VOLTA — with e open

- **open(path, "r", encoding="utf-8")** — la fopen del C: chiede al
  sistema operativo di preparare il file per la lettura e restituisce
  il MANICO (file object): il biglietto con cui si parla col file. Il
  contenuto NON viene caricato in memoria. I tre ingredienti: path =
  quale file (la stringa passata dal main); "r" = modalità sola
  lettura; encoding="utf-8" = l'etichettatura dei caratteri (argomento
  chiave, passato per nome).
- **as f** — il nome del manico (in C: FILE *f = fopen(...)).
- **with** — la porta che si chiude da sola: alla fine del blocco
  indentato (righe 103-117) il file viene chiuso SEMPRE, anche se
  dentro scoppia un errore. Risolve il bug classico del C: dimenticarsi
  la fclose (o uscire prima per un errore) lascia il file aperto.
- Il filo col main: se il file non esiste, open fallisce QUI con
  OSError; parse_config non lo cattura ("propaga") e l'errore risale
  alla SECONDA rete del try nel main → messaggio + uscita 1.

### Righe 103-106: la lettura riga per riga

- line_no = 0: contatore di righe, per i messaggi d'errore.
- for line in f: a ogni giro line diventa UNA riga intera del file; il
  for va a pescare la successiva da solo e si ferma da solo alla fine.
  Il file non è mai tutto in memoria (una scatola alla volta dal
  nastro; in C: while con fgets). La riga contiene ANCHE il carattere
  invisibile di fine riga.
- line_no = line_no + 1: il contatore sale a ogni giro.
- stripped = line.strip(): strip è un METODO delle stringhe (un
  comando che ogni stringa sa fare): toglie gli spazi alle estremità e
  il fine-riga invisibile. line resta sporca, stripped è la pulita.

### Le decisioni del loop (righe 107-117): cosa fare di ogni riga

- `if stripped == "" or stripped.startswith("#"):` — due casi in cui
  la riga NON conta: è vuota (dopo la pulizia non resta niente) oppure
  è un commento (inizia con #). ★ PRIMA VOLTA `startswith`: metodo
  delle stringhe che risponde "inizio con questa parte?" (in C:
  strncmp). `or` = "oppure": basta che una delle due condizioni sia
  vera. `==` è il confronto di uguaglianza.
- `continue` — ★ PRIMA VOLTA: "salta tutto quello che resta di QUESTO
  giro e passa alla riga successiva del for" (identico al continue del
  C).
- `if "=" not in stripped:` — ★ PRIMA VOLTA `in` su una stringa:
  "questa parte sta DENTRO l'altra?" (in C: strstr). `not in` è il
  contrario. Se la riga non contiene l'=, non è una KEY=VALUE → `raise
  ConfigError(...)`: ★ PRIMA VOLTA `raise`: "alza" l'errore —
  l'esecuzione della funzione si FERMA qui e l'errore vola alla rete
  più vicina (la prima rete del try del main). L'f-string porta il
  numero di riga: ecco a cosa serve line_no.
- `key, value = stripped.split("=", 1)` — ★ PRIMA VOLTA `split`:
  taglia la stringa al segno indicato e restituisce i PEZZI. Il
  secondo argomento 1 = "taglia solo al PRIMO =" (un valore potrebbe
  contenere altri =). `key, value =` è lo SPACCHETTAMENTO: i due pezzi
  finiscono uno per variabile (in C: strtok + copie a mano).
- `key = key.strip()` e `value = value.strip()` — pulizia dei pezzi:
  via gli spazi rimasti attorno all'= (strip già vista alla riga 106).
- `if key in values:` — `in` su un DIZIONARIO guarda le CHIAVI:
  "questa chiave c'è già?" → doppione → ConfigError (ogni chiave deve
  comparire una volta sola).
- `values[key] = value` — l'inserimento: la scatola si riempie della
  coppia chiave→valore, ancora come STRINGHE.

Quando le righe del file sono finite, il for si ferma da solo; finisce
il blocco del with e il file si chiude da solo (la porta automatica).

### La validazione (righe 119-147): dalle stringhe ai valori veri

- `missing: list[str] = []` — la lista vuota delle chiavi mancanti.
  `for key in REQUIRED_KEYS:` scorre le obbligatorie; se una non sta
  nel dizionario, `missing.append(key)`: ★ PRIMA VOLTA `append`:
  aggiunge un elemento IN CODA alla lista (in C non esiste: si faceva
  a mano con l'indice).
- Se alla fine missing non è vuota → ConfigError con
  `", ".join(missing)`: ★ PRIMA VOLTA `join`: incolla i pezzi della
  lista con la virgola+spazio in mezzo (il rovescio di split; in C: un
  ciclo di strcat).
- Ora le CONVERSIONI, nell'ordine delle chiamate.
  `width = _parse_int(values["WIDTH"], "WIDTH")`: il pallino salta alla
  riga 54 — QUI viene chiamata la prima funzione di servizio.
  `values["WIDTH"]` è la parola "20"; dentro, `int(raw)` (★ PRIMA
  VOLTA `int`: la atoi del C: la parola diventa numero) dentro un
  try/except: se la parola non è un numero, int alza ValueError
  (eccezione predefinita) e la rete della funzione la trasforma in
  ConfigError col messaggio chiaro, che vola al main; se riesce,
  return consegna il numero e il pallino torna alla riga 126. height
  identico.
- `if width < 2 or height < 2:` — un labirinto deve essere almeno 2x2.
- `entry = _parse_coords(values["ENTRY"], "ENTRY")` — salta alla riga
  71: split(",") taglia "0,0" in due pezzi; se non sono ESATTAMENTE
  due → errore; altrimenti converte i pezzi (dopo strip) con _parse_int
  e li impacchetta: `return (x, y)` — ★ PRIMA VOLTA la COPPIA
  (tupla): il pacchetto di valori tra parentesi tonde (in C: una
  struct o due variabili separate; qui il pacchetto viaggia intero).
- `_check_bounds(entry, width, height, "ENTRY")` — salta alla riga 81:
  spacchetta la coppia (`x, y = point`) e controlla i quattro bordi;
  fuori → ConfigError. exit identico — con un dettaglio di nome: la
  variabile si chiama `exit_` col trattino IN FONDO perché exit è una
  funzione predefinita di Python e non vogliamo coprirla (convenzione).
- `if entry == exit_:` — entrata e uscita devono essere diverse.
- `perfect = _parse_bool(values["PERFECT"], "PERFECT")` — salta alla
  riga 62: accetta solo "True" e "False" ESATTI, altrimenti
  ConfigError. ★ PRIMA VOLTA i VALORI DI VERITÀ: True/False sono il
  bool (in C non esistevano: si usava int 0/1).
- `output_file = values["OUTPUT_FILE"]` — resta testo così com'è (è un
  nome di file); si controlla solo che non sia vuoto.
- SEED è FACOLTATIVA: `if "SEED" in values:` — se nel config non c'è,
  seed resta None. ★ PRIMA VOLTA `None`: il "nessun valore" (il NULL
  del C): significherà "usa un seme casuale vero". Se c'è → _parse_int.

### La nascita del Config e il ritorno al main (riga 148)

`return Config(width, height, entry, exit_, output_file, perfect,
seed)` — QUI viene chiamata la classe Config: il pallino salta al suo
__init__ (riga 42), la FABBRICA della scatola: ogni campo
`self.width = width` ecc. ★ PRIMA VOLTA `self`: il pronome "io"
dell'oggetto — ogni oggetto tiene i propri valori nei propri campi,
come i campi di una struct in C, ma qui la struct si passa DA SOLA:
self arriva come primo parametro di ogni metodo, senza scriverlo nella
chiamata. Poi return consegna la scatola finita al chiamante → il
pallino torna al MAIN, riga 33: `config =` la riceve. TAPPA A
COMPLETA: da qui in poi il main userà config.width, config.height...

### Chi è cosa

| Nome | Predefinito o nostro |
|------|----------------------|
| open, int, len, print | predefinite (funzioni built-in) |
| with, for, if, return, raise, continue, or, not, in, == | predefinite (parole chiave/operatori) |
| startswith, strip, split, append, join | predefiniti (metodi di stringhe e liste) |
| ValueError | predefinita (eccezione) |
| None, True, False | predefiniti (valori speciali) |
| tuple (la coppia) | predefinito (tipo) |
| path, key | NOSTRI (parametri) |
| values, f, line, line_no, stripped, missing, width, height, entry, exit_, perfect, output_file, seed | NOSTRE variabili |
| parse_config, _parse_int, _parse_bool, _parse_coords, _check_bounds | NOSTRE funzioni |
| REQUIRED_KEYS | NOSTRA costante |
| ConfigError, Config | NOSTRE classi |
| self | NOSTRO (parametro speciale dei metodi) |

### Analogie col C

| Python | C |
|--------|---|
| open(path, "r") | fopen(path, "r") |
| as f | FILE *f = ... |
| with | non esiste: fclose a mano (rischio di dimenticarla) |
| for line in f | while (fgets(...) != NULL) |
| line.strip() | non esiste: spazi e fine-riga da togliere a mano |
| encoding="utf-8" | la scelta dell'encoding/locale |
| startswith("#") | strncmp(line, "#", 1) == 0 |
| "=" not in stripped | strstr(line, "=") == NULL |
| split("=", 1) | strtok |
| raise ConfigError | non esiste: return -1 + if a cascata |
| int(raw) | atoi |
| append | non esiste in C (C++: push_back) |
| ", ".join(missing) | ciclo di strcat |
| tupla (x, y) | struct o due variabili |
| True/False | int 0/1 |
| None | NULL |
| self | la struct passata per puntatore (in C++: this) |

### Risposte pronte per l'evaluation

- "Quando viene eseguito config_parser.py?" All'import (riga 20 del
  main): Python prepara le definizioni; parse_config viene CHIAMATO
  alla riga 33 e solo lì parte il suo corpo.
- "Cosa fa open? Perché gli dai 3 argomenti?" Apre il file in lettura
  e restituisce il manico. path = quale file, "r" = sola lettura,
  encoding = etichettatura dei caratteri.
- "Perché with?" Garantisce la chiusura del file a fine blocco anche
  in caso di errore: in C la fclose si dimentica facilmente.
- "Il file viene caricato tutto in memoria?" No: il for legge una riga
  alla volta.
- "Dove finisce l'errore se il file non esiste?" open alza OSError;
  parse_config lo lascia propagare; lo prende la seconda rete del try
  nel main (messaggio + uscita 1).
- "Cosa succede se una riga è un commento o è vuota?" startswith("#")
  o stringa vuota → continue: la riga viene saltata.
- "Perché split('=', 1) e non split('=')?" Per tagliare solo al PRIMO
  = (il valore può contenerne altri).
- "Cosa fa raise?" Interrompe la funzione e consegna l'errore alla
  rete più vicina (il try del main).
- "Perché le funzioni hanno il trattino basso davanti?" Convenzione:
  sono di uso interno del file.
- "Perché exit_ col trattino in fondo?" Per non coprire la funzione
  predefinita exit.
- "Se SEED manca dal config cosa succede?" Resta None: il generatore
  userà un seme casuale vero.
- "Quando nasce il Config?" Alla riga del return, che chiama la classe
  Config: è l'ultima cosa prima di tornare al main.

---

## 3.3 mazegen.py — il cuore: talpa, piccone, 42 e fuoco

### Cos'è

Il modulo con la classe MazeGenerator: genera il labirinto (talpa +
piccone + 42, teoria 1.4) e trova il percorso (BFS, teoria 1.5). È
AUTONOMO: non sa niente di config.txt, del file di output o del
display — per questo è anche il modulo riusabile del subject. Studio
in ordine di chiamate: tappa B del main (creazione + generazione),
poi tappa C (solve).

### All'import (righe 28-62): la preparazione

- `import random` — il cassetto dei DADI (teoria 1.3).
  `from collections import deque` — ★ PRIMA VOLTA `from ... import`:
  prende UN pezzo solo dal cassetto (qui la coda, spiegata in solve).
- Le 4 monete N/E/S/W = 1/2/4/8 (teoria 1.2).
- FOUR e TWO: i disegni delle cifre come LISTE DI COPPIE (x, y),
  ciascuna relativa all'angolo del disegno (il commento con # e . nel
  file mostra la forma delle cifre). Sono costanti: non cambiano mai.
- La definizione della classe (righe 65-78): la docstring coi campi. I
  METODI (le funzioni dell'oggetto) si spiegano quando vengono
  chiamati.

### __init__ (righe 80-89): la nascita dell'oggetto — tappa B, prima chiamata

`MazeGenerator(config.width, config.height, config.seed)` nel main fa
scattare la fabbrica:

- `self.width = width` ecc. — self = "io": l'oggetto nasce e si mette
  i valori in tasca (i campi della struct del C, ma col punto).
- `self.rng = random.Random(seed)` — ★ PRIMA VOLTA `Random`: la
  macchinetta dei dadi col seme (teoria 1.3: il librone). Con seed=None
  userà un seme casuale vero (il None del 3.2).
- grid = [] (vuota: la riempirà generate), forty_two = [] (nessun
  mattoncino ancora), has_42 = False, entry/exit/perfect PROVVISORI
  (saranno riscritti da generate).

### generate (righe 109-149): il direttore della generazione

- Salva i parametri: perfect, entry; per exit: `if exit is None:` (★
  PRIMA VOLTA `is None`: il controllo "è davvero nessun valore?" — non
  si confronta con ==) usa l'angolo in basso a destra.
- La validazione: _in_bounds (riga 91: dentro i bordi?) — se fuori, o
  se entry == exit → `raise ValueError` (eccezione predefinita: "chi
  ha chiamato ha sbagliato"; è la rete di sicurezza per chi importa il
  modulo).
- La griglia: DOPPIO FOR annidato (righe 138-142): ★ PRIMA VOLTA
  `range`: la sequenza 0, 1, 2... fino a n-1 (il for (int i = 0; i <
  n; i++) del C). Per ogni riga si crea una lista e per ogni cella si
  mette N+E+S+W = 1+2+4+8 = 15: TUTTE le scatole chiuse (il punto di
  partenza della teoria 1.4).
- I tre passi nell'ordine: _carve_42, _carve_maze, poi
  _carve_extra_walls SOLO se not perfect (i cicli del piccone).

### _carve_42 (righe 151-186): il disegno "42" (teoria 1.4, già a fondo)

- forty_two azzerata e has_42 = False: si riparte puliti a ogni
  generazione.
- `if not with_42: return` — il ritorno anticipato: esce subito senza
  disegnare.
- `if self.width < 9 or self.height < 6: return` — troppo piccolo →
  salta (has_42 resta False → il messaggio del main).
- start_x e start_y: `(self.width - 7) // 2` — ★ PRIMA VOLTA `//`: la
  DIVISIONE INTERA (il quoziente senza resto, come la divisione tra
  int del C; è il centraggio del capitolo "Il 42 deve essere
  perfettamente centrato?"). Poi `if start_y < 1: start_y = 1` — la
  correzione del bug: sempre almeno una riga libera sopra le cifre.
- La costruzione: per ogni coppia del disegno FOUR si aggiunge
  (start_x + dx, start_y + dy) — il disegno TRASLATO al centro; per TWO
  si aggiunge +4 in orizzontale (3 colonne del 4 + 1 di spazio tra le
  cifre).
- Se un mattoncino coprirebbe entry o exit → return senza disegnare
  (entrata e uscita devono restare celle normali).
- Altrimenti forty_two = pattern e has_42 = True. NOTA: qui NON si
  tocca nessun muro: i mattoncini verranno marcati "visitati" in
  _carve_maze.

### Approfondimento: with_42 e has_42 — la richiesta e il risultato

Due booleani con due mestieri diversi (analogia del ristorante):

- **with_42 = la RICHIESTA** ("voglio il 42?"). È un parametro di
  generate, col default True: il main non lo scrive nemmeno, il display
  lo passa esplicitamente col menu 1. NON è un "permesso di accesso":
  generate chiama _carve_42 SEMPRE, e la decisione sta DENTRO di lei,
  come primissima riga (if not with_42: return).
- **has_42 = il RISULTATO** ("questo labirinto HA davvero il 42?"). È
  un campo dell'oggetto letto DOPO la generazione: il main lo usa per
  decidere se stampare il messaggio di omissione, i test per la soglia
  9x6.

Volere non è ottenere: la richiesta può fallire per 3 motivi (nessuna
richiesta, labirinto troppo piccolo, il disegno coprirebbe entry o
exit). has_42 parte PESSIMISTA (False) e diventa True SOLO all'ultima
riga di _carve_42, quando il disegno è stato davvero piazzato: ogni
return anticipato lascia il False.

Perché azzerarlo a OGNI generazione: generate può essere richiamata
sullo STESSO oggetto (il menu 1 del display). Il True di ieri sarebbe
lo scontrino vecchio in tasca: senza l'azzeramento, il main non
stamperebbe il messaggio anche se il labirinto nuovo non ha il 42.
Ogni generazione riparte da zero e racconta solo se stessa.

Risposta da evaluation: "with_42 è la richiesta di disegnare il 42,
has_42 è il resoconto onesto di cosa è successo davvero: il main
stampa il messaggio di omissione solo se il 42 non c'è, e ogni
generazione riparte da False per non ereditare il risultato della
precedente."

### _carve_maze (righe 188-218): la talpa (teoria 1.4, le 3 regole)

- visited: la griglia dei segni "già visto", tutta False (i valori di
  verità del 3.2), costruita col doppio for.
- I mattoncini del 42 marcati True SUBITO: per la talpa sono GIÀ
  visitati → non ci scava mai dentro → restano isole chiuse. (Il
  trucco del 42.)
- `stack = [self.entry]` — la CORDA: la lista usata come pila (teoria
  1.4: LIFO, si tocca solo la cima). La talpa parte dall'entrata e la
  marca subito visitata.
- Il while (finché la corda non è vuota):
  - `x, y = stack[len(stack) - 1]` — guarda la CIMA (l'ultimo
    elemento) senza toglierla: la talpa è lì.
  - `_unvisited_neighbors` (riga 220): i 4 controlli (sopra, destra,
    sotto, sinistra); per ognuno: dentro i bordi? non visitato? → si
    aggiunge la terna di informazioni: (vicino, moneta del muro dal MIO
    lato, moneta dal SUO lato) — es. verso NORD: (x, y-1, N, S): io
    apro il muro NORD, il vicino apre il muro SUD: il muro si toglie
    dai DUE lati (la coerenza del subject).
  - Se la lista è vuota: `stack.pop()` — ★ PRIMA VOLTA `pop`: toglie
    l'ULTIMO elemento (la cima della corda): il BACKTRACKING — la talpa
    torna sui suoi passi.
  - Altrimenti: `nx, ny, mask_here, mask_there =
    self.rng.choice(neighbors)` — il DADO: ★ PRIMA VOLTA `choice`:
    sceglie un elemento a caso della lista (tante facce quanti vicini
    disponibili, teoria 1.4). Poi _remove_wall (riga 101: toglie la
    moneta → il muro si apre; la sottrazione funziona perché la moneta
    c'è di sicuro) da entrambi i lati, marca il vicino,
    stack.append(...): la talpa si sposta.
- Fine: la corda si svuota quando TUTTE le celle raggiungibili sono
  scavate (teoria: la generazione finisce quando tutte le celle sono
  visitate, NON all'uscita).

### Approfondimento: la coppia (x, y) contro la griglia [y][x]

- La COPPIA entry è (x, y): il PRIMO pezzo è la colonna (entry[0]), il
  SECONDO è la riga (entry[1]). L'ordine viene dal subject: ENTRY=0,0
  vuol dire colonna 0, riga 0.
- La GRIGLIA invece è [y][x]: prima la RIGA, poi la colonna. Motivo:
  la griglia è una LISTA DI RIGHE — il primo indice sceglie QUALE riga
  (la y), il secondo sceglie la posizione DENTRO la riga (la x).
- Due lingue diverse convivono: per tradurre la coppia in griglia si
  INVERTE. visited[self.entry[1]][self.entry[0]] =
  visited[y][x]. Con entry = (3, 1): visited[1][3] = riga 1, colonna
  3. Scrivere visited[3][1] sarebbe la cella SBAGLIATA (riga 3,
  colonna 1).
- Cosa FA la riga: marca la cella di partenza come "già visitata"
  PRIMA del while. La talpa parte IN PIEDI sull'entrata (la corda
  inizia proprio da lì, stack = [self.entry]): esserci significa averla
  già visitata automaticamente, e la riga è il REGISTRO ufficiale di
  questo fatto. Senza il segno, la talpa dalle celle vicine vedrebbe
  l'entrata come una cella NUOVA e ci riscenderebbe dentro.
  Lo stesso schema si ripete a ogni passo: visited[ny][nx] = True (nx
  e ny sono anche loro in ordine (x, y): sempre coppia → griglia
  invertita).
- In C: visited è int visited[H][W], entry è una struct con x e y:
  visited[entry.y][entry.x].

Risposta da evaluation: "La coppia è in ordine (x, y) perché così la
scrive l'utente nel config; la griglia è [y][x] perché è una lista di
righe. La scrittura inverte apposta: il secondo pezzo della coppia (la
y) diventa il primo indice. La riga marca l'entrata come già visitata
prima che la talpa parta."

### Approfondimento: la cima della corda, il nome neighbors e il self

- `x, y = stack[len(stack) - 1]` — con 5 elementi gli indici sono
  0-4: len-1 è l'indice dell'ULTIMO elemento, la CIMA della corda, la
  cella dove sta la talpa adesso. L'elemento è una coppia e lo
  SPACCHETTAMENTO la apre in x e y. La riga GUARDA soltanto: nessun
  pop. In C: stack[top].x, stack[top].y.
- Perché la variabile si chiama neighbors e non unvisited_neighbors:
  il filtraggio lo ha già fatto il METODO (è il suo nome a
  garantirlo). La variabile è il soprannome corto per uso interno;
  ripetere il nome intero sarebbe ridondante, e ogni uso successivo
  (len, choice) più verboso senza aggiungere nulla. Il nome lungo sta
  sull'etichetta (il metodo, usato anche da fuori); dentro il loop
  "neighbors" significa già "i vicini disponibili". I nomi non
  cambiano il comportamento: servono a chi legge, non a Python.
- Il self — il pronome "io": _unvisited_neighbors è un metodo
  dell'oggetto, e per chiamarlo si dice di QUALE oggetto
  (self._unvisited_neighbors = "il MIO metodo"). Dentro di lui si
  leggono self.width e self.height: senza self non saprebbe di quale
  labirinto controllare i bordi. Python passa l'oggetto da solo come
  primo argomento invisibile che atterra in self: non si scrive mai
  nella chiamata. In C: unvisited_neighbors(gen, x, y, visited) con la
  struct passata a mano.
- Perché visited NON è dentro self: è il foglio di lavoro di QUESTA
  generazione (nasce e muore in _carve_maze). Self porta le cose
  PERMANENTI dell'oggetto (griglia, misure, dadi); le cose temporanee
  di un singolo lavoro si passano come parametri normali.

Risposta da evaluation: "La talpa è sempre sulla cima della corda:
stack[len(stack)-1] è l'ultimo elemento, spacchettato in x e y, e si
guarda senza togliere nulla. neighbors riceve il risultato di
_unvisited_neighbors: il filtro l'ha già fatto il metodo, ripetere il
nome sarebbe ridondante. self è l'oggetto stesso, passato da Python
in automatico: il metodo ne legge width e height."

### Approfondimento: _unvisited_neighbors — il giro dei 4 controlli

- La domanda a cui risponde: "da qui, in quali celle posso ancora
  scavare?" NON scava e NON sceglie: fa solo l'ELENCO (la scelta la
  farà dopo il dado, rng.choice).
- Il risultato: una lista di PACCHETTI DA 4: (nx, ny, la mia moneta,
  la sua moneta). Le due monete sono lo STESSO muro visto dai due lati
  (la coerenza del subject); le coppie speculari sono N<->S e E<->W.
- I 4 controlli in ordine N, E, S, W — lo stesso ordine delle monete
  1, 2, 4, 8. Ogni controllo ha DUE condizioni unite da and: 1) il
  vicino ESISTE (il bordo: y>0, x<width-1, y<height-1, x>0); 2) il
  vicino NON è visitato.
- I 4 if sono INDIPENDENTI, non un if/elif: ogni cella passa SEMPRE
  per tutti e quattro, in ordine, e ogni controllo risponde da solo.
  Una cella può superarne 0, 1, 2, 3 o 4. Chi non ne supera nessuno ha
  la lista vuota (= pop): è un caso LEGALE, il motore del
  backtracking, non un errore. (Diverso da _junction e _parse_bool,
  dove l'if/elif è a cascata e il primo vince.) Non si potrebbe usare
  l'elif qui: il dado deve poter scegliere tra TUTTI i vicini
  disponibili, e l'elif ne lascerebbe al massimo uno.
- L'ORDINE è lo scudo: l'and si ferma al primo falso, quindi con y=0
  la seconda condizione non viene nemmeno letta. Se fossero invertite,
  Python leggerebbe visited[-1][x] = l'ULTIMA riga (gli indici
  negativi sono VALIDI in Python!): cella sbagliata e nessun errore;
  in C sarebbe un segfault. Il bordo si controlla PRIMA proprio per
  questo.
- ATTENZIONE: NON si escludono le celle di bordo! Da (1, 0) la talpa
  guarda in TRE direzioni (manca solo il NORD, dove il vicino NON
  ESISTE oltre il muro esterno). Le celle di bordo sono normali:
  l'entrata (0, 0) è un ANGOLO e la generazione parte proprio da lì.
  La condizione del bordo non penalizza la cella: impedisce solo di
  guardare dove non c'è niente (in C: la stessa guardia y > 0).
- Lista vuota = talpa bloccata = il chiamante fa pop (il
  backtracking). Lista non vuota = il dado sceglie un pacchetto e
  _remove_wall toglie le due monete, una per lato.
- Perché una funzione a parte: isola una domanda ben precisa e lascia
  _carve_maze leggibile.
- In C: una funzione helper che riempie un array di struct e
  restituisce quanti vicini ha trovato; l'&& corto-circuita uguale.

Risposta da evaluation: "Guarda i 4 lati in ordine N/E/S/W: per ogni
lato controlla PRIMA che la cella esista (bordo) e POI che non sia
visitata — l'ordine protegge la griglia dagli indici fuori bordo. Per
ogni vicino valido impacchetta le coordinate con le due monete
speculari. Lista vuota = bloccata → pop."

### Approfondimento: quando si svuota la corda (la fine della generazione)

- La corda cresce solo con APPEND (cella nuova) e cala solo con POP
  (passo indietro). Il POP scatta solo quando la cella in cima non ha
  vicini non visitati.
- La corda arriva a 0 in UN solo modo: l'ultimo POP dall'ENTRATA
  stessa — la talpa è tornata al punto di partenza e non c'è più
  nessuna cella nuova da scavare da NESSUN punto del percorso.
- In quel momento TUTTE le celle sono visitate (traccia reale 3x3,
  seed 42: 9 celle visitate su 9; ultimo passo: POP da (0,0)).
- Il momento arriva SEMPRE: le celle sono finite e ognuna entra nella
  corda al massimo una volta (si appendono solo celle non visitate,
  subito marcate). Quando la talpa non può più appendere, può solo
  fare POP su POP, e l'ultimo POP possibile è dall'entrata.
- In un labirinto grande salite e discese si alternano (la talpa si
  blocca, torna indietro un pezzo, riparte da un altro buco), ma il
  finale è sempre lo stesso.
- La generazione NON finisce all'uscita: l'uscita non c'entra niente
  con la talpa. Finisce quando la corda è vuota = tutte le celle
  scavate.

Risposta da evaluation: "Il while esce quando la corda è vuota:
l'ultimo pop è dall'entrata stessa. Succede quando non esiste più
nessuna cella non visitata: la generazione finisce quando TUTTE le
celle sono scavate, non all'uscita."

### _carve_extra_walls (righe 238-275): il piccone (teoria 1.4 PERFECT=False)

- `for _ in range(20):` — ★ PRIMA VOLTA il NOME USA-E-GETTA `_`: "la
  variabile non mi interessa" — ripeti 20 volte (i 20 colpi del
  piccone).
- Ogni colpo tira TRE dadi: la colonna (`self.rng.randrange(self.width)`
  — ★ PRIMA VOLTA `randrange`: numero a caso da 0 a n-1), la riga, la
  direzione (choice tra le 4 monete).
- Si calcola il vicino secondo la direzione (es. N: il vicino è sopra
  e la moneta speculare è S). Colpo al bordo (es. N ma si è in riga 0)
  → `continue`: colpo a vuoto, si passa al prossimo.
- Se la cella o il vicino sono mattoncini del 42 → `continue` (mai
  aprire le isole).
- Se il muro è GIÀ aperto → `continue`. Il controllo: `_has_wall`
  (riga 97): `(self.grid[y][x] & mask) != 0` — ★ PRIMA VOLTA `&`:
  l'AND BIT A BIT — "ho questa moneta nel sacchetto?" (teoria 1.2: il
  trucco delle monete).
- Altrimenti apre i due lati (_remove_wall) e fa il CONTROLLO 3x3:
  `_has_3x3_open` (riga 277): scorre TUTTE le finestre 3x3 possibili
  (doppi for fino a height-2 e width-2); `_window_3x3_open` (riga
  285): una finestra è "tutta aperta" se i suoi 12 muri INTERNI (6
  orizzontali + 6 verticali) sono tutti aperti. Se dopo il colpo è
  nata una piazzetta 3x3 → _add_wall (riga 105: rimette le monete): il
  colpo viene ANNULLATO. (Teoria 1.4: il 2x2 è legale, il 3x3 no — il
  subject vieta corridoi più larghi di 2 celle.)

### solve (righe 297-331): il fuoco (teoria 1.5) — tappa C del main

- `queue = deque()` — ★ PRIMA VOLTA `deque`: la CODA a due estremità
  (dal cassetto collections): la pila di fogli presa dal FONDO (FIFO)
  È il fuoco (teoria 1.5).
- queue.append(self.entry): il primo foglio è l'entrata. `came_from` —
  il registro "chi ha acceso chi"; l'entrata non è stata accesa da
  nessuno → None.
- Il while:
  - `x, y = queue.popleft()` — ★ PRIMA VOLTA `popleft`: prende il
    foglio dal FONDO (append mette in cima → il primo preso è il più
    VECCHIO: l'ordine giusto dei minuti, teoria 1.5).
  - Se è l'uscita → `break` (★ PRIMA VOLTA `break`: esce subito dal
    ciclo — il fuoco è arrivato).
  - I 4 controlli (N/E/S/W): se il muro è APERTO → `_add_neighbor`
    (riga 333): se il vicino non è MAI stato visto (non sta in
    came_from), lo "accende": segna chi l'ha acceso e lo mette in
    coda. Ogni cella si accende UNA volta sola → il primo minuto
    registrato è il MINIMO (teoria 1.5: non lo scopre, lo costruisce).
- Se l'uscita non è mai stata accesa (`if self.exit not in came_from:
  return []`) → lista vuota: nessun percorso (con un labirinto valido
  non succede, ma il codice è pronto).
- La RISALITA: si parte dall'uscita e si segue "chi ha acceso chi"
  fino a None (l'entrata), append a ogni passo; alla fine
  `path.reverse()` — ★ PRIMA VOLTA `reverse`: capovolge la lista →
  entrata → uscita. Return.

### Chi è cosa

| Nome | Predefinito o nostro |
|------|----------------------|
| random, collections | predefiniti (moduli) |
| deque, Random, range, randrange, choice | predefiniti (tipi/funzioni) |
| //, &, break, continue, while, for, if, return, raise, not | predefiniti (operatori/parole chiave) |
| pop, append, reverse, popleft | predefiniti (metodi di liste/deque) |
| ValueError | predefinita (eccezione) |
| N, E, S, W, FOUR, TWO | NOSTRE costanti |
| MazeGenerator | NOSTRA classe |
| self | NOSTRO (parametro speciale) |
| grid, forty_two, has_42, entry, exit, perfect, width, height, rng | NOSTRI campi dell'oggetto |
| visited, stack, neighbors, queue, came_from, path, x, y, nx, ny, mask... | NOSTRE variabili |

### Analogie col C

| Python | C |
|--------|---|
| range(n) | for (int i = 0; i < n; i++) |
| // | divisione tra int |
| & mask | operatore bit a bit & |
| choice / randrange | rand() % n |
| stack + pop | pila a mano (array + indice) |
| deque + popleft | coda a mano (testa e coda) |
| None | NULL |
| True/False | int 0/1 |
| tupla (x, y) | struct o coppia di variabili |
| self | la struct passata per puntatore |
| break/continue | break/continue |

### Risposte pronte per l'evaluation

- "Perché i mattoncini del 42 vengono marcati visitati PRIMA della
  talpa?" Così la talpa non scava mai dentro: restano isole chiuse.
- "Perché il muro si apre dai due lati?" Il subject esige la
  coerenza: le due celle devono essere d'accordo sullo stesso muro.
- "Come torna indietro la talpa?" pop dalla cima della corda
  (backtracking).
- "Quando finisce la generazione?" Quando la corda è vuota = tutte le
  celle scavate (NON all'uscita).
- "Perché la coda prende dal fondo (FIFO)?" È il fuoco: i minuti
  arrivano in ordine crescente e il primo che tocca l'uscita è il più
  corto.
- "Perché il percorso è sicuramente il più corto?" Ogni cella si
  accende una volta sola, al suo minuto minimo.
- "A cosa serve il controllo 3x3 del piccone?" Il subject vieta
  corridoi più larghi di 2 celle; se un colpo crea una piazzetta 3x3,
  si richiude.
- "Cosa succede se l'uscita non è raggiungibile?" solve restituisce la
  lista vuota.

---

## 3.4 output_writer.py — il file esadecimale

### Cos'è

La tappa D: scrive il file di output nel formato del subject (teoria
1.6). È il modulo più corto: una tabella, una conversione, una
scrittura.

### All'import (righe 15-18)

HEX_DIGITS = "0123456789ABCDEF": la tabella numero→cifra (teoria 1.2:
l'esadecimale vive SOLO nel file). path_to_nesw e write_output_file
vengono definite.

### write_output_file (chiamata dal main, riga 46)

- `with open(filename, "w", encoding="utf-8") as f:` — with/open del
  3.2, ma con "w" = WRITE: ★ PRIMA VOLTA la modalità "w": apre per
  SCRIVERE; se il file esiste già viene SVUOTATO e riscritto da zero
  (a differenza di "r").
- Il doppio for sulla griglia: per ogni cella `HEX_DIGITS[cell]` — ★
  PRIMA VOLTA l'INDICE su una stringa: la stringa è una sequenza di
  caratteri numerati da 0; HEX_DIGITS[12] = il carattere in posizione
  12 = 'C'. La cella (0-15) fa da indice: il numero diventa la cifra
  giusta. line accumula (line = line + ...), poi `f.write(line +
  "\n")` — ★ PRIMA VOLTA `write`: scrive nel file (il fprintf del C);
  il "\n" va aggiunto a mano perché le stringhe non ce l'hanno.
- `f.write("\n")` — la riga vuota che il formato richiede.
- Entry ed exit: `f.write(f"{entry[0]},{entry[1]}\n")` — ★ PRIMA VOLTA
  gli INDICI sulla coppia: entry[0] è il PRIMO elemento (la x),
  entry[1] il secondo (la y) — l'indice parte da 0 (il conteggio del
  capitolo sul 42).
- L'ultima riga: `path_to_nesw(path) + "\n"` — QUI viene chiamata la
  conversione (riga 18): per ogni PASSO si confronta la cella i con la
  i+1: x cresciuta di 1 → "E" (est), calata → "W", y calata → "N" (si
  sale), cresciuta → "S". `range(len(path) - 1)` — ★ PRIMA VOLTA il
  MOTIVO del -1: con 5 celle ci sono 4 PASSI (i passi sono le celle
  meno 1). Se due celle consecutive non fossero vicine (mai, con un
  percorso valido) → raise ValueError: la rete di sicurezza.
- Il with chiude il file da solo → si torna al main: tappa D completa.

### Chi è cosa

| Nome | Predefinito o nostro |
|------|----------------------|
| open, len, range | predefinite (funzioni built-in) |
| write | predefinito (metodo del manico del file) |
| with, for, if, elif, else, return, raise | predefiniti (parole chiave) |
| HEX_DIGITS | NOSTRA costante |
| path_to_nesw, write_output_file | NOSTRE funzioni |
| grid, entry, exit_, path, filename | NOSTRI (parametri) |
| f, line, row, cell, result, x1, y1, x2, y2, i | NOSTRE variabili |

### Analogie col C

| Python | C |
|--------|---|
| f.write(line + "\n") | fprintf(f, "%s\n", line) |
| HEX_DIGITS[cell] | tabella di char esadecimale |
| la stringa | array di char |
| entry[0], entry[1] | struct.x, struct.y |
| range(len(path) - 1) | i < n - 1 |
| with ("w") | fopen("w") + fclose |

### Risposte pronte per l'evaluation

- "Perché 'w' e non 'r'?" Per SCRIVERE; 'w' svuota e riscrive il file
  da zero.
- "Come fa 15 a diventare F?" 15 fa da INDICE sulla tabella
  "0123456789ABCDEF": il carattere in posizione 15 è 'F'.
- "Perché range(len(path) - 1)?" I passi sono le celle meno 1: per 5
  celle ci sono 4 spostamenti.
- "Il file quando viene chiuso?" Da solo, alla fine del with.
- "Come nasce la stringa NESW?" Cella per cella: se la x cresce → E,
  se cala → W, se la y cala → N, se cresce → S.

---

## 3.5 display.py — il terminale interattivo

### Cos'è

La tappa E (teoria 1.7): disegna il labirinto e gestisce il menu. Una
cella = 1 carattere e un muro = 1 carattere: un 20x15 è largo 41
caratteri.

### All'import (righe 20-39)

- `from mazegen import N, S, W, MazeGenerator` — il from...import del
  3.3: prende solo i pezzi che servono.
- Le COSTANTI dei COLORI: stringhe "\033[31m" ecc. — i CODICI ANSI
  (★ PRIMA VOLTA): ordini dati al terminale ("da qui scrivi in
  rosso"), non caratteri visibili; RESET spegne, CLEAR pulisce lo
  schermo. DOT = "·": il puntino del percorso.
- WALL_COLORS e WALL_BGS: le due palette ciclabili col tasto 3 (gli
  SFONDI riempiono i mattoncini del 42: il blocco uniforme). Il verde
  NON c'è: è riservato al percorso.

### run (chiamata dal main, riga 52)

- show_path = False (il percorso nasce nascosto) e color_index = 0
  (primo colore).
- `while True:` — ★ PRIMA VOLTA il GIRO INFINITO (in C: while (1)): il
  menu si ripete finché non si esce.
- A ogni giro: CLEAR (schermo pulito), il titolo, _print_maze (la
  chiamata al disegno), il menu (le righe con +---+ e le voci 1/2/3/q).
- `cmd = input("Choice > ").strip().lower()` — ★ PRIMA VOLTA `input`:
  si ferma e aspetta che l'utente SCRIVA, poi restituisce la stringa
  scritta (in C: scanf o getline). Poi strip (3.2) e ★ PRIMA VOLTA
  `lower`: minuscole (così "Q" vale "q"). I tre si ATTACCANO in
  catena: il risultato di uno diventa l'ingresso del prossimo.
- Le 4 decisioni:
  - "1" → rigenera: chiama di nuovo gen.generate con gli STESSI valori
    (gen ricorda perfect/entry/exit) e with_42=True: nasce un labirinto
    nuovo (il dado prosegue la sequenza: il risultato cambia). show_path
    rimesso a False.
  - "2" → `show_path = not show_path` — ★ PRIMA VOLTA `not`: il
    ROVESCIO (in C: !): accendi/spegni il percorso.
  - "3" → `color_index = (color_index + 1) % len(WALL_COLORS)` — ★
    PRIMA VOLTA `%`: il RESTO della divisione: 0, 1, 2, 3, 0, 1, 2,
    3... la GIOSTRA dei colori che gira in tondo (con 4 colori il
    resto torna sempre a 0; in C: %). len conta i colori della lista.
  - "q" → break → il while finisce → run finisce → si torna al main →
    il programma termina. (Il break visto nel solve del 3.3.)

### _print_maze (righe 75-148): il disegno (teoria 1.7)

- Se show_path è True → path = gen.solve() (il fuoco del 3.3, chiamato
  di nuovo solo per disegnare).
- path_n e path_w: le liste dei punti dove il percorso ATTRAVERSA un
  muro N o W: per ogni passo si guarda la direzione: verso l'alto → il
  puntino andrà sul muro nord della cella di PARTENZA; verso il basso
  → sul muro nord della cella di ARRIVO (è lo stesso muro!); verso
  destra → sul muro ovest dell'arrivo; verso sinistra → sul muro ovest
  della partenza. Servono perché il puntino si disegna SUL muro
  attraversato.
- Il triplo for: per ogni riga y: prima la RIGA DEI MURI (wall): per
  ogni x il giunto (_junction) + il muro N: chiuso → "─"; aperto ma
  attraversato dal percorso → puntino verde; altrimenti spazio. Poi la
  RIGA DELLE CELLE (line): per ogni x il muro W (│ / puntino / spazio)
  + il CONTENUTO: mattoncino del 42 → sfondo colorato (il blocco
  uniforme); entrata → "I"; uscita → "O"; cella del percorso →
  puntino verde; altrimenti spazio. In fondo la RIGA DI FONDO coi muri
  S.
- I colori: wall_color si "accende" prima di ogni riga e RESET alla
  fine: i codici ANSI vanno spenti o colorerebbero tutto ciò che segue.

### _junction (righe 151-203): l'incrocio

Guarda i 4 LATI del nodo (sinistra, destra, sopra, sotto) e sceglie il
glifo giusto (┼ con 4 muri, ┬ quando manca il basso, ─ per il solo
orizzontale...). Ai BORDI (x == width o y == height) il bordo esterno
conta come muro. La cascata di if: si controlla dal caso più pieno al
più vuoto e il PRIMO che combacia vince (l'ordine conta!). Se nessun
lato ha un muro → spazio.

### Chi è cosa

| Nome | Predefinito o nostro |
|------|----------------------|
| input, print, len | predefinite (funzioni built-in) |
| while, if, elif, else, break, not, in | predefiniti (parole chiave/operatori) |
| %, ==, + | predefiniti (operatori) |
| strip, lower | predefiniti (metodi delle stringhe) |
| N, S, W | NOSTRE costanti (dal 3.3) |
| MazeGenerator | NOSTRA classe |
| RED, GREEN, BLUE, MAGENTA, CYAN, NORMAL, DOT, NO_BG, RESET, CLEAR | NOSTRE costanti (codici ANSI) |
| WALL_COLORS, WALL_BGS | NOSTRE liste |
| run, _print_maze, _junction | NOSTRE funzioni |
| show_path, color_index, cmd, path, path_n, path_w, wall, line, bottom | NOSTRE variabili |

### Analogie col C

| Python | C |
|--------|---|
| while True | while (1) |
| input(...) | scanf / getline |
| not | ! |
| % | l'operatore resto del C |
| break | break |
| codici ANSI | printf("\033[31m") |
| stringa come sequenza | array di char |

### Risposte pronte per l'evaluation

- "Come si rigenera un labirinto?" Il menu 1 richiama generate con gli
  stessi parametri; il dado prosegue la sequenza → labirinto diverso
  (il seed NON cambia).
- "Come funzionano i colori?" Codici ANSI inviati al terminale; il
  menu 3 cicla la palette con il resto %.
- "Perché path_n e path_w?" Il puntino del percorso deve stare SUL
  muro attraversato.
- "Cosa fa _junction?" Sceglie il glifo dell'incrocio guardando i 4
  lati.
- "Come si esce?" q → break → si torna al main e il programma finisce.
- "Il verde perché non è tra i colori dei muri?" È riservato al
  percorso.

---

# 4. Glossario

- **nibble:** 4 bit = mezza byte = una cifra esadecimale
- **BFS:** visita in ampiezza, trova il percorso più corto
- **DFS:** visita in profondità, alla base del recursive backtracker
- **albero ricoprente:** grafo connesso senza cicli che tocca tutte le celle
- **Config:** oggetto che contiene i parametri validati del labirinto
- **grid:** la griglia del labirinto, grid[y][x] = numero 0-15 della cella
- **seed:** punto di partenza della sequenza casuale (riproducibilità)
- **open():** funzione predefinita: apre un file e restituisce il manico (niente contenuto in memoria)
- **with:** parola chiave: il file si chiude da solo a fine blocco, anche con errori
- **manico (file object):** il "biglietto" con cui si parla col file aperto
- **strip():** metodo delle stringhe: toglie spazi e fine-riga dalle estremità
- **startswith():** metodo delle stringhe: "inizio con questa parte?"
- **split():** taglia la stringa al segno indicato e restituisce i pezzi
- **join():** incolla i pezzi di una lista con un separatore in mezzo
- **append():** aggiunge un elemento in coda alla lista
- **pop():** toglie l'ultimo elemento (la cima della pila)
- **int():** funzione predefinita che converte la parola in numero (la atoi del C)
- **raise:** parola chiave: "alza" un errore e lo consegna alla rete più vicina
- **tupla:** il pacchetto di valori tra parentesi tonde, es. (x, y)
- **None:** il "nessun valore" (il NULL del C)
- **True/False:** i valori di verità (in C: int 0/1)
- **self:** il pronome "io" dell'oggetto: ogni metodo lo riceve come primo parametro
- **range(n):** la sequenza 0, 1, 2... fino a n-1 (il for del C)
- **// (divisione intera):** il quoziente senza resto, come la divisione tra int in C
- **% (modulo):** il resto della divisione (fa girare in tondo una lista)
- **& (AND bit a bit):** controlla se una moneta (bit) è presente nel numero
- **deque:** coda a due estremità (append in cima, popleft dal fondo = FIFO)
- **FIFO/LIFO:** primo entrato primo uscito (il fuoco) / ultimo entrato primo uscito (la corda della talpa)
- **break/continue:** escono dal ciclo / saltano al giro successivo
- **codici ANSI:** ordini invisibili al terminale (colori, pulizia dello schermo)
- **input():** funzione predefinita: aspetta la scrittura dell'utente e la restituisce
- **with_42:** la RICHIESTA di disegnare il 42 (parametro di generate, default True)
- **has_42:** il RISULTATO ("il 42 c'è davvero?") — campo dell'oggetto letto dal main per il messaggio di omissione
