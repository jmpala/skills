---
name: learning-notes
description: Extract computer-science concepts, theory and techniques that came up in a Claude conversation and record them in a daily Markdown study log (~/learning/YYYY-MM-DD.md), each with a short explanation, the context it came up in, verified book chapters to read, online resources and related concepts. Use this whenever the user asks to log, capture or note what they learned, wants reading recommendations for concepts from the current session, says things like "update my learning notes", "process my learning queue", "add this to my learning notes", "what should I read about this", "save the concepts from this chat".
---

# Learning Notes

The user wants every conversation with Claude to double as a study session: concepts they ran into while working get captured, explained briefly, and paired with the exact book chapters that teach them properly. The value of the log depends on two things — picking concepts that are genuinely worth studying, and giving book references that are actually correct. A wrong chapter number sends them to the wrong place, so verification matters more than speed.

## Inputs

The log directory is `$LEARNING_NOTES_DIR` if set, otherwise `~/learning/`. Each day has its own file, `<log dir>/<YYYY-MM-DD>.md`.

A SessionEnd hook saves every finished Claude Code session into `<log dir>/.queue/` as `<session-id>.txt`. That's plain dialogue with `### USER` / `### ASSISTANT` turns, under a header giving `Project:`, `Date:` and `Ended:`. The hook does no analysis; that's your job here.

Pick the mode from what the user asked:

1. **Queue mode** (default, e.g. "update my learning notes") — process every `.txt` file in the queue. Also count the current conversation as one more session, unless it's only about running this skill. If the queue is empty, say so and stop.
2. **This-conversation mode** (e.g. "add what we just discussed to my notes") — use only the current conversation; project = current working directory; date = today. Leave the queue alone.

In queue mode, work through Steps 1–4 across *all* sessions together rather than one session at a time. The same concept often shows up in several sessions, and researching it once is the point of batching. Write each concept into the day file for the date of the session where it came up; if it came up in sessions on different days, give each day its own entry. After the entries are written, delete the queue files you processed, so they're not logged twice. Delete a session's file even if it yielded no concepts. Leave the queue alone if anything failed before the writes.

## Step 1: Pick the concepts

Read the conversation(s) and list candidate concepts. A good concept is a piece of *transferable* knowledge — something with a name that books and courses teach, which the user would benefit from understanding more deeply. Examples: "B-tree indexes", "optimistic locking", "CAP theorem", "dependency inversion", "tail-call optimization", "consistent hashing", "CSP / channels", "big-O of hash table resizing (amortized analysis)".

Skip:
- Project-specific facts (a config key, a function name in their codebase, a bug fix that's only about their code)
- Tool trivia (CLI flags, IDE shortcuts, library API signatures) unless it illustrates a real concept
- Things so basic that a book chapter would be overkill (what a variable is)
- Concepts mentioned only in passing with no substance in the conversation

Prefer the most precise name ("write-ahead logging", not "databases"). If the conversation produced nothing worth logging, stop — don't create or touch the file. An empty day is fine; filler is not.

Typical sessions yield 0–4 concepts. If you find more than ~6, keep the most substantive.

## Step 2: Check what's already logged

Grep the `*.md` files in the log directory for each concept's heading (case-insensitive, and try obvious synonyms). 

- **Already in that day's file** → add the new context line to the existing entry; don't duplicate it.
- **In another day's file** → still add an entry for this day (the user met it again in a new context, which is worth recording), but you may reuse the verified book references from the earlier entry instead of re-researching, and add a "Previously:" link to that file.

## Step 3: Find and verify book chapters

For each new concept, recommend 1–3 books. Favor well-regarded, widely available books (e.g. *Designing Data-Intensive Applications*, *CLRS*, *SICP*, *Operating Systems: Three Easy Pieces*, *Clean Architecture*, *Database Internals*, *Computer Systems: A Programmer's Perspective*, *Crafting Interpreters*, *The Art of Multiprocessor Programming*) — but choose what genuinely covers the concept best, not what's famous.

Verify every chapter with WebSearch/WebFetch: find the book's table of contents (publisher page, O'Reilly, author's site, free online edition) and confirm the chapter/section number and title. Use the edition you verified against and name it. If you can't confirm a chapter after a reasonable search, either drop that book or list it with `(chapter unverified)` — never present an unverified number as fact.

Point to the narrowest useful unit: "Ch. 7, §'Preventing Lost Updates'" beats "Ch. 7".

Also find 1–3 online resources: the original paper, authoritative docs, or a well-known article. Confirm the URL resolves.

## Step 4: Write the entries

If the file doesn't exist, start it with `# Learning Notes — <YYYY-MM-DD>`. Append each concept using exactly this structure:

```markdown
## <Concept Name>

<2–3 sentence explanation in plain language: what it is and why it matters.>

**Context:** <HH:MM> · `<project dir>` — <one line on how it came up, e.g. "while debugging duplicate order inserts under concurrent requests">

**Read:**
- *<Book Title>* (<Author>, <edition/year>) — Ch. <n> "<Chapter title>"<, §"<section>">
- ...

**Online:**
- [<Title>](<url>) — <one-line why>

**Related:** [[<Other Concept>]], [[<Other Concept>]]
```

For **Related**, prefer concepts already in the log (any day) so the notes link together; otherwise name closely related concepts worth knowing. If an entry was reused from an earlier day, add `**Previously:** [<date>](<YYYY-MM-DD>.md#<anchor>)` after Context.

When updating an existing entry with a new sighting, append another `**Context:**` line below the first.

## Finish

Tell the user briefly:
- how many sessions you processed
- which concepts you logged, by name, grouped by day file
- any chapters you marked `(chapter unverified)`

Then give the path of each file you changed.
