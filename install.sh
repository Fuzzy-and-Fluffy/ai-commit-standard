#!/usr/bin/env bash
# Install AI Commit Standard for Git, Codex, and Claude Code.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="${AI_COMMIT_STANDARD_HOME:-$HOME/.ai-commit-standard}"
MODE="${1:-install}"

fail() { printf '\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$*"; }
info() { printf '  %s\n' "$*"; }

PAIRS=(
  "hooks/commit-msg|$DATA_DIR/hooks/commit-msg"
  "hooks/pre-push|$DATA_DIR/hooks/pre-push"
  "AI-COMMIT-STANDARD.md|$DATA_DIR/AI-COMMIT-STANDARD.md"
  "scripts/commit-stats.py|$DATA_DIR/scripts/commit-stats.py"
  "scripts/install-ai-commit-standard.sh|$DATA_DIR/scripts/install-ai-commit-standard.sh"
  "skills/ai-commit-standard/SKILL.md|$HOME/.claude/skills/ai-commit-standard/SKILL.md"
  "skills/ai-commit-standard/agents/openai.yaml|$HOME/.claude/skills/ai-commit-standard/agents/openai.yaml"
  "skills/ai-commit-standard/SKILL.md|$HOME/.codex/skills/ai-commit-standard/SKILL.md"
  "skills/ai-commit-standard/agents/openai.yaml|$HOME/.codex/skills/ai-commit-standard/agents/openai.yaml"
)

splice() {
  python3 - "$1" "$2" <<'PY'
import os, sys
target, snippet = sys.argv[1], sys.argv[2]
begin = "<!-- BEGIN commit-format managed block -->"
end = "<!-- END commit-format managed block -->"
block = begin + "\n" + open(snippet, encoding="utf-8").read().strip("\n") + "\n" + end + "\n"
os.makedirs(os.path.dirname(target), exist_ok=True)
text = open(target, encoding="utf-8").read() if os.path.exists(target) else ""
if begin in text and end in text:
    head, rest = text.split(begin, 1)
    _, tail = rest.split(end, 1)
    text = head + block + tail.lstrip("\n")
elif text.strip():
    text = text.rstrip("\n") + "\n\n" + block
else:
    text = block
with open(target, "w", encoding="utf-8") as fh:
    fh.write(text)
PY
}

case "$MODE" in
  check)
    drift=0
    for pair in "${PAIRS[@]}"; do
      src="$REPO/${pair%%|*}"; dst="${pair##*|}"
      if [ ! -f "$dst" ]; then info "MISSING: $dst"; drift=1
      elif ! diff -q "$src" "$dst" >/dev/null; then info "DRIFT: $dst"; drift=1
      fi
    done
    [ "$drift" = 0 ] && ok "installed copies match this release" || fail "installed copies drifted; run ./install.sh"
    exec "$DATA_DIR/scripts/install-ai-commit-standard.sh" check
    ;;
  install) ;;
  *) fail "unknown argument: $MODE (use: install | check)" ;;
esac

mkdir -p "$DATA_DIR/hooks" "$DATA_DIR/scripts" \
  "$HOME/.claude/skills/ai-commit-standard/agents" \
  "$HOME/.codex/skills/ai-commit-standard/agents"
for pair in "${PAIRS[@]}"; do
  cp "$REPO/${pair%%|*}" "${pair##*|}"
done
chmod +x "$DATA_DIR/hooks/commit-msg" "$DATA_DIR/hooks/pre-push" \
  "$DATA_DIR/scripts/install-ai-commit-standard.sh"

splice "$HOME/.claude/CLAUDE.md" "$REPO/snippets/global-CLAUDE.md"
splice "$HOME/.codex/AGENTS.md" "$REPO/snippets/global-AGENTS.md"

AI_COMMIT_STANDARD_HOME="$DATA_DIR" "$DATA_DIR/scripts/install-ai-commit-standard.sh" install

ok "AI Commit Standard installed from $REPO"
info "GitHub Action: Fuzzy-and-Fluffy/ai-commit-standard@v1"
