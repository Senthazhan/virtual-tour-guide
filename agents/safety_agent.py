from typing import Tuple
from better_profanity import profanity
import re

# Load profanity dictionary (already includes strong words)
profanity.load_censor_words()

BANNED_SUBSTRINGS = {
    # Violence and harm
    "kill", "harm", "bomb", "terror", "suicide", "murder", "die", "death",
    "violence", "attack", "assault", "weapon", "gun", "knife", "fight",
    "destroy", "damage", "hurt", "injure", "wound", "bleed", "blood",
    
    # Profanity and offensive language
    "fuck", "shit", "damn", "hell", "bitch", "asshole", "bastard", "crap",
    "fucking", "shitty", "damned", "hellish", "bitchy", "crap", "piss",
    "dick", "cock", "pussy", "whore", "slut", "faggot", "nigger", "retard",
    
    # Cyber security threats
    "hack", "ddos", "phish", "malware", "ransomware", "virus", "trojan",
    "password dump", "credit card", "steal", "fraud", "scam", "exploit",
    "inject", "bypass", "crack", "brute force", "social engineering",
    
    # Drugs and illegal substances
    "meth", "cocaine", "heroin", "marijuana", "weed", "drugs", "pills",
    "overdose", "addiction", "dealer", "smuggling",
    
    # Technical attacks
    "rm -rf", "drop table", "union select", "exec(", "system(", "xp_cmdshell",
    "sql injection", "xss", "csrf", "buffer overflow", "privilege escalation",
    
    # HTML/JavaScript injection
    "<script", "</script", "javascript:", "onclick", "onload", "onerror",
    "iframe", "object", "embed",
    
    # Sexual content
    "sex", "porn", "nude", "naked", "breast", "penis", "vagina", "orgasm",
    "masturbat", "fuck", "fucking", "screw", "bang", "hooker", "prostitute",
    "prostitution", "escort", "brothel", "strip club", "adult entertainment",
    "sexual services", "sex worker", "massage parlor", "red light district",
    
    # Hate speech and discrimination
    "racist", "sexist", "homophobic", "transphobic", "discriminat", "prejudice",
    "hate", "bigot", "supremacist", "nazi", "fascist", "terrorist",
    
    # Self-harm and mental health
    "suicide", "self-harm", "cut", "bleed", "hang", "overdose", "poison",
    "depression", "anxiety", "panic", "trauma", "ptsd", "mental illness"
}

