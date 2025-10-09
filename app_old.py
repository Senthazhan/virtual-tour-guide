import os
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from utils.auth import login as do_login, logout as do_logout, require_auth
from utils.crypto_log import write_event
from utils.llm import polish_text
from agents.safety_agent import check_input, sanitize, check_output, get_violation_response
from agents.dialogue_agent import route_intent, parse_minutes
from agents.ir_agent import lookup_place, list_places, get_enhanced_place_info, search_wikipedia_places, comprehensive_place_search, get_comprehensive_information
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

# Removed rigid slot system - now using flexible conversation flow

def suggest_for(intent: str, payload: dict | None = None, extra_city: str | None = None):
    """Flexible suggestions based on context."""
    payload = payload or {}
    city = extra_city or payload.get("city") or payload.get("place")
    
    if intent in ("help", "unknown"):
        return ["Tell me about Sigiriya", "Beaches in Colombo", "Plan a 3-hour tour in Kandy", "Weather in Galle"]
    elif intent == "facts" and city:
        return [f"Plan a tour in {city}", f"More about {city}", "Weather in {city}", "Another place"]
    elif intent == "itinerary" and city:
        return [f"Tell me about {city}", "Plan another tour", "Weather in {city}", "Help"]
    elif intent == "chitchat":
        return ["Tell me about Sigiriya", "Beaches in Colombo", "Plan a tour", "Help"]
    else:
        # Default suggestions for any other case
        return ["Tell me about Sigiriya", "Beaches in Colombo", "Plan a tour in Kandy", "Weather in Galle"]

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

@app.post("/new-chat")
def new_chat():
    """Start a new chat session."""
    if not require_auth():
        return jsonify({"reply": "Please login first.", "suggestions": []}), 401
    
    # Clear the current chat history
    session["history"] = []
    session["last_place"] = None
    
    # Return a welcome message
    welcome_msg = (
        "Hello! I'm your Virtual Tour Guide for Sri Lanka. 🌴\n\n"
        "I can help you with:\n"
        "• Information about places and attractions\n"
        "• Lists of beaches, temples, and other locations\n"
        "• Weather information for your destinations\n"
        "• Planning tours and itineraries\n\n"
        "What would you like to explore today?"
    )
    
    return respond(
        welcome_msg,
        ["Tell me about Sigiriya", "Beaches in Colombo", "Plan a 3-hour tour in Kandy", "Weather in Kandy"]
    )

