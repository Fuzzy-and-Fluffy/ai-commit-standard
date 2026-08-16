#!/usr/bin/env bash
# Install or verify the shared AI Commit Standard Git gate.
set -euo pipefail

DATA_DIR="${AI_COMMIT_STANDARD_HOME:-$HOME/.ai-commit-standard}"
HOOKS_DIR="$DATA_DIR/hooks"
HOOK="$HOOKS_DIR/commit-msg"
SPEC="$DATA_DIR/AI-COMMIT-STANDARD.md"

fail() { printf '\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$*"; }
info() { printf '  %s\n' "$*"; }

case "${1:-install}" in
  disable)
    git rev-parse --git-dir >/dev/null 2>&1 || fail "not inside a git repository"
    git config commitformat.enabled false
    ok "AI Commit Standard disabled in $(git rev-parse --show-toplevel)"
    exit 0
    ;;
  enable)
    git rev-parse --git-dir >/dev/null 2>&1 || fail "not inside a git repository"
    git config --unset commitformat.enabled 2>/dev/null || true
    ok "AI Commit Standard enabled in $(git rev-parse --show-toplevel)"
    exit 0
    ;;
  check|install) ;;
  *) fail "unknown argument: $1 (use: install | check | disable | enable)" ;;
esac

[ -f "$SPEC" ] || fail "spec missing: $SPEC"
[ -f "$HOOK" ] || fail "hook missing: $HOOK"

if [ "${1:-install}" = "install" ]; then
  chmod +x "$HOOK"
  current="$(git config --global --get core.hooksPath || true)"
  legacy="$HOME/.claude/git-hooks"
  if [ -n "$current" ] && [ "$current" != "$HOOKS_DIR" ] && [ "$current" != "$legacy" ]; then
    fail "core.hooksPath is already '$current'; refusing to overwrite an unrelated hook directory"
  fi
  git config --global core.hooksPath "$HOOKS_DIR"
fi

[ -x "$HOOK" ] || fail "hook is not executable: $HOOK"
[ "$(git config --global --get core.hooksPath || true)" = "$HOOKS_DIR" ] || fail "core.hooksPath is not $HOOKS_DIR"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf 'Add a thing without any type prefix\n' > "$tmp/bad"
if "$HOOK" "$tmp/bad" >/dev/null 2>&1; then fail "gate accepted an untyped message"; fi
printf 'chore: Rename the worker entry point\n' > "$tmp/good"
if ! "$HOOK" "$tmp/good" >/dev/null 2>&1; then fail "gate rejected a valid chore message"; fi
printf 'fix: Stop paying for the same homepage twice\n\nThe discovery pass fetched it twice.\n\nTests: pytest -q -> 96 passed\n' > "$tmp/good2"
if ! "$HOOK" "$tmp/good2" >/dev/null 2>&1; then fail "gate rejected a valid fix message"; fi
printf 'fix: Stop paying for the same homepage twice\n\nThe discovery pass fetched it twice.\n' > "$tmp/bad2"
if "$HOOK" "$tmp/bad2" >/dev/null 2>&1; then fail "gate accepted a fix without evidence"; fi

ok "AI Commit Standard is installed and proven able to fail"
info "spec: $SPEC"
info "hook: $HOOK"
info "scope: every repository on this machine"
