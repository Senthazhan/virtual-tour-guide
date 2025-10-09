import re
from typing import Tuple, Literal, Dict, Any, Optional

Intent = Literal["facts", "itinerary", "help", "chitchat", "unknown"]

# Accept: "2h", "2 hr", "2 hours", "120m", "120 minutes", "1.5 hours"
TIME_PAT = re.compile(
    r"(?:(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h))|(?:(\d+)\s*(?:minutes?|mins?|m))",
    re.I,
)

CITY_PAT = re.compile(
    r"(?:in|at|around|for)\s+([a-zA-Z][a-zA-Z\s\-']{1,40})\b", re.I
)

FACTS_TRIGGERS = (
    "tell me about", "facts", "history", "info about", "information about",
    "what is", "where is", "ticket", "opening", "close time"
)
PLAN_TRIGGERS = (
    "plan", "route", "itinerary", "tour", "make a plan", "schedule",
    "visit plan", "trip plan", "route plan"
)

CHITCHAT_TRIGGERS = (
    "hi", "hello", "hey", "good morning", "good evening", "good night",
    "how are you", "what's up", "whats up", "good afternoon", "greetings"
)

GREETING_SIMPLE = ("hi", "hello", "hey", "greetings")
GREETING_TIME = ("good morning", "good afternoon", "good evening", "good night")

def parse_minutes(text: str) -> Optional[int]:
    t = (text or "").lower()
    m = TIME_PAT.search(t)
    if not m:
        return None
    if m.group(1):  # hours (possibly float)
        hours = float(m.group(1))
        return max(30, int(round(hours * 60)))
    if m.group(2):  # minutes
        return max(15, int(m.group(2)))
    return None

def _extract_city(text: str) -> Optional[str]:
    t = (text or "").strip()
    m = CITY_PAT.search(t)
    if m:
        return m.group(1).strip(" ?!.").title()
    # fallback: if user wrote a short query like "kandy tour 2h"
    words = [w for w in re.split(r"[^a-zA-Z]+", t) if w]
    if len(words) <= 3:
        return " ".join(words).title() if words else None
    return None

def route_intent(text: str) -> Tuple[Intent, Dict[str, Any]]:
    t = (text or "").lower().strip()

    # Help
    if any(k in t for k in ("help", "how to use", "what can you do")):
        return "help", {}

    # Check for itinerary/tour planning keywords
    if any(k in t for k in PLAN_TRIGGERS):
        return "itinerary", {
            "city": _extract_city(text),
            "minutes": parse_minutes(text)
        }

    # Check for facts/information keywords
    if any(k in t for k in FACTS_TRIGGERS):
        # try to grab the substring after "about"
        place = None
        if "about" in t:
            place = text.lower().split("about", 1)[1]
        place = (place or text).strip(" ?!.")
        return "facts", {"place": place}

    # Check for greetings - but only if they're exact matches or very short queries
    words = t.split()
    if len(words) <= 2:  # Only check very short queries for greetings
        if any(k in t for k in CHITCHAT_TRIGGERS):
            kind = "generic"
            if any(k in t for k in GREETING_TIME):
                if "good morning" in t:
                    kind = "morning"
                elif "good afternoon" in t:
                    kind = "afternoon"
                elif "good evening" in t:
                    kind = "evening"
                elif "good night" in t:
                    kind = "night"
            elif any(k in t for k in GREETING_SIMPLE):
                kind = "simple"
            return "chitchat", {"greeting": kind}
    
    # Also check for exact greeting matches regardless of length
    if t.strip() in CHITCHAT_TRIGGERS:
        return "chitchat", {"greeting": "simple"}

    # For any other query, treat as facts/information request
    # This makes the system more flexible - it will try to provide information for any query
    return "facts", {"place": text.strip(" ?!.")}
