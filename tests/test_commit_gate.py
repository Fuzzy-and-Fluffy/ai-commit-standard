#!/usr/bin/env python3
"""Adversarial test of hooks/commit-msg.

Runs against a throwaway message file only -- never against a real commit.
Every case asserts a direction: REJECT means the gate must turn red.
"""
import os
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "commit-msg")
REJECT, ACCEPT = "REJECT", "ACCEPT"

CASES = [
    # --- must be REJECTED -------------------------------------------------
    (REJECT, "no type prefix at all", "Add stateful Windows navigation and Finder shortcuts\n"),
    (REJECT, "conventional type we dropped", "style: Reformat the parser\n"),
    (REJECT, "scoped commit in a repo with NO .commit-scopes registry", "feat(api): Add a thing\n\nBody.\n\nTests: x -> ok\n"),
    (REJECT, "unknown type", "hotfix: Patch the thing\n"),
    (REJECT, "lowercase after type", "chore: rename the worker entry point\n"),
    (REJECT, "trailing period", "chore: Rename the worker entry point.\n"),
    (REJECT, "past tense", "chore: Renamed the worker entry point\n"),
    (REJECT, "third person -s", "chore: Adds a retry to the uploader\n"),
    (REJECT, "gerund", "chore: Adding a retry to the uploader\n"),
    (REJECT, "no blank line before body", "chore: Rename the entry point\nBody starts immediately.\n"),
    (REJECT, "subject at 89 columns (one over the limit)",
     "chore: Rename the worker entry points and also every single one of its callers everywhere\n"),
    (ACCEPT, "subject at exactly 88 columns (the boundary itself)",
     "chore: Rename the worker entry point and also every single one of its callers everywhere\n"),
    (REJECT, "595-char monster (the real one from history)", "chore: " + "x" * 595 + "\n"),
    (REJECT, "feat with no body", "feat: Add a room dropdown\n\nTests: pytest -q -> 12 passed\n"),
    (REJECT, "feat with no evidence trailer", "feat: Add a room dropdown\n\nIt was missing.\n"),
    (REJECT, "fix with no evidence trailer", "fix: Stop double-fetching\n\nIt fetched twice.\n"),
    (REJECT, "evidence-looking prose is not a trailer",
     "fix: Stop double-fetching\n\nIt fetched twice. I ran the tests and they passed.\n"),
    (REJECT, "empty Security trailer",
     "chore: Move secrets out of the tree\n\nThey were committed.\n\nSecurity:  \n"),
    (REJECT, "CJK subject over 88 columns",
     "feat: 让用户导出全部设置并且保留原来的排序方式同时兼容旧版本数据而且不包含任何私密字段\n"),
    (REJECT, "perf without a measurement",
     "perf: Make the sync cheaper\n\nIt fetched the homepage twice per run.\n"),
    (REJECT, "alias 'feature:'", "feature: Add a room dropdown\n"),
    (REJECT, "alias 'bugfix:'", "bugfix: Stop the crash on empty rooms\n"),
    (REJECT, "alias 'deps:'", "deps: Bump requests to 2.32\n"),

    # --- must be ACCEPTED -------------------------------------------------
    (ACCEPT, "minimal chore (warning only, still passes)", "chore: Rename the worker entry point\n"),
    (ACCEPT, "refactor needs no evidence",
     "refactor: Extract the pack-size parser into one module\n\nThree copies had drifted.\n"),
    (ACCEPT, "test type", "test: Cover the duplicate-listing rejection path\n"),
    (ACCEPT, "ci type", "ci: Run pytest and ruff on every push\n"),
    (ACCEPT, "build type", "build: Bump the notarization tooling\n"),
    (ACCEPT, "manual revert with Reverts: trailer",
     "revert: Back out the eager homepage cache\n\nIt served a logged-out page.\n\nReverts: 41d2c07\n"),
    (REJECT, "manual revert without Reverts: trailer",
     "revert: Back out the eager homepage cache\n\nIt served a logged-out page.\n"),
    (REJECT, "empty Fixes: trailer",
     "fix: Stop double-fetching\n\nIt fetched twice.\n\nTests: pytest -q -> 96 passed\nFixes:  \n"),
    (ACCEPT, "fix with regression-genealogy Fixes: trailer",
     "fix: Stop double-fetching\n\nIt fetched twice.\n\nTests: pytest -q -> 96 passed\nFixes: 9f31c02 (\"feat: Cache the homepage\")\n"),
    (ACCEPT, "perf with the measurement",
     "perf: Make the sync cheaper\n\nIt fetched the homepage twice per run.\n\nEvidence: full run -> 41 requests, was 78\n"),
    (ACCEPT, "chore with body", "chore: Rename the worker entry point\n\nThe old name lied.\n"),
    (ACCEPT, "docs only", "docs: Record the room-identifier gotcha\n"),
    (ACCEPT, "wip escape hatch", "wip: Boards round 3, review pending\n\nDo not merge.\n"),
    (ACCEPT, "release", "release: Ship TestFlight build 0.1 (97)\n\nTests: xcodebuild test -> TEST SUCCEEDED\n"),
    (ACCEPT, "fix with Tests trailer",
     "fix: Stop paying for the same homepage twice\n\nIt fetched the homepage twice.\n\nTests: pytest -q -> 96 passed\n"),
    (ACCEPT, "feat with Evidence instead of Tests",
     "feat: Give profiles an export format\n\nThey arrived untraceable.\n\nEvidence: live run -> 41 requests, was 78\n"),
    (ACCEPT, "feat with Verified alias",
     "feat: Give profiles an export format\n\nThey arrived untraceable.\n\nVerified: on device build 97\n"),
    (ACCEPT, "CJK subject inside the limit",
     "feat: Give users a portable settings export\n\nThey arrived untraceable.\n\nTests: pytest -q -> 48 passed\n"),
    (ACCEPT, "full standard message with all trailers",
     "fix: Reject duplicate registry listing IDs\n\nTwo listings could claim the same id.\n\n"
     "Tests: pytest tests/test_registry.py -q -> 31 passed\nCloses: #92\nSecurity: none\n"
     "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n"),
    (REJECT, "merge-imitating subject with NO merge in progress (the 2026-08-14 backdoor)",
     "Merge the pack-size parser into one module\n"),
    (REJECT, "git-style merge subject outside a real merge",
     "Merge branch 'codex/window-manager-first'\n"),
    (REJECT, "merge: prefix outside a real merge", "merge: wave1/w148\n"),
    (REJECT, "revert-imitating subject with NO revert in progress",
     'Revert "chore: Rename the worker entry point"\n'),
    (ACCEPT, "autosquash fixup", "fixup! chore: Rename the worker entry point\n"),
    (ACCEPT, "comments are stripped before checking",
     "chore: Rename the worker entry point\n# Please enter the commit message\n# On branch main\n"),
    (ACCEPT, "warn-only zone: 73..88 columns",
     "chore: " + "Rename the worker entry point and all of its callers today\n"),
]


