#!/usr/bin/env python3
"""hooks/pre-push must always chain the user's own pre-push.local.

core.hooksPath makes git read only one hooks directory, so a hub that stops
calling pre-push.local silently removes every machine-wide gate kept there
(a personal-data scan, for example). Runs in a throwaway directory only.
"""
import os
import shutil
import stat
import subprocess
import sys
import tempfile

HUB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "pre-push")
REFS = "refs/heads/main 1111111111111111111111111111111111111111 refs/heads/main 0000000000000000000000000000000000000000\n"


def run(case, local_body, executable=True):
    with tempfile.TemporaryDirectory() as tmp:
        hooks = os.path.join(tmp, "hooks")
        os.makedirs(hooks)
        hub = os.path.join(hooks, "pre-push")
        shutil.copy(HUB, hub)
        os.chmod(hub, 0o755)
        seen = os.path.join(tmp, "seen.txt")
        if local_body is not None:
            local = os.path.join(hooks, "pre-push.local")
            with open(local, "w") as fh:
                fh.write("#!/bin/sh\ncat > '%s'\n%s\n" % (seen, local_body))
            os.chmod(local, 0o755 if executable else 0o644)
        repo = os.path.join(tmp, "repo")
        subprocess.run(["git", "init", "-q", repo], check=True)
        result = subprocess.run([hub, "origin", "file:///dev/null"], input=REFS, cwd=repo,
                                capture_output=True, text=True)
        got = open(seen).read() if os.path.exists(seen) else None
        return result.returncode, got


failures = 0
checks = [
    ("refusing pre-push.local blocks the push", run("refuse", "exit 1"), lambda rc, got: rc != 0 and got == REFS),
    ("passing pre-push.local receives the ref list", run("pass", "exit 0"), lambda rc, got: rc == 0 and got == REFS),
    ("non-executable pre-push.local refuses the push", run("broken", "exit 0", executable=False), lambda rc, got: rc != 0),
    ("no pre-push.local still allows the push", run("absent", None), lambda rc, got: rc == 0),
]
for name, (rc, got), ok in checks:
    good = ok(rc, got)
    print(("PASS " if good else "FAIL ") + name + ("" if good else " (exit %d, local saw %r)" % (rc, got)))
    failures += not good
sys.exit(1 if failures else 0)
