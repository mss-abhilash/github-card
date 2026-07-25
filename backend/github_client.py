"""
GitHub API client — handles both REST (repos, profile) and GraphQL
(contribution calendar) calls. Uses a server-owned personal access token
(set via GITHUB_TOKEN env var) so we get 5,000 req/hr instead of 60/hr,
and so we can query the contribution calendar (REST doesn't expose it).

The token only needs `public_repo` / default read scopes — it is NOT tied
to any end user, it's just your app's own credential for higher rate limits.
"""
import os
import httpx

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REST_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


class GitHubUserNotFound(Exception):
    pass


class GitHubRateLimited(Exception):
    pass


class GitHubClient:
    def __init__(self):
        self._client = httpx.AsyncClient(headers=HEADERS, timeout=15.0)

    async def close(self):
        await self._client.aclose()

    async def get_profile(self, username: str) -> dict:
        resp = await self._client.get(f"{REST_BASE}/users/{username}")
        if resp.status_code == 404:
            raise GitHubUserNotFound(username)
        if resp.status_code == 403 and resp.headers.get("x-ratelimit-remaining") == "0":
            raise GitHubRateLimited(
                "GitHub API rate limit hit. Set GITHUB_TOKEN for 5,000 req/hr instead of 60/hr."
            )
        resp.raise_for_status()
        return resp.json()

    async def get_repos(self, username: str) -> list[dict]:
        """Fetch all public, non-fork repos (paginated)."""
        repos = []
        page = 1
        while True:
            resp = await self._client.get(
                f"{REST_BASE}/users/{username}/repos",
                params={"per_page": 100, "page": page, "type": "owner", "sort": "updated"},
            )
            if resp.status_code in (401, 403):
                raise GitHubRateLimited("GitHub API rate limit hit.")
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            repos.extend(r for r in batch if not r.get("fork"))
            if len(batch) < 100:
                break
            page += 1
            if page > 5:  # safety cap: 500 repos is plenty for stats
                break
        return repos

    async def get_pr_and_issue_counts(self, username: str) -> dict:
        """Use the Search API to count PRs/issues without walking every repo."""
        async def search_count(query: str) -> int:
            resp = await self._client.get(
                f"{REST_BASE}/search/issues",
                params={"q": query, "per_page": 1},
            )
            if resp.status_code in (401, 403):
                raise GitHubRateLimited("GitHub API rate limit hit.")
            resp.raise_for_status()
            return resp.json().get("total_count", 0)

        prs_opened = await search_count(f"author:{username} type:pr")
        prs_merged = await search_count(f"author:{username} type:pr is:merged")
        issues_opened = await search_count(f"author:{username} type:issue")
        return {"prs_opened": prs_opened, "prs_merged": prs_merged, "issues_opened": issues_opened}

    async def get_contribution_calendar(self, username: str) -> dict:
        """
        GraphQL is the only way to get the contribution calendar.
        Returns weekly contribution counts for the last year.
        """
        query = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
            }
          }
        }
        """
        resp = await self._client.post(
            GRAPHQL_URL, json={"query": query, "variables": {"login": username}}
        )
        if resp.status_code in (401, 403):
            raise GitHubRateLimited("GitHub API rate limit hit. GraphQL requires a valid token.")
        resp.raise_for_status()
        data = resp.json()
        if data.get("errors") or not data.get("data", {}).get("user"):
            return {"totalContributions": 0, "weeks": []}
        return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
