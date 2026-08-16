---
name: ai-commit-standard
description: Enforce and explain AI Commit Standard, including its deterministic commit type ladder, evidence trailers, registered scopes, Git hook, CI gate, and history analytics. Use when creating or reviewing commits in AI-assisted or vibe coding projects, selecting feat/fix/refactor and related types, diagnosing a rejected commit, installing commit enforcement, or studying Git history quality.
---

# AI Commit Standard

Read `AI-COMMIT-STANDARD.md` at the repository root before changing the
standard or answering detailed policy questions.

## Write a commit

1. Inspect the complete staged and unstaged diff before composing the message.
2. Confirm the changes form one coherent commit. Split unrelated outcomes.
3. Walk the ladder top-to-bottom and stop at the first match:

   `wip → revert → release → feat → fix → perf → refactor → docs → test → ci → build → chore`

4. Write an imperative, capitalised subject naming the user-visible outcome.
5. For `feat` and `fix`, explain what was wrong or impossible before and why
   this approach was selected.
6. For `feat`, `fix`, and `perf`, run relevant verification and record the real
   result in `Tests:`, `Evidence:`, or `Verified:`. Never invent evidence.
7. Use a scope only when `.commit-scopes` exists and lists that lasting product
   module. Register a genuinely new module in the same commit that first uses
   it; do not create scopes for one-off features.

```text
<type>: <Imperative sentence naming the user-visible outcome>

<What was wrong before and why this approach>

Tests: <command actually run> -> <real result>
```

## Classify consistently

| Type | First matching question |
|---|---|
| `wip` | Is this knowingly incomplete or unreviewed? |
| `revert` | Does this undo an earlier commit? |
| `release` | Does this only ship what already exists? |
| `feat` | Can the user now do something previously impossible? |
| `fix` | Was an existing capability broken and is it now correct? |
| `perf` | Is behaviour identical but measurably faster or cheaper? |
| `refactor` | Did production code change with identical behaviour? |
| `docs` | Did only prose change? |
| `test` | Did only tests or fixtures change? |
| `ci` | Did only pipeline automation change? |
| `build` | Did only dependencies, packaging, signing, or project files change? |
| `chore` | Does the residue fit none of the above? Re-walk once. |

Classify by what changed for the user, not by the activity performed. A code
rewrite that preserves behaviour is `refactor`; a one-line change that unlocks
a new capability is `feat`. Do not use `perf` without a measurement.

## Operate the toolkit

- Install: `./install.sh`
- Verify installed artifacts and gate behaviour: `./install.sh check`
- Disable in one repository: `git config commitformat.enabled false`
- Re-enable: `~/.ai-commit-standard/scripts/install-ai-commit-standard.sh enable`
- Analyze history: `python3 ~/.ai-commit-standard/scripts/commit-stats.py --weekly --gaps REPO`

When the hook rejects a message, fix the named rule. Do not suggest
`--no-verify` as a workaround.
