import os
from flask import session

# Read from .env if available, else use defaults
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def login(user: str, pwd: str) -> bool:
    """Check username and password against .env or defaults."""
    if user == ADMIN_USER and pwd == ADMIN_PASSWORD:
        session["user"] = user
        return True
    return False

def logout():
    """Remove user from session."""
    session.pop("user", None)

def require_auth() -> bool:
    """Check if user is logged in."""
    return bool(session.get("user"))
