# PROGRESS

Status, osoby i terminy: Issues i milestone'y na GitHubie. Tu tylko dziennik zmian —
każdy pisze wyłącznie we własnej sekcji (brak konfliktów przy merge'u).

## #1 Setup

- 2026-11-20 — uv/ruff/pytest, CI tylko na PR (lint → testy Ubuntu/Windows/macOS), model
  cp-grafu (networkx, bondy jako węzły), `Production` + `pattern()`, `graph.bisect`,
  wizualizacja matplotlib, CLI `nvb draw|list|apply`, Issues #1–#8, materiały w `docs/`.
- 2026-11-20 — automatyczna rejestracja produkcji (brak konfliktów przy równoległych PR),
  zasady zakresu PR, `gh pr update-branch` i sprzątanie po merge'u w README/AGENTS.
- 2026-11-20 — `viz.draw(graph=...)`: duże siatki (> 64 trójkątów) rysowane bez cp-grafu,
  czytelne adaptacje jak na slajdzie 27; `nvb draw|apply --graph/--no-graph`.

## #2 P0

- 2026-11-20 — `P0(criterion)` (domyślnie każdy trójkąt + kotwica `--at`; `contains(p)` =
  trójkąt zawierający punkt), rejestracja w CLI, `tests/test_p0.py` wg DoD — wzorzec dla
  P1–P4: oczekiwany graf budowany ręcznie i porównanie `nx.utils.graphs_equal`.

## #3 P1

## #4 P2

## #5 P3

## #6 P4

## #7 Aplikacja (RefineTriangle)

## #8 Notebook
