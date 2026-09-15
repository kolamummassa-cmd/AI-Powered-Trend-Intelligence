"""Fast, explainable labels for trends before an AI analysis exists.

These labels help people scan the feed as soon as a source is fetched. They
are deliberately keyword-based rather than presented as an AI judgement; the
later Gemini analysis can still add a richer TrendJack topic and relevance
assessment.
"""

from __future__ import annotations

import re


SIGNAL_AREAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Funding & investment",
        (
            "funding", "funded", "raises", "raised", "investment", "investor", "venture",
            " vc ", "acquisition", "acquires", "acquired", "exit",
        ),
    ),
    (
        "Fintech & money",
        (
            "fintech", "payment", "payments", "banking", "bank", "wallet", "credit",
            "lending", "loan", "money", "remittance",
        ),
    ),
    (
        "AI & technology",
        (
            "artificial intelligence", " ai ", "machine learning", "llm", "software", "saas",
            "chip", "cloud", "technology", "tech",
        ),
    ),
    (
        "Creator economy & marketing",
        (
            "creator", "content", "youtube", "tiktok", "influencer", "marketing",
            "advertising", "audience",
        ),
    ),
    (
        "Startups",
        ("startup", "startups", "founder", "entrepreneur", "accelerator", "incubator"),
    ),
    (
        "Business policy",
        ("regulation", "regulatory", "policy", "law", "tax", "government", "compliance"),
    ),
    (
        "African & Kenyan markets",
        ("kenya", "kenyan", "africa", "african", "east africa", "nairobi"),
    ),
)


def detect_signal_areas(title: str, summary: str = "") -> list[str]:
    """Return at most two plain-language labels from a source headline."""

    text = f"{title} {summary}".lower()

    # Match complete words/phrases. A plain substring check labelled
    # "fintech" as technology because it contains "tech", even before any
    # AI analysis had confirmed that interpretation.
    def contains_keyword(keyword: str) -> bool:
        return bool(re.search(rf"(?<!\w){re.escape(keyword.strip())}(?!\w)", text))

    matches = [label for label, keywords in SIGNAL_AREAS if any(contains_keyword(word) for word in keywords)]
    return matches[:2] or ["Business & markets"]
