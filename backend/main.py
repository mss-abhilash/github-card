import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from github_client import GitHubClient, GitHubUserNotFound, GitHubRateLimited
from stats import build_card_data
from card_svg import render_card

app = FastAPI(title="GitHub Card API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend domain before shipping
    allow_methods=["GET"],
    allow_headers=["*"],
)

client = GitHubClient()

_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 60 * 60


async def get_card_data(username: str) -> dict:
    now = time.time()
    cached = _cache.get(username.lower())
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        profile = await client.get_profile(username)
        repos = await client.get_repos(username)
        pr_issue_data = await client.get_pr_and_issue_counts(username)
        calendar = await client.get_contribution_calendar(username)
    except GitHubUserNotFound:
        raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found")
    except GitHubRateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))

    data = build_card_data(profile, repos, pr_issue_data, calendar)
    _cache[username.lower()] = (now, data)
    return data


@app.get("/api/card/{username}")
async def get_card_json(username: str):
    return await get_card_data(username)


@app.get("/api/card/{username}/svg")
async def get_card_svg(username: str):
    data = await get_card_data(username)
    svg = render_card(data)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await client.close()

# Serve frontend static files — must be AFTER API routes
_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
