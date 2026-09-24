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
   - 1.5 Il percorso più breve (BFS: il fuoco)
   - 1.6 L'OUTPUT: il file esadecimale
   - 1.7 Il display interattivo
   - 1.8 Il main e la gestione errori
2. I moduli
3. Studio del codice (in ordine di esecuzione)
   - L'ordine di studio (perché questo)
   - 3.1 a_maze_ing.py — il direttore d'orchestra
   - 3.2 config_parser.py — dalla chiamata del main alla nascita del Config
   - 3.3 mazegen.py — il cuore: talpa, piccone, 42 e fuoco
     · approfondimenti: with_42/has_42 · (x,y) vs [y][x] · corda,
       neighbors, self · rng.choice · self.rng · piazzetta 3x3 ·
       _unvisited_neighbors · fine della generazione · queue e
       came_from · traccia completa · scudo prima della risalita
   - 3.4 output_writer.py — il file esadecimale
   - 3.5 display.py — il terminale interattivo
     · approfondimenti: l'import senza E · color_index · print(CLEAR) ·
       codici ANSI dei colori · path_n e path_w · vista d'insieme ·
       riempimento e consumo · costruzione riga per riga
4. Preparazione alla difesa (la scala di valutazione)
   - Il set di consegna
   - I test e pytest (come spiegarli)
   - 4.1 Display e menu · 4.2 Config: formato ed errori · 4.3 File di
     output · 4.4 Il generatore · 4.5 Modulo riusabile · 4.6 Le
     trappole della difesa
5. Glossario

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

Tutto parte dalla cartella del progetto (niente da attivare: il
Makefile usa il venv da solo):

```bash
cd "~/Desktop/python repo/Common_Core_2/python/AMAZEING"
make env       # 1) crea la cucina (venv) — una volta sola per macchina
make install   # 2) il corriere porta i 4 strumenti — una volta sola
```

**Eseguire il programma** (genera `maze.txt` e apre il display interattivo):

```bash
make run
# oppure direttamente:
python3 a_maze_ing.py config.txt
```

Nel display: `1` = rigenera, `2` = mostra/nascondi percorso, `3` = cambia
colore muri, `q` = esci. Uscita con codice 0 = tutto ok, 1 = errore.

**Test automatici** (22 test):

```bash
make test                                                # tutta la suite
python3 -m pytest tests/test_config_parser.py -v         # solo il parser
python3 -m pytest tests/test_output_writer.py::test_path_to_nesw_simple -v   # un singolo test
```

Cosa è pytest e come si spiegano i test in difesa: vedi la
parte 4 ("I test e pytest").

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
   (la chiave diventa MAIUSCOLA: il subject ammette anche le
   minuscole, es. width=20; PERFECT accetta pure true/false
   minuscoli)
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

### Perché proprio 20 colpi?

- Il subject NON fissa il numero: chiede solo che con PERFECT=False
  il labirinto abbia scorciatoie e che i corridoi restino larghi al
  massimo 2 celle. Il 20 è una NOSTRA scelta.
- 20 sono i TENTATIVI, non le aperture: molti colpi vengono scartati
  (bordo, mattoncino del 42, muro già aperto, piazzetta 3x3). Numeri
  reali (seed 42): 5x5 → 5 aperture su 20; 9x6 → 1 sola (8 colpi
  finiti sui mattoncini del 42); 20x15 → 6; 40x30 → 10.
- Perché 20 è abbastanza: anche nel caso peggiore resta almeno UNA
  scorciatoia → il labirinto è davvero non perfetto. Con 1 solo
  tentativo, un rifiuto lascerebbe il labirinto ancora perfetto,
  violando PERFECT=False.
- Perché non di più: con 1000 colpi il labirinto resterebbe valido
  (il controllo 3x3 protegge la regola) ma si riempirebbe di cicli.
  20 è il punto di equilibrio: qualche scorciatoia su ogni misura,
  senza stravolgere il labirinto della talpa.

Risposta da evaluation: "Il subject non fissa un numero: chiede solo
che il labirinto non sia perfetto e che i corridoi restino max 2
celle. Noi facciamo 20 TENTATIVI: dopo gli scarti ne restano meno —
abbastanza da garantire sempre qualche ciclo, pochi da non riempire
il labirinto di scorciatoie."

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

Il fuoco parte dall'entrata e si propaga un PASSO alla volta, in
TUTTE le direzioni contemporaneamente. Su ogni cella che raggiunge
scrive A QUALE PASSO l'ha toccata. Il numero scritto sull'uscita è
la lunghezza della strada più corta.

Nel 4x4 di sempre (numeri generati dal programma vero; il punto = le
celle mai toccate, il fuoco si ferma quando l'uscita esce dalla fila
— il break del solve):

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

Il fuoco avanza UN passo alla volta, ovunque: al passo 0 brucia solo
l'entrata; al passo 1 tutte le celle a 1 passo di distanza; al passo
2 tutte quelle a 2 passi... Una cella prende fuoco un passo dopo la
PRIMA delle sue vicine che brucia: non può bruciare prima (prima non
brucia nessuna sua vicina), e appena una vicina brucia, lei brucia
al passo dopo. Quindi il numero scritto su ogni cella è SEMPRE il
minimo possibile: nessuna strada più corta poteva arrivarci prima.

La catena di "chi ha acceso chi", dall'uscita all'indietro:

```
(3,3) acceso da (3,2) <- da (3,1) <- da (2,1) <- da (2,0) <- da (1,0) <- da (0,0)
```

Ogni passaggio scende di UN passo esatto: 6, 5, 4, 3, 2, 1, 0. Il
percorso, capovolto: (0,0),(1,0),(2,0),(2,1),(3,1),(3,2),(3,3) — 6
passi. Se esistesse una strada da 5, il fuoco sarebbe arrivato
all'uscita al passo 5: impossibile, perché l'uscita ha due sole
vicine, (3,2) (passo 5) e (2,3) (che il fuoco non ha nemmeno fatto
in tempo a toccare).

### Come lo fa il programma

Prima cosa: per ricostruire la strada alla fine, il programma tiene
un QUADERNO: su ogni cella scrive CHI l'ha accesa. Finito il fuoco,
parte dall'uscita, risale il quaderno ("chi ha acceso chi") fino
all'entrata e capovolge la lista: è il percorso. Nel codice il
quaderno è un dizionario chiamato came_from: un dizionario è la
tabella chiave→valore già vista in 1.1, e qui la chiave è la cella,
il valore è chi l'ha accesa (l'entrata ha scritto "nessuno").

Seconda cosa: per far avanzare il fuoco passo per passo, il
programma tiene una LISTA D'ATTESA: ogni cella accesa che deve
ancora propagare il fuoco ai vicini aspetta lì in fila. Quando una
cella prende fuoco, si mette in CODA. Il programma serve sempre la
PRIMA della fila, cioè la più vecchia: così le celle propagano il
fuoco nell'ordine in cui sono state accese — prima tutte quelle a 1
passo, poi quelle a 2 passi, e via. Servire il primo arrivato si
chiama FIFO: primo arrivato, primo servito.

(La talpa usava una struttura simile al contrario: la corda, servita
dalla CIMA — LIFO, l'ultimo arrivato è il primo servito — ma solo
per tornare indietro quando era bloccata, non per trovare strade
corte.)

Attenzione: il fuoco non è una cosa separata dalla fila — servire
sempre il primo arrivato È il fuoco. I passi non si conoscono
all'inizio: li scrive il programma cella per cella, e la fila
servita dal davanti li fa uscire nell'ordine giusto (0, 1, 2...).
Senza quell'ordine i passi uscirebbero sbagliati e il percorso
ricostruito sarebbe più lungo del necessario. Due strutture, due
mestieri: la corda della talpa RICORDA la strada già fatta (per
tornare indietro); la fila della BFS PRODUCE i passi nell'ordine
giusto mentre calcola la strada corta.

### Nel codice

- la lista d'attesa = una deque di collections ("il primo della
  fila" = popleft(), "nuova cella in coda" = append())
