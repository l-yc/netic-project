from __future__ import annotations

from enum import Enum
from typing import List


class Intent(Enum):
    FAQ_LOCATIONS = "faq_locations"
    FAQ_SERVICES = "faq_services"
    UNKNOWN = "unknown"


LOCATION_KEYWORDS: List[str] = [
    "location",
    "locations",
    "serve",
    "service area",
    "zip",
    "hours",
    "open",
]

SERVICE_KEYWORDS: List[str] = [
    "service",
    "services",
    "offer",
    "do you handle",
    "what do you do",
]


def detect_intent(message: str) -> Intent:
    """Detect the user's intent from a free-form message using keyword matching."""
    text = (message or "").lower()

    if any(keyword in text for keyword in LOCATION_KEYWORDS):
        return Intent.FAQ_LOCATIONS

    if any(keyword in text for keyword in SERVICE_KEYWORDS):
        return Intent.FAQ_SERVICES

    return Intent.UNKNOWN