def run(msg, cwd=None):
    with tempfile.NamedTemporaryFile("w", suffix=".msg", delete=False, encoding="utf-8") as fh:
        fh.write(msg)
        path = fh.name
    try:
        p = subprocess.run([HOOK, path], capture_output=True, text=True, cwd=cwd)
        return p.returncode, p.stdout + p.stderr
    finally:
        os.unlink(path)


SCOPED_CASES = [
    # Run inside a fixture repo whose .commit-scopes registers: api, web
    (ACCEPT, "registered scope",
     "feat(api): Add a thing\n\nBody.\n\nTests: x -> ok\n"),
    (ACCEPT, "unscoped commit in a registry repo",
     "feat: Add a thing\n\nBody.\n\nTests: x -> ok\n"),
    (REJECT, "unregistered scope",
     "feat(audio): Add a thing\n\nBody.\n\nTests: x -> ok\n"),
    (REJECT, "uppercase scope",
     "feat(Api): Add a thing\n\nBody.\n\nTests: x -> ok\n"),
    (REJECT, "scope colliding with a type name, even though registered",
     "fix(release): Repair the notarization step\n\nBody.\n\nTests: x -> ok\n"),
    (ACCEPT, "hyphenated registered scope",
     "feat(asr-bench): Add a thing\n\nBody.\n\nTests: x -> ok\n"),
]


