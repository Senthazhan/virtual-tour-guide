import os
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from utils.auth import login as do_login, logout as do_logout, require_auth
from utils.crypto_log import write_event
from utils.llm import polish_text
from agents.safety_agent import check_input, sanitize, check_output, get_violation_response
from agents.dialogue_agent import route_intent, parse_minutes
from agents.ir_agent import lookup_place, list_places
from agents.itinerary_agent import plan

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key")

WELCOME = (
    "Hi! I am your Virtual Tour Guide.\n"
    "Try: **Tell me about Sigiriya** or **Plan a 3-hour tour in Kandy**.\n"
    "Places in my dataset: " + ", ".join(list_places()[:12]) + " …"
)

# ---------- helpers: safe, markdown-friendly responses + smart suggestions ----------
def respond(text: str, suggestions=None, status: int = 200, extra: dict | None = None):
    """Polish + safety check + JSON envelope with optional suggestions."""
    text = polish_text(text)
    ok_out, reason_out = check_output(text)
    if not ok_out:
        write_event({"agent": "safety", "blocked_output": reason_out})
        text = "⚠️ Output blocked by Safety Agent."
        suggestions = ["Help", "Tell me about Sigiriya", "Plan a 3-hour tour in Kandy"]
    payload = {"reply": text, "suggestions": suggestions or []}
    if extra:
        payload.update(extra)
    return jsonify(payload), status

def _append_bot_history(text: str, user_id: str | None = None) -> dict:
    """Append a bot message to session history and return ids for UI if needed."""
    session.setdefault("history", [])
    bot_id = str(uuid.uuid4())
    session["history"].append({"id": bot_id, "who": "bot", "text": text, "reply_to": user_id})
    return {"bot_id": bot_id, "reply_to": user_id}

def clear_slots():
    session["pending"] = None
    session["slots"] = {}

def suggest_for(intent: str, payload: dict | None = None, extra_city: str | None = None):
    """Context-aware quick-reply chips."""
    payload = payload or {}
    city = extra_city or payload.get("city") or payload.get("place")
    if intent in ("help", "unknown"):
        return ["Tell me about Sigiriya", "Plan a 3-hour tour in Kandy"]
    if intent == "facts" and city:
        return [f"Plan a 2-hour tour in {city}", f"Ticket price in {city}", "Another city"]
    if intent == "itinerary" and city:
        return [f"Facts about {city}", "Plan another city", "Help"]
    if intent == "chitchat":
        return ["Tell me about Sigiriya", "Plan a 2-hour tour", "Help"]
    if intent == "await_city":
        return ["Kandy", "Galle", "Ella", "Sigiriya"]
    if intent == "await_minutes" and city:
        return ["1 hour", "2 hours", "3 hours"]
    return []

# ---------- Auth ----------
@app.get("/login")
def login_page():
    return render_template("login.html")

@app.post("/login")
def login_submit():
    user = request.form.get("user", "")
    pwd = request.form.get("pwd", "")
    if do_login(user, pwd):
        write_event({"agent": "auth", "event": "login", "user": user})
        return redirect(url_for("index"))
    return render_template("login.html", error="Invalid credentials.")

@app.get("/logout")
def logout():
    do_logout()
    write_event({"agent": "auth", "event": "logout"})
    return redirect(url_for("login_page"))

# ---------- UI ----------
@app.get("/")
def index():
    if not require_auth():
        return redirect(url_for("login_page"))
    session.setdefault("pending", None)
    session.setdefault("slots", {})
    session.setdefault("history", [])
    return render_template("index.html")

# expose lightweight state for UI status strip
@app.get("/state")
def state():
    if not require_auth():
        return jsonify({}), 401
    s = session.get("slots", {})
    return jsonify({"city": s.get("city"), "minutes": s.get("minutes")})

# ---------- History APIs ----------
@app.get("/history")
def get_history():
    if not require_auth():
        return jsonify([]), 401
    return jsonify(session.get("history", []))

@app.delete("/history")
def clear_history():
    if not require_auth():
        return jsonify({}), 401
    session["history"] = []
    return ("", 204)

@app.delete("/history/<msg_id>")
def delete_message(msg_id: str):
    if not require_auth():
        return jsonify({}), 401
    hist = session.get("history", [])
    hist = [m for m in hist if m.get("id") != msg_id]
    session["history"] = hist
    return ("", 204)

