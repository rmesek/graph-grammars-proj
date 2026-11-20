# Newest Vertex Bisection jako gramatyka cp-grafowa

Projekt z Gramatyk Grafowych: adaptacja siatki trójkątnej metodą *newest vertex bisection*,
zamodelowana produkcjami P0–P4 na grafach kompozycyjnych (cp-grafach).
Materiały: [NewestVertex.pdf](docs/NewestVertex.pdf) (specyfikacja),
[Lab_CP_grafyS.pdf](docs/Lab_CP_grafyS.pdf) (teoria cp-grafów),
[30 Years of Newest Vertex Bisection.pdf](docs/30%20Years%20of%20Newest%20Vertex%20Bisection.pdf)
(publikacja).

## Instalacja i uruchomienie

Wymagany [uv](https://docs.astral.sh/uv/).

```bash
uv sync                          # środowisko + zależności
uv run nvb draw -n 2             # rysuje siatkę startową -> out/mesh.png
uv run nvb draw -n 8             # duża siatka: bez cp-grafu (--graph wymusza graf)
uv run nvb list                  # zarejestrowane produkcje
uv run nvb apply P0 --at 3       # stosuje produkcje w trójkącie T3 -> out/apply.png
uv run pytest --viz              # testy + rysunki przed/po w out/tests/
uv run ruff format . && uv run ruff check .
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
- P3, P4: dzieci według `graph.bisect`, newest vertex jest ich peakiem, `R=0`, `BR=0`; siatka
  bez wiszących węzłów i z tym samym polem

Jeśli kontrakt wydaje się sprzeczny ze slajdami, zgłoś to w Issue zamiast zmieniać test w PR
produkcji.

## Model cp-grafu

Trójkąt to węzeł `T` (`R`, `P1..P3`) z trzema węzłami-bondami (`RE`, `B`, `BR`) w `networkx`;
bond `i` to bok naprzeciw `Pi`, wspólny bok to krawędź bond–bond. Produkcje dziedziczą po
`Production` (`src/nvb/productions/base.py`). Rysunek: wypełnienie = `R`, czerwony bok = `RE`,
przerywany = `BR`, gruby = `B`. Siatki powyżej 64 trójkątów rysowane są bez cp-grafu
(etykiet, bondów, krawędzi), jak na slajdzie 27; `--graph/--no-graph` wymusza tryb.

## Workflow zespołu

1. Przypisz się do Issue, utwórz gałąź `<nr>-<opis>` od aktualnego `main`, np. `3-p1`.
   PR produkcji zmienia tylko `pN.py`, `test_pN.py` i swoją sekcję `PROGRESS.md`.
2. Przed pushem: `ruff` i `pytest` zielone.
3. `gh pr create` z `Closes #<nr>`. CI działa tylko na PR; rysunki z testów są w artefakcie
   `drawings`. Gdy gałąź jest nieaktualna względem `main`: `gh pr update-branch`.
   Merge (squash) po zielonym CI.
4. Po merge'u: `git switch main && git pull --prune && git branch -D <nr>-<opis>`.