def op_fixture(kind):
    """A repo genuinely mid-merge (MERGE_HEAD) or mid-revert (REVERT_HEAD)."""
    d = tempfile.mkdtemp(prefix=f"{kind}-fixture-")
    def g(*args):
        subprocess.run(["git", "-C", d, *args], check=True, capture_output=True)
    g("init", "-q")
    g("config", "user.email", "t@t"); g("config", "user.name", "T")
    (Path(d) / "a").write_text("base\n"); g("add", "a")
    g("commit", "-q", "--no-verify", "-m", "chore: Seed")
    if kind == "merge":
        g("checkout", "-q", "-b", "side")
        (Path(d) / "b").write_text("side\n"); g("add", "b")
        g("commit", "-q", "--no-verify", "-m", "chore: Side work")
        g("checkout", "-q", "-")
        (Path(d) / "c").write_text("main\n"); g("add", "c")
        g("commit", "-q", "--no-verify", "-m", "chore: Main work")
        g("merge", "--no-ff", "--no-commit", "side")
    else:
        sha = subprocess.run(["git", "-C", d, "rev-parse", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
        (Path(d) / "a").write_text("more\n"); g("add", "a")
        g("commit", "-q", "--no-verify", "-m", "chore: More")
        g("revert", "--no-commit", "HEAD")
    return d


def scoped_fixture():
    d = tempfile.mkdtemp(prefix="scope-fixture-")
    subprocess.run(["git", "init", "-q", d], check=True)
    with open(os.path.join(d, ".commit-scopes"), "w") as fh:
        fh.write("# fixture registry\napi\nweb  # trailing comment\nrelease\nasr-bench\n")
    return d


def main():
    passed = failed = 0
    print("=" * 78)
    print("Adversarial test: %s" % HOOK)
    print("=" * 78)
    for want, name, msg in CASES:
        rc, out = run(msg)
        got = REJECT if rc != 0 else ACCEPT
        good = got == want
        passed, failed = (passed + 1, failed) if good else (passed, failed + 1)
        mark = "ok  " if good else "FAIL"
        print("%s  want %-6s got %-6s  %s" % (mark, want, got, name))
        if not good:
            print("      message: %r" % msg[:90])
            print("      output : %s" % out.strip().replace("\n", "\n      "))
    for kind, msg in (("merge", "Merge branch 'side'\n"),
                      ("revert", 'Revert "chore: More"\n\nThis reverts commit abc.\n')):
        d = op_fixture(kind)
        try:
            rc, out = run(msg, cwd=d)
            got = REJECT if rc != 0 else ACCEPT
            good = got == ACCEPT
            passed, failed = (passed + 1, failed) if good else (passed, failed + 1)
            print("%s  want ACCEPT got %-6s  [topology] real %s in progress" % ("ok  " if good else "FAIL", got, kind))
            if not good:
                print("      output : %s" % out.strip().replace("\n", "\n      "))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    fixture = scoped_fixture()
    try:
        for want, name, msg in SCOPED_CASES:
            rc, out = run(msg, cwd=fixture)
            got = REJECT if rc != 0 else ACCEPT
            good = got == want
            passed, failed = (passed + 1, failed) if good else (passed, failed + 1)
            mark = "ok  " if good else "FAIL"
            print("%s  want %-6s got %-6s  [registry] %s" % (mark, want, got, name))
            if not good:
                print("      output : %s" % out.strip().replace("\n", "\n      "))
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
    print("-" * 78)
    print("%d passed, %d failed, %d total" % (passed, failed, passed + failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
