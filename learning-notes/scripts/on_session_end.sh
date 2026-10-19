#!/usr/bin/env bash
# SessionEnd hook: save the finished session's dialogue to the learning-notes
# queue. No analysis happens here; the learning-notes skill processes the
# queue in batches when the user asks.
set -euo pipefail

# Skip headless runs of the skill itself (e.g. a scheduled `claude -p`).
[[ -n "${LEARNING_NOTES_RUN:-}" ]] && exit 0

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOTES_DIR="${LEARNING_NOTES_DIR:-$HOME/learning}"
MIN_USER_TURNS=2

input="$(cat)"
transcript="$(jq -r '.transcript_path // empty' <<<"$input")"
cwd="$(jq -r '.cwd // empty' <<<"$input")"
session="$(jq -r '.session_id // "unknown"' <<<"$input")"
[[ -f "$transcript" ]] || exit 0

mkdir -p "$NOTES_DIR/.queue"
body="$(mktemp)"
trap 'rm -f "$body"' EXIT
turns="$(python3 -I "$SKILL_DIR/scripts/extract_transcript.py" "$transcript" "$body")"
(( turns < MIN_USER_TURNS )) && exit 0

# A resumed session ends again with the full history, so overwrite by session id.
{
  echo "Project: $cwd"
  echo "Date: $(date +%F)"
  echo "Ended: $(date +%H:%M)"
  echo
  cat "$body"
} >"$NOTES_DIR/.queue/$session.txt"
