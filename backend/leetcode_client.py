"""
LeetCode GraphQL API client — fetches user profile and submission stats
from LeetCode's public GraphQL endpoint. No auth required.

Endpoint: POST https://leetcode.com/graphql
"""
import httpx

API_URL = "https://leetcode.com/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "PlayerCardApp/1.0 (github-card project)",
    "Referer": "https://leetcode.com",
}

# GraphQL query to fetch profile + submit stats in a single request
USER_PROFILE_QUERY = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      realName
      ranking
      reputation
      userAvatar
      starRating
    }
    badges {
      name
    }
    submitStats: submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
        submissions
      }
    }
  }
}
"""

# Separate query for contest info
CONTEST_QUERY = """
query userContestRankingInfo($username: String!) {
  userContestRanking(username: $username) {
    attendedContestsCount
    rating
    globalRanking
    topPercentage
  }
}
"""


class LeetCodeUserNotFound(Exception):
    pass


class LeetCodeRateLimited(Exception):
    pass


class LeetCodeClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            headers=HEADERS, timeout=15.0, follow_redirects=True
        )

    async def close(self):
        await self._client.aclose()

    async def _graphql(self, query: str, variables: dict) -> dict:
        """Send a GraphQL request and return the data."""
        resp = await self._client.post(
            API_URL,
            json={"query": query, "variables": variables},
        )
        if resp.status_code == 429:
            raise LeetCodeRateLimited("LeetCode API rate limit hit.")
        if resp.status_code == 403:
            raise LeetCodeRateLimited(
                "LeetCode API returned 403 — may be rate-limited or blocked."
            )
        resp.raise_for_status()
        return resp.json()

    async def get_user_profile(self, username: str) -> dict:
        """Fetch user profile and submission stats."""
        result = await self._graphql(USER_PROFILE_QUERY, {"username": username})
        data = result.get("data", {})
        user = data.get("matchedUser")
        if user is None:
            raise LeetCodeUserNotFound(username)
        return user

    async def get_contest_info(self, username: str) -> dict:
        """Fetch contest ranking info. Returns {} if user has no contest history."""
        result = await self._graphql(CONTEST_QUERY, {"username": username})
        data = result.get("data", {})
        contest = data.get("userContestRanking")
        return contest or {}
