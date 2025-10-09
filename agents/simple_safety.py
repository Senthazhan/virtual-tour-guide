"""
Simple and effective safety agent for Virtual Tour Guide
"""

import re
from typing import Tuple

# Core banned words - comprehensive list with variations
CORE_BANNED_WORDS = {
    # Violence
    "kill", "murder", "suicide", "bomb", "terror", "attack", "violence", "harm",
    
    # Profanity (most serious)
    "fuck", "shit", "damn", "bitch", "asshole", "bastard", "crap", "piss", "bullshit", "fucking",
    
    # Hate speech
    "nigger", "faggot", "retard", "whore", "slut",
    
    # Self-harm
    "suicide", "self-harm", "cut", "hurt"
}

# Common misspellings and variations
MISSPELLINGS_AND_VARIATIONS = {
    # Violence variations
    "kill": ["kil", "k1ll", "k!ll", "k1l", "k!l"],
    "murder": ["murd3r", "murd3r", "murderer", "murd3rer"],
    "bomb": ["b0mb", "b0m", "bom"],
    "attack": ["attak", "atak", "attac"],
    
    # Profanity variations
    "fuck": ["fuk", "f*ck", "fck", "fukc", "phuck", "f*ck", "fck", "fukc", "f0ck", "fck"],
    "shit": ["sh*t", "sht", "sh1t", "sh!t", "sht", "sh1t"],
    "damn": ["dam", "d*mn", "damn", "damn"],
    "bitch": ["b*tch", "btch", "b1tch", "b!tch"],
    "asshole": ["ashole", "ash*le", "assh0le", "assh*le"],
    "bastard": ["bast*rd", "bastrd", "bastard"],
    "crap": ["cr*p", "crp", "crapp"],
    "piss": ["p*ss", "pss", "pissed"],
    
    # Hate speech variations
    "nigger": ["n*gger", "ngger", "n1gger", "n!gger"],
    "faggot": ["f*ggot", "fggot", "fagot", "fagg0t"],
    "retard": ["ret*rd", "retrd", "retard"],
    "whore": ["wh*re", "whre", "wh0re"],
    "slut": ["sl*t", "slt", "sl1t"],
    
    # Self-harm variations
    "suicide": ["sucide", "suc1de", "su!cide"],
    "hurt": ["hrt", "h*rt", "hurts"],
    "cut": ["c*t", "ct", "cuts"]
}

# Short forms and abbreviations
SHORT_FORMS = {
    "wtf": "what the fuck",
    "stfu": "shut the fuck up", 
    "fml": "fuck my life",
    "smh": "shaking my head",
    "gtfo": "get the fuck out",
    "bs": "bullshit",
    "pos": "piece of shit",
    "sob": "son of a bitch",
    "omfg": "oh my fucking god",
    "af": "as fuck",
    "mf": "motherfucker",
    "btch": "bitch",
    "fck": "fuck",
    "sht": "shit",
    "dm": "damn"
}

# Violation responses
VIOLATION_RESPONSES = {
    "kill": "I'm here to help you plan amazing tours and discover beautiful places in Sri Lanka! Let's keep our conversation focused on travel and tourism. What would you like to explore?",
    "murder": "I'm your friendly tour guide for Sri Lanka! Let's talk about the amazing places you can visit instead. What interests you most?",
    "fuck": "I'm here to help you discover the incredible beauty of Sri Lanka! Let's focus on planning your perfect trip. Where would you like to go?",
    "shit": "I'm your personal Sri Lankan travel assistant! Let's keep our conversation positive and focused on tourism. What can I help you plan today?",
    "violence": "I'm passionate about helping you explore Sri Lanka's amazing culture and places! Let's talk about your travel plans instead.",
    "hate": "I'm here to share the beauty and wonder of Sri Lanka with you! Let's focus on planning an incredible journey together.",
    "default": "I'm your friendly Virtual Tour Guide for Sri Lanka! I'm here to help you discover amazing places, plan perfect trips, and make your Sri Lankan adventure unforgettable. What would you like to explore today?"
}

def check_input(text: str) -> Tuple[bool, str]:
    """Check if input contains inappropriate content"""
    if not text:
        return True, ""
    
    text_lower = text.lower().strip()
    
    # First, expand short forms
    expanded_text = _expand_short_forms(text_lower)
    
    # Check for core banned words as whole words only
    for banned_word in CORE_BANNED_WORDS:
        # Use word boundary regex to avoid partial matches
        pattern = r'\b' + re.escape(banned_word) + r'\b'
        if re.search(pattern, expanded_text):
            return False, banned_word
    
    # Check for misspellings and variations
    for banned_word, variations in MISSPELLINGS_AND_VARIATIONS.items():
        # Check original word
        pattern = r'\b' + re.escape(banned_word) + r'\b'
        if re.search(pattern, expanded_text):
            return False, banned_word
        
        # Check variations
        for variation in variations:
            pattern = r'\b' + re.escape(variation) + r'\b'
            if re.search(pattern, expanded_text):
                return False, banned_word
    
    # Check for short forms directly
    for short_form in SHORT_FORMS.keys():
        if isinstance(SHORT_FORMS[short_form], str):  # It's an expansion
            pattern = r'\b' + re.escape(short_form) + r'\b'
            if re.search(pattern, expanded_text):
                return False, "profanity"  # Generic violation for short forms
    
    return True, ""

def _expand_short_forms(text: str) -> str:
    """Expand common short forms and abbreviations"""
    expanded = text
    
    for short_form, expansion in SHORT_FORMS.items():
        if isinstance(expansion, str):  # It's an expansion, not a list
            # Use word boundaries to replace whole words only
            pattern = r'\b' + re.escape(short_form) + r'\b'
            expanded = re.sub(pattern, expansion, expanded, flags=re.IGNORECASE)
    
    return expanded

def get_violation_response(text: str) -> str:
    """Get appropriate violation response"""
    text_lower = text.lower()
    
    # Check for specific violations and return appropriate response
    for banned_word in CORE_BANNED_WORDS:
        if banned_word in text_lower:
            return VIOLATION_RESPONSES.get(banned_word, VIOLATION_RESPONSES["default"])
    
    return VIOLATION_RESPONSES["default"]