# Responses for different types of violations
VIOLATION_RESPONSES = {
    # Violence and harm responses
    "kill": "I can't help with anything related to violence or harm. Instead, let me help you discover peaceful and beautiful places to visit in Sri Lanka! 🏞️",
    "harm": "I'm designed to help with travel planning and tourism information. Let's focus on positive experiences and beautiful destinations! ✨",
    "violence": "I can't assist with anything related to violence. Let me help you plan amazing cultural and natural experiences in Sri Lanka instead! 🏛️",
    "attack": "I'm here to help you explore the beauty and culture of Sri Lanka safely. Let's plan something positive and enriching! 🌺",
    "weapon": "I can't help with anything related to weapons or violence. How about we plan a safe and wonderful tour instead? 🚀",
    "bomb": "I can't assist with anything related to explosives or dangerous activities. How about we plan a safe and wonderful tour instead? 🚀",
    "terror": "I'm here to help you explore the beauty and culture of Sri Lanka safely. Let's plan something positive and enriching! 🌺",
    "murder": "I can't help with anything related to violence. Let me help you plan amazing cultural and natural experiences in Sri Lanka instead! 🏛️",
    "die": "I'm here to help you live life to the fullest by discovering amazing places! Let's plan an adventure that celebrates life! 🌟",
    "death": "Let's focus on celebrating life and exploring beautiful places! I can help you plan wonderful experiences in Sri Lanka! 🌸",
    
    # Profanity responses
    "profanity": "I understand you might be frustrated, but let's keep our conversation respectful. I'm here to help you plan amazing tours and share information about beautiful places in Sri Lanka! 🌸",
    "fuck": "I understand you might be frustrated, but let's keep our conversation respectful. I'm here to help you plan amazing tours! 🌺",
    "shit": "Let's keep our conversation positive! I'm excited to help you discover beautiful places in Sri Lanka! ✨",
    "damn": "I'm here to help you plan wonderful experiences! Let's focus on the amazing destinations Sri Lanka has to offer! 🌟",
    "hell": "Let's focus on heavenly places instead! I can help you discover paradise-like destinations in Sri Lanka! 🏝️",
    "bitch": "I'm here to help you plan amazing tours! Let's keep our conversation respectful and positive! 🌸",
    "asshole": "Let's keep our conversation friendly! I'm excited to help you explore beautiful Sri Lanka! 🌺",
    "bastard": "I'm here to help you plan wonderful experiences! Let's focus on discovering amazing places together! ✨",
    "crap": "Let's focus on the amazing instead! I can help you discover incredible destinations in Sri Lanka! 🌟",
    
    # Cyber security responses
    "hack": "I can't help with anything related to hacking or cyber attacks. Let me help you plan amazing tours and discover beautiful places in Sri Lanka instead! 🔒",
    "malware": "I can't assist with anything related to malware or cyber threats. How about we plan a safe and wonderful tour instead? 🛡️",
    "steal": "I can't help with anything related to theft or illegal activities. Let me help you plan amazing cultural and natural experiences in Sri Lanka instead! 🏛️",
    
    # Drug-related responses
    "drugs": "I can't help with anything related to illegal substances. Let me help you discover beautiful and healthy experiences in Sri Lanka instead! 🌿",
    "meth": "I can't assist with anything related to illegal substances. How about we plan a safe and wonderful tour instead? 🚀",
    "cocaine": "I can't help with anything related to illegal substances. Let me help you plan amazing cultural and natural experiences in Sri Lanka instead! 🏛️",
    
    # Sexual content responses
    "sex": "I'm designed to help with travel planning and tourism information. Let's focus on positive experiences and beautiful destinations! ✨",
    "porn": "I can't help with anything related to adult content. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "prostitution": "I can't help with anything related to adult services or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "prostitute": "I can't help with anything related to adult services or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "escort": "I can't help with anything related to adult services or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "brothel": "I can't help with anything related to adult services or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "strip club": "I can't help with anything related to adult entertainment or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "adult entertainment": "I can't help with anything related to adult entertainment or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "sexual services": "I can't help with anything related to adult services or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "sex worker": "I can't help with anything related to adult services or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "massage parlor": "I can't help with anything related to adult services or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    "red light district": "I can't help with anything related to adult entertainment or illegal activities. Let me help you discover beautiful places and plan amazing tours in Sri Lanka instead! 🌸",
    
    # Hate speech responses
    "racist": "I can't help with anything related to discrimination or hate speech. Let me help you discover the beautiful diversity and culture of Sri Lanka instead! 🌈",
    "hate": "I'm here to help you explore the beauty and culture of Sri Lanka with respect and positivity. Let's plan something enriching! 🌺",
    
    # Self-harm and mental health responses
    "suicide": "If you're going through a difficult time, please reach out to a mental health professional or crisis helpline. I'm here to help you discover beautiful places that might bring you joy! 🌈",
    "self-harm": "If you're going through a difficult time, please reach out to a mental health professional or crisis helpline. I'm here to help you discover beautiful places that might bring you joy! 🌈",
    "depression": "If you're going through a difficult time, please reach out to a mental health professional or crisis helpline. I'm here to help you discover beautiful places that might bring you joy! 🌈",
    
    # Technical attack responses
    "sql injection": "I can't help with anything related to technical attacks. Let me help you plan amazing tours and discover beautiful places in Sri Lanka instead! 🔒",
    "xss": "I can't assist with anything related to technical attacks. How about we plan a safe and wonderful tour instead? 🛡️",
    
    # HTML/JavaScript injection responses
    "raw_html_tag": "I can't help with anything related to code injection. Let me help you plan amazing tours and discover beautiful places in Sri Lanka instead! 🔒",
    "script": "I can't assist with anything related to code injection. How about we plan a safe and wonderful tour instead? 🛡️",
    
    # Spam and abuse responses
    "spam": "I can't help with repetitive or spam-like messages. Let me help you plan amazing tours and discover beautiful places in Sri Lanka instead! 🚫",
    "excessive_length": "Your message is too long. Please keep it concise and I'll help you plan amazing tours in Sri Lanka! 📝"
}

URL_PAT = re.compile(r"https?://[^\s]+", re.I)
EMAIL_PAT = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I)

