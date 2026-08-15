# CLAUDE.md

## Project overview

`rics` is a personal Python toolbox: an assorted collection of small utilities that grew out of a Dropbox folder.
It has **no hard dependencies** — everything that needs one lives behind an optional extra (`cli`, `plotting`, ...).
Import optional deps inside the function that needs them, never at module scope; that is why `PLC0415` is ignored
repo-wide.

## Related repositories

Large submodules graduate to stand-alone PyPI packages once they mature, and keep depending on `rics`:

- **`id-translation`** (`../id-translation/`) — translates database IDs into human-readable labels.
- **`time-split`** (`../time-split/`) — time-based cross-validation splits.

`rics` also ships the Sphinx patches their docs builds use. **Before changing anything under
`src/rics/_internal_support/` or the docs tooling**, check the downstream effect — a break there surfaces as a
failed docs build in those repos, not here. Their `CLAUDE.md` files describe their own build constraints.

## Build and run

Run everything through `uv run`; `uv run inv --list` has the full task list. The non-obvious parts:

- **`inv mypy`, not `mypy src/rics`** — the task covers `tests/` too, and test-only type errors are otherwise
  invisible.
- **`inv tests` runs `--xdoctest` over `src/` as well as `tests/`** — a stale `>>>` example in a docstring fails
  the suite.
- **`inv docs` builds with `-W`**, and RTD sets `fail_on_warning: true`. Warnings are errors.

`tests/jupyter/test_cli.py::test_jupyter[poetry]` errors when poetry isn't installed. That is environmental noise,
not a regression.

## Docs build

RTD pins **Python 3.14** (`.readthedocs.yml`), and the build only works there: `_internal_support/` monkeypatches
`Autosummary.run` with a `functools.partial`, which became a method descriptor in 3.14. Under 3.11-3.13 the build
dies on a missing `self` argument, masking the real Sphinx warnings. Reproduce CI failures under 3.14 or not at all.

`nitpicky = True` makes an unresolved xref a hard error. A type alias used in a public signature must live in a
*documented* module (e.g. `performance/plot_types.py`, `types.py`), not a private `_util.py`.

## Conventions

Ruff enforces the mechanical rules (Google docstrings, PEP 604 unions, import order, `TYPE_CHECKING` guards) — run
`inv lint` rather than matching style by eye. Beyond that, `rics.performance` leans on generics and `TypeVarTuple`;
match the existing variadic signatures when extending it.

## Docs and comments

- **Write for the reader, not the author:** state the *why* and any non-obvious *what*; omit whatever the code
  already shows. A comment restating the line below it is noise.
- **No changelogs in prose:** docstrings describe current behavior, not what changed or what it used to be.
  `CHANGELOG.md` entries state the user-visible effect, not the mechanism behind it.
- **Keep guarantees honest:** if a docstring promises a property (memory, ordering, complexity), it must hold for
  every documented path — weaken the wording or fix the code.

## Commits

- **Group by area of concern:** one commit per concern; keep unrelated changes apart.
- **Refine with `fixup!`, don't rewrite:** when a later change reworks an earlier commit, record it
  as a `fixup!` commit (`git commit --fixup=<sha>`) instead of amending the original.
- **Never rebase on your own:** don't run the autosquash — the unsquashed history is useful during
  development. Rebase only when explicitly instructed.
- **Isolate disposable notes:** keep scratch/working notes (e.g. a `notes/` folder or `claude-todos.txt` file)
  in their own standalone commits, separate from real code/docs, so they can be dropped later.
- **Write lean messages:** state the *why* and any non-obvious *what*; omit whatever the diff shows.
  Prefer a single-line message when the subject already conveys the why. No mechanical consequences
  (renames, updated references, call-site fixups), and no "verified"/"tests pass"/"build clean" lines.
