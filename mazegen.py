
"""Generatore di labirinti riusabile (progetto AMAZEING, 42).

Modulo autonomo: contiene la classe MazeGenerator, che genera un
labirinto casuale ma riproducibile e ne trova il percorso piu' breve.

Esempio di utilizzo:

    from mazegen import MazeGenerator

    gen = MazeGenerator(width=20, height=15, seed=42)
    gen.generate(perfect=True, entry=(0, 0), exit=(19, 14))
    maze = gen.grid       # grid[y][x] = 0-15, bit 0-3 = muri N/E/S/W
    path = gen.solve()    # percorso piu' breve come lista di celle (x, y)
"""

import random
from collections import deque

N: int = 1   # moneta del muro NORD
E: int = 2   # moneta del muro EST
S: int = 4   # moneta del muro SUD
W: int = 8   # moneta del muro OVEST

# Disegno della cifra "4" (3 colonne x 5 righe):
#   # . #
#   # . #
#   # # #
#   . . #
#   . . #
FOUR: list[tuple[int, int]] = [
    (0, 0), (2, 0),
    (0, 1), (2, 1),
    (0, 2), (1, 2), (2, 2),
    (2, 3), (2, 4)
]

# Disegno della cifra "2" (3 colonne x 5 righe): lati di 3 caselle che
# si incrociano a 90 gradi, tutti gli spigoli visibili.
#   # # #
#   . . #
#   # # #
#   # . .
#   # # #
TWO: list[tuple[int, int]] = [
    (0, 0), (1, 0), (2, 0),
    (2, 1),
    (0, 2), (1, 2), (2, 2),
    (0, 3), (0, 4), (1, 4),
    (2, 4),
]


