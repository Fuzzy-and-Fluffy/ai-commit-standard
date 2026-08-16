## Commit messages

Read `~/.ai-commit-standard/AI-COMMIT-STANDARD.md` before committing. It is enforced by a
`commit-msg` hook in every repo, so a non-conforming message will be rejected.

Shape: `<type>: <Imperative sentence naming the user-visible outcome>`, blank
line, body, blank line, trailers. Scopes only where the repo has a checked-in
`.commit-scopes` registry listing them (`feat(api): ...`); otherwise none.
Manage the registry yourself: a new scope only for a lasting product module
with no near-synonym listed, registered in the same commit that first uses it;
one-off features are not modules.

Pick the type by walking this ladder and stopping at the first yes: `wip` →
`revert` → `release` → `feat` → `fix` → `perf` → `refactor` → `docs` → `test` →
`ci` → `build` → `chore`. Classify by what changed for the user, not by what
you were doing. `perf` requires a measurement — no number, no perf; call it
`refactor`. `chore` is the residue bucket: if you land there, re-walk the
ladder once (test/ci/build/refactor usually fits).

`feat` and `fix` require a body; `feat`, `fix`, and `perf` require a `Tests:`
or `Evidence:` trailer carrying the command actually run and its real output.
`revert` requires `Reverts: <sha>`; on a `fix`, add `Fixes: <sha>` for the
commit that introduced the bug when known. Never use `--no-verify` to get
past the hook; fix the message instead.
