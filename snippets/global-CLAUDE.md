## AI Commit Standard
- Every commit follows `~/.ai-commit-standard/AI-COMMIT-STANDARD.md`. A `commit-msg` hook at
  `~/.ai-commit-standard/hooks/` enforces it in every repo via global `core.hooksPath`.
- Shape: `<type>: <Imperative sentence naming the user-visible outcome>`, blank
  line, body explaining what was wrong before and why this approach, blank line,
  trailers. Scopes only where the repo has a checked-in `.commit-scopes`
  registry listing them (`feat(api): ...`); otherwise none. Agents
  manage the registry themselves: a new scope only for a lasting product
  module with no near-synonym listed, registered in the same commit that
  first uses it; one-off features are not modules.
- Type is a **partition** (exactly one), chosen by walking this ladder and
  stopping at the first yes: `wip` (incomplete/unreviewed, must not merge) →
  `revert` (undoes an earlier commit) → `release` (only ships what exists) →
  `feat` (user can now do something new) → `fix` (something already possible
  was broken, now correct) → `perf` (same behaviour, measurably faster — no
  number, no perf) → `refactor` (production code changed, behaviour identical,
  incl. formatting) → `docs` (only prose) → `test` (only tests/fixtures) →
  `ci` (only pipeline automation) → `build` (project files, packaging, signing,
  dependencies) → `chore` (residue; if you land here, re-walk the ladder once).
  Classify by the user-visible delta, not by author intent. Mixed maintenance
  commits land in `chore` — split them if you want the signal.
- Trailers are **orthogonal facts**, any number: `Tests:` / `Evidence:` /
  `Verified:` (the command actually run and its real output — **required on
  `feat`, `fix`, and `perf`**), `Closes: #N`, `Refs: #N`, `Breaking:`,
  `Security:`, `Co-Authored-By:`, `Fixes: <sha>` (commit that introduced the
  bug, when known), `Reviewed-by:`, `Reverts: <sha>` (required on `revert`).
- History analytics: `~/.ai-commit-standard/scripts/commit-stats.py REPO...` (coverage,
  per-type counts, evidence coverage, chore share; `--weekly` for trends).
- Merge commits are not typed: keep git's generated message; the hook accepts
  it only during a real merge (MERGE_HEAD), so a subject merely spelled like
  `Merge ...` gets rejected — give ordinary work a type instead.
- Never reach for `--no-verify` to get past the hook. Fix the message.
