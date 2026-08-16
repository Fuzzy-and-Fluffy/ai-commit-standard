#!/usr/bin/env python3
"""commit-stats: type-bucket analytics over git history.

Buckets every commit by the type ladder in ~/.ai-commit-standard/AI-COMMIT-STANDARD.md and
reports, per repo and overall:

  - coverage: share of commits carrying a valid type (the rest are `untyped`)
  - counts per type
  - evidence coverage: share of feat/fix/perf commits carrying a
    Tests:/Evidence:/Verified: trailer
  - chore share of typed commits (the residue-health metric)

Descriptive where the hook is normative: legacy Angular-style prefixes are
also counted (scoped `feat(x):` folds to `feat`, `style:` folds to
`refactor`), so pre-format history stays comparable.

Usage:
  commit-stats.py [--since DATE] [--until DATE] [--weekly] [--ref REF] [--gaps] REPO [REPO ...]
  (no REPO: the current directory)

--ref REF   scan only history reachable from REF (e.g. origin/main) instead of
            --all; use this to measure what actually shipped vs what is in flight
--gaps      list the offending commits: untyped ones, and feat/fix/perf ones
            missing a Tests:/Evidence:/Verified: trailer
"""
import argparse
import collections
import os
import re
import subprocess
import sys

TYPES = ["wip", "revert", "release", "feat", "fix", "perf", "refactor",
         "docs", "test", "ci", "build", "chore"]
FOLD = {"style": "refactor"}  # dropped types folded into their successor
TYPED_RE = re.compile(r"^(%s|style)(\([^)]*\))?!?: " % "|".join(TYPES))
EVIDENCE_RE = re.compile(r"^(Tests|Evidence|Verified): .+$", re.M)
LINK_RES = {"Fixes": re.compile(r"^Fixes: .+$", re.M),
            "Reverts": re.compile(r"^Reverts: .+$", re.M),
            "Reviewed-by": re.compile(r"^Reviewed-by: .+$", re.M)}
EVIDENCE_TYPES = ("feat", "fix", "perf")


def classify(subject):
    if subject.startswith('Revert "'):
        return "revert"
    if subject.startswith(("fixup!", "squash!", "amend!")):
        return "wip"
    if subject.startswith(("Release ", "Bump build number", "Bump version")):
        return "release"  # legacy release subjects that predate the ladder
    m = TYPED_RE.match(subject)
    if not m:
        return "untyped"
    return FOLD.get(m.group(1), m.group(1))


def scan(repo, since, until=None, ref=None):
    cmd = ["git", "-C", repo, "log", ref or "--all", "--no-merges",
           "--format=%h\x01%ad\x01%s\x01%b\x02", "--date=format:%G-%V"]
    if since:
        cmd += ["--since", since]
    if until:
        cmd += ["--until", until]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        sys.stderr.write("skip %s: %s\n" % (repo, out.stderr.strip().splitlines()[0] if out.stderr else "?"))
        return None
    recs = []
    for rec in out.stdout.split("\x02"):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        parts = rec.split("\x01")
        if len(parts) < 4:
            continue
        sha, week, subject, body = parts[0], parts[1], parts[2], "\x01".join(parts[3:])
        if subject.startswith("Merge "):
            continue
        t = classify(subject)
        sm = TYPED_RE.match(subject)
        scope = sm.group(2).strip("()") if sm and sm.group(2) else ""
        links = tuple(k for k, rx in LINK_RES.items() if rx.search(body))
        recs.append((sha, week, t, subject, bool(EVIDENCE_RE.search(body)), scope, links))
    return recs