def _contains_banned(text: str) -> str:
    t = (text or "").lower()
    
    # Check for exact matches first (most specific)
    for bad in BANNED_SUBSTRINGS:
        if bad in t:
            return bad
    
    # Enhanced variations and common misspellings
    variations = {
        # Profanity variations
        "fuck": ["f*ck", "f**k", "f***", "fuk", "fuking", "fucking", "fucked", "fucker", "fucking", "fucks"],
        "shit": ["sh*t", "sh**", "sht", "shitting", "shitted", "shitter", "shits"],
        "damn": ["d*mn", "d**n", "damned", "damning", "damns"],
        "hell": ["h*ll", "h**l", "hellish", "hells"],
        "bitch": ["b*tch", "b**ch", "bitchy", "bitches", "bitching"],
        "asshole": ["a**hole", "a**h*le", "assh*le", "assholes"],
        "bastard": ["b*stard", "b**tard", "basted", "bastards"],
        "crap": ["cr*p", "cr**", "craps", "crapping"],
        "piss": ["p*ss", "p**s", "pissing", "pissed", "pisses"],
        
        # Violence variations
        "kill": ["k*ll", "k**l", "killing", "killed", "killer", "kills"],
        "murder": ["m*rder", "m**der", "murdered", "murdering", "murderer", "murders"],
        "suicide": ["s*cide", "s**cide", "suicidal", "suicides"],
        "bomb": ["b*mb", "b**b", "bombing", "bombed", "bomber", "bombs"],
        "terror": ["t*rror", "t**ror", "terrorist", "terrorism", "terrorists"],
        "harm": ["h*rm", "h**m", "harming", "harmed", "harms"],
        "violence": ["v*olence", "v**lence", "violent", "violently"],
        "attack": ["att*ck", "att**k", "attacking", "attacked", "attacker", "attacks"],
        
        # Cyber security variations
        "hack": ["h*ck", "h**k", "hacking", "hacked", "hacker", "hacks"],
        "malware": ["m*lware", "m**ware", "malwares"],
        "virus": ["v*rus", "v**us", "viruses"],
        "phish": ["ph*sh", "ph**h", "phishing", "phished", "phisher"],
        "steal": ["st*al", "st**l", "stealing", "stolen", "stealer", "steals"],
        
        # Drug variations
        "drugs": ["dr*gs", "dr**s", "drugged", "drugging", "druggie", "druggies"],
        "cocaine": ["c*caine", "c**aine", "cocaines"],
        "meth": ["m*th", "m**h", "meths"],
        "heroin": ["h*roin", "h**oin", "heroins"],
        "marijuana": ["m*r*juana", "m**juana", "marijuanas"],
        "weed": ["w*ed", "w**d", "weeds"],
        
        # Sexual content variations
        "sex": ["s*x", "s**", "sexual", "sexually", "sexes", "sexing"],
        "porn": ["p*rn", "p**n", "pornographic", "pornography", "porns"],
        "prostitution": ["pr*stitution", "pr**stitution", "prostitutions"],
        "prostitute": ["pr*stitute", "pr**stitute", "prostitutes", "prostituting"],
        "escort": ["esc*rt", "esc**t", "escorts", "escorting"],
        "brothel": ["br*thel", "br**thel", "brothels"],
        "hooker": ["h*oker", "h**ker", "hookers"],
        
        # Hate speech variations
        "racist": ["r*cist", "r**cist", "racism", "racially", "racists"],
        "hate": ["h*te", "h**e", "hating", "hated", "hateful", "hates"],
        "nazi": ["n*zi", "n**i", "nazis"],
        "fascist": ["f*scist", "f**cist", "fascists", "fascism"],
        
        # Self-harm variations
        "suicide": ["s*cide", "s**cide", "suicidal", "suicides"],
        "self-harm": ["s*lf-h*rm", "s**f-h**m", "self-harming", "self-harmed"],
        "depression": ["d*pression", "d**pression", "depressed", "depressing", "depressions"]
    }
    
    # Check variations for each base word
    for base_word, variants in variations.items():
        # First check if base word is in text
        if base_word in t:
            return base_word
        # Then check all variations
        for variant in variants:
            if variant in t:
                return base_word
    
    return ""

def check_input(text: str) -> Tuple[bool, str]:
    t = (text or "")
    
    # FIRST: Check for banned substrings and variations (highest priority)
    bad = _contains_banned(t)
    if bad:
        return False, bad  # False means blocked (not allowed)
    
    # SECOND: Check for profanity using better-profanity library
    try:
        if profanity.contains_profanity(t):
            return False, "profanity"  # False means blocked (not allowed)
    except Exception as e:
        # Fallback if profanity library fails
        pass
    
    # Enhanced HTML/script detection
    if "<" in t or ">" in t:
        # Allow markdown-like "<3" or escaped html, but block raw tags
        if re.search(r"<\s*\/?\s*[a-z][a-z0-9\-]*\s*[^>]*>", t, re.I):
            return False, "raw_html_tag"
    
    # Check for JavaScript injection attempts
    js_patterns = [
        r"javascript\s*:",
        r"on\w+\s*=",
        r"<script",
        r"</script",
        r"eval\s*\(",
        r"document\.",
        r"window\.",
        r"alert\s*\(",
        r"confirm\s*\(",
        r"prompt\s*\("
    ]
    
    for pattern in js_patterns:
        if re.search(pattern, t, re.I):
            return False, "script"
    
    # Check for SQL injection patterns
    sql_patterns = [
        r"union\s+select",
        r"drop\s+table",
        r"delete\s+from",
        r"insert\s+into",
        r"update\s+set",
        r"exec\s*\(",
        r"xp_cmdshell",
        r"sp_executesql"
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, t, re.I):
            return False, "sql injection"
    
    # Check for excessive repetition (potential spam/abuse)
    words = t.split()
    if len(words) > 0:
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        max_repetition = max(word_counts.values())
        if max_repetition > 5:  # More than 5 repetitions of same word
            return False, "spam"
    
    # Check for excessive length (potential DoS)
    if len(t) > 5000:
        return False, "excessive_length"
    
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
