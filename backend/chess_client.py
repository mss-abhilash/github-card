"""
Chess.com API client — fetches player profile and stats from Chess.com's
public API. No auth required, but a User-Agent header is mandatory.

Endpoints used:
  - GET /pub/player/{username}        → profile info
  - GET /pub/player/{username}/stats  → ratings & game counts
"""
import httpx

API_BASE = "https://api.chess.com/pub"

HEADERS = {
    "User-Agent": "PlayerCardApp/1.0 (github-card project)",
    "Accept": "application/json",
}


class ChessUserNotFound(Exception):
    pass


class ChessRateLimited(Exception):
    pass


class ChessClient:
    def __init__(self):
        self._client = httpx.AsyncClient(headers=HEADERS, timeout=15.0, follow_redirects=True)

    async def close(self):
        await self._client.aclose()

    async def get_profile(self, username: str) -> dict:
        """Fetch player profile (name, avatar, title, followers, joined)."""
        resp = await self._client.get(f"{API_BASE}/player/{username.lower()}")
        if resp.status_code == 404:
            raise ChessUserNotFound(username)
        if resp.status_code == 429:
            raise ChessRateLimited("Chess.com API rate limit hit.")
        resp.raise_for_status()
        return resp.json()

    async def get_stats(self, username: str) -> dict:
        """
        Fetch player stats — ratings and win/loss/draw for each time control,
        plus puzzle rating if available.
        """
        resp = await self._client.get(f"{API_BASE}/player/{username.lower()}/stats")
        if resp.status_code == 404:
            # Stats endpoint 404s if the player exists but has no games
            return {}
        if resp.status_code == 429:
            raise ChessRateLimited("Chess.com API rate limit hit.")
        resp.raise_for_status()
        return resp.json()