def table(rows, headers):
    widths = [max(len(str(r[i])) for r in rows + [headers]) for i in range(len(headers))]
    def fmt(r):
        return "  ".join(str(c).rjust(w) if i else str(c).ljust(w)
                         for i, (c, w) in enumerate(zip(r, widths)))
    print(fmt(headers))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print(fmt(r))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="*", default=["."])
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--ref", help="scan only this ref (e.g. origin/main) instead of --all")
    ap.add_argument("--weekly", action="store_true",
                    help="per-week type matrix (typed commits only)")
    ap.add_argument("--gaps", action="store_true",
                    help="list untyped commits and feat/fix/perf commits without evidence")
    args = ap.parse_args()

    cols = TYPES + ["untyped"]
    grand = collections.Counter()
    grand_ev = [0, 0]  # evidenced, eligible
    rows = []
    weekly = collections.defaultdict(collections.Counter)
    gaps_untyped, gaps_unevidenced = [], []
    scope_counts = collections.Counter()
    link_counts = collections.Counter()

    for repo in args.repos:
        recs = scan(repo, args.since, args.until, args.ref)
        if recs is None:
            continue
        c = collections.Counter(t for _, _, t, _, _, _, _ in recs)
        ev = [sum(1 for _, _, t, _, e, _, _ in recs if t in EVIDENCE_TYPES and e),
              sum(1 for _, _, t, _, _, _, _ in recs if t in EVIDENCE_TYPES)]
        total = len(recs)
        typed = total - c["untyped"]
        rows.append([os.path.basename(os.path.abspath(repo)), total,
                     "%d%%" % (100 * typed / total) if total else "-"]
                    + [c[t] or "" for t in cols]
                    + ["%d/%d" % (ev[0], ev[1]) if ev[1] else "-"])
        grand.update(c)
        grand_ev[0] += ev[0]
        grand_ev[1] += ev[1]
        name = os.path.basename(os.path.abspath(repo))
        for sha, week, t, subject, e, scope, links in recs:
            if t != "untyped":
                weekly[week][t] += 1
            else:
                gaps_untyped.append("%s %s %s" % (name, sha, subject))
            if t in EVIDENCE_TYPES and not e:
                gaps_unevidenced.append("%s %s %s" % (name, sha, subject))
            if scope:
                scope_counts[scope] += 1
            for k in links:
                link_counts[k] += 1

    if not rows:
        return 1
    total = sum(grand.values())
    typed = total - grand["untyped"]
    rows.append(["ALL", total, "%d%%" % (100 * typed / total) if total else "-"]
                + [grand[t] or "" for t in cols]
                + ["%d/%d" % tuple(grand_ev) if grand_ev[1] else "-"])
    table(rows, ["repo", "commits", "typed"] + cols + ["evidence"])

    if typed:
        print("\nchore share of typed commits: %.1f%%  (residue health; lower is better)"
              % (100 * grand["chore"] / typed))
    if grand_ev[1]:
        print("evidence coverage on feat/fix/perf: %.1f%%"
              % (100 * grand_ev[0] / grand_ev[1]))

    if scope_counts:
        top = ", ".join("%s %d" % kv for kv in scope_counts.most_common(15))
        more = len(scope_counts) - 15
        print("scopes (typed commits): %s%s"
              % (top, "  ... +%d more" % more if more > 0 else ""))

    if link_counts:
        print("trailer graph: " + " · ".join("%s %d" % (k, link_counts[k])
              for k in ("Fixes", "Reverts", "Reviewed-by") if link_counts[k]))

    if args.weekly and weekly:
        print()
        wrows = [[w] + [weekly[w][t] or "" for t in TYPES] + [sum(weekly[w].values())]
                 for w in sorted(weekly)]
        table(wrows, ["week"] + TYPES + ["typed"])

    if args.gaps:
        for title, items in (("untyped commits", gaps_untyped),
                             ("feat/fix/perf without Tests:/Evidence:", gaps_unevidenced)):
            print("\n%s: %d" % (title, len(items)))
            for line in items[:20]:
                print("  " + line)
            if len(items) > 20:
                print("  ... and %d more" % (len(items) - 20))
    return 0


if __name__ == "__main__":
    sys.exit(main())
