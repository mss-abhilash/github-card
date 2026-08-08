"""
Turns raw GitHub data into 0-99 "FIFA style" attribute ratings.

Design principle: don't map raw numbers 1:1 to a rating. Use log-scaling
so that early progress moves the needle a lot (motivating for new devs)
and the scale doesn't blow past 99 for outliers (Linus Torvalds shouldn't
break the UI). This is a heuristic curve, not a true population percentile —
documented here so it's easy to defend in an interview, and easy to swap
for real percentile data later if you collect a reference sample.
"""
import math
from datetime import datetime, timezone


def log_scale(value: float, midpoint: float, max_rating: int = 99) -> int:
    """
    Maps a raw value to 0-99 using a log curve.
    `midpoint` = the raw value that should land around rating 50.
    """
    if value <= 0:
        return 0
    scaled = 50 * math.log(value / midpoint + 1) / math.log(2)
    return max(0, min(max_rating, round(scaled)))


def compute_consistency(calendar: dict) -> int:
    weeks = calendar.get("weeks", [])
    if not weeks:
        return 0
    active_weeks = sum(
        1 for w in weeks if any(d["contributionCount"] > 0 for d in w["contributionDays"])
    )
    total_weeks = len(weeks)
    active_ratio = active_weeks / total_weeks if total_weeks else 0

    all_days = [d for w in weeks for d in w["contributionDays"]]
    streak = 0
    for day in reversed(all_days):
        if day["contributionCount"] > 0:
            streak += 1
        else:
            break

    ratio_score = active_ratio * 60
    streak_score = min(39, log_scale(streak, midpoint=14, max_rating=39))
    return min(99, round(ratio_score + streak_score))


def compute_depth(repos: list[dict]) -> int:
    if not repos:
        return 0
    sizes = [r.get("size", 0) for r in repos]
    avg_size = sum(sizes) / len(sizes)
    return log_scale(avg_size, midpoint=800)


def compute_range(repos: list[dict]) -> int:
    languages = {r["language"] for r in repos if r.get("language")}
    return log_scale(len(languages), midpoint=4)


def compute_impact(profile: dict, repos: list[dict]) -> int:
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    followers = profile.get("followers", 0)

    star_score = log_scale(total_stars, midpoint=15) * 0.6
    fork_score = log_scale(total_forks, midpoint=8) * 0.2
    follower_score = log_scale(followers, midpoint=20) * 0.2
    return min(99, round(star_score + fork_score + follower_score))


def compute_collaboration(pr_issue_data: dict) -> int:
    merged = pr_issue_data.get("prs_merged", 0)
    opened = pr_issue_data.get("prs_opened", 0)
    issues = pr_issue_data.get("issues_opened", 0)

    merge_score = log_scale(merged, midpoint=5) * 0.6
    pr_score = log_scale(opened, midpoint=8) * 0.2
    issue_score = log_scale(issues, midpoint=5) * 0.2
    return min(99, round(merge_score + pr_score + issue_score))


def compute_overall(attributes: dict) -> int:
    weights = {
        "consistency": 0.25,
        "depth": 0.2,
        "range": 0.15,
        "impact": 0.25,
        "collaboration": 0.15,
    }
    weighted = sum(attributes[k] * w for k, w in weights.items())
    return round(weighted)


def account_age_years(profile: dict) -> float:
    created = datetime.fromisoformat(profile["created_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return round((now - created).days / 365.25, 1)


def build_card_data(profile: dict, repos: list[dict], pr_issue_data: dict, calendar: dict) -> dict:
    attrs = {
        "consistency": compute_consistency(calendar),
        "depth": compute_depth(repos),
        "range": compute_range(repos),
        "impact": compute_impact(profile, repos),
        "collaboration": compute_collaboration(pr_issue_data),
    }
    overall = compute_overall(attrs)

    if overall >= 85:
        tier = "Legendary"
    elif overall >= 70:
        tier = "Elite"
    elif overall >= 55:
        tier = "Skilled"
    elif overall >= 35:
        tier = "Rising"
    else:
        tier = "Rookie"

    top_languages = sorted(
        {r["language"] for r in repos if r.get("language")},
        key=lambda lang: sum(1 for r in repos if r.get("language") == lang),
        reverse=True,
    )[:3]

    public_repos = profile.get("public_repos", 0)
    followers = profile.get("followers", 0)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    age = account_age_years(profile)
    langs = " · ".join(top_languages) or "—"

    return {
        "card_type": "github",
        "username": profile["login"],
        "name": profile.get("name") or profile["login"],
        "avatar_url": profile.get("avatar_url"),
        "overall": overall,
        "tier": tier,
        "attributes": attrs,
        "top_languages": top_languages,
        "public_repos": public_repos,
        "followers": followers,
        "account_age_years": age,
        "total_stars": total_stars,
        # Generalized fields for card_svg renderer
        "badge_text": langs,
        "info_line": f"{public_repos} repos · {followers} followers · {total_stars}★",
        "subtitle": f"{age} yrs on GitHub",
    }
