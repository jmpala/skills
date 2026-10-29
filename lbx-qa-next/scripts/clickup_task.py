#!/usr/bin/env python3
"""Print a ClickUp task, looked up by its custom task ID, as JSON.

Usage: clickup_task.py <custom-task-id>

Output: {"id", "custom_id", "name", "status", "url"} on stdout, exit 0.
On an error, prints a message on stderr and exits 1.
Reads the API token from CLICKUP_API_TOKEN and the workspace ID from
CLICKUP_TEAM_ID (default 36654621, "Local Brand X"). ClickUp needs the
workspace ID to resolve a custom task ID.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_TEAM_ID = "36654621"


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: clickup_task.py <custom-task-id>")
    token = os.environ.get("CLICKUP_API_TOKEN")
    if not token:
        sys.exit("CLICKUP_API_TOKEN is not set")
    team_id = os.environ.get("CLICKUP_TEAM_ID", DEFAULT_TEAM_ID)
    custom_id = sys.argv[1]
    query = urllib.parse.urlencode({"custom_task_ids": "true", "team_id": team_id})
    url = f"https://api.clickup.com/api/v2/task/{urllib.parse.quote(custom_id)}?{query}"
    request = urllib.request.Request(url, headers={"Authorization": token})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            task = json.load(response)
    except urllib.error.HTTPError as error:
        sys.exit(f"ClickUp returned HTTP {error.code} for task {custom_id}: {error.read().decode(errors='replace')}")
    except urllib.error.URLError as error:
        sys.exit(f"Cannot connect to ClickUp: {error.reason}")
    print(json.dumps({
        "id": task["id"],
        "custom_id": task.get("custom_id"),
        "name": task["name"],
        "status": task["status"]["status"],
        "url": task["url"],
    }))


if __name__ == "__main__":
    main()