# ---------- Chat ----------
@app.post("/chat")
def chat():
    if not require_auth():
        return jsonify({"reply": "Please login first.", "suggestions": []}), 401

    data = request.get_json(silent=True) or {}
    raw = data.get("message", "")

    ok, reason = check_input(raw)
    if not ok:
        write_event({"agent": "safety", "blocked_input": reason, "text": raw})
        violation_response = get_violation_response(reason)
        return respond(violation_response, ["Tell me about Sigiriya", "Plan a 3-hour tour in Kandy", "Help"])

    user_msg = sanitize(raw)

    # Ensure history
    session.setdefault("history", [])
    history = session["history"]

    # Record user message
    user_id = str(uuid.uuid4())
    history.append({"id": user_id, "who": "user", "text": user_msg})
    session["history"] = history

    # Slot filling state
    pending = session.get("pending")
    slots = session.get("slots", {})

    # If we are waiting for city / minutes, capture them first
    if pending == "city":
        slots["city"] = user_msg
        session["pending"] = "minutes"
        session["slots"] = slots
        return respond(
            f"Great. How much time do you have for **{slots['city']}**? (e.g., *2 hours* or *120 min*)",
            suggest_for("await_minutes", extra_city=slots["city"]),
            extra=_append_bot_history(f"Great. How much time do you have for **{slots['city']}**? (e.g., *2 hours* or *120 min*)", user_id)
        )

    if pending == "minutes":
        mins = parse_minutes(user_msg)
        if not mins:
            return respond(
                "Please tell me the time like **2 hours** or **150 min**.",
                ["1 hour", "2 hours", "3 hours"],
                extra=_append_bot_history("Please tell me the time like **2 hours** or **150 min**.", user_id)
            )
        slots["minutes"] = int(mins)
        # proceed to plan
        res = plan(slots.get("city", ""), slots.get("minutes", 180))
        clear_slots()
        if not res or not res.get("stops"):
            reply = "I couldn't plan that. Try **Plan a 3-hour tour in Kandy**."
            return respond(reply, ["Plan a 3-hour tour in Kandy", "Help"], extra=_append_bot_history(reply, user_id))
        else:
            lines = [f"{i+1}. {s['name']} — ~{s['minutes']} min" for i, s in enumerate(res["stops"])]
            reply = (
                f"**{res['city']} — {res['planned_minutes']}/{res['total_minutes']} min**\n"
                + "\n".join(lines)
                + f"\n\nNeed **transportation tips** or **local dining recommendations** for **{res['city']}**?"
            )
        # remember last itinerary city for follow-up requests
        session["last_itinerary_city"] = res.get("city")
        write_event({"agent": "dialogue", "intent": "itinerary",
                     "payload": {"city": res.get("city"), "minutes": res.get("total_minutes")}})
        return respond(reply, suggest_for("itinerary", extra_city=res.get("city")), extra=_append_bot_history(reply, user_id))

    # No pending slot → normal intent routing
    # Confirmation shortcut: if user says yes after facts, jump to itinerary for last place
    confirm_words = {"yes", "yeah", "yep", "sure", "ok", "okay", "ya", "affirmative"}
    if (user_msg or "").lower().strip() in confirm_words and session.get("last_place"):
        intent, payload = "itinerary", {"city": session.get("last_place"), "minutes": None}
    # Follow-up shortcuts: ticket info, quick facts, transportation tips, or dining recommendations for last itinerary city
    elif (user_msg or "").lower().strip() in {"ticket info", "quick facts", "transportation tips", "local dining recommendations"} and session.get("last_itinerary_city"):
        city = session.get("last_itinerary_city")
        if "ticket info" in (user_msg or "").lower():
            # Show ticket info for last itinerary city
            res = lookup_place(city)
            if res:
                reply = f"**{res['place']} Ticket Info:**\n\n{res['ticket']}"
                if res.get("opening_hours"):
                    reply += f"\n\n**Hours:** {res['opening_hours']}"
                if res.get("website"):
                    reply += f"\n\n**Website:** {res['website']}"
                return respond(reply, suggest_for("facts", {"place": res["place"]}), extra=_append_bot_history(reply, user_id))
        elif "transportation tips" in (user_msg or "").lower():
            # Show transportation tips for the city
            reply = f"**Transportation Tips for {city}:**\n\n"
            if city.lower() in ["colombo", "kandy", "galle"]:
                reply += f"• **Tuk-tuks**: Negotiate fares upfront; ~LKR 200-500 for short trips\n"
                reply += f"• **Buses**: Cheap and frequent; ask locals for routes\n"
                reply += f"• **Taxis**: Use apps like PickMe or Uber for convenience\n"
                reply += f"• **Walking**: City centers are walkable; carry water\n"
            elif city.lower() in ["anuradhapura", "polonnaruwa", "sigiriya"]:
                reply += f"• **Private driver**: Best for cultural triangle sites\n"
                reply += f"• **Bus**: Budget option; longer travel times\n"
                reply += f"• **Bicycle**: Rent locally for temple circuits\n"
                reply += f"• **Walking**: Many sites within walking distance\n"
            else:
                reply += f"• **Local transport**: Ask hotel/hostel for best options\n"
                reply += f"• **Tuk-tuks**: Always negotiate fares before starting\n"
                reply += f"• **Walking**: Explore city centers on foot\n"
                reply += f"• **Private hire**: Consider for day trips\n"
            return respond(reply, suggest_for("facts", {"place": city}), extra=_append_bot_history(reply, user_id))
        elif "local dining recommendations" in (user_msg or "").lower():
            # Show dining recommendations for the city
            reply = f"**Local Dining Recommendations for {city}:**\n\n"
            if city.lower() == "colombo":
                reply += f"• **Street food**: Galle Face Green evening vendors\n"
                reply += f"• **Local cuisine**: Pettah Market area restaurants\n"
                reply += f"• **Seafood**: Mount Lavinia Beach restaurants\n"
                reply += f"• **Traditional**: Try hoppers, kottu, and curry\n"
            elif city.lower() == "kandy":
                reply += f"• **Local spots**: Around Temple of the Tooth area\n"
                reply += f"• **Traditional**: Kandyan rice and curry\n"
                reply += f"• **Street food**: Lake area evening stalls\n"
                reply += f"• **Cultural**: Try local sweets and tea\n"
            elif city.lower() == "galle":
                reply += f"• **Fort area**: Colonial-style cafes and restaurants\n"
                reply += f"• **Seafood**: Fresh catch near the harbor\n"
                reply += f"• **Local**: Try Galle's unique coastal cuisine\n"
                reply += f"• **Cafes**: Dutch Hospital area for modern dining\n"
            else:
                reply += f"• **Local restaurants**: Ask hotel staff for recommendations\n"
                reply += f"• **Street food**: Try local specialties safely\n"
                reply += f"• **Traditional**: Look for rice and curry houses\n"
                reply += f"• **Fresh**: Opt for busy local eateries\n"
            return respond(reply, suggest_for("facts", {"place": city}), extra=_append_bot_history(reply, user_id))
        else:  # quick facts
            intent, payload = "facts", {"place": city}
    else:
        intent, payload = route_intent(user_msg)

    if intent in ("help", "unknown"):
        return respond(WELCOME, suggest_for(intent), extra=_append_bot_history(WELCOME, user_id))

    if intent == "chitchat":
        greet_kind = (payload or {}).get("greeting", "generic")
        if greet_kind == "simple":
            reply = (
                "Hello! 👋 How can I help with your travel plans today?\n\n"
                "Try: **Tell me about Sigiriya** or **Plan a 2-hour tour in Kandy**."
            )
        elif greet_kind == "morning":
            reply = (
                "Good morning! ☀️ Ready to explore? I can share quick facts or build a mini tour.\n\n"
                "Try: **Tell me about Galle** or **Plan a 3-hour tour in Kandy**."
            )
        elif greet_kind == "afternoon":
            reply = (
                "Good afternoon! 🌤️ Looking for places to visit or a short itinerary?\n\n"
                "Try: **Facts about Ella** or **Plan a 2-hour tour in Colombo**."
            )
        elif greet_kind == "evening":
            reply = (
                "Good evening! 🌙 I can suggest highlights and plan a quick tour.\n\n"
                "Try: **Tell me about Sigiriya** or **Plan a 2-hour tour in Galle**."
            )
        elif greet_kind == "night":
            reply = (
                "Good night! 🌙 Before you rest, want a plan for tomorrow?\n\n"
                "Try: **Facts about Kandy** or **Plan a 3-hour tour in Ella**."
            )
        else:
            reply = (
                "Hello! I'm glad you're here. I can share quick facts about places or plan a mini tour.\n\n"
                "Try: **Tell me about Sigiriya** or **Plan a 2-hour tour in Kandy**."
            )
        return respond(reply, suggest_for("chitchat"), extra=_append_bot_history(reply, user_id))

    if intent == "facts":
        res = lookup_place(payload.get("place", ""))
        if not res:
            return respond(
                "I couldn't find that place. Try one of these: " + ", ".join(list_places()[:12]) + " …",
                ["Tell me about Sigiriya", "Tell me about Kandy", "Plan a 3-hour tour in Kandy"],
                extra=_append_bot_history("I couldn't find that place. Try one of these: " + ", ".join(list_places()[:12]) + " …", user_id)
            )
        facts = "\n- " + "\n- ".join(res["facts"]) if res["facts"] else "No facts."
        meta_lines = []
        if res.get("city"): meta_lines.append(f"City: {res['city']}")
        if res.get("best_time"): meta_lines.append(f"Best time: {res['best_time']}")
        if res.get("opening_hours"): meta_lines.append(f"Hours: {res['opening_hours']}")
        if res.get("website"): meta_lines.append(f"Website: {res['website']}")
        if res.get("tags"): meta_lines.append("Tags: " + ", ".join(res["tags"]))
        if res.get("coords") and res["coords"].get("lat") is not None:
            c = res["coords"]
            meta_lines.append(f"Coords: {c['lat']}, {c['lng']}")
        highlights = res.get("highlights", [])
        highlights_md = ("\n- " + "\n- ".join(highlights)) if highlights else ""
        meta_md = ("\n" + "\n".join(["- " + m for m in meta_lines])) if meta_lines else ""
        safety_md = f"\n\n> Safety: {res['safety_notes']}" if res.get("safety_notes") else ""
        reply = (
            f"**{res['place']}**{facts}\n\n"
            f"**Ticket:** {res['ticket']}\n"
            f"{meta_md}"
            f"{('\n\n**Highlights:**' + highlights_md) if highlights_md else ''}"
            f"{safety_md}\n\n"
            f"Would you like a 2–3 stop **mini tour** in **{res['place']}**? "
            f"Tell me your time (e.g., *2 hours*)."
        )
        # remember last place for quick confirmations like "yes"
        session["last_place"] = res["place"]
        write_event({"agent": "dialogue", "intent": "facts", "payload": {"place": res["place"]}})
        return respond(reply, suggest_for("facts", {"place": res["place"]}), extra=_append_bot_history(reply, user_id))

    if intent == "itinerary":
        city = payload.get("city")
        minutes = payload.get("minutes")
        if not city:
            session["pending"] = "city"
            session["slots"] = {}
            return respond(
                "Which **city** would you like a tour for?",
                suggest_for("await_city"),
                extra=_append_bot_history("Which **city** would you like a tour for?", user_id)
            )
        if not minutes:
            session["pending"] = "minutes"
            session["slots"] = {"city": city}
            return respond(
                f"How much **time** do you have for **{city}**? (e.g., *2 hours* or *120 min*)",
                suggest_for("await_minutes", extra_city=city),
                extra=_append_bot_history(f"How much **time** do you have for **{city}**? (e.g., *2 hours* or *120 min*)", user_id)
            )
        # have both -> plan
        res = plan(city, int(minutes))
        if not res or not res.get("stops"):
            reply = "I couldn't plan that. Try **Plan a 3-hour tour in Kandy**."
            return respond(reply, ["Plan a 3-hour tour in Kandy", "Help"], extra=_append_bot_history(reply, user_id))
        else:
            lines = [f"{i+1}. {s['name']} — ~{s['minutes']} min" for i, s in enumerate(res["stops"])]
            reply = (
                f"**{res['city']} — {res['planned_minutes']}/{res['total_minutes']} min**\n"
                + "\n".join(lines)
                + f"\n\nNeed **transportation tips** or **local dining recommendations** for **{res['city']}**?"
            )
        # remember last itinerary city for follow-up requests
        session["last_itinerary_city"] = city
        write_event({"agent": "dialogue", "intent": "itinerary", "payload": {"city": city, "minutes": minutes}})
        return respond(reply, suggest_for("itinerary", {"city": city}), extra=_append_bot_history(reply, user_id))

    # Fallback
    return respond(WELCOME, suggest_for("help"), extra=_append_bot_history(WELCOME, user_id))

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
