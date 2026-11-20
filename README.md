# Newest Vertex Bisection jako gramatyka cp-grafowa

Projekt z Gramatyk Grafowych: adaptacja siatki trójkątnej metodą *newest vertex bisection*,
zamodelowana produkcjami P0–P4 na grafach kompozycyjnych (cp-grafach).
Materiały w [docs/](docs/): `NewestVertex.pdf` (specyfikacja), `Lab_CP_grafyS.pdf` (teoria cp-grafów),
`30 Years of Newest Vertex Bisection.pdf` (publikacja).

## Instalacja i uruchomienie

Wymagany [uv](https://docs.astral.sh/uv/) (sam pobierze Pythona 3.13).

```bash
uv sync                          # środowisko + zależności
uv run nvb draw -n 2             # rysuje siatkę startową -> out/mesh.png
uv run nvb list                  # zarejestrowane produkcje
uv run nvb apply P0 P1 --at 3    # stosuje produkcje (po #2, #3) -> out/apply.png
uv run pytest --viz              # testy + rysunki przed/po w out/tests/
uv run ruff format . && uv run ruff check .
```

## Wymagania (prezentacja, slajdy 29–35)

Część 1: szablon bazowy produkcji oraz produkcje P0–P4, każda z testami jednostkowymi
i wizualizacją grafu (współrzędne muszą pokazywać, który węzeł to który trójkąt).

| Issue | Produkcja | LHS | Predykat | Efekt |
|---|---|---|---|---|
| #2 | P0 | 1 trójkąt | kryterium ∧ `R==0` | `R=1` |
| #3 | P1 | 1 trójkąt | `R==1` ∧ `BR1..3==0` ∧ `RE1==1` | `BR1=1` |
| #4 | P2 | 2 trójkąty (6–3) | `BR6==1` ∧ `BR1..3==0` ∧ `RE1==1` | `BR1=1` u sąsiada |
| #5 | P3 | 2 trójkąty (6–1) | `BR6==RE6==1` ∧ `BR1..3==0` ∧ `RE1==1` | bisekcja obu → 4 trójkąty |
| #6 | P4 | 1 trójkąt | `BR1==B1==RE1==1` | bisekcja → 2 trójkąty |

### Definition of Done produkcji (kryteria oceny)

Testy przygotowują i sprawdzają:

- [ ] graf izomorficzny z LHS → produkcja się wykonuje
- [ ] ten sam graf ze złą wartością atrybutu → produkcja się **nie** wykonuje
- [ ] LHS bez wymaganej krawędzi (produkcje 2-trójkątne) → **nie** pasuje
- [ ] LHS jako podgraf większego grafu → działa, reszta grafu nieuszkodzona, osadzenie poprawnie przepięte
- [ ] RHS kompletny: węzły, bondy, krawędzie, etykiety, atrybuty
- [ ] poprawne współrzędne nowych wierzchołków
- [ ] rysunek przed/po pokazuje wszystkie węzły, bondy, krawędzie i atrybuty

## Model cp-grafu

Trójkąt to węzeł `T` (`R`, `P1..P3`) z trzema węzłami-bondami (`RE`, `B`, `BR`) w `networkx`;
bond `i` to bok naprzeciw `Pi`, wspólny bok to krawędź bond–bond. Produkcje dziedziczą po
`Production` (`src/nvb/productions/base.py`). Rysunek: wypełnienie = `R`, czerwony bok = `RE`,
przerywany = `BR`, gruby = `B`.

## Workflow zespołu

1. Przypisz się do Issue, utwórz gałąź `<nr>-<opis>`, np. `3-p1`.
2. Przed pushem: `ruff` i `pytest` zielone, wpis w `PROGRESS.md`.
3. `gh pr create` z `Closes #<nr>`. Merge (squash) po zielonym CI, 1 approve i aktualizacji
   gałęzi względem `main`. CI działa tylko na PR; rysunki z testów są w artefakcie `drawings`.