- chi ha acceso chi = il dizionario came_from (l'entrata ha None)
- i 4 lati = i 4 controlli con _has_wall (le monete)
- la ricostruzione = il while che risale came_from e poi reverse

**Frase pronta per l'evaluation:** "La BFS è come un fuoco che parte
dall'entrata e avanza un passo alla volta in tutte le direzioni: ogni
cella prende fuoco al passo minimo possibile e annota chi l'ha
accesa. Quando il fuoco raggiunge l'uscita, risalgo la catena di chi
ha acceso chi fino all'entrata e la capovolgo: è il percorso più
corto, perché il fuoco raggiunge ogni cella nel minor numero di
passi possibile."

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
cella = 3 caratteri**, muri `───` orizzontali e `│` verticali con
**gli incroci giusti** (`┼`, `┬`, `┴`, `├`, `┤`, `┌`, `┐`, `└`, `┘`):
la struttura si legge come un labirinto vero, con le proporzioni
giuste. Un labirinto 20x15 è largo 61 caratteri. Lo sfondo NON viene
forzato: vale il tema del
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

### Perché le celle sono larghe 3 caratteri (e prima sembrava alto)

I caratteri del terminale non sono quadrati: uno è circa 2 volte più
ALTO che largo. Se ogni cella fosse 1 carattere largo e 1 alto (1x1),
il labirinto uscirebbe stirato in verticale: 20 colonne occuperebbero
meno spazio visivo di 15 righe. Per questo ogni cella è larga 3
caratteri e alta 1: il rettangolo 3x1 compensa l'altezza del
carattere e il labirinto appare con le proporzioni vere, come il
rendering d'esempio del subject. Il muro orizzontale è `───`, il
verticale resta `│` (è già verticale, non va allargato). La modifica
tocca SOLO _print_maze: le stringhe del disegno (1 carattere → 3), la
logica non cambia.

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

1. controlla gli argomenti da terminale (righe 18-20)
2. tappa A: parse del config, dentro un try (righe 23-31)
3. tappa B: crea il generatore e genera il labirinto (righe 34-36)
4. tappa C: trova il percorso (riga 39)
5. tappa D: scrive il file di output (righe 41-42)
6. se il 42 manca, avvisa con un messaggio (righe 45-46)
7. tappa E: apre il display (riga 49)
8. in fondo: il "pulsante di avvio" (righe 53-63)

### Esecuzione riga per riga

**Righe 2-5: la docstring.** Il file comincia direttamente con la
docstring (il primo `"""..."""` dentro un file o una funzione non è
un semplice commento: è la DOCUMENTAZIONE ufficiale di quel file o
funzione, si legge con help()). Qui dice a cosa serve il programma e
come si usa. (Niente header 42: rimosso alla pulizia di consegna.)

**Riga 7: `import sys`.** sys è un MODULO PREDEFINITO di Python: una
libreria già pronta dentro Python, come le librerie standard del C
(#include <stdlib.h>). Porta con sé due strumenti che servono qui:
sys.argv (gli argomenti da terminale) e sys.exit (spegnere il
programma con un codice d'uscita).

**Righe 9-12: gli import dei NOSTRI file.** config_parser, display,
mazegen, output_writer sono i NOSTRI moduli: gli altri file .py della
cartella del progetto. `import` = "aggancia quel file: da ora posso
usare le sue funzioni e classi". In C si fa con #include + compilazione
di più file .c; in Python basta scrivere il nome del file senza .py.

**Riga 15: `def main():`** NOSTRA funzione. Il nome main è una
convenzione (non è obbligatorio come in C). `-> None` è il type hint:
la funzione non restituisce niente (come void in C), serve a mypy e al
lettore.

**Righe 18-20: il controllo degli argomenti.**
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

**Righe 23-31: tappa A protetta dal try.**
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

**Righe 34-36: tappa B (in breve, studiata nel file 3).**
- `gen = mazegen.MazeGenerator(...)` — crea un oggetto della NOSTRA
  classe MazeGenerator: il "laboratorio" con larghezza, altezza e
  seed. `config.width` = il campo width della scatola Config (il
  punto è l'accesso ai campi, come struct.field in C).
- `gen.generate(perfect=..., entry=..., exit=...)` — genera il
  labirinto. I nomi con = sono gli ARGOMENTI CHIAVE: i valori si
  passano per nome e l'ordine non conta (in C non esistono). Al
  ritorno, gen.grid contiene la griglia.

**Riga 39: tappa C.** `path = gen.solve()` — il BFS (capitolo 1.5)
trova il percorso più corto e lo restituisce come lista di celle.

**Righe 41-42: tappa D.** `output_writer.write_output_file(...)` —
scrive il file di output (capitolo 1.6, file 4).

**Righe 45-46: il messaggio del 42.** Se `gen.has_42` è False (maze
troppo piccolo, sotto 9x6), il main stampa il messaggio richiesto dal
subject e il programma CONTINUA lo stesso.

**Riga 49: tappa E.** `display.run(gen)` — apre il display
interattivo (capitolo 1.7, file 5).

**Righe 53-63: il pulsante di avvio e l'ultima rete.**
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

Il modulo che il main chiama per PRIMO (tappa A, riga 24): legge
config.txt (righe KEY=VALUE), lo valida e restituisce l'oggetto Config
coi parametri del labirinto. Studio in ordine di CHIAMATE: entriamo
qui dalla riga 24 del main e ci restiamo finché parse_config non
ritorna al main col Config in mano.

### Prima della chiamata: cosa è successo all'import (righe 8-84)

Il file config_parser.py NON nasce alla riga 24 del main: nasce alla
riga 9, all'import. In quel momento Python ha eseguito il file
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

### Dentro parse_config (righe 85-99)

- La docstring è il contratto: "mi dai il percorso, ti restituisco
  Config; contenuto sbagliato → ConfigError; file illeggibile → OSError
  che PROPAGA al chiamante".
- Riga 99: values, la scatola vuota — chiavi stringhe (WIDTH,
  HEIGHT...) e valori stringhe (ancora grezzi: "20" come parola, non
  come numero). Ci finiscono le righe del config NON ancora
  interpretate.

### Riga 101: ★ PRIMA VOLTA — with e open

- **open(path, "r", encoding="utf-8")** — la fopen del C: chiede al
  sistema operativo di preparare il file per la lettura e restituisce
  il MANICO (file object): il biglietto con cui si parla col file. Il
  contenuto NON viene caricato in memoria. I tre ingredienti: path =
  quale file (la stringa passata dal main); "r" = modalità sola
  lettura; encoding="utf-8" = l'etichettatura dei caratteri (argomento
  chiave, passato per nome).
- **as f** — il nome del manico (in C: FILE *f = fopen(...)).
- **with** — la porta che si chiude da sola: alla fine del blocco
  indentato (righe 102-121) il file viene chiuso SEMPRE, anche se
  dentro scoppia un errore. Risolve il bug classico del C: dimenticarsi
  la fclose (o uscire prima per un errore) lascia il file aperto.
- Il filo col main: se il file non esiste, open fallisce QUI con
  OSError; parse_config non lo cattura ("propaga") e l'errore risale
  alla SECONDA rete del try nel main → messaggio + uscita 1.

### Righe 102-105: la lettura riga per riga

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

### Le decisioni del loop (righe 106-121): cosa fare di ogni riga

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
- `key = key.strip().upper()` e `value = value.strip()` — pulizia dei
  pezzi: via gli spazi attorno all'=, e la chiave diventa MAIUSCOLA
  (il subject ammette le minuscole: width=20). Il valore resta com'è:
  per esempio è un nome di file.
- `if key in values:` — `in` su un DIZIONARIO guarda le CHIAVI:
  "questa chiave c'è già?" → doppione → ConfigError (ogni chiave deve
  comparire una volta sola).
- `values[key] = value` — l'inserimento: la scatola si riempie della
  coppia chiave→valore, ancora come STRINGHE.

Quando le righe del file sono finite, il for si ferma da solo; finisce
il blocco del with e il file si chiude da solo (la porta automatica).

### La validazione (righe 123-156): dalle stringhe ai valori veri

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
  riga 45 — QUI viene chiamata la prima funzione di servizio.
  `values["WIDTH"]` è la parola "20"; dentro, `int(raw)` (★ PRIMA
  VOLTA `int`: la atoi del C: la parola diventa numero) dentro un
  try/except: se la parola non è un numero, int alza ValueError
  (eccezione predefinita) e la rete della funzione la trasforma in
  ConfigError col messaggio chiaro, che vola al main; se riesce,
  return consegna il numero e il pallino torna alle righe 132-133. height
  identico.
- `if width < 2 or height < 2:` — un labirinto deve essere almeno 2x2.
- `entry = _parse_coords(values["ENTRY"], "ENTRY")` — salta alla riga
  66: split(",") taglia "0,0" in due pezzi; se non sono ESATTAMENTE
  due → errore; altrimenti converte i pezzi (dopo strip) con _parse_int
  e li impacchetta: `return (x, y)` — ★ PRIMA VOLTA la COPPIA
  (tupla): il pacchetto di valori tra parentesi tonde (in C: una
  struct o due variabili separate; qui il pacchetto viaggia intero).
- `_check_bounds(entry, width, height, "ENTRY")` — salta alla riga 76:
  spacchetta la coppia (`x, y = point`) e controlla i quattro bordi;
  fuori → ConfigError. exit identico — con un dettaglio di nome: la
  variabile si chiama `exit_` col trattino IN FONDO perché exit è una
  funzione predefinita di Python e non vogliamo coprirla (convenzione).
- `if entry == exit_:` — entrata e uscita devono essere diverse.
- `perfect = _parse_bool(values["PERFECT"], "PERFECT")` — salta alla
  riga 53: accetta solo "True" e "False" ESATTI, altrimenti
  ConfigError. ★ PRIMA VOLTA i VALORI DI VERITÀ: True/False sono il
  bool (in C non esistevano: si usava int 0/1).
- `output_file = values["OUTPUT_FILE"]` — resta testo così com'è (è un
  nome di file); si controlla solo che non sia vuoto.
- SEED è FACOLTATIVA: `if "SEED" in values:` — se nel config non c'è,
  seed resta None. ★ PRIMA VOLTA `None`: il "nessun valore" (il NULL
  del C): significherà "usa un seme casuale vero". Se c'è → _parse_int.

### La nascita del Config e il ritorno al main (riga 157)

`return Config(width, height, entry, exit_, output_file, perfect,
seed)` — QUI viene chiamata la classe Config: il pallino salta al suo
__init__ (riga 33), la FABBRICA della scatola: ogni campo
`self.width = width` ecc. ★ PRIMA VOLTA `self`: il pronome "io"
dell'oggetto — ogni oggetto tiene i propri valori nei propri campi,
come i campi di una struct in C, ma qui la struct si passa DA SOLA:
self arriva come primo parametro di ogni metodo, senza scriverlo nella
chiamata. Poi return consegna la scatola finita al chiamante → il
pallino torna al MAIN, riga 24: `config =` la riceve. TAPPA A
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

- "Quando viene eseguito config_parser.py?" All'import (riga 9 del
  main): Python prepara le definizioni; parse_config viene CHIAMATO
  alla riga 24 e solo lì parte il suo corpo.
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

### All'import (righe 19-53): la preparazione

- `import random` — il cassetto dei DADI (teoria 1.3).
  `from collections import deque` — ★ PRIMA VOLTA `from ... import`:
  prende UN pezzo solo dal cassetto (qui la coda, spiegata in solve).
- Le 4 monete N/E/S/W = 1/2/4/8 (teoria 1.2).
- FOUR e TWO: i disegni delle cifre come LISTE DI COPPIE (x, y),
  ciascuna relativa all'angolo del disegno (il commento con # e . nel
  file mostra la forma delle cifre). Sono costanti: non cambiano mai.
- La definizione della classe (righe 54-69): la docstring coi campi. I
  METODI (le funzioni dell'oggetto) si spiegano quando vengono
  chiamati.

### __init__ (righe 70-81): la nascita dell'oggetto — tappa B, prima chiamata

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

### generate (righe 100-144): il direttore della generazione

- Salva i parametri: perfect, entry; per exit: `if exit is None:` (★
  PRIMA VOLTA `is None`: il controllo "è davvero nessun valore?" — non
  si confronta con ==) usa l'angolo in basso a destra.
- La validazione: _in_bounds (riga 82: dentro i bordi?) — se fuori, o
  se entry == exit → `raise ValueError` (eccezione predefinita: "chi
  ha chiamato ha sbagliato"; è la rete di sicurezza per chi importa il
  modulo).
- La griglia: DOPPIO FOR annidato (righe 130-135): ★ PRIMA VOLTA
  `range`: la sequenza 0, 1, 2... fino a n-1 (il for (int i = 0; i <
  n; i++) del C). Per ogni riga si crea una lista e per ogni cella si
  mette N+E+S+W = 1+2+4+8 = 15: TUTTE le scatole chiuse (il punto di
  partenza della teoria 1.4).
- I tre passi nell'ordine: _carve_42, _carve_maze, poi
  _carve_extra_walls SOLO se not perfect (i cicli del piccone).

### _carve_42 (righe 145-181): il disegno "42" (teoria 1.4, già a fondo)

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

### _carve_maze (righe 182-222): la talpa (teoria 1.4, le 3 regole)

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
  - `_unvisited_neighbors` (riga 223): i 4 controlli (sopra, destra,
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
    disponibili, teoria 1.4). Poi _remove_wall (riga 92: toglie la
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

### Approfondimento: il dado e il pacchetto da 4 (rng.choice)

La riga: nx, ny, mask_here, mask_there = self.rng.choice(neighbors).

Come si legge ad alta voce: "il dado della talpa pesca un pacchetto a
caso dalla lista delle porte aperte; il pacchetto si apre e i suoi 4
pezzi finiscono in nx, ny, mask_here e mask_there".

Tre cose in una:

| Pezzo della riga | Cosa fa |
|---|---|
| self.rng | il DADO della talpa: la macchinetta col seme (il librone 1.3) |
| .choice(neighbors) | pesca UN pacchetto a caso dalla lista |
| nx, ny, mask_here, mask_there = | il pacchetto si apre: 4 pezzi in 4 variabili (lo spacchettamento del 3.2, ma con 4) |

- Il dado pesca un PACCHETTO e non una direzione: ogni elemento della
  lista contiene gia' tutto cio' che serve — dove andare (nx, ny) e le
  due monete speculari del muro (la mia e la sua). Scelta e
  conseguenze viaggiano insieme.
- Le due righe dopo usano esattamente i 4 pezzi: _remove_wall dal mio
  lato con mask_here e dal lato del vicino con mask_there (stesso
  muro, due lati, monete speculari).
- Lo scudo: choice([]) sarebbe un crash, ma il dado vive solo nel ramo
  else, raggiunto esclusivamente con lista NON vuota (il controllo
  len(neighbors) == 0 fa il pop prima).
- Le facce del dado = il numero di pacchetti in lista: con 3 porte
  aperte 3 facce, con 1 porta 1 faccia (nessuna scelta vera, ma
  funziona). Stesso seme -> stesso pescaggio (la riproducibilita' del
  1.3 in azione).
- In C: int i = rand() % n; poi i campi dall'array di struct. choice
  fa entrambe le cose in una.

Risposta da evaluation: "choice pesca a caso uno dei pacchetti da 4
(destinazione + le due monete speculari) e lo spacchetta nelle quattro
variabili; il dado non vede mai la lista vuota perche' il ramo del pop
la intercetta prima."

### Approfondimento: self.rng — il dado PERSONALE (un oggetto, non una funzione)

- self.rng NON è una funzione importata: è un CAMPO dell'oggetto, come
  self.width. Dentro c'è un OGGETTO: la macchinetta dei dadi. Nasce in
  __init__: self.rng = random.Random(seed). Tre nomi diversi: random
  (minuscolo) = il MODULO importato (il cassetto dei dadi); Random
  (maiuscolo) = la CLASSE delle macchinette; Random(seed) = la
  FABBRICA che crea una macchinetta che parte dalla pagina del seme
  (il librone 1.3).
- Lettura ad alta voce di self.rng.randrange(self.width): "il MIO
  dado: dammi un numero a caso da 0 a larghezza-meno-1".

| Pezzo | Cos'è |
|---|---|
| self | l'oggetto (la talpa/piccone) |
| .rng | il MIO dado: campo creato in __init__ |
| .randrange(self.width) | il comando al dado: numero da 0 a width-1 |

- randrange(n) tira un numero da 0 a n-1 (lo stesso conto di range):
  con width=20 esce 0..19, ESATTAMENTE gli indici validi delle
  colonne. choice([N, E, S, W]) pesca una delle 4 monete.
- Perché un dado PERSONALE e non le funzioni globali di random: il
  dado globale (random.randrange, senza oggetto) ignora il nostro
  seed e ha uno stato condiviso da tutto il programma. Il dado
  personale invece garantisce la riproducibilita' (stesso seed ->
  stessa sequenza) e i generatori non si disturbano a vicenda. In C:
  srand(seed) è globale, un dado solo per tutto il programma; qui
  ogni oggetto porta il proprio.
- Lo STESSO dado fa tutta la generazione: la talpa (choice sui
  vicini) e il piccone (randrange e choice) leggono la stessa
  sequenza, un lancio dopo l'altro: per questo l'intero labirinto è
  riproducibile, non solo un pezzo.

Risposta da evaluation: "rng è un campo dell'oggetto: una macchinetta
Random creata in __init__ col seme. randrange e choice sono i SUOI
metodi. Ogni generatore ha il suo dado personale: stesso seme, stesso
labirinto — mentre in C srand è globale."

### Approfondimento: la piazzetta 3x3 — _has_3x3_open e _window_3x3_open

- Lettura ad alta voce: _window_3x3_open(x, y) = "la finestra 3x3 il
  cui angolo in alto a sinistra è (x, y) è tutta aperta?";
  _has_3x3_open = "esiste ALMENO UNA finestra tutta aperta, da
  qualsiasi parte?".
- La finestra ha 9 celle; contano solo i 12 muri INTERNI: 6
  orizzontali (i muri SUD delle celle delle prime DUE righe: tra riga
  1-2 e 2-3) + 6 verticali (i muri EST delle celle delle prime DUE
  colonne: tra colonna 1-2 e 2-3). Il perimetro della finestra non si
  guarda mai: la piazzetta si giudica da dentro.
- Il giro: primo loop per le righe y..y+1 e le colonne x..x+2 ->
  muro SUD; secondo loop per le righe y..y+2 e le colonne x..x+1 ->
  muro EST. Al PRIMO muro chiuso -> return False subito (basta un
  muro per non essere una piazzetta: i controlli dopo non si fanno).
  Tutti e 12 aperti -> return True.
- Le finestre possibili: l'angolo (x, y) può stare da 0 a width-3 e
  height-3, cioè i for vanno fino a width-2 e height-2 (range conta
  fino a n-1). Un 5x5 ha 9 finestre (angoli 0,1,2 x 0,1,2); un 20x15
  ne ha 18 x 13 = 234. _has_3x3_open si ferma alla PRIMA aperta
  (return True) e solo alla fine risponde False.
- Dove serve: il piccone la chiama DOPO ogni colpo; se il colpo ha
  creato una piazzetta si richiudono i due lati (colpo annullato). Sul
  labirinto vero (20x15, PERFECT=False) risponde False: la garanzia
  "corridoi max 2 celle" è mantenuta.
- In C: due for annidati identici su un array di bool.

### Il codice giro per giro (i for e il range)

- range(a, b) produce a, a+1, ..., b-1: il secondo numero è ESCLUSO.
  Per questo range(y, y+2) dà ESATTAMENTE 2 valori (y, y+1) e
  range(x, x+3) dà ESATTAMENTE 3 (x, x+1, x+2): il +2 e il +3 sono il
  CONTO dei giri, non l'ultimo valore. range(height-2) = 0 fino a
  height-3: l'ultimo angolo valido, perché l'ultima cella della
  finestra (y+2) deve stare dentro la griglia.
- I due for ANNIDATI girano come il contachilometri: il for interno
  completa TUTTI i suoi giri, poi l'esterno avanza di uno e l'interno
  ricomincia da capo. In C: for (int wy = y; wy < y+2; wy++) {
  for (int wx = x; wx < x+3; wx++) ... }.
- Traccia di _window_3x3_open(1, 1). Primo doppio for (muri SUD), 6
  giri nell'ordine: (1,1), (2,1), (3,1) con wy=1, poi (1,2), (2,2),
  (3,2) con wy=2. Secondo doppio for (muri EST), 6 giri: (1,1), (2,1)
  con wy=1; (1,2), (2,2) con wy=2; (1,3), (2,3) con wy=3 — solo 2
  colonne per giro, perché range(x, x+2).
- Il return DENTRO il for esce da TUTTA la funzione (i for si fermano
  subito). Il return DOPO i for (il return False di _has_3x3_open) si
  raggiunge SOLO se nessuna finestra era aperta.
- Traccia di _has_3x3_open su un 5x5 (9 finestre, ordine di
  scansione): (0,0) no → (1,0) no → (2,0) no → (0,1) no → (1,1)
  APERTA → return True: le 4 finestre rimaste non vengono provate.

Risposta da evaluation: "_window_3x3_open controlla i 12 muri interni
(6 orizzontali + 6 verticali) e basta un muro chiuso per rispondere
False. _has_3x3_open scorre tutte le finestre possibili e si ferma
alla prima aperta. Il piccone lo usa per annullare i colpi che
creerebbero corridoi larghi 3."

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
- Gli if sono DOMANDE, non porte da attraversare: la talpa sta FERMA
  nella sua stanza, prova le 4 porte in fila e si segna solo quelle
  aperte. Il pallino esegue SEMPRE tutti e quattro gli if; quando la
  condizione è falsa salta SOLO il corpo (la riga dell'append), mai la
  funzione. L'attraversamento vero della porta succede DOPO, nel while
  di _carve_maze, quando il dado sceglie un pacchetto dalla lista.

  Traccia di (2,0) in un 5x4 (niente visitato):

| Riga del codice | Domanda | Risposta | Cosa succede |
|---|---|---|---|
| neighbors = [] | — | — | la lista nasce vuota |
| if NORD | esiste la cella sopra? | NO (y=0) | append saltato, riga dopo |
| if EST | esiste a destra? e non visitata? | SI | append (3,0): lista = 1 |
| if SUD | esiste sotto? e non visitata? | SI | append (2,1): lista = 2 |
| if OVEST | esiste a sinistra? e non visitata? | SI | append (1,0): lista = 3 |
| return | — | — | consegna 3 pacchetti |
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
- La mappa delle direzioni disponibili (con nulla visitato): ANGOLI =
  2, BORDI = 3, INTERNO = 4. Esempio reale 5x4 generato dal codice:

```
   0 1 2 3 4
0:  2 3 3 3 2
1:  3 4 4 4 3
2:  3 4 4 4 3
3:  2 3 3 3 2
```

- Le coordinate valide sono x da 0 a width-1 e y da 0 a height-1:
  (width, 0) e (0, height) NON esistono. E la talpa non riceve mai
  celle invalide: la prima è l'entry (già controllata da generate con
  _in_bounds), tutte le altre sono vicini prodotti dalla funzione
  stessa, che per costruzione sono sempre dentro i bordi. Il cerchio
  si chiude: i controlli sul bordo garantiscono che la funzione
  produca solo celle valide, quindi ne riceve solo di valide.
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

### _carve_extra_walls (righe 248-294): il piccone (teoria 1.4 PERFECT=False)

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
  (riga 88): `(self.grid[y][x] & mask) != 0` — ★ PRIMA VOLTA `&`:
  l'AND BIT A BIT — "ho questa moneta nel sacchetto?" (teoria 1.2: il
  trucco delle monete).
