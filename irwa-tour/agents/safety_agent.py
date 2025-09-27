from typing import Tuple
from better_profanity import profanity
import re

# Load profanity dictionary (already includes strong words)
profanity.load_censor_words()

BANNED_SUBSTRINGS = {
    "kill", "harm", "bomb", "terror", "suicide", "murder", "die", "death",
    "fuck", "shit", "damn", "hell", "bitch", "asshole", "bastard", "crap",
    "hack", "ddos", "phish", "malware", "ransomware",
    "password dump", "credit card", "steal",
    "meth", "cocaine",
    "rm -rf", "drop table", "union select", "exec(", "system(", "xp_cmdshell",
    "<script", "</script"
}

# Responses for different types of violations
VIOLATION_RESPONSES = {
    "profanity": "I understand you might be frustrated, but let's keep our conversation respectful. I'm here to help you plan amazing tours and share information about beautiful places in Sri Lanka! 🌸",
    "kill": "I can't help with anything related to violence or harm. Instead, let me help you discover peaceful and beautiful places to visit in Sri Lanka! 🏞️",
    "harm": "I'm designed to help with travel planning and tourism information. Let's focus on positive experiences and beautiful destinations! ✨",
    "bomb": "I can't assist with anything related to explosives or dangerous activities. How about we plan a safe and wonderful tour instead? 🚀",
    "terror": "I'm here to help you explore the beauty and culture of Sri Lanka safely. Let's plan something positive and enriching! 🌺",
    "suicide": "If you're going through a difficult time, please reach out to a mental health professional or crisis helpline. I'm here to help you discover beautiful places that might bring you joy! 🌈",
    "murder": "I can't help with anything related to violence. Let me help you plan amazing cultural and natural experiences in Sri Lanka instead! 🏛️",
    "die": "I'm here to help you live life to the fullest by discovering amazing places! Let's plan an adventure that celebrates life! 🌟",
    "death": "Let's focus on celebrating life and exploring beautiful places! I can help you plan wonderful experiences in Sri Lanka! 🌸",
    "fuck": "I understand you might be frustrated, but let's keep our conversation respectful. I'm here to help you plan amazing tours! 🌺",
    "shit": "Let's keep our conversation positive! I'm excited to help you discover beautiful places in Sri Lanka! ✨",
    "damn": "I'm here to help you plan wonderful experiences! Let's focus on the amazing destinations Sri Lanka has to offer! 🌟",
    "hell": "Let's focus on heavenly places instead! I can help you discover paradise-like destinations in Sri Lanka! 🏝️",
    "bitch": "I'm here to help you plan amazing tours! Let's keep our conversation respectful and positive! 🌸",
    "asshole": "Let's keep our conversation friendly! I'm excited to help you explore beautiful Sri Lanka! 🌺",
    "bastard": "I'm here to help you plan wonderful experiences! Let's focus on discovering amazing places together! ✨",
    "crap": "Let's focus on the amazing instead! I can help you discover incredible destinations in Sri Lanka! 🌟"
}

URL_PAT = re.compile(r"https?://[^\s]+", re.I)
EMAIL_PAT = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I)

def _contains_banned(text: str) -> str:
    t = (text or "").lower()
    for bad in BANNED_SUBSTRINGS:
        if bad in t:
            return bad
    return ""

def check_input(text: str) -> Tuple[bool, str]:
    t = (text or "")
    if profanity.contains_profanity(t):
        return False, "profanity"
    bad = _contains_banned(t)
    if bad:
        return False, bad
    # crude HTML/script detection
    if "<" in t or ">" in t:
        # allow markdown-like "<3" or escaped html, but block raw tags
        if re.search(r"<\s*\/?\s*[a-z][a-z0-9\-]*\s*[^>]*>", t, re.I):
            return False, "raw_html_tag"
    return True, ""

def sanitize(text: str) -> str:
    # strip angle brackets + collapse whitespace
    clean = (text or "").replace("<", "").replace(">", "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:2000]  # avoid giant payloads

def get_violation_response(violation_type: str) -> str:
    """Get appropriate response for different types of violations."""
    return VIOLATION_RESPONSES.get(violation_type, 
        "I'm here to help you plan amazing tours and discover beautiful places in Sri Lanka! Let's keep our conversation positive and respectful! 🌸")

def check_output(text: str) -> Tuple[bool, str]:
    t = (text or "")
    if "<script" in t.lower() or "</script" in t.lower():
        return False, "script"
    # prevent accidental leakage of emails/links if needed (demo policy—allow links if you prefer)
    if URL_PAT.search(t) and "http" in t.lower():
        # allow; flip to False to block links
        return True, ""
    if EMAIL_PAT.search(t):
        # allow; flip to False to block emails
        return True, ""
    return True, ""
