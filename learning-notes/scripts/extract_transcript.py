#!/usr/bin/env python3
"""Turn a Claude Code session transcript (.jsonl) into plain USER/ASSISTANT dialogue.

Usage: extract_transcript.py <transcript.jsonl> <output.txt>
Prints the number of user turns kept, so the caller can skip trivial sessions.
"""
import json
import re
import sys

REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
COMMAND_TAGS = re.compile(r"<(command-[a-z-]+|local-command-[a-z-]+)>.*?</\1>", re.S)


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if b.get("type") == "text")
    return ""


def main(src, dst):
    turns = []
    user_turns = 0
    with open(src) as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = entry.get("type")
            # isMeta marks injected text (skill bodies, reminders), not real turns.
            if kind not in ("user", "assistant") or entry.get("isSidechain") or entry.get("isMeta"):
                continue
            text = text_of(entry.get("message", {}).get("content"))
            text = COMMAND_TAGS.sub("", REMINDER.sub("", text)).strip()
            if not text:
                continue
            if kind == "user":
                user_turns += 1
            turns.append(f"### {kind.upper()}\n{text}\n")
    with open(dst, "w") as f:
        f.write("\n".join(turns))
    print(user_turns)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