- Altrimenti apre i due lati (_remove_wall) e fa il CONTROLLO 3x3:
  `_has_3x3_open` (riga 295): scorre TUTTE le finestre 3x3 possibili
  (doppi for fino a height-2 e width-2); `_window_3x3_open` (riga
  306): una finestra è "tutta aperta" se i suoi 12 muri INTERNI (6
  orizzontali + 6 verticali) sono tutti aperti. Se dopo il colpo è
  nata una piazzetta 3x3 → _add_wall (riga 96: rimette le monete): il
  colpo viene ANNULLATO. (Teoria 1.4: il 2x2 è legale, il 3x3 no — il
  subject vieta corridoi più larghi di 2 celle.)

### Approfondimento: le due strutture del fuoco — queue e came_from

**Le DEFINIZIONI (sono le uniche due cose che servono):**

- **queue** = la LISTA D'ATTESA delle celle che devono ancora
  prendere fuoco, nell'ordine in cui sono state accese. Nel codice è
  una deque del modulo collections: append = mettersi in coda,
  popleft = servire il primo della fila (FIFO: il perché è nella
  teoria 1.5).
- **came_from** = il REGISTRO che risponde alla domanda "chi ha
  acceso questa cella?". È un dizionario da cella a cella; l'entrata
  ha None perché non l'ha accesa nessuno. Serve SOLO alla fine: per
  risalire il percorso dall'uscita fino all'entrata.

**Lettura ad alta voce delle 4 righe:** queue = deque() → "la lista
d'attesa nasce vuota"; queue.append(self.entry) → "il primo in
attesa è l'entrata"; came_from = {} → "il
registro nasce vuoto"; came_from[self.entry] = None → "l'entrata non
è stata accesa da nessuno".

**La meccanica FIFO in breve** (la fila del panettiere): append =
mettersi in coda, popleft = servire il davanti. anna, bruno, carla
arrivano in fila: si serve anna, poi bruno, poi carla; dario,
arrivato dopo, aspetta. Chi arriva prima esce prima — e per il fuoco
questo significa: le celle escono in ordine di distanza dall'entrata
(chi è stato acceso prima sta più vicino). La corda della talpa usava
l'estremità opposta (LIFO): lì serviva tornare indietro, qui servire
in ordine di arrivo.

**Chi è cosa:** collections = MODULO predefinito (libreria
standard); deque = CLASSE predefinita dentro collections (from
collections import deque); deque() = la FABBRICA che crea la fila
vuota; queue = NOSTRA variabile. Deque = double-ended queue (coda a
due estremità). In C: fila a mano con array circolare o due indici
testa/coda; il None del registro = parent[entry] = -1 (NULL).

**Il None è il capolinea:** seguendo "chi ha acceso chi" dall'uscita,
la catena finisce esattamente qui (cell diventa None e il while della
risalita si ferma).

Risposta da evaluation: "queue è una deque del modulo collections:
una fila FIFO che contiene l'entrata come prima arrivata. came_from è
il registro di chi ha acceso chi, e l'entrata ha None: punto di
partenza della catena e capolinea della risalita."

### Approfondimento: la traccia completa — da queue e came_from vuoti al path

Il labirinto dell'esempio (generato dal codice: I = entrata, O =
uscita; ogni cella è larga 3 caratteri):

```
+---+---+---+
| I         |
+   +---+   +
|   |   |   |
+   +---+   +
|   |   | O |
+---+---+---+
```

Leggi il disegno: da I si va a DESTRA lungo la riga di sopra (tutto
aperto), poi GIU' nella colonna di destra fino a O. Da I si scende
anche a SINISTRA: giù e giù, poi muro = vicolo cieco.

Ramo basso (0,0)-(1,0)-(2,0)-(2,1)-(2,2) = l'uscita; ramo sinistro
(0,0)-(0,1)-(0,2) = vicolo cieco.

La regola dei giri: ESCE = popleft (serve il primo della fila);
ENTRANO = le celle nuove accese, in coda alla fila (append).

- STADIO 0 (le 4 righe): queue = [(0,0)]; came_from = {(0,0): None}.
- GIRO 1: ESCE (0,0). ENTRANO (1,0) e (0,1), accese da
  (0,0): il bivio. queue = [(1,0), (0,1)]; came_from = {(0,0): None,
  (1,0): (0,0), (0,1): (0,0)}.
- GIRO 2: ESCE (1,0). ENTRA (2,0), accesa da (1,0). queue
  = [(0,1), (2,0)]; came_from = {(0,0): None, (1,0): (0,0), (0,1):
  (0,0), (2,0): (1,0)}.
- GIRO 3: ESCE (0,1). ENTRA (0,2), accesa da (0,1). queue
  = [(2,0), (0,2)]; came_from = {(0,0): None, (1,0): (0,0), (0,1):
  (0,0), (2,0): (1,0), (0,2): (0,1)}.
- GIRO 4: ESCE (2,0). ENTRA (2,1), accesa da (2,0). queue
  = [(0,2), (2,1)]; came_from = {(0,0): None, (1,0): (0,0), (0,1):
  (0,0), (2,0): (1,0), (0,2): (0,1), (2,1): (2,0)}.
- GIRO 5: ESCE (0,2). NIENTE in entrata: vicolo cieco.
  queue = [(2,1)]; came_from invariato.
- GIRO 6: ESCE (2,1). ENTRA (2,2), accesa da (2,1):
  l'uscita. queue = [(2,2)]; came_from = {(0,0): None, (1,0): (0,0),
  (0,1): (0,0), (2,0): (1,0), (0,2): (0,1), (2,1): (2,0), (2,2):
  (2,1)}.
- GIRO 7: ESCE (2,2) = l'uscita → break, il while finisce.
- LA RISALITA: path = [] → [(2,2)] → [(2,2),(2,1)] →
  [(2,2),(2,1),(2,0)] → [(2,2),(2,1),(2,0),(1,0)] →
  [(2,2),(2,1),(2,0),(1,0),(0,0)] → cell = None, il while si ferma.
  reverse → [(0,0),(1,0),(2,0),(2,1),(2,2)]: è il RETURN di solve.
- Nota chiave: (0,1) e (0,2) stanno nel registro ma NON nel percorso:
  la risalita segue la catena SOLO dall'uscita, e il ramo morto non
  porta all'uscita. Ogni cella già nel registro viene rifiutata:
  per questo ogni cella brucia una volta sola.