class MazeGenerator:
    """Genera labirinti casuali riproducibili e ne trova il percorso.

    Attributes:
        width: larghezza del labirinto in celle.
        height: altezza del labirinto in celle.
        rng: generatore di numeri casuali (parte dal seed).
        grid: griglia del labirinto, grid[y][x] = 0-15
            (bit 0-3 = muri N/E/S/W).
        forty_two: celle del pattern "42" (vuota se assente).
        has_42: True se il pattern "42" e' presente.
        entry: coordinate (x, y) dell'entrata.
        exit: coordinate (x, y) dell'uscita.
        perfect: True se l'ultimo labirinto generato e' perfetto.
    """

    def __init__(self, width: int, height: int,
                 seed: int | None = None) -> None:
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.grid: list[list[int]] = []
        self.forty_two: list[tuple[int, int]] = []
        self.has_42 = False
        self.entry = (0, 0)
        self.exit = (width - 1, height - 1)
        self.perfect = True

    def _in_bounds(self, x: int, y: int) -> bool:
        """True se (x, y) sta dentro la griglia."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return True

    def _has_wall(self, x: int, y: int, mask: int) -> bool:
        """True se la cella (x, y) ha la moneta 'mask' (muro chiuso)."""
        return (self.grid[y][x] & mask) != 0

    def _remove_wall(self, x: int, y: int, mask: int) -> None:
        """Toglie la moneta 'mask' dalla cella (x, y): il muro si apre."""
        self.grid[y][x] = self.grid[y][x] - mask

    def _add_wall(self, x: int, y: int, mask: int) -> None:
        """Rimette la moneta 'mask' nella cella (x, y): il muro si chiude."""
        self.grid[y][x] = self.grid[y][x] + mask

    def generate(self, perfect: bool = True, entry: tuple[int, int] = (0, 0),
                 exit: tuple[int, int] | None = None,
                 with_42: bool = True) -> None:
        """Genera un nuovo labirinto.

        Args:
            perfect: True per un labirinto perfetto (un solo percorso).
            entry: coordinate (x, y) dell'entrata.
            exit: coordinate (x, y) dell'uscita
                (None = angolo in basso a destra).
            with_42: True per disegnare il pattern "42" (se c'e' spazio).

        Raises:
            ValueError: entry o exit fuori dai bordi, o uguali tra loro.
        """
        self.perfect = perfect
        self.entry = entry
        if exit is None:
            self.exit = (self.width - 1, self.height - 1)
        else:
            self.exit = exit

        if not self._in_bounds(self.entry[0], self.entry[1]):
            raise ValueError("entry is outside the maze")
        if not self._in_bounds(self.exit[0], self.exit[1]):
            raise ValueError("exit is outside the maze")
        if self.entry == self.exit:
            raise ValueError("entry and exit must be different")

        # ogni cella nasce come scatola chiusa: N+E+S+W = 15 (le monete 1.2)
        self.grid = []
        for y in range(self.height):
            row: list[int] = []
            for x in range(self.width):
                row.append(N + E + S + W)
            self.grid.append(row)

        # il muro esterno resta COMPLETAMENTE chiuso: entry ed exit sono
        # celle marcate dentro il bordo, non aperture nel bordo
        # i tre passi nell'ordine: il 42, la talpa, poi il piccone
        self._carve_42(with_42)
        self._carve_maze()
        if not perfect:
            self._carve_extra_walls()

    def _carve_42(self, with_42: bool) -> None:
        """Disegna il pattern "42" come celle completamente chiuse.

        Il pattern viene piazzato al centro della griglia, ma sempre con
        almeno una riga interamente libera SOPRA le cifre: il "buco" in
        alto del 4 deve toccare celle libere, altrimenti resta sigillato
        dai mattoncini e diventa un'area isolata. Le celle dei mattoncini
        restano chiuse e vengono marcate come gia' visitate, cosi' la
        generazione non le attraversa mai e le cifre restano isole
        chiuse. Le celle vuote delle cifre invece sono normali: il
        labirinto ci scava dentro e il percorso puo' passarci. Se il
        labirinto e' troppo piccolo (sotto 9x6, perche' a 5 righe le
        cifre occuperebbero tutta l'altezza spezzando il labirinto in
        parti non collegate) o il pattern coprirebbe entry/exit, si
        salta e has_42 resta False.
        """
        self.forty_two = []
        self.has_42 = False
        if not with_42:
            return
        if self.width < 9 or self.height < 6:
            return
        start_x = (self.width - 7) // 2
        start_y = (self.height - 5) // 2
        if start_y < 1:
            start_y = 1
        pattern: list[tuple[int, int]] = []
        for dx, dy in FOUR:
            pattern.append((start_x + dx, start_y + dy))
        for dx, dy in TWO:
            pattern.append((start_x + 4 + dx, start_y + dy))
        for cell in pattern:
            if cell == self.entry or cell == self.exit:
                return
        self.forty_two = pattern
        self.has_42 = True

    def _carve_maze(self) -> None:
        """La TALPA scava il labirinto perfetto (recursive backtracker).

        Parte dall'entrata e apre i muri verso i vicini non ancora
        scavati, togliendo la moneta da ENTRAMBI i lati. Quando non ha
        piu' porte aperte torna indietro con la CORDA (lo stack), e
        finisce quando la corda e' vuota: tutte le celle sono scavate.
        """
        # il foglio dei segni "gia' scavato", tutto falso
        visited: list[list[bool]] = []
        for y in range(self.height):
            row: list[bool] = []
            for x in range(self.width):
                row.append(False)
            visited.append(row)

        # i mattoncini del 42 sono cemento: la talpa non ci scava mai
        for x, y in self.forty_two:
            visited[y][x] = True

        # la CORDA parte dall'entrata: la talpa e' li' e l'ha gia' scavata
        stack: list[tuple[int, int]] = [self.entry]
        visited[self.entry[1]][self.entry[0]] = True

        while len(stack) > 0:
            # la cima della corda: la talpa e' qui, senza togliere nulla
            x, y = stack[len(stack) - 1]
            neighbors = self._unvisited_neighbors(x, y, visited)
            if len(neighbors) == 0:
                # nessuna porta aperta: la talpa risale la corda
                stack.pop()
            else:
                # il DADO sceglie una delle porte aperte
                nx, ny, mask_here, mask_there = self.rng.choice(neighbors)
                # il muro si apre dai due lati: le due monete speculari
                self._remove_wall(x, y, mask_here)
                self._remove_wall(nx, ny, mask_there)
                # il vicino e' scavato: la talpa si sposta, la corda cresce
                visited[ny][nx] = True
                stack.append((nx, ny))

    def _unvisited_neighbors(
            self, x: int, y: int, visited: list[list[bool]]
    ) -> list[tuple[int, int, int, int]]:
        """Le 4 porte della stanza dove sta la talpa, in ordine N, E, S, W.

        Per ogni porta aperta (il vicino esiste e non e' ancora scavato)
        restituisce il vicino con le due monete speculari del muro da
        aprire: la mia e la sua. Il bordo si controlla PRIMA, cosi' la
        griglia non viene mai letta fuori dai bordi.
        """
        neighbors: list[tuple[int, int, int, int]] = []
        # porta NORD: esiste la cella sopra? e non e' ancora scavata?
        if y > 0 and not visited[y - 1][x]:
            neighbors.append((x, y - 1, N, S))
        # porta EST: esiste la cella a destra? e non e' ancora scavata?
        if x < self.width - 1 and not visited[y][x + 1]:
            neighbors.append((x + 1, y, E, W))
        # porta SUD: esiste la cella sotto? e non e' ancora scavata?
        if y < self.height - 1 and not visited[y + 1][x]:
            neighbors.append((x, y + 1, S, N))
        # porta OVEST: esiste la cella a sinistra? e non e' ancora scavata?
        if x > 0 and not visited[y][x - 1]:
            neighbors.append((x - 1, y, W, E))
        return neighbors

    def _carve_extra_walls(self) -> None:
        """Il PICCONE: apre scorciatoie a caso (labirinto non perfetto).

        Venti colpi, ognuno con tre dadi (colonna, riga, direzione). Il
        colpo a vuoto (bordo, mattoncino del 42 o muro gia' aperto) non
        conta, e se il colpo crea una piazzetta 3x3 viene annullato:
        i corridoi restano larghi al massimo 2 celle.
        """
        # i 20 colpi di piccone
        for _ in range(20):
            # tre dadi: colonna, riga e direzione del colpo
            x = self.rng.randrange(self.width)
            y = self.rng.randrange(self.height)
            mask = self.rng.choice([N, E, S, W])
            nx = x
            ny = y
            mask_here = mask
            mask_there = mask
            if mask == N and y > 0:
                ny = y - 1
                mask_there = S
            elif mask == E and x < self.width - 1:
                nx = x + 1
                mask_there = W
            elif mask == S and y < self.height - 1:
                ny = y + 1
                mask_there = N
            elif mask == W and x > 0:
                nx = x - 1
                mask_there = E
            else:
                # colpo a vuoto: si e' mirato al bordo esterno
                continue
            # mai aprire i mattoncini del 42: sono isole chiuse
            if (x, y) in self.forty_two or (nx, ny) in self.forty_two:
                continue
            # il muro e' gia' aperto: colpo a vuoto
            if not self._has_wall(x, y, mask_here):
                continue
            # il colpo apre il muro dai due lati...
            self._remove_wall(x, y, mask_here)
            self._remove_wall(nx, ny, mask_there)
            # ...ma se nasce una piazzetta 3x3 si richiude: colpo annullato
            if self._has_3x3_open():
                self._add_wall(x, y, mask_here)
                self._add_wall(nx, ny, mask_there)

    def _has_3x3_open(self) -> bool:
        """True se esiste una piazzetta 3x3 tutta aperta.

        Vietata: i corridoi devono restare larghi al massimo 2 celle.
        """
        for y in range(self.height - 2):
            for x in range(self.width - 2):
                if self._window_3x3_open(x, y):
                    return True
        return False

    def _window_3x3_open(self, x: int, y: int) -> bool:
        """True se la finestra 3x3 con angolo in alto a sinistra
        (x, y) e' tutta aperta.
        """
        for wy in range(y, y + 2):
            for wx in range(x, x + 3):
                if self._has_wall(wx, wy, S):
                    return False
        for wy in range(y, y + 3):
            for wx in range(x, x + 2):
                if self._has_wall(wx, wy, E):
                    return False
        return True

    def solve(self) -> list[tuple[int, int]]:
        """Il FUOCO sull'erba secca (BFS): trova il percorso piu' breve.

        Ogni cella prende fuoco al suo minuto minimo possibile: la coda
        si serve dal davanti (FIFO). Quando l'uscita brucia, risalendo
        la catena di "chi ha acceso chi" si ottiene il percorso piu'
        corto, o la lista vuota se l'uscita non brucia mai.
        """
        # la LISTA D'ATTESA delle celle da accendere (FIFO: primo arrivato,
        # primo servito)
        queue: deque[tuple[int, int]] = deque()
        queue.append(self.entry)
        # il registro di "chi ha acceso chi": l'entrata non brucia da nessuno
        came_from: dict[tuple[int, int], tuple[int, int] | None] = {}
        came_from[self.entry] = None

        while len(queue) > 0:
            # il primo della fila: questa cella prende fuoco adesso
            x, y = queue.popleft()
            # l'uscita ha preso fuoco: tutti i minuti sono al minimo
            if (x, y) == self.exit:
                break
            # il fuoco prova le 4 direzioni, solo dove il muro e' aperto
            if y > 0 and not self._has_wall(x, y, N):
                self._add_neighbor(queue, came_from, x, y - 1, x, y)
            if x < self.width - 1 and not self._has_wall(x, y, E):
                self._add_neighbor(queue, came_from, x + 1, y, x, y)
            if y < self.height - 1 and not self._has_wall(x, y, S):
                self._add_neighbor(queue, came_from, x, y + 1, x, y)
            if x > 0 and not self._has_wall(x, y, W):
                self._add_neighbor(queue, came_from, x - 1, y, x, y)

        # l'uscita non ha mai preso fuoco: nessun percorso
        if self.exit not in came_from:
            return []

        # la RISALITA: dall'uscita si segue "chi ha acceso chi" fino
        # all'entrata (che non e' stata accesa da nessuno)...
        path: list[tuple[int, int]] = []
        cell: tuple[int, int] | None = self.exit
        while cell is not None:
            path.append(cell)
            cell = came_from[cell]
        # ...poi si capovolge: entrata -> uscita
        path.reverse()
        return path

    def _add_neighbor(self, queue: deque[tuple[int, int]],
                      came_from: dict[tuple[int, int], tuple[int, int] | None],
                      nx: int, ny: int, x: int, y: int) -> None:
        """Accende il vicino (nx, ny) se non ha mai preso fuoco.

        Segna chi l'ha acceso (came_from) e lo mette in fondo alla coda:
        brucera' al minuto successivo.
        """
        if (nx, ny) not in came_from:
            came_from[(nx, ny)] = (x, y)
            queue.append((nx, ny))
