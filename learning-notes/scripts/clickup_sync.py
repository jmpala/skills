#!/usr/bin/env python3
"""Send learning-notes concepts to a personal ClickUp list, one task per concept.

Usage: clickup_sync.py [--dry-run]

The day files are the source of truth. A sent entry carries a line
`**ClickUp:** [<id>](<url>) · sent <date>`. Entries are grouped by concept name
across all day files: a concept with a marker anywhere is never sent again, and
its other entries get the same marker copied. Reads LEARNING_NOTES_DIR (default
~/learning) and the credentials file CONFIG_FILE (overridable with
LEARNING_NOTES_CLICKUP_ENV), which holds LEARNING_NOTES_CLICKUP_TOKEN and
LEARNING_NOTES_CLICKUP_LIST_ID as KEY=value lines.
"""
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

CONFIG_FILE = Path.home() / ".config" / "learning-notes" / "personal-clickup.env"
DAY_FILE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
MARKER = re.compile(r"^\*\*ClickUp:\*\* .*$", re.M)
FIELD = re.compile(r"^\*\*(Context|Previously|Read|Online|Related):\*\*\s*(.*)$")


def parse_entries(path):
    """Split a day file into its `## ` entries; returns (lines, entries)."""
    lines = path.read_text().split("\n")
    starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    entries = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        entries.append({"file": path, "start": start, "end": end, "lines": lines[start:end]})
    for entry in entries:
        body = entry["lines"]
        entry["name"] = body[0][3:].strip()
        entry["marker"] = next((l for l in body if MARKER.match(l)), None)
        entry["explanation"], entry["fields"] = split_fields(body[1:])
    return lines, entries


def split_fields(body):
    explanation, fields, current = [], {}, None
    for line in body:
        match = FIELD.match(line)
        if match:
            current = match.group(1)
            fields.setdefault(current, [])
            if match.group(2):
                fields[current].append(match.group(2))
        elif line.startswith("- ") and current in ("Read", "Online"):
            fields[current].append(line[2:])
        elif current is None and line.strip():
            explanation.append(line.strip())
    return " ".join(explanation), fields


def describe(name, entries):
    first = entries[0]
    date = first["file"].stem
    actions = [f"- [ ] Re-read the notes: `{first['file']}` → \"{name}\""]
    actions += [f"- [ ] Read {r}" for r in first["fields"].get("Read", [])]
    actions += [f"- [ ] Open {o}" for o in first["fields"].get("Online", [])]
    actions.append("- [ ] Explain the concept in 3 sentences without the notes, then compare with the summary")
    actions.append("- [ ] Find one more place in your own code where it applies, or where it is violated")
    related = first["fields"].get("Related", [])
    if related:
        actions.append(f"- [ ] Review the related concepts: {related[0].replace('[[', '').replace(']]', '')}")
    contexts = [f"- {e['file'].stem} {c}" for e in entries for c in e["fields"].get("Context", [])]
    return "\n".join(
        [f"Review the concept **{name}** (first logged {date}).", "", "## Actions", *actions, "",
         "## Summary", first["explanation"], "", "## Where it came up", *contexts]
    )


def create_task(token, list_id, name, description):
    body = json.dumps({"name": name, "markdown_content": description, "description": description}).encode()
    request = urllib.request.Request(
        f"https://api.clickup.com/api/v2/list/{list_id}/task",
        data=body,
        headers={"Authorization": token, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        task = json.load(response)
    return task["id"], task.get("url") or f"https://app.clickup.com/t/{task['id']}"


def write_marker(path, name, marker):
    """Re-read the file and add the marker to every unmarked entry with this name."""
    lines, entries = parse_entries(path)
    for entry in reversed(entries):
        if entry["name"].casefold() != name.casefold() or entry["marker"]:
            continue
        end = entry["end"]
        while end > entry["start"] and not lines[end - 1].strip():
            end -= 1
        lines[end:end] = ["", marker]
    tmp = path.with_suffix(".md.tmp")
    tmp.write_text("\n".join(lines))
    tmp.replace(path)


def load_config():
    """Returns (token, list_id, error); error is None when both values are present."""
    path = Path(os.environ.get("LEARNING_NOTES_CLICKUP_ENV", CONFIG_FILE))
    if not path.is_file():
        return "", "", f"MISSING_CONFIG: {path} not found"
    values = {}
    for line in path.read_text().splitlines():
        key, sep, value = line.strip().removeprefix("export ").partition("=")
        if sep and not key.startswith("#"):
            values[key.strip()] = value.strip().strip("\"'")
    missing = [k for k in ("LEARNING_NOTES_CLICKUP_TOKEN", "LEARNING_NOTES_CLICKUP_LIST_ID") if not values.get(k)]
    if missing:
        return "", "", f"MISSING_CONFIG: {path} has no value for {', '.join(missing)}"
    if path.stat().st_mode & 0o077:
        print(f"WARNING: {path} is readable by other users; run chmod 600 {path}")
    return values["LEARNING_NOTES_CLICKUP_TOKEN"], values["LEARNING_NOTES_CLICKUP_LIST_ID"], None


def main(dry_run):
    notes = Path(os.environ.get("LEARNING_NOTES_DIR", Path.home() / "learning"))
    token, list_id, error = load_config()
    if error and not dry_run:
        print(error)
        return 2
    if error:
        print(f"{error} (dry run continues)")

    groups = {}
    for path in sorted(p for p in notes.iterdir() if DAY_FILE.match(p.name)):
        for entry in parse_entries(path)[1]:
            groups.setdefault(entry["name"].casefold(), []).append(entry)

    today = datetime.date.today().isoformat()
    failed = False
    for entries in groups.values():
        unmarked = [e for e in entries if not e["marker"]]
        if not unmarked:
            continue
        name = entries[0]["name"]
        marker = next((e["marker"] for e in entries if e["marker"]), None)
        if marker:
            print(f"{'WOULD COPY' if dry_run else 'COPIED'}: {name}")
            if dry_run:
                continue
        elif dry_run:
            print(f"WOULD SEND: {name}\n{describe(name, entries)}\n")
            continue
        else:
            try:
                task_id, url = create_task(token, list_id, name, describe(name, entries))
            except (urllib.error.URLError, KeyError, ValueError) as error:
                print(f"FAILED: {name}: {error}")
                failed = True
                continue
            marker = f"**ClickUp:** [{task_id}]({url}) · sent {today}"
            print(f"SENT: {name} → {url}")
        # Write per concept, so a later failure keeps the markers of tasks already created.
        for path in {e["file"] for e in unmarked}:
            write_marker(path, name, marker)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main("--dry-run" in sys.argv[1:]))
