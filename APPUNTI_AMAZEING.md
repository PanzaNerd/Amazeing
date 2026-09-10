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
gestirli tutti. Il "42" invece richiede spazio (almeno 9 colonne x 5
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
(F = tutti i muri) piazzate al CENTRO della griglia. Prima che la talpa
parta vengono marcate come "già visitate": per la talpa sono cemento
armato → non ci scava mai dentro → i mattoncini restano isole chiuse, e
anche il risolutore (1.5) non ci passa mai. Le celle VUOTE delle cifre
invece sono celle normali: la generazione ci scava dentro e il percorso
può passarci — il 42 resta leggibile perché i mattoncini sono blocchi
pieni. Nel display i mattoncini sono quadratini pieni del colore dei
muri: il 42 appare come un blocco compatto e le cifre si leggono bene.
Se il labirinto è troppo piccolo il 42 si omette: il main stampa un
messaggio e il programma CONTINUA.

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

# 3. Glossario

- **nibble:** 4 bit = mezza byte = una cifra esadecimale
- **BFS:** visita in ampiezza, trova il percorso più corto
- **DFS:** visita in profondità, alla base del recursive backtracker
- **albero ricoprente:** grafo connesso senza cicli che tocca tutte le celle
- **Config:** oggetto che contiene i parametri validati del labirinto
- **grid:** la griglia del labirinto, grid[y][x] = numero 0-15 della cella
- **seed:** punto di partenza della sequenza casuale (riproducibilità)
