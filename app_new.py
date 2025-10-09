"""
High-Tech Virtual Tour Guide - Complete Rebuild
ChatGPT-like conversational AI for Sri Lankan tourism
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from agents.smart_guide import SmartGuide
from utils.auth import login, logout, require_auth
from config import Config
import json

# Initialize Flask app
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialize Smart Guide
smart_guide = SmartGuide()

# Authentication routes
@app.get("/login")
def login_page():
    return render_template("login.html")

@app.post("/login")
def login_submit():
    user = request.form.get("user", "")
    pwd = request.form.get("pwd", "")
    if login(user, pwd):
        return redirect(url_for("index"))
    return render_template("login.html", error="Invalid credentials.")

@app.get("/logout")
def logout_user():
    logout()
    return redirect(url_for("login_page"))

# Main application routes
@app.get("/")
def index():
    if not require_auth():
        return redirect(url_for("login_page"))
    
    # Initialize session
    session.setdefault("history", [])
    session.setdefault("user", "admin")
    
    return render_template("index.html")

@app.post("/chat")
def chat():
    """Main chat endpoint - processes all user queries"""
    if not require_auth():
        return jsonify({"error": "Please login first."}), 401
    
    # Get user message
    data = request.get_json()
    user_msg = data.get("message", "").strip()
    
    if not user_msg:
        return jsonify({"error": "Message cannot be empty."}), 400
    
    # Initialize session history
    session.setdefault("history", [])
    history = session["history"]
    
    # Generate unique ID for this conversation
    conversation_id = str(uuid.uuid4())
    
    # Process query with Smart Guide
    try:
        response = smart_guide.process_query(user_msg)
        
        # Format response for frontend
        formatted_response = {
            "id": conversation_id,
            "reply": response.get("text", "Sorry, I couldn't process that request."),
            "suggestions": _generate_suggestions(response),
            "type": response.get("type", "general"),
            "data": response,
            "images": response.get("images", [])
        }
        
        # Store in session history
        history.append({
            "id": conversation_id,
            "who": "user",
            "text": user_msg,
            "timestamp": smart_guide._get_timestamp()
        })
        
        history.append({
            "id": conversation_id + "_bot",
            "who": "bot", 
            "text": formatted_response["reply"],
            "timestamp": smart_guide._get_timestamp(),
            "type": response.get("type", "general"),
            "data": response
        })
        
        session["history"] = history
        
        return jsonify(formatted_response)
        
    except Exception as e:
        return jsonify({
            "error": f"Sorry, I encountered an error: {str(e)}"
        }), 500

@app.post("/new-chat")
def new_chat():
    """Start a new chat session"""
    if not require_auth():
        return jsonify({"error": "Please login first."}), 401
    
    # Clear conversation history
    smart_guide.clear_history()
    session["history"] = []
    
    welcome_message = (
        "Hello! 👋 I'm your **High-Tech Virtual Tour Guide** for Sri Lanka! 🇱🇰\n\n"
        "I'm powered by advanced AI and real-time APIs to provide you with:\n\n"
        "🗺️ **Smart Trip Planning** - \"Plan a 3-hour trip to Kandy\"\n"
        "🌤️ **Real-time Weather** - \"Weather in Colombo\"\n"
        "🍽️ **Restaurant Discovery** - \"Restaurants in Galle\"\n"
        "🏨 **Hotel Recommendations** - \"Hotels in Anuradhapura\"\n"
        "📍 **Place Information** - \"Tell me about Sigiriya\"\n"
        "🎯 **Attraction Lists** - \"Attractions in Negombo\"\n\n"
        "What would you like to explore in Sri Lanka today?"
    )
    
    return jsonify({
        "reply": welcome_message,
        "suggestions": [
            "Plan a 3-hour trip to Kandy",
            "Weather in Colombo", 
            "Tell me about Sigiriya",
            "Restaurants in Galle"
        ],
        "type": "welcome"
    })

@app.get("/history")
def get_history():
    """Get chat history"""
    if not require_auth():
        return jsonify({"error": "Please login first."}), 401
    
    return jsonify(session.get("history", []))

@app.delete("/history")
def clear_history():
    """Clear all chat history"""
    if not require_auth():
        return jsonify({"error": "Please login first."}), 401
    
    session["history"] = []
    smart_guide.clear_history()
    
    return jsonify({"success": True})

@app.delete("/history/<message_id>")
def delete_message(message_id):
    """Delete a specific message"""
    if not require_auth():
        return jsonify({"error": "Please login first."}), 401
    
    history = session.get("history", [])
    session["history"] = [msg for msg in history if msg.get("id") != message_id]
    
    return jsonify({"success": True})

@app.get("/state")
def get_state():
    """Get current application state"""
    if not require_auth():
        return jsonify({"error": "Please login first."}), 401
    
    return jsonify({
        "user": session.get("user", "admin"),
        "history_count": len(session.get("history", [])),
        "timestamp": smart_guide._get_timestamp()
    })

def _generate_suggestions(response: dict) -> list:
    """Generate contextual suggestions based on response type"""
    response_type = response.get("type", "general")
    
    if response_type == "trip_plan":
        city = response.get("city", "Colombo")
        return [
            f"Weather in {city}",
            f"Restaurants in {city}",
            f"Hotels in {city}",
            f"Plan a 2-day trip to {city}"
        ]
    
    elif response_type == "weather":
        location = response.get("location", "Colombo")
        return [
            f"Plan a trip to {location}",
            f"Restaurants in {location}",
            f"Attractions in {location}",
            "Weather in Kandy"
        ]
    
    elif response_type == "restaurants":
        city = response.get("city", "Colombo")
        return [
            f"Hotels in {city}",
            f"Attractions in {city}",
            f"Weather in {city}",
            f"Plan a trip to {city}"
        ]
    
    elif response_type == "hotels":
        city = response.get("city", "Colombo")
        return [
            f"Restaurants in {city}",
            f"Attractions in {city}",
            f"Weather in {city}",
            f"Plan a trip to {city}"
        ]
    
    elif response_type == "place_info":
        place = response.get("place", "Sigiriya")
        return [
            f"Weather in {place}",
            f"Plan a trip to {place}",
            f"Attractions in {place}",
            "Tell me about Kandy"
        ]
    
    elif response_type == "attractions":
        city = response.get("city", "Colombo")
        return [
            f"Plan a trip to {city}",
            f"Restaurants in {city}",
            f"Hotels in {city}",
            f"Weather in {city}"
        ]
    
    else:
        return [
            "Plan a 3-hour trip to Kandy",
            "Weather in Colombo",
            "Tell me about Sigiriya", 
            "Restaurants in Galle"
        ]

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