Risposta da evaluation: "queue si riempie con i vicini appena accesi
e si serve dal davanti (in ordine di distanza dall'entrata);
came_from registra chi
ha acceso chi e le celle già accese non rientrano. Il path si
costruisce risalendo il registro dall'uscita fino al None
dell'entrata, poi si capovolge."

### Approfondimento: lo scudo prima della risalita (exit not in came_from)

- Lettura ad alta voce: "se l'uscita non è mai stata accesa — non
  sta nel registro — restituisci la lista vuota: nessun percorso".
- Il while finisce in DUE modi soli: 1) break perché l'uscita è
  uscita dalla fila (allora STA nel registro); 2) la fila si svuota
  da sola = il fuoco ha bruciato tutto ciò che poteva senza mai
  toccare l'uscita. Con un labirinto valido il modo 2 non succede
  mai (la talpa collega tutto e l'uscita non è un mattoncino), ma
  solve non lo sa: è un modulo riusabile, chi lo importa potrebbe
  passare una griglia sconnessa o un'uscita in una tasca isolata.
- Cosa protegge DAVVERO: la RISALITA subito dopo usa l'uscita come
  CHIAVE del dizionario (cell = came_from[cell] a ogni passo). Se
  l'uscita non fosse una chiave: KeyError = crash. Il controllo
  garantisce: o l'uscita ha la sua catena (e si risale), o si esce
  prima con la lista vuota.
- È lo stesso schema degli altri scudi: il bordo prima di leggere la
  griglia, len(neighbors) prima del dado, qui la CHIAVE prima di
  usarla.
- Dopo il return [] non crasha niente: path_to_nesw([]) produce una
  stringa vuota e il file di output ha la riga del percorso vuota.

Risposta da evaluation: "Se l'uscita è irraggiungibile il fuoco non
la accende mai e la fila si svuota da sola: solve restituisce la
lista vuota invece di crashare nella risalita. Con i nostri
labirinti non succede mai, ma la funzione è difensiva: è il
controllo di sicurezza prima di usare l'uscita come chiave del
registro."

### solve (righe 320-367): il fuoco (teoria 1.5) — tappa C del main

- `queue = deque()` — ★ PRIMA VOLTA `deque`: la LISTA D'ATTESA delle
  celle che devono ancora prendere fuoco (append = in coda, popleft =
  primo della fila: FIFO — il perché è nella teoria 1.5).
- queue.append(self.entry): il primo in attesa è l'entrata.
  `came_from` — il REGISTRO che risponde "chi ha acceso questa
  cella?"; l'entrata non è stata accesa da nessuno → None.
- Il while:
  - `x, y = queue.popleft()` — ★ PRIMA VOLTA `popleft`: serve il
    PRIMO della fila (quello in attesa da più tempo): l'ordine di
    servizio È l'ordine di distanza dall'entrata (teoria 1.5).
  - Se è l'uscita → `break` (★ PRIMA VOLTA `break`: esce subito dal
    ciclo — il fuoco è arrivato).
  - I 4 controlli (N/E/S/W): se il muro è APERTO → `_add_neighbor`
    (riga 368): se il vicino non è MAI stato visto (non sta in
    came_from), lo "accende": segna chi l'ha acceso e lo mette in
    coda. Ogni cella si accende UNA volta sola → la prima
    registrazione è la distanza minima (teoria 1.5: non la scopre, la
    costruisce).
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
- "Perché la coda prende dal fondo (FIFO)?" È il fuoco: le celle
  escono in ordine di distanza dall'entrata, e la prima uscita
  dell'uscita dà il percorso più corto.
- "Perché il percorso è sicuramente il più corto?" Ogni cella si
  accende una volta sola, alla sua distanza minima dall'entrata.
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

### All'import (righe 5-8)

