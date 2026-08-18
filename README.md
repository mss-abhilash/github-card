# GitHub Player Card

Enter a GitHub username, get a shareable FIFA-style stat card generated
from their real public activity.

## How the ratings work (the part worth explaining in interviews)

Raw numbers are **not** mapped 1:1 to ratings. Every stat goes through a
log-scale curve (`stats.py::log_scale`) so that early progress moves the
needle a lot and outliers don't blow past 99. This is a heuristic, not a
true population percentile — the natural v2 upgrade is to sample a
reference population of real usernames and rank against the actual
distribution instead of a hand-picked curve.

| Attribute | What it measures | Source |
|---|---|---|
| Consistency | Active-week ratio + current streak | GraphQL contribution calendar |
| Depth | Avg repo size as an effort proxy | REST repos list |
| Range | Language diversity | REST repos list |
| Impact | Stars + forks + followers | REST repos + profile |
| Collaboration | PRs opened/merged + issues | Search API |

## Setup

### 1. Get a GitHub personal access token
This is **your own** token, not the end user's — it just raises your rate
limit from 60/hr to 5,000/hr and unlocks the GraphQL contribution calendar.
Create one at https://github.com/settings/tokens.

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
export GITHUB_TOKEN=ghp_yourtokenhere
uvicorn main:app --reload --port 8000
```

### 3. Frontend
Open `frontend/index.html` in a browser. Update `API_BASE` in the
`<script>` tag once you deploy the backend.

## Deploying
- **Backend:** Render or Railway. Set `GITHUB_TOKEN` env var there.
- **Frontend:** Vercel or Netlify.

