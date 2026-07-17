---
name: hubdoc-reviewer
description: Review all unreviewed documents in Hubdoc. Use when reviewing, processing or publishing Hubdoc receipts and bills.
---

# Hubdoc Reviewer

Reviews all documents in the Hubdoc Review tab, one by one, and (when
that is empty) the Failed tab.

## Skill maintenance goal

When adding or updating instructions in this skill, all documented methods
(JS selectors, click sequences, field-setting approaches) **must be tested
and verified to work** before being committed to the skill. Never document
untested code. The goal is to build bulletproof, reliable documentation so
that Hubdoc automation works first time without painful trial and error.

## Prerequisites

- The `agent-browser` skill is installed
- `agent-browser` connected to Chrome
- Tab open on https://app.hubdoc.com (open new one if necessary)

**Do not use** `agent-browser wait --load networkidle` — Xero never
reaches `networkidle`; use `agent-browser wait 3000` instead.

## Logging in

Always use "Sign In With Xero" — never use the email/password form:

```bash
# If the login page appears, click "Sign In With Xero"
agent-browser snapshot -i  # find the Sign In With Xero link
agent-browser click @eN
agent-browser wait 3000
```

**Click the "Sign In With Xero" button yourself — do not ask the user to.**
When already logged into Xero, this is SSO/OAuth to an already-authorized app,
NOT credential entry, so it is not a prohibited action. A stale
`?timeout=true` URL does NOT mean the session carried through — the button
must actually be clicked. Being too timid here just makes the user do a click
they delegated to you.

## Finding and interacting with page elements

**Always use `snapshot -i -C`** (not just `-i`) when looking for interactive
elements. The `-C` flag includes cursor-interactive elements (divs with
onclick, cursor:pointer) which many Hubdoc buttons and controls rely on.
Omitting `-C` will cause buttons to be invisible to the snapshot.

Choose the approach based on the nature of the element you're looking for:

- **Element with a known ID** (see [`references/fields.md`](references/fields.md))
  → JS eval to confirm which ref corresponds to that ID. Use JS only to
  *identify*, not to set values.
- **Labelled interactive element** (button, link, named input) →
  `snapshot -i -C`; use the ref directly.
- **Element identified by surrounding label text** (e.g. an unlabelled combobox
  next to an "Account Code" label) → `snapshot` (no `-i`) to get the full
  accessibility tree including non-interactive text, then find the label and
  identify the adjacent ref.
- **Nothing else works** → screenshot as a last resort for visual confirmation.

Taking into account some exceptions listed in the references below, as a
general rule once the correct ref is identified, first try to interact via

    agent-browser select/fill/click @eN

and similar, and only move onto other techniques like `eval` with JS
if that fails.

## Xero vs Xero Files

Hubdoc has a **Xero** destination section and a separate **Xero Files**
section. They are not interchangeable.

- For accounting publish configuration, always use the **Xero** section.
- **Never use the Xero Files section** when configuring or publishing a
  document for accounting.
- If publish fields are not visible, expand the **Xero** section itself,
  not the Xero Files section.
- When inspecting the DOM, verify you are using `xero-edit-integration`
  or `push-to-xero-*` fields, not `xerofiles-edit-integration` or
  `push-to-xerofiles-*` fields.
- **Scroll the Xero section into view before interacting with it.** Its
  controls (Status, Account Code, Contact, Publish button) sit below the
  fold on most viewports, and clicks on off-screen refs can miss or hit
  the wrong element. Use `agent-browser scrollintoview @ref` on the Xero
  section header (or any ref inside it) before snapshotting and acting:
  ```bash
  agent-browser snapshot -i -C            # find the Xero section ref
  agent-browser scrollintoview @eN        # scroll Xero section into view
  agent-browser snapshot -i -C            # re-snapshot for in-view refs
  ```
  Do NOT use `eval` with `scrollIntoView()` — prefer the native
  `agent-browser scrollintoview` command (same convention as
  `xero-browser` skill).

## Account code guidance

### FIND the written conventions and READ them — do not guess, do not ask first

Account-code conventions are **organisation-specific** and are usually
already **written down somewhere**. Locate that source and read it *before*
choosing a code — and before asking the user, who will rightly point you at
the file you failed to read.

Typical locations, in order of likelihood:

- a notes file under the user's notes directory (search for
  "Accounting", "accounts", "codes")
- an env var such as `$ACCOUNTING_NOTES`
- the project's `CLAUDE.md` / `AGENTS.md`, or a project-level skill
- the private project repo's own `.claude/skills/`

```bash
# Search likely sources for the supplier or a keyword:
grep -rinE "<supplier>|<keyword>" "$ACCOUNTING_NOTES" ~/notes ~/org 2>/dev/null
```

Record the location in the **project's own private skill or memory** once
found — not here (see AGENTS.md: this repo is public).

### Rules of thumb — VERIFY against the organisation's own conventions

These are common patterns, **not** authority. The organisation's written
conventions always win:

- **Capital equipment vs expense is threshold-based.** Many organisations
  capitalise equipment above some value (to a fixed-asset account such as
  *Computer Equipment*) and expense it below (to a repairs/maintenance or
  general account). **Find the threshold; never invent one.**
- **A part-payment can be ambiguous — flag it, don't silently decide.** When
  a deposit or instalment is *below* the threshold but the equipment's total
  cost is *above* it, the convention may not say which governs. Both readings
  are arguable: per-payment keeps each transaction self-consistent;
  per-item keeps one asset in one account instead of splitting it. **Surface
  the ambiguity to the user** rather than picking one and presenting it as
  the rule.
- **"IT Software and Consumables"-style accounts are for software and
  subscriptions — not hardware.** Hardware misfiled there is a common error.
- Fixed-asset accounts pair with an accumulated-depreciation account, so
  coding there has real tax/accounting consequences. If capitalise-vs-expense
  is genuinely unresolved by the written conventions, **stop and ask** — it
  is the adviser's call, not yours.

**Evidence (2026-07-17):** two hardware bills sat on an IT-software account.
The agent presented account options to the user instead of first locating the
organisation's written conventions — despite this section already saying to
consult local guidance. The file existed and answered it unambiguously.

Never rely on memorised codes from another tenant, and never guess when a
written convention exists.

## References

| Topic                                                         | File                                                       |
|---------------------------------------------------------------|------------------------------------------------------------|
| Field IDs and how to set values via JS                        | [references/fields.md](references/fields.md)               |
| Uploading PDFs / images                                       | [references/uploading.md](references/uploading.md)         |
| Downloading and reading Hubdoc PDFs                           | [references/downloading.md](references/downloading.md)     |
| Searching for documents                                       | [references/searching.md](references/searching.md)         |
| End-to-end review-tab process (per-document workflow)         | [references/review-process.md](references/review-process.md) |
| Duplicate-document detection, decision, trashing, drawer close | [references/duplicates.md](references/duplicates.md)       |
| Failed-tab processing (validation errors and re-publishing)   | [references/failed-tab.md](references/failed-tab.md)       |

Load the relevant reference for the specific subtask. The review-process
reference is the main per-document workflow and is needed for any
document review session; the others are loaded on demand.
