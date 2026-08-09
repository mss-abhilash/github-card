import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from github_client import GitHubClient, GitHubUserNotFound, GitHubRateLimited
from stats import build_card_data
from chess_client import ChessClient, ChessUserNotFound, ChessRateLimited
from chess_stats import build_chess_card_data
from leetcode_client import LeetCodeClient, LeetCodeUserNotFound, LeetCodeRateLimited
from leetcode_stats import build_leetcode_card_data
from card_svg import render_card

app = FastAPI(title="Player Card API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend domain before shipping
    allow_methods=["GET"],
    allow_headers=["*"],
)

github_client = GitHubClient()
chess_client = ChessClient()
leetcode_client = LeetCodeClient()

_github_cache: dict[str, tuple[float, dict]] = {}
_chess_cache: dict[str, tuple[float, dict]] = {}
_leetcode_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 60 * 60


# ============ GITHUB ============

async def get_github_card_data(username: str) -> dict:
    now = time.time()
    cached = _github_cache.get(username.lower())
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        profile = await github_client.get_profile(username)
        repos = await github_client.get_repos(username)
        pr_issue_data = await github_client.get_pr_and_issue_counts(username)
        calendar = await github_client.get_contribution_calendar(username)
    except GitHubUserNotFound:
        raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found")
    except GitHubRateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))

    data = build_card_data(profile, repos, pr_issue_data, calendar)
    _github_cache[username.lower()] = (now, data)
    return data


@app.get("/api/card/{username}")
async def get_card_json(username: str):
    return await get_github_card_data(username)


@app.get("/api/card/{username}/svg")
async def get_card_svg(username: str):
    data = await get_github_card_data(username)
    svg = render_card(data)
    return Response(content=svg, media_type="image/svg+xml")


# ============ CHESS.COM ============

async def get_chess_card_data(username: str) -> dict:
    now = time.time()
    cached = _chess_cache.get(username.lower())
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        profile = await chess_client.get_profile(username)
        stats = await chess_client.get_stats(username)
    except ChessUserNotFound:
        raise HTTPException(status_code=404, detail=f"Chess.com user '{username}' not found")
    except ChessRateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))

    data = build_chess_card_data(profile, stats)
    _chess_cache[username.lower()] = (now, data)
    return data


@app.get("/api/chess/{username}")
async def get_chess_json(username: str):
    return await get_chess_card_data(username)


@app.get("/api/chess/{username}/svg")
async def get_chess_svg(username: str):
    data = await get_chess_card_data(username)
    svg = render_card(data)
    return Response(content=svg, media_type="image/svg+xml")


# ============ LEETCODE ============

async def get_leetcode_card_data(username: str) -> dict:
    now = time.time()
    cached = _leetcode_cache.get(username.lower())
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        user_data = await leetcode_client.get_user_profile(username)
        contest_info = await leetcode_client.get_contest_info(username)
    except LeetCodeUserNotFound:
        raise HTTPException(status_code=404, detail=f"LeetCode user '{username}' not found")
    except LeetCodeRateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))

    data = build_leetcode_card_data(user_data, contest_info)
    _leetcode_cache[username.lower()] = (now, data)
    return data


@app.get("/api/leetcode/{username}")
async def get_leetcode_json(username: str):
    return await get_leetcode_card_data(username)


@app.get("/api/leetcode/{username}/svg")
async def get_leetcode_svg(username: str):
    data = await get_leetcode_card_data(username)
    svg = render_card(data)
    return Response(content=svg, media_type="image/svg+xml")


# ============ HEALTH & LIFECYCLE ============

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await github_client.close()
    await chess_client.close()
    await leetcode_client.close()

# Serve frontend static files — must be AFTER API routes
_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
