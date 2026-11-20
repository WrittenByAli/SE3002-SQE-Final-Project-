---
name: sqe-ai-log
description: "Record generative-AI use in docs/team/ai-use-record.md as the assignment requires (tool, purpose, output, what was checked or changed) and save the prompts. Use before committing anything AI-assisted, at the end of a session, or when asked \"log this\", \"AI record\", \"disclose AI\"."
---

# AI-use logging (assignment §7, examined in the viva, part of the 20 marks)

Undisclosed AI use = zero for the component, and possibly for the whole project. Log **every** AI-assisted output that is committed.

## Steps
1. Identify the member and what was produced in this session (files, analysis, explanations used).
2. Append one row per distinct purpose to `docs/team/ai-use-record.md`:
   `| # | YYYY-MM-DD | <member> | Claude Code (<model>) | <purpose> | <output files/paths> | <what the member verified or changed> |`
   - The last column must be **specific** ("ran tests, 2 failed, fixed fixture; rewrote MC/DC table rows 3–5 after checking source"),
     never "reviewed". If the member has not checked it yet, write `PENDING: <what must be checked>` and tell them.
3. Save the prompts: `docs/team/ai-prompts/<member>/<YYYY-MM-DD>-<topic>.md` (the member's prompts plus a short summary of the answer).
4. Add the trailer to AI-assisted commits: `Co-Authored-By: Claude <noreply@anthropic.com>` (commit stays authored by the member).

## Guardrails
- Never mark AI output as checked on the member's behalf.
- If the output is evidence (tool reports), confirm it came from a real run and record the artifact path.
