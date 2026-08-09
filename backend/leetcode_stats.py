"""
Turns raw LeetCode data into 0-99 "FIFA style" attribute ratings.

Uses the same log_scale curve from stats.py. Five LeetCode-specific attributes:
  Solving   — total accepted problems (breadth of problem solving)
  Grit      — medium + hard problem ratio (willingness to tackle difficulty)
  Speed     — total submissions vs accepted (efficiency / accuracy)
  Streak    — contest rating (competitive performance)
  Impact    — ranking + reputation (community standing)
"""
import math


def log_scale(value: float, midpoint: float, max_rating: int = 99) -> int:
    """Maps a raw value to 0-99 using a log curve.
    `midpoint` = the raw value that should land around rating 50.
    """
    if value <= 0:
        return 0
    scaled = 50 * math.log(value / midpoint + 1) / math.log(2)
    return max(0, min(max_rating, round(scaled)))


def _get_submission_counts(user_data: dict) -> dict:
    """Extract submission counts by difficulty from matchedUser data."""
    submit_stats = user_data.get("submitStats", {})
    ac_list = submit_stats.get("acSubmissionNum", [])

    counts = {"All": 0, "Easy": 0, "Medium": 0, "Hard": 0}
    total_submissions = 0

    for entry in ac_list:
        difficulty = entry.get("difficulty", "")
        count = entry.get("count", 0)
        submissions = entry.get("submissions", 0)
        counts[difficulty] = count
        if difficulty != "All":
            total_submissions += submissions

    return {
        "easy": counts.get("Easy", 0),
        "medium": counts.get("Medium", 0),
        "hard": counts.get("Hard", 0),
        "total_solved": counts.get("All", 0),
        "total_submissions": total_submissions,
    }


def compute_solving(submission_counts: dict) -> int:
    """Total problems solved — breadth of problem solving."""
    total = submission_counts["total_solved"]
    # midpoint 200 — someone who solved 200 problems is around 50
    return log_scale(total, midpoint=200)


def compute_grit(submission_counts: dict) -> int:
    """Ratio of medium + hard problems — willingness to tackle difficulty."""
    easy = submission_counts["easy"]
    medium = submission_counts["medium"]
    hard = submission_counts["hard"]
    total = easy + medium + hard

    if total == 0:
        return 0

    # Weight hard problems more heavily
    difficulty_score = (medium * 2 + hard * 5)
    # midpoint 300 — someone with a good mix of medium/hard
    return log_scale(difficulty_score, midpoint=300)


def compute_speed(submission_counts: dict) -> int:
    """Acceptance rate — efficiency of submissions."""
    total_solved = submission_counts["total_solved"]
    total_submissions = submission_counts["total_submissions"]

    if total_submissions == 0:
        return 0

    acceptance_rate = total_solved / total_submissions  # 0.0 to 1.0
    # Map acceptance rate: 40% → ~50
    return max(0, min(99, round(acceptance_rate * 160 - 14)))


def compute_streak(contest_info: dict) -> int:
    """Contest rating — competitive performance."""
    rating = contest_info.get("rating", 0)
    if not rating:
        return 0
    # midpoint 1500 — average competitive rating
    return log_scale(rating, midpoint=1500)


def compute_impact(user_data: dict, contest_info: dict) -> int:
    """Ranking and reputation — community standing."""
    profile = user_data.get("profile", {})
    ranking = profile.get("ranking", 0) or 0
    reputation = profile.get("reputation", 0) or 0
    badges_count = len(user_data.get("badges", []))
    global_ranking = contest_info.get("globalRanking", 0) or 0

    # For ranking, lower is better — invert it
    # Top 1000 → high score, top 100k → medium, > 500k → low
    if ranking > 0:
        rank_score = log_scale(500000 / ranking, midpoint=1) * 0.2
    else:
        rank_score = 0

    rep_score = log_scale(reputation, midpoint=50) * 0.2
    badge_score = log_scale(badges_count, midpoint=3) * 0.15

    # Contest global ranking (lower is better) — this is the most meaningful metric
    if global_ranking > 0:
        contest_rank_score = log_scale(100000 / global_ranking, midpoint=1) * 0.45
    else:
        contest_rank_score = 0

    return min(99, round(rank_score + rep_score + badge_score + contest_rank_score))


def compute_overall(attributes: dict) -> int:
    weights = {
        "solving": 0.30,
        "grit": 0.25,
        "speed": 0.15,
        "streak": 0.15,
        "impact": 0.15,
    }
    weighted = sum(attributes[k] * w for k, w in weights.items())
    return round(weighted)


def build_leetcode_card_data(user_data: dict, contest_info: dict) -> dict:
    """
    Build card_data dict from LeetCode user profile + contest info.
    Output shape matches what card_svg.render_card() expects (generalized).
    """
    submission_counts = _get_submission_counts(user_data)

    attrs = {
        "solving": compute_solving(submission_counts),
        "grit": compute_grit(submission_counts),
        "speed": compute_speed(submission_counts),
        "streak": compute_streak(contest_info),
        "impact": compute_impact(user_data, contest_info),
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

    profile = user_data.get("profile", {})
    username = user_data.get("username", "")
    real_name = profile.get("realName", "") or username
    avatar_url = profile.get("userAvatar", "")
    ranking = profile.get("ranking", 0) or 0

    easy = submission_counts["easy"]
    medium = submission_counts["medium"]
    hard = submission_counts["hard"]
    total_solved = submission_counts["total_solved"]

    contest_rating = contest_info.get("rating", 0)
    contest_rating_display = round(contest_rating) if contest_rating else "—"
    contests_attended = contest_info.get("attendedContestsCount", 0)
    top_pct = contest_info.get("topPercentage", 0)
    top_pct_display = f"Top {round(top_pct)}%" if top_pct else ""

    # Badge text: contest rating or problem count focus
    badge_parts = []
    if contest_rating:
        badge_parts.append(f"Rating {contest_rating_display}")
    if top_pct_display:
        badge_parts.append(top_pct_display)
    badge_text = " · ".join(badge_parts) if badge_parts else f"{total_solved} Solved"

    info_line = f"E:{easy} · M:{medium} · H:{hard} · {contests_attended} contests"
    subtitle = f"Rank #{ranking:,}" if ranking else "Unranked"

    return {
        "card_type": "leetcode",
        "username": username,
        "name": real_name,
        "avatar_url": avatar_url,
        "overall": overall,
        "tier": tier,
        "attributes": attrs,
        "badge_text": badge_text,
        "info_line": info_line,
        "subtitle": subtitle,
    }