@app.delete("/history/<message_id>")
def delete_history_message(message_id):
    """Delete a specific message from chat history."""
    if not require_auth():
        return jsonify({"error": "Please login first."}), 401
    
    history = session.get("history", [])
    
    # Find and remove the message with the given ID
    original_length = len(history)
    session["history"] = [msg for msg in history if msg.get("id") != message_id]
    
    if len(session["history"]) < original_length:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Message not found"}), 404

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
        
        # Add the blocked message to history (for user to see what they sent)
        session.setdefault("history", [])
        user_id = str(uuid.uuid4())
        session["history"].append({"id": user_id, "who": "user", "text": raw})
        
        # Add the violation response to history
        bot_id = str(uuid.uuid4())
        session["history"].append({"id": bot_id, "who": "bot", "text": violation_response, "reply_to": user_id})
        session["history"] = session["history"]
        
        return respond(violation_response, ["Tell me about Sigiriya", "Plan a 3-hour tour in Kandy", "Help"], 
                     extra={"bot_id": bot_id, "reply_to": user_id})

    user_msg = sanitize(raw)

    # Ensure history
    session.setdefault("history", [])
    history = session["history"]

    # Record user message
    user_id = str(uuid.uuid4())
    history.append({"id": user_id, "who": "user", "text": user_msg})
    session["history"] = history

    # Simplified conversation flow - no hardcoded rules
    # Just route to the appropriate intent and handle it directly

    # Route the intent naturally - no hardcoded conversation flow
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
        # Use comprehensive information search that handles both specific places and general topics
        res = get_comprehensive_information(payload.get("place", ""))
        
        if not res:
            return respond(
                "I couldn't find information about that. Try one of these: " + ", ".join(list_places()[:12]) + " …",
                ["Tell me about Sigiriya", "Tell me about Kandy", "Plan a 3-hour tour in Kandy"],
                extra=_append_bot_history("I couldn't find information about that. Try one of these: " + ", ".join(list_places()[:12]) + " …", user_id)
            )
        # Handle list queries differently
        if res.get("is_list_query"):
            # For list queries, provide a clear list format
            facts = "\n".join(res["facts"]) if res["facts"] else "No information available."
            
            # Add weather information only if specifically requested and available
            weather_info = ""
            if res.get("weather"):
                weather = res["weather"]
                weather_info = f"\n\n🌤️ **Current Weather:**\n"
                weather_info += f"- **Temperature:** {weather.get('temperature', 'N/A')}\n"
                weather_info += f"- **Condition:** {weather.get('condition', 'N/A')}\n"
                weather_info += f"- **Humidity:** {weather.get('humidity', 'N/A')}\n"
                weather_info += f"- **Description:** {weather.get('description', 'N/A')}\n"
            
            # Add Wikipedia information if available
            wikipedia_info = ""
            if res.get("has_wikipedia_data"):
                wikipedia_info = "\n\n📚 **Additional Information:**\n"
                if res.get("wikipedia_description"):
                    wikipedia_info += f"- **Description:** {res['wikipedia_description']}\n"
                if res.get("wikipedia_url"):
                    wikipedia_info += f"- **Learn More:** [Wikipedia Article]({res['wikipedia_url']})\n"
                if res.get("search_term"):
                    wikipedia_info += f"- **Found using:** {res['search_term']}\n"
            
            reply = (
                f"**{res['place']}**\n\n"
                f"{facts}\n\n"
                f"{weather_info}"
                f"{wikipedia_info}\n\n"
                f"💡 **Tip:** Ask me about any specific place from this list for more details!"
            )
        else:
            # For specific places, use the original format
            facts = "\n- " + "\n- ".join(res["facts"]) if res["facts"] else "No facts available."
            meta_lines = []
            if res.get("city"): meta_lines.append(f"City: {res['city']}")
            if res.get("best_time"): meta_lines.append(f"Best time: {res['best_time']}")
            if res.get("opening_hours"): meta_lines.append(f"Hours: {res['opening_hours']}")
            if res.get("website"): meta_lines.append(f"Website: {res['website']}")
            if res.get("tags"): meta_lines.append("Tags: " + ", ".join(res["tags"]))
            if res.get("coords") and res["coords"].get("lat") is not None:
                c = res["coords"]
                meta_lines.append(f"Coords: {c['lat']}, {c['lng']}")
            
            # Add Wikipedia information if available
            wikipedia_info = ""
            if res.get("has_wikipedia_data"):
                wikipedia_info = "\n\n📚 **Additional Information:**\n"
                if res.get("wikipedia_description"):
                    wikipedia_info += f"- **Description:** {res['wikipedia_description']}\n"
                if res.get("wikipedia_url"):
                    wikipedia_info += f"- **Learn More:** [Wikipedia Article]({res['wikipedia_url']})\n"
            
            # Add weather information if available
            weather_info = ""
            if res.get("weather"):
                weather = res["weather"]
                weather_info = f"\n\n🌤️ **Current Weather:**\n"
                weather_info += f"- **Temperature:** {weather.get('temperature', 'N/A')}\n"
                weather_info += f"- **Condition:** {weather.get('condition', 'N/A')}\n"
                weather_info += f"- **Humidity:** {weather.get('humidity', 'N/A')}\n"
                weather_info += f"- **Description:** {weather.get('description', 'N/A')}\n"
            
            highlights = res.get("highlights", [])
            highlights_md = ("\n- " + "\n- ".join(highlights)) if highlights else ""
            meta_md = ("\n" + "\n".join(["- " + m for m in meta_lines])) if meta_lines else ""
            safety_md = f"\n\n> Safety: {res['safety_notes']}" if res.get("safety_notes") else ""
            reply = (
                f"**{res['place']}**{facts}\n\n"
                f"**Ticket:** {res['ticket']}\n"
                f"{meta_md}"
                f"{('\n\n**Highlights:**' + highlights_md) if highlights_md else ''}"
                f"{safety_md}"
                f"{weather_info}"
                f"{wikipedia_info}\n\n"
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
        
        # If no city specified, ask for it
        if not city:
            return respond(
                "Which city would you like a tour for?",
                ["Kandy", "Colombo", "Galle", "Anuradhapura"],
                extra=_append_bot_history("Which city would you like a tour for?", user_id)
            )
        
        # If no time specified, ask for it
        if not minutes:
            return respond(
                f"How much time do you have for {city}? (e.g., 2 hours or 120 min)",
                ["1 hour", "2 hours", "3 hours"],
                extra=_append_bot_history(f"How much time do you have for {city}? (e.g., 2 hours or 120 min)", user_id)
            )
        
        # Plan the itinerary
        res = plan(city, int(minutes))
        if not res or not res.get("stops"):
            reply = f"I couldn't plan a tour for {city}. Try a different city or time."
            return respond(reply, ["Plan a 3-hour tour in Kandy", "Plan a 2-hour tour in Colombo"], extra=_append_bot_history(reply, user_id))
        else:
            lines = [f"{i+1}. {s['name']} — ~{s['minutes']} min" for i, s in enumerate(res["stops"])]
            reply = (
                f"**{res['city']} Tour — {res['planned_minutes']}/{res['total_minutes']} minutes**\n\n"
                + "\n".join(lines)
                + f"\n\nWould you like more information about any of these places?"
            )
        
        # Remember last itinerary city for follow-up requests
        session["last_itinerary_city"] = city
        write_event({"agent": "dialogue", "intent": "itinerary", "payload": {"city": city, "minutes": minutes}})
        return respond(reply, suggest_for("itinerary", {"city": city}), extra=_append_bot_history(reply, user_id))

    # Fallback
    return respond(WELCOME, suggest_for("help"), extra=_append_bot_history(WELCOME, user_id))

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
