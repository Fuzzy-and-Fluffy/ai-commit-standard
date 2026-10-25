#!/usr/bin/env python3
"""action/check.py must judge a push by topology, not by spelling.

A push to main after a pull-request merge lists git's generated merge commit;
the checker must skip it (2026-10-07: every merge into main turned CI red),
while a single-parent commit that only LOOKS like a merge must still fail.
Runs in a throwaway repository only.
"""
import json
import os
import subprocess
import sys
import tempfile

CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "action", "check.py")
GOOD = "chore: Rename the worker entry point\n"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout.strip()


def commit(repo, name, msg):
    with open(os.path.join(repo, name), "w") as fh:
        fh.write(name)
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "HEAD")


def run(repo, tmp, ids):
    ev = os.path.join(tmp, "event.json")
    with open(ev, "w") as fh:
        json.dump({"commits": [{"id": i} for i in ids]}, fh)
    env = dict(os.environ, GITHUB_EVENT_PATH=ev, INPUT_RANGE="", INPUT_FORBID_WIP="true")
    result = subprocess.run([sys.executable, CHECK], cwd=repo, env=env,
                            capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


with tempfile.TemporaryDirectory() as tmp:
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                      GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                      GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    repo = os.path.join(tmp, "repo")
    subprocess.run(["git", "init", "-q", "-b", "main", repo], check=True)
    base = commit(repo, "a", GOOD)
    git(repo, "checkout", "-q", "-b", "topic")
    work = commit(repo, "b", "docs: Record the room-identifier gotcha\n")
    git(repo, "checkout", "-q", "main")
    commit(repo, "c", "test: Cover the duplicate-listing rejection path\n")
    git(repo, "merge", "-q", "--no-ff", "topic", "-m", "Merge pull request #3 from someone/topic")
    merge = git(repo, "rev-parse", "HEAD")
    fake = commit(repo, "d", "Merge the parsers into one module\n")

    failures = 0
    checks = [
        ("push with a real merge commit passes",
         run(repo, tmp, [work, merge]), lambda rc, out: rc == 0 and "checked 1 commits" in out),
        ("merge-only push checks nothing and walks no ancestors",
         run(repo, tmp, [merge]), lambda rc, out: rc == 0 and "checked 0 commits" in out),
        ("single-parent commit spelled like a merge still fails",
         run(repo, tmp, [merge, fake]), lambda rc, out: rc == 1 and "Merge the parsers" in out),
        ("unknown commit id refuses instead of passing",
         run(repo, tmp, [base, "f" * 40]), lambda rc, out: rc == 2),
    ]
    for name, (rc, out), ok in checks:
        good = ok(rc, out)
        print(("PASS " if good else "FAIL ") + name + ("" if good else " (exit %d)\n%s" % (rc, out)))
        failures += not good
sys.exit(1 if failures else 0)
