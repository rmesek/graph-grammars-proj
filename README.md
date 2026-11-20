# Newest Vertex Bisection jako gramatyka cp-grafowa

Projekt z Gramatyk Grafowych: adaptacja siatki trójkątnej metodą *newest vertex bisection*,
zamodelowana produkcjami P0–P4 na grafach kompozycyjnych (cp-grafach).
Materiały: [NewestVertex.pdf](docs/NewestVertex.pdf) (specyfikacja),
[Lab_CP_grafyS.pdf](docs/Lab_CP_grafyS.pdf) (teoria cp-grafów),
[30 Years of Newest Vertex Bisection.pdf](docs/30%20Years%20of%20Newest%20Vertex%20Bisection.pdf)
(publikacja).

## Instalacja i uruchomienie

Wymagany tylko [uv](https://docs.astral.sh/uv/) (Python 3.13 pobiera się automatycznie przy `uv sync`).

```bash
uv sync                                        # środowisko + zależności
uv run nvb draw -n 2                           # siatka startowa -> out/mesh.png
uv run nvb draw -n 8 -o out/mesh-big.png       # duża siatka: bez cp-grafu (--graph wymusza)
uv run nvb list                                # zarejestrowane produkcje
uv run nvb apply P0 --at 3                     # stosuje produkcje w T3 -> out/apply.png
uv run pytest --viz                            # testy + rysunki przed/po w out/tests/ (pominięte = brakujące P1–P4)
uv run ruff format .
uv run ruff check --fix .
```

## Wymagania

Zgodnie ze [specyfikacją](docs/NewestVertex.pdf) (slajdy 29–35): szablon bazowy produkcji
oraz produkcje P0–P4, każda z testami jednostkowymi i wizualizacją grafu, w której współrzędne
pokazują, który węzeł odpowiada któremu trójkątowi.

| Issue | Produkcja | LHS | Predykat | Efekt |
|---|---|---|---|---|
| #2 | P0 | 1 trójkąt | kryterium ∧ `R==0` | `R=1` |
| #3 | P1 | 1 trójkąt | `R==1` ∧ `BR1..3==0` ∧ `RE1==1` | `BR1=1` |
| #4 | P2 | 2 trójkąty (6–3) | `BR6==1` ∧ `BR1..3==0` ∧ `RE1==1` | `BR1=1` u sąsiada |
| #5 | P3 | 2 trójkąty (6–1) | `BR6==RE6==1` ∧ `BR1..3==0` ∧ `RE1==1` | bisekcja obu → 4 trójkąty |
| #6 | P4 | 1 trójkąt | `BR1==B1==RE1==1` | bisekcja → 2 trójkąty |

### Definition of Done produkcji

Na podstawie kryteriów oceny testy przygotowują i sprawdzają:

- [ ] graf izomorficzny z LHS → produkcja się wykonuje
- [ ] ten sam graf ze złą wartością atrybutu → produkcja się **nie** wykonuje
- [ ] LHS bez wymaganej krawędzi (produkcje 2-trójkątne) → **nie** pasuje
- [ ] LHS jako podgraf większego grafu → działa, reszta grafu nieuszkodzona, osadzenie poprawnie przepięte
- [ ] RHS kompletny: węzły, bondy, krawędzie, etykiety, atrybuty
- [ ] poprawne współrzędne nowych wierzchołków
- [ ] rysunek przed/po pokazuje wszystkie węzły, bondy, krawędzie i atrybuty

### Kontrakt produkcji

Wspólny `tests/test_contract.py` opisuje, co produkcja przekazuje kolejnemu etapowi. Sprawdza
każdą produkcję osobno na ręcznie przygotowanym stanie, więc nie zależy od produkcji innych
osób; testy produkcji jeszcze niezarejestrowanych są pomijane.

- `pN.py` z klasą `PN(Production)`, `name = "PN"`, LHS jak w tabeli powyżej
- w każdym stanie (np. „RE oznaczona i na brzegu”) pasuje tylko właściwa produkcja, inne nie
  zmieniają grafu
- P1, P2: `BR=1` tylko na krawędzi refinacji, bez ponownego zastosowania
- P3, P4: dzieci według `graph.bisect`, newest vertex jest ich peakiem, rodzice usunięci
  (`graph.remove_triangle`), `R=0`, na nowych bokach `BR=0` (na zewnętrznych `B`/`BR` dziedziczone);
  siatka bez wiszących węzłów i z tym samym polem

Jeśli kontrakt wydaje się sprzeczny ze slajdami, zgłoś to w Issue zamiast zmieniać test w PR
produkcji.

## Model cp-grafu

Trójkąt to węzeł `T` (`R`, `P1..P3`) z trzema węzłami-bondami (`RE`, `B`, `BR`) w `networkx`;
bond `i` to bok naprzeciw `Pi`, wspólny bok to krawędź bond–bond. Rysunek: wypełnienie = `R`,
czerwony bok = `RE`, przerywany = `BR`, gruby = `B`. Siatki powyżej 64 trójkątów rysowane są
bez cp-grafu (etykiet, bondów, krawędzi), jak na slajdzie 27; `--graph/--no-graph` wymusza tryb.

### Jak napisać produkcję (`Production`)

Produkcje dziedziczą po `Production` (`src/nvb/productions/base.py`) i używają `pattern()`:

- `pattern(1)` tworzy trójkąt `0` i bondy `(0, 1)`, `(0, 2)`, `(0, 3)`;
- `pattern(2, [((0, 3), (1, 1))])` tworzy 2 trójkąty połączone krawędzią bond–bond — ze slajdów
  22 i 24 bondy `4,5,6` to `(0, 1..3)`, a `1,2,3` to `(1, 1..3)`;
- słownik `m` w `predicate(g, m)` i `transform(g, m)` mapuje węzły wzorca na węzły hosta, np.
  `g.nodes[m[0]]["R"]` albo `g.nodes[m[(0, 1)]]["RE"]`;
- numery bondów we wzorcu są swobodne (`GraphMatcher` sprawdza wszystkie permutacje), więc do
  geometrii (np. `graph.bisect`) zawsze bierz indeks z hosta: `ref = g.nodes[m[(0, 1)]]["index"]`.

Wzorzec kodu i testów: `src/nvb/productions/p0.py` i `tests/test_p0.py`. W testach P0–P2 cały
graf najprościej porównać przez `nx.utils.graphs_equal(g, expected)`, a w P3–P4 (gdzie nowe
trójkąty dostają nowe ID) przez `nx.is_isomorphic(g, expected, node_match=operator.eq)`.
Test CLI (`nvb apply`) nie jest wymagany dla P2–P4 (do uruchomienia z CLI potrzebują P1).

## Workflow zespołu

1. Przypisz się do Issue, utwórz gałąź `<nr>-<opis>` od aktualnego `main`, np. `3-p1`.
   PR produkcji zmienia tylko `pN.py`, `test_pN.py` i swoją sekcję `PROGRESS.md`.
2. Przed pushem uruchom:
   ```bash
   uv run ruff format .
   uv run ruff check --fix .
   uv run pytest
   ```
3. Wypchnij gałąź (`git push -u origin <nr>-<opis>`) i otwórz PR na GitHubie (w przeglądarce
   albo przez `gh pr create`) z `Closes #<nr>` w opisie. Rysunki z testów są w artefakcie CI
   `drawings`. Po zielonym CI kliknij **Squash and merge**.
4. Po merge'u posprzątaj lokalnie:
   ```bash
   git switch main
   git pull --prune
   git branch -D <nr>-<opis>
   ```
