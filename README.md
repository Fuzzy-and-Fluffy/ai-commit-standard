# AI Commit Standard

A practical, enforceable and reusable commit standard for
AI-assisted and vibe coding projects.

AI coding makes changes faster than people can explain, review, or rediscover
them. AI Commit Standard turns Git history into a durable engineering record:
one decidable type, the reason behind the change, and real verification where
it matters.

```text
fix: Stop duplicate refreshes after reconnecting

Reconnects registered the same observer twice, so one event triggered two
network requests. Keep a single observer owned by the session lifecycle.

Tests: npm test -> 48 passed
Fixes: a13c92e
```

## What is different

- **Deterministic classification.** Walk one ordered ladder and stop at the
  first match: `wip → revert → release → feat → fix → perf → refactor → docs →
  test → ci → build → chore`.
- **Evidence is part of the record.** `feat`, `fix`, and `perf` require an
  actual `Tests:`, `Evidence:`, or `Verified:` trailer.
- **Scopes do not decay.** A repository may opt into a checked-in
  `.commit-scopes` vocabulary; free-form scopes are rejected.
- **Humans and agents use the same rules.** The repository includes a Codex
  and Claude skill, managed instruction snippets, a local Git hook, CI gate,
  and history analytics.
- **The gate proves it can fail.** Installation verifies both rejection and
  acceptance paths instead of only checking that files were copied.

Read the complete specification in
[AI-COMMIT-STANDARD.md](AI-COMMIT-STANDARD.md).

## Install

Requires Git, Python 3, and Bash. The installer supports macOS and Linux.

```bash
git clone https://github.com/Fuzzy-and-Fluffy/ai-commit-standard.git
cd ai-commit-standard
./install.sh
```

The installer:

- installs a global `commit-msg` gate under `~/.ai-commit-standard`;
- preserves and chains repository-local Git hooks;
- installs the `ai-commit-standard` skill for Codex and Claude Code;
- adds replaceable managed instruction blocks to global `AGENTS.md` and
  `CLAUDE.md` files;
- refuses to overwrite an unrelated existing `core.hooksPath`.

Verify the installation and detect drift:

```bash
./install.sh check
```

Disable the standard for one repository without affecting others:

```bash
git config commitformat.enabled false
```

## Use in GitHub Actions

```yaml
name: commit-standard
on: [push, pull_request]

jobs:
  commits:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: Fuzzy-and-Fluffy/ai-commit-standard@v1
        with:
          forbid-wip: "true"
```

Pin a full release tag or commit SHA when your supply-chain policy requires
immutable dependencies.

## Use with coding agents

The machine installer configures both Codex and Claude Code. For a repository
used in cloud sandboxes, copy [snippets/repo-agents.md](snippets/repo-agents.md)
into its `AGENTS.md` or `CLAUDE.md`.

The standalone skill lives at
[skills/ai-commit-standard](skills/ai-commit-standard) and follows the open
Agent Skills folder convention.

## Study a repository's history

```bash
python3 ~/.ai-commit-standard/scripts/commit-stats.py \
  --weekly --gaps --ref origin/main /path/to/repository
```

The report measures typed coverage, evidence coverage, type distribution,
scope vocabulary, trailer links, and `chore` residue.

## Development

```bash
python3 tests/test_commit_gate.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

The suite exercises valid and invalid subjects, bodies, scopes, evidence,
merge topology, revert topology, width rules, and CI behaviour.

## License

MIT. See [LICENSE](LICENSE).
