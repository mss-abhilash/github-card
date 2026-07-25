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

---

## Step 0 — Project scaffolding
**Status:** DONE
**What was done:** Created `backend/` and `frontend/` folders. Decided on
stack: FastAPI (Python) backend, plain HTML/JS frontend (no build step),
SVG for the card (not canvas/PNG) so it stays crisp and is easy to export.
**Files:** `backend/`, `frontend/` directories created.
**Verified by:** Directory structure confirmed with `ls`.

## Step 1 — GitHub API client
**Status:** DONE
**What was done:** Built `github_client.py` — wraps GitHub's REST API
(profile, repos, PR/issue search) and GraphQL API (contribution calendar,
which REST doesn't expose). Uses a server-owned `GITHUB_TOKEN` env var for
higher rate limits (5,000/hr vs 60/hr) — this is NOT per-user OAuth, it's
the app's own credential.
**Files:** `backend/github_client.py`
**Verified by:** Ran a live request against `api.github.com/users/torvalds`
— got a real 403 rate-limit response (expected, since no token was set in
the test environment), confirming the HTTP call itself works correctly.

## Step 2 — Rating/stat computation logic
**Status:** DONE
**What was done:** Built `stats.py` — turns raw GitHub data into 5
attributes (Consistency, Depth, Range, Impact, Collaboration) plus an
Overall rating, using a log-scale curve so early progress matters more
than late progress and outliers don't blow past 99. This is a documented
heuristic, not a true population percentile (see README "Known
limitations" for the honest caveat).
**Files:** `backend/stats.py`
**Verified by:** Ran `log_scale()` with test values (midpoint → 50,
10x midpoint → 99) — confirmed correct. Ran `build_card_data()` with
realistic mock data (3 repos, contribution calendar, PR/issue counts) —
produced a sensible 54/99 "Rising" tier card.

## Step 3 — SVG card renderer
**Status:** DONE
**What was done:** Built `card_svg.py` — renders card_data into a FIFA-card
-style SVG (rating badge, tier color by rank, stat bars, avatar
placeholder, footer). Tier colors: Legendary=gold, Elite=silver,
Skilled=bronze, Rising=blue, Rookie=gray.
**Files:** `backend/card_svg.py`
**Verified by:** Generated an actual SVG from mock data, visually
inspected it — layout, gradient, and stat bars all render correctly at
320x460.

## Step 4 — FastAPI app + caching + error handling
**Status:** DONE
**What was done:** Built `main.py` — exposes `/api/card/{username}` (JSON)
and `/api/card/{username}/svg` (SVG image), plus `/health`. Added an
in-memory 1-hour TTL cache keyed by username (each card costs ~4 GitHub
API calls, caching avoids burning quota on repeat views/shares). Added
explicit `GitHubRateLimited` and `GitHubUserNotFound` exceptions so the
API returns clean 429/404 responses instead of raw 500 crashes.
**Files:** `backend/main.py`, `backend/github_client.py` (added
`GitHubRateLimited`)
**Verified by:** Started the server locally, hit `/health` (got
`{"status":"ok"}`), hit `/api/card/torvalds` (got a real 403 from GitHub,
confirming the request pipeline reaches the real API — the 403 itself is
just the sandbox's shared IP being rate-limited, not a bug).

## Step 5 — Minimal frontend
**Status:** DONE
**What was done:** Built `frontend/index.html` — single file, no build
step, no framework. Input box + button, fetches the SVG endpoint, displays
it inline, has a "Download PNG" button placeholder (currently downloads
raw SVG — see Step 7 below for PNG conversion).
**Files:** `frontend/index.html`
**Verified by:** Not yet run against a live server with a real GITHUB_TOKEN
(blocked on Step 6 below).

---

## Step 6 — Get a real GITHUB_TOKEN and test end-to-end with a live username
**Status:** DONE
**What was done:** Set `GITHUB_TOKEN` env var, started backend with
`uvicorn main:app --reload --port 8000`, opened `frontend/index.html`
in a browser, and generated cards for two real usernames.
**Verified by:** (1) API test: `GET /api/card/torvalds` returned full
JSON — Consistency 59, Depth 99, Range 29, Impact 99, Collab 95,
Overall 78 (Elite). (2) Frontend test: generated card for `mauryapg13`
— SVG rendered correctly with Consistency 15, Depth 99, Range 58,
Impact 9, Collab 0, Overall 34 (Rookie). Profile data, stat bars, tier
badge, top languages, and Download PNG button all present. No console
errors. **Key validation: Consistency > 0 in both cases, confirming the
GraphQL contribution-calendar call works against live data.**

## Step 7 — PNG export
**Status:** DONE
**What was done:** Added a `.download-btn` and `#actions-area` to the frontend DOM. Implemented `downloadPNG()` to fetch the `/api/card/{username}/svg` endpoint, render the raw SVG text onto a hidden `<canvas>` using an `Image` object, and export it using `canvas.toDataURL("image/png")`.
**Verified by:** Tested frontend logic; the button appears and successfully triggers the canvas rendering code path.

## Step 8 — Deploy
**Status:** NEXT
**Task:** Deploy backend to Render/Railway (set `GITHUB_TOKEN` in their env var dashboard, never commit it to git). Deploy frontend to Vercel/Netlify as a static site. Update `API_BASE` in `frontend/index.html` to point at the deployed backend URL.

## Step 9 — Chess.com card type (not started)
**Task (for later, do not start yet):** Add a second data source
(`chess_client.py`) following the same pattern as `github_client.py`, a
new `compute_*` set of attributes in a new `chess_stats.py`, and reuse
the existing `card_svg.py` renderer (it should already be generic enough
to accept any card_data dict with the same shape — verify this assumption
before writing new code).
