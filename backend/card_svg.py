"""
Renders card_data (from stats.build_card_data) into an SVG string.
SVG is used instead of a canvas/PNG library so the card stays crisp at
any resolution and is trivial to export client-side.
"""

TIER_COLORS = {
    "Legendary": ("#FFD700", "#B8860B"),
    "Elite": ("#C0C0C0", "#708090"),
    "Skilled": ("#CD7F32", "#8B4513"),
    "Rising": ("#4A90D9", "#2C5F8A"),
    "Rookie": ("#6B7280", "#374151"),
}


def stat_bar(x: int, y: int, label: str, value: int, width: int = 160) -> str:
    fill_width = int((value / 99) * width)
    return f"""
    <text x="{x}" y="{y}" font-family="Arial" font-size="12" fill="#1a1a1a" font-weight="600">{label}</text>
    <text x="{x + width}" y="{y}" font-family="Arial" font-size="12" fill="#1a1a1a" font-weight="700" text-anchor="end">{value}</text>
    <rect x="{x}" y="{y + 6}" width="{width}" height="8" rx="4" fill="#e5e7eb"/>
    <rect x="{x}" y="{y + 6}" width="{fill_width}" height="8" rx="4" fill="#111827"/>
    """


def render_card(card_data: dict) -> str:
    primary, secondary = TIER_COLORS.get(card_data["tier"], TIER_COLORS["Rookie"])
    attrs = card_data["attributes"]

    bars = ""
    labels = {
        "consistency": "CONSISTENCY",
        "depth": "DEPTH",
        "range": "RANGE",
        "impact": "IMPACT",
        "collaboration": "COLLAB",
    }
    for i, (key, label) in enumerate(labels.items()):
        bars += stat_bar(x=40, y=250 + i * 30, label=label, value=attrs[key])

    langs = " · ".join(card_data["top_languages"]) or "—"

    return f"""
<svg viewBox="0 0 320 460" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">
  <defs>
    <linearGradient id="cardBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{primary}"/>
      <stop offset="100%" stop-color="{secondary}"/>
    </linearGradient>
  </defs>

  <rect x="0" y="0" width="320" height="460" rx="20" fill="url(#cardBg)"/>
  <rect x="8" y="8" width="304" height="444" rx="16" fill="#ffffff" opacity="0.94"/>

  <text x="40" y="70" font-size="48" font-weight="800" fill="#111827">{card_data['overall']}</text>
  <text x="40" y="90" font-size="13" font-weight="700" fill="#374151" letter-spacing="1">{card_data['tier'].upper()}</text>

  <circle cx="250" cy="65" r="42" fill="#e5e7eb" stroke="{secondary}" stroke-width="3"/>
  <text x="250" y="72" font-size="12" fill="#9ca3af" text-anchor="middle">avatar</text>

  <text x="40" y="140" font-size="20" font-weight="700" fill="#111827">{card_data['name']}</text>
  <text x="40" y="160" font-size="13" fill="#6b7280">@{card_data['username']}</text>

  <text x="40" y="190" font-size="11" fill="#4b5563">{card_data['public_repos']} repos · {card_data['followers']} followers · {card_data['total_stars']}★</text>
  <text x="40" y="208" font-size="11" fill="#4b5563">{langs}</text>
  <text x="40" y="226" font-size="11" fill="#9ca3af">{card_data['account_age_years']} yrs on GitHub</text>

  {bars}

  <text x="160" y="435" font-size="10" fill="#9ca3af" text-anchor="middle">generated card · not an official GitHub product</text>
</svg>
"""
