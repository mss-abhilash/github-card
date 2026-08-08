# Project Step Log — GitHub Player Card

## How to use this file (read this first, every time)
This file is the single source of truth for project state. Rules for
whoever (or whatever) is working on this next:

1. **Read the whole file before doing anything.** Don't assume — check
   what's actually marked DONE below.
2. **Only work on the step marked `NEXT`.** Do not jump ahead, do not
   redo a step marked DONE, do not "improve" a DONE step unless the user
   explicitly asks for that as a new step.
3. **When a `NEXT` step is finished:** change its status to `DONE`, add a
   one-line verification note (what you ran/checked to confirm it works),
   then add a new step below it marked `NEXT` with a concrete, narrow task.
4. **Never mark something DONE without verifying it** — run it, test it,
   or explain exactly why it can't be tested right now.
5. **If something in this log looks wrong or outdated, stop and ask the
   user** rather than silently reinterpreting it.
6. **Check the "Decisions" section below before suggesting new features** —
   some ideas were deliberately considered and rejected. Don't re-propose
   them without the user raising it first.

---

## Decisions (things considered and settled — don't relitigate these)
- **BGMI card: rejected.** No official public API exists for BGMI (the
  official PUBG Developer API is for PC/console PUBG only, separate
  backend). A Gemini-vision-based screenshot extraction workaround was
  scoped and is technically viable, but the user decided against adding
  it to keep the resume/project story clean and focused on API-integration
  card types (GitHub, Chess.com, Codeforces). Do not re-add BGMI or
  propose it again unless the user brings it up.
- **Token type: classic PAT, not fine-grained.** Fine-grained tokens have
  a resource-owner restriction on GraphQL calls (the token's resource
  owner must match the resource being queried), which breaks the
  "look up any username's contribution calendar" use case. Classic PATs
  with no scopes checked read all public data without this restriction.
  Use classic tokens for this project.
- **Roadmap after GitHub:** Chess.com next, then Codeforces/LeetCode.
  Both follow the same pattern as the GitHub card (client → stats →
  reuse `card_svg.py`). No 4th card type is planned unless the user
  requests one.

---

## Step 0 — Project scaffolding
**Status:** DONE
**What was done:** Created `backend/` and `frontend/` folders. Stack:
FastAPI backend, plain HTML/JS frontend (no build step), SVG cards.

## Step 1 — GitHub API client
**Status:** DONE
**What was done:** `github_client.py` — REST for profile/repos, GraphQL
for contribution calendar. Uses server-owned `GITHUB_TOKEN`.
**Verified by:** Live request against `api.github.com/users/torvalds`.

## Step 2 — Rating/stat computation logic
**Status:** DONE
**What was done:** `stats.py` — 5 attributes (Consistency, Depth, Range,
Impact, Collaboration) + Overall, via log-scale curve.
**Verified by:** Tested `log_scale()` boundary values and `build_card_data()`
with realistic mock data.

## Step 3 — SVG card renderer
**Status:** DONE
**What was done:** `card_svg.py` — FIFA-style card, tier colors, stat bars.
**Verified by:** Generated and visually inspected an SVG from mock data.

## Step 4 — FastAPI app + caching + error handling
**Status:** DONE
**What was done:** `main.py` — `/api/card/{username}` and
`/api/card/{username}/svg` endpoints, 1hr in-memory cache, clean
404/429 error handling.
**Verified by:** Local server, `/health` check, live 403 confirming the
request pipeline reaches GitHub's real API.

## Step 5 — Minimal frontend
**Status:** DONE
**What was done:** `frontend/index.html` — single file, no framework,
input box, fetches SVG endpoint, download button.

## Step 6 — Get a real GITHUB_TOKEN and test end-to-end with a live username
**Status:** DONE
**What was done:** Initial attempt used a fine-grained token, which hit
the resource-owner restriction on GraphQL (Consistency stat stayed at 0
for non-owner usernames). Switched to a classic PAT with no scopes
checked — resolved the issue. Also fixed two setup issues along the way:
(1) `export` doesn't work in PowerShell, needed `$env:GITHUB_TOKEN=...`
instead; (2) uvicorn was being run from the project root instead of
`backend/`, causing "could not import module main."
**Verified by:** Full end-to-end run — backend serving real card data
(including non-zero Consistency for a live username), frontend rendering
the SVG card correctly in-browser.

## Step 6.5 — Deployment
**Status:** DONE
**What was done:** Project deployed (backend + frontend live).
**Verified by:** User confirmed deployment is live.
**Note for next session:** if deployment specifics (host used, live URL,
CORS origin restriction) aren't recorded elsewhere, ask the user to fill
them in here for future reference — currently not logged in detail.

---

## Step 7 — Chess.com card type
**Status:** DONE
**What was done:** Built `chess_client.py` (async httpx, profile + stats endpoints,
`User-Agent` header required by Chess.com, `follow_redirects=True` for username
casing redirects), `chess_stats.py` (5 attributes: Speed, Strategy, Tactical,
Consistency, Experience — using log_scale), generalized `card_svg.py` to accept
both GitHub and Chess card data via generic `badge_text`/`info_line`/`subtitle`
fields, added `/api/chess/{username}` and `/api/chess/{username}/svg` endpoints
to `main.py` with separate cache, updated `frontend/index.html` with pill-style
card-type toggle (GitHub / Chess.com), chess-specific stat labels (SPD/STR/TAC/
CON/EXP), chess piece icon, and GM/IM/FM title badge display.
**Verified by:** Live end-to-end test — `magnuscarlsen` returns Elite 77 card
with SPD 97, STR 90, TAC 21, CON 76, EXP 99. Frontend renders card with
correct stats, tier colors, chess icon, GM title badge, and "Chess.com Player
Card" footer. GitHub cards still work (same generalized SVG renderer). Also
changed `API_BASE` from hardcoded Render URL to relative paths (empty string)
so the frontend works both locally and when deployed via same-origin serving.
**Note:** `hikaru` returns empty stats from Chess.com's API (appears to be a
server-side issue on Chess.com), so all stats come back as 0 for that user.
Other users (magnuscarlsen, gothamchess) work fine.

## Step 8 — Codeforces/LeetCode card type
**Status:** NEXT
**Task:** Same pattern again — `codeforces_client.py` (public API, no
auth: `codeforces.com/api/user.info?handles=...`), matching stats module,
reuse `card_svg.py`.

## Step 9 — PNG export
**Status:** Not started — low priority, do after Steps 7-8.
**Task:** Client-side SVG→PNG conversion via canvas, for platforms that
don't render inline SVG well.

## Step 10 — BGMI / Gemini vision card
**Status:** Rejected — see "Decisions" section above. Do not start this
unless the user explicitly reopens it.