HEX_DIGITS = "0123456789ABCDEF": la tabella numero→cifra (teoria 1.2:
l'esadecimale vive SOLO nel file). path_to_nesw e write_output_file
vengono definite.

### write_output_file (chiamata dal main, riga 41)

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
  conversione (riga 8): per ogni PASSO si confronta la cella i con la
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
cella = 3 caratteri e un muro orizzontale = 3: un 20x15 è largo
61 caratteri.

### All'import (righe 9-28)

- `from mazegen import N, S, W, MazeGenerator` — il from...import del
  3.3: prende solo i pezzi che servono.
- Le COSTANTI dei COLORI: stringhe "\033[31m" ecc. — i CODICI ANSI
  (★ PRIMA VOLTA): ordini dati al terminale ("da qui scrivi in
  rosso"), non caratteri visibili; RESET spegne, CLEAR pulisce lo
  schermo. DOT = "·": il puntino del percorso.
- WALL_COLORS e WALL_BGS: le due palette ciclabili col tasto 3 (gli
  SFONDI riempiono i mattoncini del 42: il blocco uniforme). Il verde
  NON c'è: è riservato al percorso.

### Approfondimento: perché l'import non prende E (e il from...import spiegato)

- COME SI LEGGE: "dal modulo mazegen prendi i nomi N, S, W e
  MazeGenerator".
- DOMANDA: e la E? Non c'è perché il display non la usa MAI.
- Il disegno fa UNA cosa per ogni cella: disegna il muro SOPRA (N) e
  il muro a SINISTRA (W). Basta questo:
  - il muro EST della cella (x,y) è il muro OVEST della cella (x+1,y):
    lo disegna la vicina di destra quando tocca a lei;
  - il muro SUD della cella (x,y) è il muro NORD della cella (x,y+1):
    lo disegna la cella sotto.
- I 4 bordi esterni, e chi li disegna:
  - ALTO: N della riga 0, primo giro del loop dei muri. Il bordo
    esterno non si apre MAI (la talpa si ferma ai bordi): sempre "─".
  - SINISTRA: W della colonna 0: sempre "│".
  - BASSO: S dell'ultima riga, nel loop del fondo: l'UNICO punto del
    display dove si legge S.
  - DESTRA: una "│" FISSA attaccata a fine riga, senza guardare
    nessun bit. Giusto così: il bordo esterno è sempre chiuso, il
    segno non cambia mai.
- Se importassimo E senza usarla: flake8 F401 "imported but unused".
  Un import che non serve è un errore di igiene.
- from...import, i DUE modi di prendere da un modulo:
  1. import mazegen: entra TUTTO il modulo; i nomi si usano col punto
     (mazegen.N). In C: l'#include, ti porti il file intero.
  2. from mazegen import N: copia SOLO il nome N nel nostro file; da
     lì si scrive N da solo. In C: copiare a mano nel file la sola
     riga #define N 1.
- N, S, W sono VARIABILI normali (le monete 1, 4, 8 di 1.2, definite
  in cima a mazegen.py). Python non distingue: variabili, funzioni e
  classi si importano tutte con la stessa sintassi — nella stessa
  riga c'è anche MazeGenerator, che è una classe.
- Il nome importato è una COPIA: se dopo l'import mazegen.N cambiasse,
  il nostro N resterebbe il valore vecchio. Qui non importa: le monete
  non cambiano mai.
- Risposta da evaluation: "il display disegna solo i muri N e W di
  ogni cella; l'E di una cella è il W della vicina di destra e il S è
  il N di quella sotto; il bordo destro è una barra fissa perché
  esterno. Importare un nome che non si usa darebbe un errore di
  flake8."

### run (chiamata dal main, riga 49)

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

### Approfondimento: color_index — l'indice della giostra dei colori

- COME SI LEGGE: `color_index = 0` → "la variabile color_index vale 0".
- Chi è cosa: color_index è una VARIABILE NOSTRA, LOCALE di run (non
  self.color_index: non è un attributo del generatore — è un affare
  del menu, nasce dentro run e vive finché vive run). In C: una
  variabile locale della funzione, int color_index = 0.
- A cosa serve: è la POSIZIONE sulla giostra. WALL_COLORS è una lista
  di 4 stringhe (RED, BLUE, MAGENTA, CYAN) e WALL_BGS le 4 stringhe
  degli sfondi (41, 44, 45, 46). color_index dice QUALE delle 4
  prendere: _print_maze riceve WALL_COLORS[color_index] (il colore
  dei muri) e WALL_BGS[color_index] (lo sfondo del 42, lo stesso
  colore: il blocco uniforme).
- Perché 0: due motivi.
  1. Le liste di Python (come gli array del C) contano da 0: l'indice
     0 è il PRIMO elemento. color_index = 0 vuol dire "partiamo dal
     primo colore della lista": WALL_COLORS[0] = RED — il menu si apre
     sempre coi muri rossi.
  2. La variabile deve ESISTERE prima di essere letta: al primo giro
     del while, _print_maze legge subito WALL_COLORS[color_index]; se
     color_index non fosse ancora nata, Python alzerebbe NameError.
     Per questo nasce PRIMA del while, insieme a show_path.
- La traccia della nascita (all'apertura del menu):

  | riga | domanda | risposta | cosa succede |
  |---|---|---|---|
  | color_index = 0 | — | — | la variabile nasce e vale 0 |
  | _print_maze(..., WALL_COLORS[color_index], ...) | quale stringa ha l'indice 0? | RED | i muri escono rossi |
  | WALL_BGS[color_index] | quale sfondo ha l'indice 0? | \033[41m | il 42 col fondo rosso |

- Come cambia (tasto 3): color_index = (color_index + 1) % 4: la
  giostra 0→1→2→3→0. Il % len(WALL_COLORS) tiene l'indice DENTRO la
  lista: 3+1 farebbe 4, ma WALL_COLORS[4] non esiste (IndexError): il
  resto della divisione per 4 riporta a 0 (RED).
- ATTENZIONE: la variabile nasce UNA volta sola, PRIMA del while. Se
  nascesse DENTRO il while, a ogni giro verrebbe rimessa a 0 e la
  giostra si bloccherebbe sul colore 1.
- Risposta da evaluation: "color_index è l'indice della lista
  WALL_COLORS: dice quale colore usare per i muri (e lo stesso indice
  per WALL_BGS, lo sfondo del 42). Parte da 0 perché le liste contano
  da 0 e 0 è il primo colore (RED), e nasce prima del ciclo perché al
  primo giro viene già letta. Il tasto 3 la fa girare in tondo con
  l'operatore %."

### Approfondimento: print(CLEAR) — l'ordine di cancellare lo schermo

- COME SI LEGGE: `CLEAR: str = "\033[2J\033[H"` → "la costante CLEAR
  vale la stringa ESC [ 2 J ESC [ H". E `print(CLEAR)` → "stampa la
  stringa CLEAR".
- Ma print non la MOSTRA: la CONSEGNA al terminale. Il carattere
  `\033` è l'ESC (il numero 27, invisibile — i byte veri sono
  1b 5b 32 4a 1b 5b 48) e significa: "attenzione terminale, quello
  che segue NON è testo da scrivere, è un ORDINE".
- I due ordini:
  - `2J`: cancella TUTTO lo schermo (J = cancellare, 2 = tutto);
  - `H`: porta il cursore a CASA, in alto a sinistra (da dove
    comincia il titolo). Serve perché dopo il 2J la posizione del
    cursore non è garantita.
- Perché li mandiamo: il menu è un giro infinito che ridisegna il
  labirinto ogni volta. Senza la cancellata, a ogni giro il labirinto
  nuovo si stamperebbe SOTTO quello vecchio e la schermata si
  accatasta (il labirinto cammina giù). CLEAR svuota e il cursore
  torna su: ogni giro ridisegna la stessa schermata. In C: lo stesso
  identico printf("\033[2J\033[H") — i codici ANSI sono del
  TERMINALE, non del linguaggio.
- IL BLOCCO VUOTO (visto lanciando make run): sì, è colpa di CLEAR.
  Due casi:
  - Terminale VERO (Terminal/iTerm del Mac, quello della scuola):
    esegue l'ordine davvero — cancella e il labirinto appare subito
    in alto. Il blocco non si vede MAI: cancellare e riscrivere
    avviene nello stesso istante.
  - Terminale che NON sa cancellare (il pannello dove gira Claude
    Code o VS Code, o un output catturato): non può svuotare davvero
    lo schermo, allora "cancella" a modo suo emettendo TANTE RIGHE
    VUOTE. Le righe vuote spingono via il comando make run, e il
    labirinto appare una pagina più in basso. Quel blocco vuoto È la
    cancellata fatta male.
- Non tocca la valutazione: l'evaluator lancia in un terminale vero.
- Risposta da evaluation: "CLEAR è una stringa con due codici ANSI:
  \033[2J cancella lo schermo e \033[H porta il cursore in alto a
  sinistra; serve perché il menu ridisegna il labirinto ogni giro e
  senza la cancellata i disegni si accatasterebbero uno sotto
  l'altro".

### Approfondimento: i codici ANSI dei colori (RED e compagnia)

- COME SI LEGGE: `RED: str = "\033[31m"` → "la costante RED, di tipo
  stringa, vale la stringa ESC [ 31 m".
- La stringa ha 5 caratteri (byte veri: 1b 5b 33 31 6d):
  - `\033`: il carattere ESC (27) — come con CLEAR: "ORDINE in
    arrivo";
  - `[`: l'ordine comincia qui;
  - `3` `1`: DUE caratteri '3' e '1' — testo, NON il numero 31: è il
    codice del colore che il terminale legge, come un modulo da
    compilare;
  - `m`: fine dell'ordine: "modifica l'aspetto del testo" (SGR).
- La famiglia dei codici:
  - 30-37 = colore del TESTO: 30 nero, 31 rosso, 32 verde, 33 giallo,
    34 blu, 35 magenta, 36 ciano, 37 bianco;
  - 40-47 = colore dello SFONDO (stessi colori + 40: WALL_BGS usa
    41, 44, 45, 46);
  - 0 = spegni tutto (RESET); 49 = sfondo di default (NO_BG: spegne
    SOLO lo sfondo, non il testo).
- Come agisce — la penna: il codice non è un carattere visibile, è il
  momento in cui prendi in mano la penna rossa. Tutto quello stampato
  DOPO esce rosso finché non arriva un ordine contrario. Nel display
  la stringa è INCOLLATA DAVANTI ai muri: print(wall_color + wall):
  il terminale riceve prima "ESC[31m", poi i caratteri, e li scrive
  tutti rossi. (Vista con cat -v: ^[[31mrosso^[[0m normale: il codice
  sta in mezzo al testo, invisibile.)
- Perché le COSTANTI: RED è una variabile NOSTRA (in cima a
  display.py), un NOME per la stringa — il codice dice "stampa in
  RED" invece di "stampa quell'accozzaglia". In C identico:
  printf("\033[31mrosso\033[0m") — i codici ANSI sono del TERMINALE,
  non del linguaggio.
- ATTENZIONE onesta: `NORMAL: str = ""` è la stringa VUOTA: stampare
  "" non fa niente, nessun ordine. Viene messa prima di I e O con
  l'idea "qui scrivi senza colori", ma la stringa vuota NON spegne il
  colore già acceso (per quello serve RESET): I e O escono del colore
  dei muri. Cosmetico, non cambia nulla.
- Risposta da evaluation: "RED è una costante che vale '\033[31m':
  ESC[ apre un ordine ANSI, 31 è il codice del rosso, m chiude (SGR).
  Il terminale non la mostra: da lì scrive rosso finché non arriva
  \033[0m. Il display la incolla davanti ai caratteri del labirinto
  (wall_color + wall): i muri escono del colore scelto, e il tasto 3
  cambia quale stringa viene usata."

### _print_maze (righe 69-146): il disegno (teoria 1.7)

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
  ogni x il giunto (_junction) + il muro N: chiuso → "───"; aperto ma
  attraversato dal percorso → puntino verde; altrimenti spazio. Poi la
  RIGA DELLE CELLE (line): per ogni x il muro W (│ / puntino / spazio)
  + il CONTENUTO: mattoncino del 42 → sfondo colorato (il blocco
  uniforme); entrata → "I"; uscita → "O"; cella del percorso →
  puntino verde; altrimenti spazio. In fondo la RIGA DI FONDO coi muri
  S.
- I colori: wall_color si "accende" prima di ogni riga e RESET alla
  fine: i codici ANSI vanno spenti o colorerebbero tutto ciò che segue.

### Approfondimento: path_n e path_w — a chi appartiene il muro attraversato

- Il fine del procedimento: NIENTE generazione (il labirinto è già
  costruito: questo loop gira solo nel display, quando si preme 2).
  Il solve restituisce la lista delle CELLE; ma tra due celle
  consecutive c'è un MURO da attraversare, e il disegno ha 1
  carattere per muro. Il puntino verde deve cadere ESATTAMENTE su
  quel carattere: le due liste sono il promemoria di DOVE.
- Il loop non confronta "chi ha la Y più piccola": fa 4 DOMANDE in
  fila (cascata), una per direzione del passo:
  - y2 == y1 - 1 → "la seconda è una riga SOPRA?" → si SALE;
  - y2 == y1 + 1 → "la seconda è una riga SOTTO?" → si SCENDE;
  - x2 == x1 + 1 → "la seconda è una colonna a DESTRA?" → si va a
    DESTRA;
  - else → resta solo SINISTRA.
- LA REGOLA UNICA dietro tutto: nel disegno ogni muro è disegnato
  UNA volta sola e appartiene a UNA cella sola:
  - il muro ORIZZONTALE tra due celle = il muro NORD della cella
    SOTTO;
  - il muro VERTICALE tra due celle = il muro OVEST della cella a
    DESTRA.
  (È la stessa lezione dell'import senza E: ogni muro è il N di
  qualcuno o il W di qualcuno.)
- Quindi il loop fa una cosa sola: "di chi è il muro che attraversiamo
  in questo passo? Segna QUELLA cella nella lista giusta":
  - SU → cella sotto = la PRIMA (la partenza) → path_n riceve
    (x1, y1);
  - GIÙ → cella sotto = la SECONDA (l'arrivo) → path_n riceve
    (x2, y2);
  - DESTRA → cella a destra = la SECONDA → path_w riceve (x2, y2);
  - SINISTRA → cella a destra = la PRIMA → path_w riceve (x1, y1).
- Traccia VERA (labirinto 6x4, seed 42, path da solve):
  - passo 0: (0,0) -> (1,0) DESTRA → W di (1,0) → path_w
  - passo 2: (2,0) -> (2,1) GIÙ → N di (2,1) → path_n
  - passo 4: (3,1) -> (3,0) SU → il muro è orizzontale, la cella
    sotto è (3,1) che è la PRIMA → path_n
  - passo 8: (5,1) -> (4,1) SINISTRA → il muro è verticale, la cella
    a destra è (5,1) che è la PRIMA → path_w
  - alla fine: path_n = [(2,1), (3,1), (5,1), (4,2), (5,3)],
    path_w = [(1,0), (2,0), (3,1), (4,0), (5,0), (5,1), (5,2)].
- Poi i due loop del disegno, quando il muro è aperto (else),
  domandano (x, y) in path_n / in path_w: sì → puntino verde, no →
  spazio. Nel disegno vero i puntini stanno tutti sui muri
  attraversati dalla catena.
- Risposta da evaluation: "solve dà le celle, il display ha un
  carattere per muro: il loop traduce ogni passo tra due celle nella
  marcatura del muro attraversato. Siccome ogni muro è disegnato una
  volta sola — come N della cella sotto o W della cella a destra —
  per ogni passo si appende nella lista giusta la cella che possiede
  quel muro; i loop del disegno poi mettono il puntino sui muri
  marcati."

### LA VISTA D'INSIEME: chi produce cosa (tre attori separati)

```
generate() (talpa+piccone) -> gen.grid = IL LABIRINTO
solve()    (il fuoco)      -> path     = IL PERCORSO (solo celle)
_print_maze                 -> la schermata = labirinto + puntini
```

_print_maze stampa il labirinto eccome — ma il labirinto viene SEMPRE
da gen.grid (già fatto dalla talpa). Solve non genera nulla: quando si
preme 2 viene chiamato dentro _print_maze solo per calcolare il
percorso da disegnarci sopra.

I tre stadi, col labirinto VERO della traccia (6x4, seed 42):

1) Quello che si vede SEMPRE (menu appena aperto): solo i muri di
   gen.grid.

```
+---+---+---+---+---+---+
| I         |           |
+---+---+   +   +---+   +
|       |       |       |
+   +   +---+---+   +---+
|   |           |       |
+   +---+---+   +---+   +
|           |         O |
+---+---+---+---+---+---+
```

2) Quello che dà solve: i NUMERI sono l'ordine nella lista path, le *
   sono i muri che ogni passo attraversa (messe lì da path_n e
   path_w). Ogni * sta ESATTAMENTE tra due numeri consecutivi: quella
   * È il muro attraversato in quel passo.

```
+---+---+---+---+---+---+
| I *  1*  2|  5*  6*  7|
+---+---+ * + * +---+ * +
|       |  3*  4|  9*  8|
+   +   +---+---+ * +---+
|   |           | 10* 11|
+   +---+---+   +---+ * +
|           |         O |
+---+---+---+---+---+---+
```

   Leggila così: I -> 1 -> 2 scende (la * sopra il 3), 3 -> 4 a destra
   (la * tra 3 e 4), 4 RISALE (la * sopra il 4), e così via fino a O.
   Due zoom:
   - passo 2 (il 2 scende sul 3): la * sta SOPRA il 3 → è il muro N
     di (2,1), la cella SOTTO, che era la SECONDA del passo → path_n;
   - passo 8 (l'8 va a sinistra sul 9): la * sta a SINISTRA dell'8 →
     è il muro W di (5,1), la cella a DESTRA, che era la PRIMA del
     passo → path_w. (La cella 8 ha due *: è in TUTTE E DUE le liste:
     entrata dall'alto al passo 7 e uscita a sinistra al passo 8.)

3) Il disegno finale (dopo aver premuto 2). Nel display vero i
   puntini sono TUTTI verdi; qui le * sui muri restano * per far
   vedere che sono DUE meccanismi diversi: i puntini sulle CELLE
   nascono da (x, y) in path, i puntini sui MURI da (x, y) in path_n
   / path_w. Senza il loop che stavamo studiando avremmo le celle
   puntinate ma i muri attraversati resterebbero spazi vuoti.

```
+---+---+---+---+---+---+
| I * . * . | . * . * . |
+---+---+ * + * +---+ * +
|       | . * . | . * . |
+   +   +---+---+ * +---+
|   |           | . * . |
+   +---+---+   +---+ * +
|           |         O |
+---+---+---+---+---+---+
```

### Come vengono riempite e consumate le due liste

- RIEMPIMENTO: il loop prende il path A COPPIE consecutive e per ogni
  coppia risponde a UNA domanda (si sale? si scende? si va a destra?
  a sinistra?) e appende UNA cella a UNA lista — la cella che
  POSSiede il muro attraversato. Contenuto finale del labirinto 6x4
  (12 passi):
  - path_n = [(2,1), (3,1), (5,1), (4,2), (5,3)] → 5 muri ORIZZONTALI
  - path_w = [(1,0), (2,0), (3,1), (4,0), (5,0), (5,1), (5,2)] → 7
    muri VERTICALI
  - 5 + 7 = 12: ogni passo marca esattamente un muro.
- CONSUMO: le liste da sole non disegnano niente: sono il promemoria
  che i due loop del disegno consultano. Quando il disegno trova un
  muro APERTO fa UNA domanda: "la cella è nella lista?" Sì → puntino
  verde, no → spazio.
- Riga dei muri SOPRA la riga 1 (muri N, labirinto vero):
  (0,1) chiuso → "───"; (1,1) chiuso; (2,1) aperto e in path_n →
  puntino; (3,1) aperto e in path_n → puntino; (4,1) chiuso; (5,1)
  aperto e in path_n → puntino.
- Riga delle CELLE 1 (muri W): (1,1) aperto ma NON in path_w →
  spazio (il percorso non passa di lì!); (3,1) e (5,1) aperti e in
  path_w → puntini; gli altri chiusi → "│".
- Questo è il dettaglio che spiega tutto: NON basta che il muro sia
  aperto — il puntino va solo dove il percorso passa davvero.

### _junction (righe 147-198): l'incrocio

Guarda i 4 LATI del nodo (sinistra, destra, sopra, sotto) e sceglie il
glifo giusto (┼ con 4 muri, ┬ quando manca il basso, ─ per il solo
orizzontale...). Ai BORDI (x == width o y == height) il bordo esterno
conta come muro. La cascata di if: si controlla dal caso più pieno al
più vuoto e il PRIMO che combacia vince (l'ordine conta!). Se nessun
lato ha un muro → spazio.

### Approfondimento: la costruzione riga per riga (il blocco dei due for + junction)

- Il blocco costruisce la SCHERMATA INTERA: una riga di muri + una
  riga di celle per OGNI riga del labirinto, più la riga di fondo:
  2*height + 1 righe. Ogni riga è UNA stringa che cresce pezzo per
  pezzo: wall = wall + ...
- Anatomia della riga dei muri: GIUNTO + muro, GIUNTO + muro, ...,
  GIUNTO finale (i giunti chiudono anche le estremità). Il giunto è
  l'incrocio della griglia, il muro è il segmento orizzontale
  ("─", spazio o puntino).
- Il giunto fa 4 DOMANDE (dal nodo partono muri verso sinistra,
  destra, sopra, sotto?) e la cascata va dal più pieno al più vuoto:
  il PRIMO che combacia vince.
- Traccia vera (6x4, seed 42), la riga y=0 cresce così:
  '┌───' → '┌───────' → '┌───────────' → '┌───────────┬───' →
  '┌───────────┬───────' → '┌───────────┬───────────' →
  '┌───────────┬───────────┐'
  - giunto (0,0): sin=F des=T su=F giù=T → ┌ (l'angolo in alto a
    sinistra: niente a sinistra, niente sopra);
  - giunto (1,0) e (2,0): solo sin e des → ─;
  - giunto (3,0): giù=T (da lì scende il muro W di (3,0)) → ┬;
  - giunto (6,0), il bordo destro: sin=T des=F giù=T → ┐.
- Riga delle celle: muro W (│/spazio/puntino) + contenuto (I/O/42/
  puntino/spazio) per ogni cella + bordo destro fisso │.
- Riga di fondo: come la riga dei muri ma con y = height: le domande
  cambiano — sin/des guardano i muri S dell'ultima riga, su guarda i
  W dell'ultima riga, giù è sempre F (sotto il fondo non c'è niente).
  Traccia: '└───' → '└───────' → '└───────────' → '└───────────┴───' →
  '└───────────┴───────' → '└───────────┴───────────' →
  '└───────────┴───────────┘' (il ┴ al giunto (3,4): sale il
  muro W di (3,3)).
- Perché i giunti servono: con un carattere per NODO, un bivio a T
  disegnato col simbolo sbagliato avrebbe un moncone di muro
  fantasma o un buco. I cartelli giusti riproducono gli incroci
  dell'esempio del subject.
- Risposta da evaluation: "ogni riga di muri è una stringa costruita
  come giunto+muro ripetuti; _junction guarda i 4 muri che si
  incontrano al nodo della griglia e con una cascata di if dal caso
  più pieno al più vuoto sceglie il simbolo giusto (┼ ┬ ┴ ├ ┤ ┌ ┐ └
  ┘ ─ │); la riga di fondo usa y = height e guarda i muri S
  dell'ultima riga."

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

# 4. Preparazione alla difesa (la scala di valutazione)

La scala della difesa ha 7 sezioni. Per ognuna: cosa fa l'evaluator,
dove sta la risposta nel codice, cosa dire. I punti con ▼ sono quelli
dove si scava di più.

## Il set di consegna (niente di più)

- DA CONSEGNARE: a_maze_ing.py (il main), config_parser.py,
  mazegen.py (generatore + solve, anche il modulo riusabile della
  sezione 6), display.py, output_writer.py, Makefile (le regole del
  subject III.2 — install/run/debug/clean/lint — piu' env/test/
  lint-strict/build/wheel, in ordine cronologico di utilizzo),
  config.txt (il programma si lancia con lui e l'evaluator lo
  EDITA), README.md (tutte le sezioni del VII), pyproject.toml (il
  build della wheel; e `mypy .` pulito senza pytest), tests/ (i 3
  file di test — il subject III.3 dice "not submitted or graded",
  li teniamo per noi: make test verde), .gitignore (richiesto da
  III.3: esclude gli artefatti Python), .flake8 (minimo: esclude
  solo .venv, cosi' `flake8 .` del subject resta pulito anche con un
  venv dentro la cartella), mazegen-1.0.0-py3-none-any.whl (VI: "the
  file must be located at the root of your git repository" — il
  pacchetto costruito sta alla radice; l'evaluator lo RICOSTRUIRA'
  comunque dalle sorgenti).
- DA NON CONSEGNARE (restano in locale, esclusi dai .gitignore):
  output_validator.py (strumento del subject, non nostro), maze.txt (output di
  un run), __pycache__/, .venv/, dist/ e build/.
- LA CARTELLA DI PROVA: ~/Desktop/consegna_amazeing contiene ESATTAMENTE
  i 14 pezzi (nient'altro): è ciò che si copia sulla macchina della
  scuola. Lì è stata fatta la prova generale da zero: venv nuovo +
  pip install flake8 mypy pytest build → flake8 . pulito → mypy .
  --strict pulito → 22 test verdi → run con "q" (maze.txt scritto,
  uscita pulita) → validator OK → wheel ricostruita. Dopo ogni
  modifica al progetto: ricopiare i file cambiati anche lì.

## I test e pytest (come spiegarli in difesa)

### Approfondimento: pytest — il vigile dei test (cos'è, come becca gli errori)

- pytest è un PROGRAMMA (un pacchetto installato con pip, come
  flake8 e mypy): lo lanci, lui scorre i file tests/, esegue ogni
  funzione test_* e per ognuna decide: la domanda (assert) è vera o
  falsa? Alla fine stampa il resoconto: "22 passed" (tutto vero)
  oppure "3 failed, 19 passed" (tre domande false → qualcosa è
  rotto). Si lancia con python3 -m pytest o con make test. In C:
  l'equivalente non esiste di serie — testi a mano col debugger o
  con un framework esterno.
- Come fa a TROVARE i test: cerca da solo i file test_*.py e dentro
  le funzioni test_*: non serve iscriverli da nessuna parte. È per
  questo che i file della cartella tests/ si chiamano così.
- Un TEST = una funzione con nome test_* in un file test_*.py. Dentro
  fa due cose: PREPARA (costruisce l'input, es. un config in un file
  temporaneo) e DOMANDA (una riga assert: la domanda vera e propria).
  assert condizione = "se la condizione è falsa, ALZA la mano":
  pytest raccoglie le mani alzate e alla fine fa il resoconto.
- I 3 file della cartella tests/:
  - test_config_parser.py (14 test): ogni test prepara un config e
    domanda una cosa — es. test_lowercase_keys_ok domanda "le chiavi
    minuscole sono accettate?", test_missing_key domanda "senza
    PERFECT salta fuori ConfigError?" (e per questo usa
    pytest.raises: "mi aspetto proprio QUESTO errore").
  - test_mazegen.py (4 test): connettività del perfetto/non perfetto,
    la soglia 9x6 del 42, i mattoncini tutti chiusi.
  - test_output_writer.py (4 test): il formato del file e la
    conversione del percorso in NESW.
- PROVA VERA che i test servono (fatta davanti ai nostri occhi):
  abbiamo ROTTO il parser (tolto il .lower() del PERFECT) e
  make test ha subito segnalato 3 test rossi (test_valid_config,
  test_unknown_keys_ignored, test_no_seed_is_none) — il bug delle
  minuscole, quello che la scala valutava. Ripristinato il codice:
  22 verdi in 0.01s. Ecco il valore: una modifica che rompe qualcosa
  viene beccata in UN secondo, prima dell'evaluator.
- Il subject III.3 dice "not submitted or graded": li teniamo per
  NOI, come prova pronta alla mano se l'evaluator chiede una modifica
  (cap. IX: "a brief modification... may occasionally be requested").
- Chi è cosa: pytest = pacchetto predefinito (pip); assert = parola
  chiave predefinita di Python; pytest.raises = strumento di pytest;
  le funzioni test_* = NOSTRE.
- Risposte pronte: "Cos'è pytest?" Il programma che esegue i test e
  fa il resoconto dei fallimenti. "Cos'è un test?" Una funzione che
  prepara un input e fa una domanda con assert. "A cosa vi servono?"
  A beccare subito qualsiasi modifica che rompe il programma: li
  abbiamo visti fermare un bug vero del parser.

### Come si spiega all'evaluator (e quanto basta saperne)

- LA SPIEGAZIONE in 3 frasi: "tests/ contiene i 22 test del progetto,
  eseguiti con pytest. Ogni test prepara un input e fa una domanda
  con assert: se la domanda è falsa, pytest lo segnala — make test dà
  il verdetto in un secondo. Il subject III.3 li dice esplicitamente
  'not submitted or graded': sono il nostro strumento di lavoro, non
  fanno parte del programma."
- IL CONFINE (cosa DEVI sapere e cosa no):
  - DEVI: cos'è pytest (il vigile); cosa controllano i 3 file
    (config: chiavi ed errori; mazegen: connettività e 42; output:
    formato del file e NESW); come funziona UN test (prepara +
    assert); che make test è verde.
  - NON serve: il riga-per-riga di tutti i 22. Motivo onesto e
    difendibile: il subject NON li valuta — sono uno strumento come
    flake8; l'evaluator valuta il PROGRAMMA, e quello si sa riga per
    riga.
  - MA: se l'evaluator ne indica uno, lo si legge a voce lì per lì —
    sono funzioni semplici e i pezzi (join, TemporaryDirectory,
    assert) sono roba già studiata.
- UN TEST LETTO A VOCE (test_lowercase_keys_ok), col pallino:
  - content = "
".join([...]) — prepara un config TUTTO minuscolo
    (le 7 righe attaccate coi ritorni a capo);
  - with tempfile.TemporaryDirectory() — apre una cartella
    temporanea (esiste solo per il test, poi sparisce);
  - config = parse_config(_write(...)) — scrive il config lì dentro
    e lo dà al NOSTRO parser;
  - assert config.width == 20 — DOMANDA: il parser ha accettato le
    minuscole e ha letto 20? Se sì si passa oltre, se no test rosso;
  - alla fine: 4 assert tutte vere → test verde.
- FRASE PRONTA se insistono: "I test non sono in valutazione (subject
  III.3): sono il nostro vigile. So cosa controllano e come
  funzionano — se vuoi te ne leggo uno riga per riga." (E saperlo
  fare davvero.)

## 4.1 Display e menu (sezione 2 della scala)

- Esegue a_maze_ing.py col config di default → labirinto + menu.
  Basta `make run` (o python3 a_maze_ing.py config.txt).
- Menu obbligatori: 1 = rigenera, 2 = mostra/nasconde il percorso
  più corto, 3 = cambia colore dei muri. q = extra (uscita).
- Da dire: il menu è il while True di display.run; il 2 usa `not`
  per accendere/spegnere e ricalcola il percorso con solve() solo
  per disegnarlo; il 3 cicla la giostra dei colori col resto %.

## 4.2 Config: formato ed errori (sezione 3) ▼

- Formato: commenti con #, righe KEY=VALUE (MINUSCOLE OK: il parser
  fa .upper() sulla chiave), chiavi obbligatorie WIDTH HEIGHT ENTRY
  EXIT OUTPUT_FILE PERFECT (SEED facoltativa).
- L'evaluator EDITERA' config.txt e proverà TUTTI questi errori (mai
  crashare: messaggio + uscita 1):
  - chiave mancante → "missing mandatory keys"
  - riga senza = → "expected 'KEY=VALUE'"
  - lettere al posto dei numeri → "must be an integer"
  - PERFECT sbagliato → "must be True or False"
  - ENTRY/EXIT sbagliati → "must be 'x,y'" / "must be an integer" /
    "outside the maze"
- Da dire: il try/except del main con le reti; ogni errore è un
  ConfigError col messaggio chiaro; il programma non crasha MAI
  (richiesta esplicita della scala).

## 4.3 File di output (sezione 4)

- Formato: HEIGHT righe di WIDTH cifre, riga vuota, ENTRY, EXIT,
  percorso NESW. Il validator del subject resta muto (verificato).
- "Il percorso nel file combacia col display": la lista è la stessa
  (solve()), il BFS è deterministico: pallini verdi = lettere NESW.
- Da dire: la cifra esadecimale = le monete della cella (bit
  N/E/S/W), tradotta da HEX_DIGITS[cell].

## 4.4 Il generatore (sezione 5) ▼▼ — il cuore della difesa

- Casuale ma riproducibile: random.Random(seed) personale (il
  librone 1.3). Stesso seed → stesso labirinto.
- Parametri incoerenti: generate alza ValueError (entry/exit fuori o
  uguali); width/height negativi fanno risultare l'entry fuori →
  stesso errore.
- Tutte le celle raggiungibili tranne il 42: la talpa scava tutto
  (la corda si svuota solo quando tutte le celle sono scavate); i
  mattoncini sono marcati visitati = cemento.
- Muri tutto intorno: il bordo esterno non si apre MAI.
- Niente 3x3 aperte: il piccone controlla dopo ogni colpo
  (_has_3x3_open, i 12 muri interni) e richiude se nasce la
  piazzetta. "Come l'hai verificato?" → test + tracce negli appunti.
- 42 presente, o messaggio sul terminale se troppo piccolo (sotto
  9x6): è il resoconto has_42 letto dal main.
- PERFECT=True → un solo percorso: la talpa costruisce un albero
  ricoprente.

## 4.5 Modulo riusabile (sezione 6) — PROVA DAL VIVO ▼

L'evaluator chiede di RICOSTRUIRE il pacchetto e installarlo in un
altro ambiente. I comandi esatti, in ordine, stanno nella sottosezione "Le due
sequenze da zero" (qui sotto). In breve: venv1 RICOSTRUISCE la
scatola dalle nostre sorgenti, venv2 la INSTALLA e la usa.

- Da dire: pyproject.toml + setuptools fanno il pacchetto; mazegen.py
  è autonomo (non importa config, output né display): funziona
  installato da solo.

### Le 4 parole (pacchetto, wheel, venv, pip)

- Prima di tutto le parole, senza darle per scontate:
  - PACCHETTO = una scatola di biscotti: dentro il modulo
    (mazegen.py), sopra l'etichetta (nome, versione).
  - WHEEL = la scatola già sigillata, pronta da installare (il file
    mazegen-1.0.0-py3-none-any.whl, che è uno zip).
  - VENV (ambiente virtuale) = una seconda CUCINA, separata dal
    Python di sistema: ci installi dentro quello che vuoi senza
    toccare nient'altro.
  - PIP = il CORRIERE: porta le scatole dal magazzino (PyPI) alla
    cucina giusta (site-packages).
- CHI FA COSA (per non confondersi): il Makefile NON crea il venv e
  NON installa il pacchetto — il venv lo crea l'evaluator (o noi)
  con python3 -m venv; il pacchetto è già committato alla radice.
- ATTENZIONE ai due "venv" di make env: la ricetta è python3 -m venv
  venv — il PRIMO venv è il MODULO di Python che crea gli ambienti
  virtuali, il SECONDO è il NOME della cartella. Si crea UNA cucina
  sola. (Come si legge: "python3, esegui il modulo venv, e chiama la
  cartella 'venv'".)
- IN TUTTA LA STORIA CI SONO TRE CUCINE, ognuna col suo mestiere:
  - venv/ (nel progetto): fatta con make env, UNA volta; contiene i
    4 STRUMENTI (flake8, mypy, pytest, build); usata TUTTI i giorni
    dal Makefile (ogni ricetta chiama venv/bin/python).
  - /tmp/venv1 (sezione 6): fatta a mano; contiene solo build;
    usata UNA volta per RICOSTRUIRE la scatola davanti all'evaluator.
  - /tmp/venv2 (sezione 6): fatta a mano; contiene la wheel
    installata; usata UNA volta per PROVARE che si installa e
    funziona.
  Non è vero che "non vengono usate finché non si fanno i comandi a
  mano": venv/ la usa il Makefile tutti i giorni; le due di /tmp non
  ESISTONO nemmeno fino alla sezione 6.
- PERCHÉ la sezione 6 ne vuole DUE: la dimostrazione ha due passi
  separati. venv1 = la FABBRICA: ricostruisce il pacchetto dalle
  sorgenti in un ambiente pulito (prova che chiunque può rifarlo).
  venv2 = il CLIENTE: riceve la scatola finita e la usa (prova che
  si installa e funziona da solo). In UNA cucina sola la prova
  dell'installazione pulita non esisterebbe: il modulo potrebbe
  funzionare solo perché le sorgenti sono lì vicino.

### Approfondimento: pip — il gestore di pacchetti

- pip = "Pip Installs Packages": il GESTORE DI PACCHETTI di Python.
  Programma PREDEFINITO che viaggia con Python (si lancia con
  python3 -m pip: "chiedi a python3 di eseguire il modulo pip" — così
  installa nel Python giusto, quello del venv).
- Da dove scarica: PyPI (Python Package Index, pypi.org), il magazzino
  online con ~500.000 pacchetti. Ci parla pip, non l'utente.
- Cosa vuol dire "installare": copiare i file .py del pacchetto dentro
  site-packages — LA cartella dove Python cerca quando si fa import
  (nel venv: .venv/lib/.../site-packages/; ogni pacchetto ha la sua
  cartella + una cartella .dist-info coi metadati, la stessa della
  wheel). Da quel momento l'import funziona da qualunque programma.
- In più fa da solo le DIPENDENZE (se un pacchetto ne richiede un
  altro, lo installa: mccabe, pycodestyle, pyflakes sono dipendenze
  di flake8; pluggy e iniconfig di pytest) e le versioni
  (pip install x==1.2.3).
- Analogia col C: in C non c'è l'equivalente standard — si scaricano
  i sorgenti e si compila, o si usa il gestore del sistema. pip è
  l'apt/brew del mondo Python.
- NEL NOSTRO CASO, tre momenti precisi:
  1. make install → pip install flake8 mypy pytest build: i 4
     strumenti di sviluppo nel venv;
  2. make build → python3 -m build: il modulo build (installato da
     pip!) legge pyproject.toml e produce la wheel;
  3. sezione 6 → pip install dist/mazegen-1.0.0-py3-none-any.whl:
     copia il NOSTRO mazegen.py in site-packages → chiunque può fare
     from mazegen import MazeGenerator.
- Punto chiave per la difesa: il PROGRAMMA non usa pip — a_maze_ing
  importa solo la libreria standard (sys, random, collections), zero
  dipendenze esterne: gira su qualunque Python pulito. pip serve per
  i tool di sviluppo e per rendere il NOSTRO modulo installabile
  dagli altri (il requisito del cap. VI). Il blocco [project] del
  pyproject.toml è scritto per pip/setuptools: nome, versione,
  requires-python — pip lo legge per decidere se può installare.
- Risposte pronte:
  - "Cos'è pip?" Il gestore di pacchetti di Python: scarica da PyPI
    e installa in site-packages.
  - "Il programma dipende da pip?" No: solo libreria standard. pip
    serve ai tool e all'installazione del modulo riusabile.
  - "Come si installa il vostro modulo?" pip install
    mazegen-1.0.0-py3-none-any.whl in un venv, poi from mazegen
    import MazeGenerator.
  - "Perché python3 -m pip e non pip?" Per installare nel Python del
    venv, non in quello di sistema (bloccato da PEP 668).

### pyproject.toml dalla A alla Z (il "Tom")

- COME SI LEGGE il nome: py-project-toml = "il file TOML di
  configurazione del progetto Python". TOML = Tom's Obvious Minimal
  Language: un formato standard per i file di configurazione —
  sezioni in parentesi quadre [sezione] e righe chiave = valore. È il
  config.txt del sistema di COSTRUZIONE (in C non c'è l'equivalente
  diretto: è una ricetta letta da pip, come un Makefile ma per
  l'installazione).
- PERCHÉ esiste: il cap. VI vuole il modulo riusabile "suitable for a
  later installation by pip". pip, per installare, ha bisogno della
  RICETTA: nome, versione, quali file. pyproject.toml È la ricetta.
- I 4 blocchi del NOSTRO file, chi è cosa:
  1. [build-system]: chi fa il lavoro di costruzione. requires =
     setuptools (la libreria standard per fare pacchetti, predefinita
     di Python) e build-backend = setuptools.build_meta (il motore).
  2. [project]: la CARTA D'IDENTITÀ del pacchetto: name = "mazegen",
     version = "1.0.0", description, requires-python = ">=3.10".
  3. [tool.setuptools]: py-modules = ["mazegen"] → QUALE file entra
     nel pacchetto: il solo mazegen.py.
  4. [tool.mypy]: exclude = [".venv", "output_validator.py",
     "tests/"] → NON c'entra col pacchetto: è la configurazione di
     mypy, che vive qui perché questo è il posto standard dove mypy
     la cerca (così `mypy .` è pulito anche senza pytest installato).
- IL BUILD, in ordine di esecuzione:
  1. python3 -m build (o make build) → setuptools legge pyproject.toml
     → produce dist/mazegen-1.0.0-py3-none-any.whl E il tar.gz (il
     subject ammette entrambi).
  2. Il NOME della wheel si scompone: nome-versione-python-ABI-
     piattaforma: py3 = gira su qualunque Python 3; none = nessuna
     ABI specifica (è puro codice Python, niente compilato); any =
     qualunque sistema operativo. (In C sarebbe una libreria
     compilata per architettura: qui "any".)
  3. La wheel è letteralmente uno ZIP (si apre con unzip): dentro
     mazegen.py + la cartella mazegen-1.0.0.dist-info con METADATA
     (la carta d'identità copiata dal pyproject), WHEEL e RECORD (la
     lista dei file).
  4. pip install dist/mazegen-1.0.0-py3-none-any.whl (dentro un venv)
     → copia mazegen.py dove Python lo trova → da qualunque
     programma: from mazegen import MazeGenerator funziona.
  5. Il venv: un Python ISOLATO (una copia di Python con le sue
     librerie in una cartella a parte) — serve per non sporcare il
     sistema e per provare l'installazione da zero, come farà
     l'evaluator.
- Perché SOLO mazegen.py entra nel pacchetto: è autonomo — importa
  solo random e collections (mai config_parser, output_writer,
  display). Il resto del programma non fa parte del modulo riusabile.
- SEZIONE 6 della difesa, passo passo:
  - l'evaluator vede la wheel alla radice del repo (cap. VI);
  - in un venv installa i tool e RICOSTRUISCE il pacchetto dalle
    nostre sorgenti (python3 -m build);
  - in un altro venv installa la wheel e prova a USARE il modulo:
    import, MazeGenerator, generate, solve;
  - domande probabili, con risposta pronta:
    - "Cos'è pyproject.toml?" La ricetta del pacchetto: nome,
      versione, file, officina (setuptools).
    - "Cos'è una wheel?" Il pacchetto pronto: uno zip con mazegen.py
      e i metadati; nome = nome-versione-py3-none-any.
    - "Cos'è un venv?" Un Python isolato per provare l'installazione
      senza sporcare il sistema.
    - "Come si usa il generatore?" Le 3 cose del cap. VI:
      istanziare MazeGenerator(width, height, seed), passare i
      parametri a generate(perfect, entry, exit), accedere a grid e
      solve() (il docstring di mazegen.py mostra l'esempio).

### Approfondimento: perché un modulo riusabile (la direzione delle frecce)

- La generazione del labirinto è la PARTE PREZIOSA (l'algoritmo);
  parser e display sono solo la pelle di QUESTO programma. Il cap. VI
  vuole che la parte preziosa possa vivere in progetti futuri (un
  videogioco, un simulatore...) senza portarsi dietro config.txt, il
  menu e il file di output. In C: la libreria maze.c compilata una
  volta e linkata da qualunque programma; in Python: mazegen.py +
  pip install.
- LA REGOLA D'ORO: nessuna dipendenza dal programma che lo usa.
  Prova 1: gli UNICI import di mazegen.py sono `import random` e
  `from collections import deque` (libreria standard): non sa nemmeno
  che config.txt, display e output_writer esistono — cancellandoli
  tutti, lui continua a funzionare identico. Prova 2: gli altri file
  importano LUI (a_maze_ing: import mazegen; display: from mazegen
  import ...), mai il contrario: la freccia va in una sola
  direzione.
- PROVA VERA del riuso (fatta da /tmp, fuori dal progetto, con la
  SOLA wheel installata): un "progetto futuro" ha importato mazegen
  (mazegen.__file__ → site-packages del venv), ha generato un 12x8
  NON perfetto con seed 7, ha contato i vicoli ciechi (celle con 3
  muri: 10) e ha chiesto il percorso — senza aprire nessun altro
  nostro file.
- IL CONTRATTO (l'intero manuale d'uso, 5 righe, le stesse che il
  cap. VI obbliga a documentare e che stanno nel docstring e nel
  README): from mazegen import MazeGenerator; gen =
  MazeGenerator(width, height, seed) [1. istanzia]; gen.generate(
  perfect, entry, exit) [2. parametri]; gen.grid e gen.solve()
  [3. struttura e soluzione]. Un futuro programmatore legge il
  docstring e usa il generatore senza aprire nient'altro (in C: il
  docstring = l'header .h con le firme).
- Risposte pronte: "Perché un modulo riusabile?" Il generatore è la
  parte preziosa, deve poter essere importato in progetti futuri
  (cap. VI). "Come fa a funzionare da solo?" Importa solo random e
  collections; gli altri importano lui, mai il contrario. "Come si
  usa?" Istanzio, passo i parametri, leggo grid e solve().

- PROVATA DAVVERO (prova generale 2026-09-23): venv1 → install build
  → ricostruita la wheel dalle sorgenti; venv2 → installata la wheel
  → da una cartella QUALUNQUE (non quella del progetto):
  import mazegen funziona e mazegen.__file__ punta a
  venv2/lib/.../site-packages/mazegen.py (la prova che si usa il
  modulo INSTALLATO, non il file del progetto). Stesso labirinto di
  sempre con seed 42.
- Il subject VI vuole anche il pacchetto costruito alla radice del
  repo ("the file must be located at the root of your git
  repository"): mazegen-1.0.0-py3-none-any.whl è committato lì, e
  l'evaluator lo ricostruirà comunque dalle sorgenti (pyproject.toml
  + mazegen.py).

### Il nuovo Makefile: dove lanciare cosa, quando il venv, uv, come si legge

- IL MAKEFILE È IN ORDINE CRONOLOGICO DI UTILIZZO (ogni bersaglio ha
  un commento breve nel file):
  1. make env — crea la cucina (venv) nella cartella; una volta sola
     per macchina;
  2. make install — il corriere porta i 4 strumenti (flake8, mypy,
     pytest, build) nella cucina; una volta sola;
  3. make run / make debug / make test / make lint / make lint-strict
     — il programma, il debugger (pdb), i 22 test, i controlli;
  4. make build — costruisce la scatola in dist/; make wheel — la
     costruisce E copia la scatola pronta alla radice (quella
     committata, cap. VI);
  5. make clean — butta cache e artefatti (NON tocca la cucina).
- TUTTO gira nel venv senza attivarlo: le ricette chiamano
  venv/bin/python (es. venv/bin/python -m pytest). Ecco perché make
  lint funziona anche se non si è fatto source/activate.
- DOVE LANCIARE I COMANDI (le tre postazioni):
  1. LA TUA CARTELLA DI SVILUPPO (Common_Core_2/python/AMAZEING): qui
     si lavora e si studia; make env/install una volta, poi il resto
     a ogni modifica.
  2. LA CARTELLA DI CONSEGNA (~/Desktop/consegna_amazeing, poi la
     repo sulla macchina della scuola): qui si fa la prova generale e
     l'evaluation; APPENA clonata: make env e make install, poi
     make lint/test/run.
  3. LE CARTELLE /tmp/venv1 e /tmp/venv2 DURANTE la sezione 6: create
     AL MOMENTO con i comandi a mano (python3 -m venv /tmp/venv1 ...)
     — NON col Makefile: servono a RICOSTRUIRE e INSTALLARE la
     scatola davanti all'evaluator, e si buttano via subito dopo.
- QUANDO CREARE IL VENV E COSA METTERCI: la cucina del progetto
  (venv/) si crea UNA volta appena clonato il progetto; dentro ci
  finiscono SOLO i 4 strumenti — il codice NON si sposta, resta
  nella cartella del progetto. I venv di /tmp si creano solo alla
  sezione 6, al momento, e sono usa-e-getta.
- UV (visto nei Makefile di altri): il gestore MODERNO che fa venv e
  pip insieme, più veloce (scritto in Rust): uv venv, uv pip install.
  Noi NON lo usiamo: richiede un'installazione in più sulla macchina,
  mentre python3 ce l'hanno tutti. Il subject III.2 ammette "pip,
  uv, pipx o qualunque altro": pip è la scelta più semplice da
  spiegare.
- COME SI LEGGE UN MAKEFILE: ogni bersaglio è "nome:" seguito dalla
  ricetta (le righe rientrate con un TAB, non spazi). Le variabili
  (NAME, CONFIG) in cima valgono per tutte le ricette. .PHONY =
  "questi nomi sono comandi, non file". all: lint-strict = il
  bersaglio di default: bare make fa i controlli severi (all sta in
  cima proprio per questo). In C: è lo stesso make dei progetti C —
  qui i bersagli non compilano, lanciano comandi Python.

### Tutti i comandi da imparare (singoli e aggregati, uno per uno)

PREPARAZIONE (una volta per macchina):

| comando | cosa fa |
|---|---|
| make env = python3 -m venv venv | crea la cucina 'venv': una cartella con una copia di Python + pip, separata dal sistema |
| make install = venv/bin/python -m pip install flake8 mypy pytest build | il corriere porta i 4 STRUMENTI nella cucina (li scarica da PyPI e li mette in site-packages) |

LAVORO QUOTIDIANO:

| comando | cosa fa |
|---|---|
| make run = venv/bin/python a_maze_ing.py config.txt | genera maze.txt e apre il display interattivo (1 rigenera, 2 percorso, 3 colori, q esce) |
| make debug = venv/bin/python -m pdb a_maze_ing.py config.txt | esegue il programma dentro pdb, il debugger passo-passo (come gdb) |
| make test = venv/bin/python -m pytest tests/ -v | il vigile esegue i 22 test e dà il verdetto |
| make lint = venv/bin/python -m flake8 . POI venv/bin/python -m mypy . coi flag del subject | i controlli di stile (79 colonne ecc.) e di tipo (type hints), richiesti dal subject III.2 |
| make lint-strict = gli stessi due, ma con mypy . --strict | la versione più severa dei controlli |
| make build = venv/bin/python -m build | l'officina legge pyproject.toml e costruisce la scatola in dist/ |
| make wheel = build + cp dist/mazegen-1.0.0-py3-none-any.whl . | costruisce E copia la scatola pronta alla radice (quella committata, cap. VI) |
| make clean = rm -rf __pycache__ .mypy_cache .pytest_cache build dist *.egg-info | butta cache e artefatti (NON tocca la cucina) |

SENZA SCORCIATOIA (locale, mai pushato):

| comando | cosa fa |
|---|---|
| python3 output_validator.py maze.txt | il validatore del subject controlla la coerenza dei muri nel file appena generato |

SEZIONE 6 (solo a mano, davanti all'evaluator):

| comando | cosa fa |
|---|---|
| python3 -m venv /tmp/venv1 | crea la FABBRICA (usa-e-getta) |
| /tmp/venv1/bin/pip install build | porta lo strumento build nella fabbrica |
| /tmp/venv1/bin/python -m build | RICOSTRUISCE la scatola dalle nostre sorgenti (va lanciato DENTRO la cartella del progetto) |
| python3 -m venv /tmp/venv2 | crea il CLIENTE (usa-e-getta) |
| /tmp/venv2/bin/pip install dist/mazegen-1.0.0-py3-none-any.whl | il cliente riceve la scatola |
| cd /tmp && /tmp/venv2/bin/python -c "from mazegen import MazeGenerator; print('funziona')" | la prova finale FUORI dal progetto: il modulo installato funziona ovunque |

### Le due sequenze da zero (i comandi ORIGINALI che make esegue)

CASE 1 — STUDIO, nella cartella di lavoro, da zero:

```
cd "~/Desktop/python repo/Common_Core_2/python/AMAZEING"
python3 -m venv venv                       # = make env (una volta sola)
venv/bin/python -m pip install flake8 mypy pytest build
                                           # = make install (una volta sola)
# poi, ogni giorno:
venv/bin/python a_maze_ing.py config.txt   # = make run
venv/bin/python -m pytest tests/ -v        # = make test
venv/bin/python -m flake8 .                # = make lint (prima meta')
venv/bin/python -m mypy . --strict         # = make lint-strict (seconda meta')
venv/bin/python -m build                   # = make build (la scatola in dist/)
cp dist/mazegen-1.0.0-py3-none-any.whl .   # = make wheel (la scatola pronta)
rm -rf __pycache__ .mypy_cache .pytest_cache build dist *.egg-info
                                           # = make clean
python3 output_validator.py maze.txt       # il validatore (locale, mai pushato)
```

CASE 2 — EVALUATION, in ordine esatto (dopo aver clonato la repo o
copiato la cartella di consegna sulla macchina della scuola, ed essere
ENTRATI nella cartella):

```
python3 -m venv venv                       # = make env
venv/bin/python -m pip install flake8 mypy pytest build   # = make install

# sezioni 1-5: si mostra il progetto e il programma
make lint        # i controlli del subject (flake8 . + mypy . coi flag)
make test        # i 22 test (se chiesto)
make run         # labirinto + menu: 1 rigenera, 2 percorso, 3 colori, q esce
#   l'evaluator edita config.txt e ripete make run (errori e casi speciali)

# sezione 6: il modulo riusabile, i 6 comandi A MANO
python3 -m venv /tmp/venv1
/tmp/venv1/bin/pip install build
#   RIENTRARE nella cartella del progetto (dove sta pyproject.toml):
/tmp/venv1/bin/python -m build
python3 -m venv /tmp/venv2
/tmp/venv2/bin/pip install dist/mazegen-1.0.0-py3-none-any.whl
#   USCIRE dalla cartella: la prova che il modulo funziona ovunque:
cd /tmp
/tmp/venv2/bin/python -c "from mazegen import MazeGenerator; print('funziona')"
```

- Nota 1: il build della sezione 6 va lanciato DENTRO la cartella del
  progetto (setuptools cerca lì pyproject.toml); la prova finale va
  fatta FUORI (per dimostrare che si usa il modulo INSTALLATO, non il
  file locale).
- Nota 2: i venv di /tmp sono usa-e-getta: a fine sezione 6 si
  buttano via con rm -rf /tmp/venv1 /tmp/venv2.
- Nota 3: PERCHÉ la sezione 6 si fa a MANO e non con le shortcut:
  le shortcut (make lint/test/run) si usano eccome, per le sezioni
  1-5. Ma nella sezione 6 i comandi SONO la dimostrazione: la scala
  vuole vedere ogni passo (creo la cucina, ricostruisco la scatola,
  la installo) — digitandoli uno a uno è tutto visibile. In più i
  venv della sezione 6 stanno FUORI dal progetto (usa-e-getta),
  mentre i bersagli del Makefile puntano alla cucina del progetto:
  per cose una-tantum non si scrivono scorciatoie. Frase pronta:
  "Le shortcut le uso per il lavoro quotidiano; nella sezione 6 i
  comandi a mano sono voluti, così ogni passo è visibile." 

### Perché le cose si scrivono così (due lint, -m, venv/bin, cp, /tmp)

- PERCHÉ DUE LINT: il subject III.2 OBBLIGA la regola lint con quei
  flag ESATTI (--warn-return-any --warn-unused-ignores
  --ignore-missing-imports --disallow-untyped-defs
  --check-untyped-defs) e raccomanda lint-strict (facoltativa) con
  --strict. --strict = tutti i flag insieme, controllo PIÙ severo.
  Noi li teniamo tutti e due: make lint = esattamente ciò che chiede
  il subject; make lint-strict = la versione severa per noi.
- PERCHÉ python3 -m flake8 e non flake8 da solo: -m = "chiedi A
  questo python di eseguire il MODULO flake8". Senza -m il sistema
  cercherebbe un programma di nome flake8 nel PATH — che senza venv
  attivato punta al Python di sistema, dove flake8 non c'è (o è
  un'altra versione). Con python3 -m usi SEMPRE il tool del python
  che hai scelto tu.
- PERCHÉ venv/bin/python: venv/bin/ è la cartella degli attrezzi
  DELLA CUCINA (dentro ci sono python, pip e i tool installati).
  Scrivere venv/bin/python = "usa il python della cucina" anche
  senza attivarla. È questo che rende il Makefile autonomo:
  funziona appena fatto make env, senza source/activate.
- PERCHÉ cp dist/mazegen-...whl . : dist/ è la cartella dove
  l'officina (build) lascia la scatola; il punto (.) è la cartella
  in cui sei, la RADICE del progetto. Il cap. VI vuole il pacchetto
  alla radice della repo → la copia fa esattamente quello (make
  wheel = build + cp).
- COSA SONO /tmp/venv1 e /tmp/venv2: /tmp è la cartella TEMPORANEA
  del sistema (il suo contenuto si può buttare quando si vuole).
  venv1 e venv2 sono due cucine usa-e-getta create DURANTE la
  sezione 6: la prima per RICOSTRUIRE la scatola, la seconda per
  INSTALLARLA e provarla. A fine sezione: rm -rf /tmp/venv1
  /tmp/venv2.
- IL (VENV) NEL PROMPT: appare SOLO se si attiva la cucina a mano
  con source venv/bin/activate: il terminale mostra "(venv) $" e da
  lì i comandi nudi (python3, flake8, pytest...) trovano da soli le
  versioni della cucina. Attivare = mettere venv/bin in testa al
  PATH: è una scorciatoia, non un obbligo. Noi NON attiviamo mai: il
  Makefile chiama sempre venv/bin/python esplicitamente, quindi il
  (venv) non appare — ed è voluto. Risposta pronta: "Non serve
  attivarlo: il Makefile punta sempre a venv/bin/python, funziona
  anche senza activation."
- I COMANDI DIVISI PER CASA:
  - FUORI dalla cucina (python DI SISTEMA o operazioni sui file):
    python3 -m venv venv (il sistema CREA la cucina), make (lancia
    le ricette), cp dist/...whl . (copia la scatola), rm -rf
    (pulizia), cd e git.
  - DENTRO la cucina (partono con venv/bin/python): pip install
    (porta i tool), flake8, mypy, pytest, build, e l'esecuzione del
    programma (a_maze_ing.py).
- DOVE STARE IN PIEDI: tutti i make si lanciano DENTRO la cartella
  del progetto — e "cartella clonata" e "cartella di lavoro" sono la
  STESSA cosa: sulla scuola si clona il repo e quella diventa la
  cartella di lavoro (la cartella di sviluppo ha solo in più le
  scorie locali: output_validator.py ecc.). Nella sezione 6: la
  creazione dei venv può avvenire ovunque; il build va nella
  cartella del progetto (cerca pyproject.toml); l'install della
  wheel va nella cartella del progetto (cerca dist/); la prova
  finale va FUORI.

L'ALBERO DELLE CARTELLE (dove sei e cosa stai facendo):

```
~/Desktop/
├── python repo/                          ← cartella di PIANIFICAZIONE (doc)
│   └── Common_Core_2/
│       └── python/AMAZEING/              ← LA CARTELLA DI STUDIO
│           ├── a_maze_ing.py ... config.txt   (i file del programma)
│           ├── tests/                    ← i 3 file di test
│           ├── venv/                     ← LA CUCINA (fatta con make env)
│           │   ├── bin/                  ← gli attrezzi: python, pip
│           │   └── lib/python3.14/site-packages/  ← qui vivono i tool
│           ├── dist/                     ← l'uscita dell'officina (build)
│           │   └── mazegen-1.0.0-py3-none-any.whl
│           └── mazegen-1.0.0-py3-none-any.whl   ← copia alla RADICE (make wheel)
├── consegna_amazeing/                    ← la consegna PULITA (i 14 pezzi)
└── amazeing_repo/                        ← mirror git degli appunti

/tmp/                                     ← cartella temporanea del sistema
├── venv1/                                ← cucina 1 della sezione 6
│   └── bin/python                        ← con dentro lo strumento build
└── venv2/                                ← cucina 2 della sezione 6
    ├── bin/python
    └── lib/python3.14/site-packages/mazegen.py  ← i biscotti installati
```

## 4.6 Le trappole della difesa

- Mai crash: anche Ctrl+C è gestito (uscita 0); l'ultimo except
  Exception copre tutto. La scala dà 0 a un programma che termina in
  modo inatteso.
- Non modificare nessun file se non config.txt.
- TRAPPOLA SCOVATA ALLA PROVA GENERALE: se l'evaluator crea un venv
  DENTRO la cartella (python3 -m venv venv), `flake8 .` lo scansiona
  e fallisce con migliaia di errori di site-packages. Risolta: il
  .flake8 esclude sia .venv che venv e il pyproject [tool.mypy]
  esclude "venv". Se l'evaluator usa un altro nome... fa parte delle
  sue scelte: i due nomi canonici sono coperti.
- La scala premia chi spiega: usa le metafore (talpa, piccone,
  fuoco) e le tracce riga per riga degli appunti.
- Bonus (sezione 7): facoltativi, non ne abbiamo — non prometterne.

---

# 5. Glossario

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
