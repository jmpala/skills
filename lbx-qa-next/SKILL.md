---
name: lbx-qa-next
description: Move a finished feature branch to merge. Read the ClickUp custom task ID from a `task/<custom-id>/<name>` branch, merge the latest main into the branch and push it, check that the ClickUp task is in status QA, find the draft GitLab merge request for the branch, and mark it ready (not draft) with the glab CLI. A GitLab automation then moves the ClickUp task to merge. Use this whenever the user says things like "ready for merge", "move this to merge", "mark the MR ready", "undraft the MR", "QA passed, ship it", "release this branch", "set the ticket to merge", or asks to update a branch with main and un-draft its merge request, even if they do not name ClickUp or GitLab.
---

# LBX QA Next

The user works on GitLab projects (for example `marketing-portal`) with ClickUp tasks. When QA approves a task, the branch must get the latest `main`, and its draft merge request (MR) must become ready. A GitLab automation then moves the ClickUp task to "merge". This skill does those steps in a fixed order and stops at the first problem.

Every step below is a gate. If a gate fails, stop, tell the user what failed and what to do, and do not do the next steps. Never work around a failed gate (for example, never resolve merge conflicts yourself and never create the MR yourself). The user wants to make those decisions.

Run all commands in the repository of the project the user works on (the current working directory, unless the user names another one).

## Step 1: Check glab

Run `glab --version`. If the command is not found, stop. Tell the user to install glab and give the options:

- `! sudo snap install glab` (Ubuntu with snap)
- `! brew install glab` (Homebrew)
- Other ways: https://gitlab.com/gitlab-org/cli#installation

Then run `glab auth status`. If glab is not logged in to the host of the `origin` remote, stop and tell the user to run `! glab auth login`.

## Step 2: Read the task ID from the branch

Run `git branch --show-current`. The branch format is `task/<custom-id>/<branch-name>`, for example `task/MP-1234/new-landing-page`. The custom ID is the second segment.

If the branch does not start with `task/`, or has no second segment, stop. Tell the user the branch name and the expected format.

## Step 3: Merge main and push

1. Run `git status --porcelain`. If it shows changes to tracked files, stop. Tell the user to commit or stash them first. Untracked files are fine.
2. Run `git fetch origin`.
3. Run `git merge origin/main --no-edit`.
   - If the merge has conflicts, run `git merge --abort`, then stop. List the files with conflicts and tell the user to resolve them by hand.
   - If the result is "Already up to date", continue.
4. Run `git push` (use `git push -u origin <branch>` if the branch has no upstream). Do not force-push. If the push fails, stop and show the error.

## Step 4: Check the ClickUp status

Run:

```bash
python3 <this skill's directory>/scripts/clickup_task.py <custom-id>
```

The script prints the task as JSON with `name`, `status` and `url`. It needs `CLICKUP_API_TOKEN` in the environment. If the script fails, stop and show its error.

Compare `status` with "qa", without regard to case. If the status is not QA, stop. Tell the user the task name, the current status and the task URL. The branch push from Step 3 stays. That is harmless.

## Step 5: Find the merge request

Run:

```bash
glab mr list --source-branch "<branch>" --output json
```

If this glab version does not know a flag, check `glab mr list --help` and use the matching flag.

- No open MR → stop. Tell the user to create a draft MR for the branch (for example `! glab mr create --draft --fill`), then run this skill again. Do not create it yourself.
- More than one open MR → stop and list them. Ask the user which one to use.
- One open MR → continue with its IID (the `iid` field).

## Step 6: Mark the MR ready

The MR is a draft if `draft` (or `work_in_progress` in older GitLab versions) is true, or if the title starts with `Draft:`.

- If the MR is a draft, run `glab mr update <iid> --ready`. Then run `glab mr view <iid> --output json` and check that it is no longer a draft.
- If the MR is already ready, do not change it. Tell the user.

## Report

End with a short report:

```
Branch:  task/MP-1234/new-landing-page  (merged origin/main, pushed)
ClickUp: MP-1234 "New landing page" — status QA  <task url>
MR:      !87 "New landing page" — marked ready  <mr url>
The GitLab automation now moves the task to merge.
```

If the skill stopped at a gate, report the steps that completed, the gate that failed and the next action for the user.
