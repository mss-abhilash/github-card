"""
Turns raw Chess.com data into 0-99 "FIFA style" attribute ratings.

Uses the same log_scale curve from stats.py. Five chess-specific attributes:
  Speed     — bullet/blitz rating (fast time controls)
  Strategy  — rapid/daily rating (slow, strategic play)
  Tactical  — puzzle/tactics rating
  Consistency — win-rate across all time controls
  Experience  — total games played
"""
import math
from datetime import datetime, timezone


def log_scale(value: float, midpoint: float, max_rating: int = 99) -> int:
    """Maps a raw value to 0-99 using a log curve.
    `midpoint` = the raw value that should land around rating 50.
    """
    if value <= 0:
        return 0
    scaled = 50 * math.log(value / midpoint + 1) / math.log(2)
    return max(0, min(max_rating, round(scaled)))


def _best_rating(stats: dict, *keys: str) -> int:
    """Return the highest rating across the given stat categories.
    Checks 'last.rating', 'best.rating', and 'highest.rating' (tactics format).
    """
    best = 0
    for key in keys:
        cat = stats.get(key, {})
        if not isinstance(cat, dict):
            continue
        # Standard time controls: last.rating and best.rating
        for subkey in ("last", "best", "highest"):
            entry = cat.get(subkey, {})
            if isinstance(entry, dict):
                rating = entry.get("rating", 0)
                if rating > best:
                    best = rating
    return best


def _total_games(stats: dict, *keys: str) -> tuple[int, int, int]:
    """Sum up (wins, losses, draws) across given stat categories.
    Chess.com puts record at the category root level: {record: {win, loss, draw}}.
    """
    wins, losses, draws = 0, 0, 0
    for key in keys:
        cat = stats.get(key, {})
        if not isinstance(cat, dict):
            continue
        record = cat.get("record", {})
        wins += record.get("win", 0)
        losses += record.get("loss", 0)
        draws += record.get("draw", 0)
    return wins, losses, draws


ALL_TIME_CONTROLS = [
    "chess_blitz", "chess_bullet", "chess_rapid", "chess_daily",
]


def compute_speed(stats: dict) -> int:
    """Speed rating from bullet/blitz — fast time controls."""
    rating = _best_rating(stats, "chess_bullet", "chess_blitz")
    # midpoint 1200 — average club player
    return log_scale(rating, midpoint=1200)


def compute_strategy(stats: dict) -> int:
    """Strategy rating from rapid/daily — slow, strategic play."""
    rating = _best_rating(stats, "chess_rapid", "chess_daily")
    return log_scale(rating, midpoint=1200)


def compute_tactical(stats: dict) -> int:
    """Tactical rating from puzzle/tactics trainer."""
    rating = _best_rating(stats, "tactics", "puzzle_rush")
    return log_scale(rating, midpoint=1200)


def compute_consistency(stats: dict) -> int:
    """Win-rate across all time controls as a consistency measure."""
    wins, losses, draws = _total_games(stats, *ALL_TIME_CONTROLS)
    total = wins + losses + draws
    if total == 0:
        return 0
    win_rate = wins / total  # 0.0 to 1.0
    # Map win_rate directly — 50% (0.5) → ~50 rating
    # Use a simple scale: win_rate * 99, capped
    return max(0, min(99, round(win_rate * 130 - 15)))


def compute_experience(stats: dict) -> int:
    """Total games played across all time controls."""
    wins, losses, draws = _total_games(stats, *ALL_TIME_CONTROLS)
    total = wins + losses + draws
    return log_scale(total, midpoint=500)


def compute_overall(attributes: dict) -> int:
    weights = {
        "speed": 0.25,
        "strategy": 0.25,
        "tactical": 0.20,
        "consistency": 0.15,
        "experience": 0.15,
    }
    weighted = sum(attributes[k] * w for k, w in weights.items())
    return round(weighted)


def _account_age_years(profile: dict) -> float:
    """Calculate account age from joined timestamp."""
    joined = profile.get("joined", 0)
    if not joined:
        return 0.0
    joined_dt = datetime.fromtimestamp(joined, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    return round((now - joined_dt).days / 365.25, 1)


def _get_title_display(profile: dict) -> str:
    """Get chess title (GM, IM, FM, etc.) for display."""
    title = profile.get("title", "")
    return title if title else ""


def build_chess_card_data(profile: dict, stats: dict) -> dict:
    """
    Build card_data dict from Chess.com profile + stats.
    Output shape matches what card_svg.render_card() expects (generalized).
    """
    attrs = {
        "speed": compute_speed(stats),
        "strategy": compute_strategy(stats),
        "tactical": compute_tactical(stats),
        "consistency": compute_consistency(stats),
        "experience": compute_experience(stats),
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

    # Build game totals for info line
    wins, losses, draws = _total_games(stats, *ALL_TIME_CONTROLS)
    total_games = wins + losses + draws
    title = _get_title_display(profile)
    followers = profile.get("followers", 0)
    age = _account_age_years(profile)

    # Best rating across all time controls
    best_overall_rating = max(
        _best_rating(stats, tc) for tc in ALL_TIME_CONTROLS
    ) if stats else 0

    # Determine primary time control
    time_control_labels = {
        "chess_bullet": "Bullet",
        "chess_blitz": "Blitz",
        "chess_rapid": "Rapid",
        "chess_daily": "Daily",
    }
    primary_tc = "Blitz"
    best_tc_rating = 0
    for tc in ALL_TIME_CONTROLS:
        r = _best_rating(stats, tc)
        if r > best_tc_rating:
            best_tc_rating = r
            primary_tc = time_control_labels.get(tc, "Blitz")

    return {
        "card_type": "chess",
        "username": profile.get("username", ""),
        "name": profile.get("name") or profile.get("username", ""),
        "avatar_url": profile.get("avatar", ""),
        "overall": overall,
        "tier": tier,
        "attributes": attrs,
        "badge_text": f"{title} · {primary_tc}" if title else primary_tc,
        "info_line": f"{total_games} games · {followers} followers · Peak {best_overall_rating}",
        "subtitle": f"{age} yrs on Chess.com",
        "chess_title": title,
    }
