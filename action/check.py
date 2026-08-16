#!/usr/bin/env python3
"""CI validator: run the commit-msg gate over a range of commits.

Used by action.yml inside GitHub Actions, and runnable locally:

    INPUT_RANGE=origin/main..HEAD python3 action/check.py

Environment:
  INPUT_RANGE       explicit rev range A..B; overrides event detection
  INPUT_FORBID_WIP  'true' to fail on wip:/fixup!/squash! commits (enable on
                    PRs targeting main: wip must be squashed before merge)
  GITHUB_EVENT_PATH set by Actions; pull_request and push events are handled
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "commit-msg")


def rev_list(rng):
    out = subprocess.run(["git", "rev-list", "--no-merges", rng],
                         capture_output=True, text=True)
    if out.returncode:
        sys.stderr.write(out.stderr)
        sys.exit(2)
    return out.stdout.split()


def shas():
    rng = os.environ.get("INPUT_RANGE", "").strip()
    if rng:
        return rev_list(rng)
    ev_path = os.environ.get("GITHUB_EVENT_PATH")
    if ev_path and os.path.exists(ev_path):
        ev = json.load(open(ev_path))
        pr = ev.get("pull_request")
        if pr:
            return rev_list("%s..%s" % (pr["base"]["sha"], pr["head"]["sha"]))
        commits = ev.get("commits")
        if commits is not None:
            return [c["id"] for c in commits]
    sys.stderr.write("no range: set INPUT_RANGE=A..B or run inside GitHub Actions\n")
    sys.exit(2)


def main():
    forbid_wip = os.environ.get("INPUT_FORBID_WIP", "false").lower() in ("1", "true", "yes")
    failures = []
    lst = shas()
    for sha in lst:
        msg = subprocess.run(["git", "log", "-1", "--format=%B", sha],
                             capture_output=True, text=True).stdout
        subject = msg.splitlines()[0] if msg.splitlines() else ""
        with tempfile.NamedTemporaryFile("w", suffix=".msg", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(msg)
            path = fh.name
        try:
            p = subprocess.run([sys.executable, HOOK, path],
                               capture_output=True, text=True)
        finally:
            os.unlink(path)
        if p.returncode:
            failures.append((sha[:9], subject, p.stderr.strip()))
        elif forbid_wip and (subject.startswith("wip: ")
                             or subject.startswith(("fixup!", "squash!", "amend!"))):
            failures.append((sha[:9], subject,
                             "wip/fixup commit present; squash into a typed commit before merge"))
    print("ai-commit-standard: checked %d commits" % len(lst))
    for sha, subject, err in failures:
        print("\nFAIL %s %s" % (sha, subject))
        print("  " + err.replace("\n", "\n  "))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
