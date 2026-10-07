#!/usr/bin/env python3
"""install.sh must not write into a profile-generated agent root.

Runs install.sh against a throwaway HOME only -- never the real one.
Both directions are asserted: an ordinary root gains the managed block,
a generated root and an opted-out root stay byte-identical.
"""
import os
import subprocess
import sys
import tempfile

INSTALL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "install.sh")
BEGIN = "<!-- BEGIN commit-format managed block -->"
GENERATED = "# Rules\n\n## Global instruction files are generated\n\n- Do not edit.\n"
ORDINARY = "# My notes\n\n- Keep this.\n"


def run(case, root_text, env_extra=None):
    with tempfile.TemporaryDirectory() as home:
        roots = [os.path.join(home, ".claude", "CLAUDE.md"), os.path.join(home, ".codex", "AGENTS.md")]
        for path in roots:
            os.makedirs(os.path.dirname(path))
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(root_text)
        env = dict(os.environ, HOME=home, GIT_CONFIG_NOSYSTEM="1", XDG_CONFIG_HOME=os.path.join(home, ".config"))
        env.pop("AI_COMMIT_STANDARD_HOME", None)
        env.update(env_extra or {})
        result = subprocess.run(["bash", INSTALL], env=env, capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"FAIL {case}: install.sh exited {result.returncode}\n{result.stdout}{result.stderr}")
        return [open(path, encoding="utf-8").read() for path in roots]


failures = 0
for case, text, env, expect_block in [
    ("ordinary root gains the block", ORDINARY, None, True),
    ("generated root stays byte-identical", GENERATED, None, False),
    ("opt-out leaves an ordinary root alone", ORDINARY, {"AI_COMMIT_STANDARD_SKIP_ROOTS": "1"}, False),
]:
    after = run(case, text, env)
    ok = all((BEGIN in a) == expect_block for a in after) and (expect_block or all(a == text for a in after))
    print(("PASS " if ok else "FAIL ") + case)
    failures += not ok
sys.exit(1 if failures else 0)
