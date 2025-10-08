"""
Smart Tour Guide Agent - ChatGPT-like conversational AI for tourism
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from services.api_service import APIService
from agents.simple_safety import check_input, get_violation_response

class SmartGuide:
    """Intelligent tour guide that works like ChatGPT for tourism"""
    
    def __init__(self):
        self.api_service = APIService()
        self.conversation_history = []
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process user query and return intelligent response"""
        
        # Safety check first - block inappropriate content
        safety_result = check_input(user_query)
        if isinstance(safety_result, tuple):
            is_safe, violation_word = safety_result
            if not is_safe:
                violation_response = get_violation_response(user_query)
                return {
                    "type": "safety_violation",
                    "text": violation_response,
                    "blocked": True
                }
        elif not safety_result:
            violation_response = get_violation_response(user_query)
            return {
                "type": "safety_violation",
                "text": violation_response,
                "blocked": True
            }
        
        # Clean and analyze the query
        query = user_query.strip().lower()
        
        # Detect query type and extract information
        query_type, extracted_info = self._analyze_query(query)
        
        # Generate appropriate response
        response = self._generate_response(query_type, extracted_info, user_query)
        
        # Store in conversation history
        self.conversation_history.append({
            "user": user_query,
            "response": response,
            "timestamp": self._get_timestamp()
        })
        
        return response
    
    def _analyze_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Analyze query to determine type and extract key information"""
        
        # Normalize query for better matching
        query = self._normalize_query(query)
        
        # Trip planning patterns
        trip_patterns = [
            r'plan\s+a\s+(\d+)\s+hour\s+trip\s+(?:to\s+)?(\w+)',
            r'plan\s+a\s+(\d+)\s+day\s+trip\s+(?:to\s+)?(\w+)',
            r'(\d+)\s+hour\s+trip\s+(?:to\s+)?(\w+)',
            r'(\d+)\s+day\s+trip\s+(?:to\s+)?(\w+)',
            r'trip\s+(?:to\s+)?(\w+)\s+for\s+(\d+)\s+(?:hours?|days?)'
        ]
        
        for pattern in trip_patterns:
            match = re.search(pattern, query)
            if match:
                duration = int(match.group(1))
                city = match.group(2)
                # Convert days to hours
                if 'day' in query:
                    duration *= 24
                return "trip_planning", {"duration": duration, "city": city}
        
        # Weather queries
        weather_patterns = [
            r'weather\s+(?:in|at|for)\s+(\w+)',
            r'(\w+)\s+weather',
            r'temperature\s+(?:in|at)\s+(\w+)',
            r'climate\s+(?:in|at)\s+(\w+)'
        ]
        
        for pattern in weather_patterns:
            match = re.search(pattern, query)
            if match:
                location = match.group(1)
                return "weather", {"location": location}
        
        # Restaurant/Hotel queries
        if any(word in query for word in ['restaurant', 'food', 'eat', 'dining']):
            city_match = re.search(r'(?:in|at|near)\s+(\w+)', query)
            city = city_match.group(1) if city_match else "colombo"
            return "restaurants", {"city": city}
        
        if any(word in query for word in ['hotel', 'stay', 'accommodation', 'lodging']):
            city_match = re.search(r'(?:in|at|near)\s+(\w+)', query)
            city = city_match.group(1) if city_match else "colombo"
            return "hotels", {"city": city}
        
        # Place information queries
        place_patterns = [
            r'tell\s+me\s+about\s+(\w+)',
            r'what\s+is\s+(\w+)',
            r'information\s+about\s+(\w+)',
            r'(\w+)\s+details',
            r'about\s+(\w+)'
        ]
        
        for pattern in place_patterns:
            match = re.search(pattern, query)
            if match:
                place = match.group(1)
                return "place_info", {"place": place}
        
        # General tourism queries
        if any(word in query for word in ['attractions', 'places', 'visit', 'see', 'things to do']):
            city_match = re.search(r'(?:in|at)\s+(\w+)', query)
            city = city_match.group(1) if city_match else "colombo"
            return "attractions", {"city": city}
        
        # Transportation queries
        if any(word in query for word in ['how to go', 'how to reach', 'transportation', 'travel to', 'get to', 'go to']):
            place_match = re.search(r'(?:to|in)\s+(\w+)', query)
            place = place_match.group(1) if place_match else "sri lanka"
            return "transportation", {"place": place}
        
        # History queries
        if any(word in query for word in ['history', 'historical', 'ancient', 'heritage']):
            place_match = re.search(r'(?:of|in|about)\s+(\w+)', query)
            place = place_match.group(1) if place_match else "sri lanka"
            return "history", {"place": place}
        
        # Best time queries
        if any(word in query for word in ['best time', 'when to visit', 'season', 'climate']):
            place_match = re.search(r'(?:to visit|in)\s+(\w+)', query)
            place = place_match.group(1) if place_match else "sri lanka"
            return "best_time", {"place": place}
        
        # Cost queries
        if any(word in query for word in ['cost', 'price', 'expensive', 'budget', 'cheap']):
            place_match = re.search(r'(?:of|in|for)\s+(\w+)', query)
            place = place_match.group(1) if place_match else "sri lanka"
            return "cost", {"place": place}
        
        # Distance queries
        if any(word in query for word in ['distance', 'how far', 'from', 'to']):
            return "distance", {"query": query}
        
        # Recommendation queries
        if any(word in query for word in ['recommend', 'suggest', 'advise', 'best']):
            return "recommendations", {"query": query}
        
        # Comparison queries
        if any(word in query for word in ['compare', 'vs', 'versus', 'difference']):
            return "comparison", {"query": query}
        
        # Specific list queries (beaches, temples, etc.)
        if 'beaches' in query:
            place_match = re.search(r'beaches\s+(?:in|at|near)\s+(\w+)', query)
            place = place_match.group(1) if place_match else "sri lanka"
            return "beaches_list", {"place": place}
        
        if 'temples' in query:
            place_match = re.search(r'temples\s+(?:in|at|near)\s+(\w+)', query)
            place = place_match.group(1) if place_match else "sri lanka"
            return "temples_list", {"place": place}
        
        # Specific activity queries
        if any(word in query for word in ['hiking', 'photography', 'nightlife', 'shopping']):
            place_match = re.search(r'(?:in|at|near)\s+(\w+)', query)
            place = place_match.group(1) if place_match else "sri lanka"
            return "activities", {"activity": query, "place": place}
        
        # Default to general chat
        return "general", {"query": query}
    
    def _generate_response(self, query_type: str, extracted_info: Dict, original_query: str) -> Dict[str, Any]:
        """Generate intelligent response based on query type"""
        
        if query_type == "trip_planning":
            return self._generate_trip_plan(extracted_info)
        
        elif query_type == "weather":
            return self._generate_weather_response(extracted_info)
        
        elif query_type == "restaurants":
            return self._generate_restaurants_response(extracted_info)
        
        elif query_type == "hotels":
            return self._generate_hotels_response(extracted_info)
        
        elif query_type == "place_info":
            return self._generate_place_info_response(extracted_info)
        
        elif query_type == "attractions":
            return self._generate_attractions_response(extracted_info)
        
        elif query_type == "transportation":
            return self._generate_transportation_response(extracted_info)
        
        elif query_type == "history":
            return self._generate_history_response(extracted_info)
        
        elif query_type == "best_time":
            return self._generate_best_time_response(extracted_info)
        
        elif query_type == "cost":
            return self._generate_cost_response(extracted_info)
        
        elif query_type == "distance":
            return self._generate_distance_response(extracted_info)
        
        elif query_type == "recommendations":
            return self._generate_recommendations_response(extracted_info)
        
        elif query_type == "comparison":
            return self._generate_comparison_response(extracted_info)
        
        elif query_type == "activities":
            return self._generate_activities_response(extracted_info)
        
        elif query_type == "beaches_list":
            return self._generate_beaches_list_response(extracted_info)
        
        elif query_type == "temples_list":
            return self._generate_temples_list_response(extracted_info)
        
        else:
            return self._generate_general_response(original_query)
    
    def _generate_trip_plan(self, info: Dict) -> Dict[str, Any]:
        """Generate comprehensive trip plan"""
        duration = info["duration"]
        city = info["city"].title()
        
        # Get trip suggestions from API service
        suggestions = self.api_service.get_trip_suggestions(city, duration)
        
        # More natural, ChatGPT-like response
        if duration < 5:
            response_text = f"Perfect! I'd love to help you plan a {duration}-hour trip to {city}. That's a great amount of time for a quick but memorable visit! 🚀\n\n"
            response_text += f"Here's what I recommend for your {duration}-hour adventure in {city}:\n\n"
        elif duration <= 12:
            response_text = f"Excellent choice! A {duration}-hour trip to {city} gives you plenty of time to explore the city's highlights. 🌅\n\n"
            response_text += f"Let me create a perfect itinerary for your {duration}-hour visit to {city}:\n\n"
        elif duration <= 24:
            response_text = f"Wonderful! A full day in {city} is perfect for really experiencing what this amazing city has to offer. 🌞\n\n"
            response_text += f"Here's your comprehensive {duration}-hour itinerary for {city}:\n\n"
        else:
            response_text = f"Fantastic! A {duration}-hour journey in {city} will let you dive deep into the local culture and see everything this incredible destination offers. 🌟\n\n"
            response_text += f"Here's your detailed {duration}-hour exploration plan for {city}:\n\n"
        
        for i, place in enumerate(suggestions, 1):
            response_text += f"**{i}. {place['name']}** ⭐ {place['rating']}\n"
            response_text += f"📍 {place['address']} | {place['type']}\n\n"
        
        response_text += "**💡 Pro Tips for Your Trip:**\n"
        response_text += f"• Start your day early (around 6-8 AM) to beat the crowds and enjoy cooler temperatures\n"
        response_text += f"• Tuk-tuks are perfect for short distances, but consider a taxi for longer trips\n"
        response_text += f"• Don't forget sunscreen, a hat, and plenty of water - Sri Lanka can get quite warm!\n"
        response_text += f"• Book tickets online for popular attractions to skip the queues\n"
        response_text += f"• Try the local street food - it's absolutely delicious and very affordable!\n\n"
        response_text += f"Have an amazing time exploring {city}! Feel free to ask me about any specific places or if you need restaurant recommendations! 😊"
        
        return {
            "type": "trip_plan",
            "text": response_text,
            "suggestions": suggestions,
            "city": city,
            "duration": duration,
            "images": self.api_service.get_place_images(city)
        }
    
    def _generate_weather_response(self, info: Dict) -> Dict[str, Any]:
        """Generate weather information"""
        location = info["location"].title()
        
        # Get weather data
        weather_data = self.api_service.get_weather_info(location)
        
        if weather_data:
            response_text = f"Great question! Let me check the current weather in {location} for you. 🌤️\n\n"
            response_text += f"**Current Weather in {location}:**\n"
            response_text += f"🌡️ **Temperature:** {weather_data['temperature']}\n"
            response_text += f"☁️ **Condition:** {weather_data['condition']}\n"
            response_text += f"🤔 **Feels Like:** {weather_data['feels_like']}\n"
            response_text += f"💧 **Humidity:** {weather_data['humidity']}\n"
            response_text += f"💨 **Wind:** {weather_data['wind_speed']}\n\n"
            response_text += f"**Description:** {weather_data['description']}\n\n"
            
            # Add tourism advice based on weather
            if "sunny" in weather_data['condition'].lower() or "clear" in weather_data['condition'].lower():
                response_text += "☀️ **Perfect weather for outdoor activities!** This is ideal for visiting beaches, hiking, or exploring outdoor attractions. Don't forget your sunscreen! 😎"
            elif "rain" in weather_data['condition'].lower():
                response_text += "🌧️ **Rainy day ahead!** No worries though - Sri Lanka has amazing indoor attractions like museums, temples, and cultural centers. It's actually a great time to experience the local culture! 🏛️"
            elif "cloud" in weather_data['condition'].lower():
                response_text += "⛅ **Comfortable weather for sightseeing!** The clouds will keep you cool while exploring. Perfect for walking tours and outdoor photography! 📸"
            else:
                response_text += "🌤️ **Good weather for tourism!** This should be comfortable for most activities. Enjoy your time in Sri Lanka! 🇱🇰"
            
            return {
                "type": "weather",
                "text": response_text,
                "weather_data": weather_data,
                "location": location
            }
        
        return {
            "type": "error",
            "text": f"I'm sorry, I couldn't get the current weather information for {location}. Please try again or ask me about something else I can help you with! 😊"
        }
    
    def _generate_restaurants_response(self, info: Dict) -> Dict[str, Any]:
        """Generate restaurant recommendations"""
        city = info["city"].title()
        
        restaurants = self.api_service.get_google_places(city, "restaurant")
        
        response_text = f"**🍽️ Top Restaurants in {city}**\n\n"
        
        for i, restaurant in enumerate(restaurants, 1):
            response_text += f"{i}. **{restaurant['name']}** ⭐ {restaurant['rating']}\n"
            response_text += f"   🍴 {restaurant['type']}\n"
            response_text += f"   📍 {restaurant['address']}\n\n"
        
        response_text += "**💡 Dining Tips:**\n"
        response_text += "• Try local Sri Lankan cuisine\n"
        response_text += "• Book tables in advance for popular restaurants\n"
        response_text += "• Ask for recommendations from locals\n"
        
        return {
            "type": "restaurants",
            "text": response_text,
            "restaurants": restaurants,
            "city": city
        }
    
    def _generate_hotels_response(self, info: Dict) -> Dict[str, Any]:
        """Generate hotel recommendations"""
        city = info["city"].title()
        
        hotels = self.api_service.get_google_places(city, "lodging")
        
        response_text = f"**🏨 Recommended Hotels in {city}**\n\n"
        
        for i, hotel in enumerate(hotels, 1):
            response_text += f"{i}. **{hotel['name']}** ⭐ {hotel['rating']}\n"
            response_text += f"   🏨 {hotel['type']}\n"
            response_text += f"   📍 {hotel['address']}\n\n"
        
        response_text += "**💡 Booking Tips:**\n"
        response_text += "• Book in advance for better rates\n"
        response_text += "• Check for package deals\n"
        response_text += "• Read recent reviews before booking\n"
        
        return {
            "type": "hotels",
            "text": response_text,
            "hotels": hotels,
            "city": city
        }
    
    def _generate_place_info_response(self, info: Dict) -> Dict[str, Any]:
        """Generate place information using Wikipedia"""
        place = info["place"].title()
        
        # Get Wikipedia information
        wiki_data = self.api_service.get_wikipedia_info(place)
        
        if wiki_data:
            response_text = f"**📍 {wiki_data['title']}**\n\n"
            response_text += f"{wiki_data['extract']}\n\n"
            
            if wiki_data.get('description'):
                response_text += f"**Type:** {wiki_data['description']}\n"
            
            if wiki_data.get('url'):
                response_text += f"**Learn More:** [Wikipedia]({wiki_data['url']})\n"
            
            # Add tourism-specific information
            response_text += "\n**🎯 Tourism Highlights:**\n"
            response_text += "• Historical significance\n"
            response_text += "• Cultural importance\n"
            response_text += "• Great for photography\n"
            response_text += "• Family-friendly destination\n"
            
            return {
                "type": "place_info",
                "text": response_text,
                "wiki_data": wiki_data,
                "place": place,
                "images": self.api_service.get_place_images(place)
            }
        
        return {
            "type": "error",
            "text": f"Sorry, I couldn't find detailed information about {place}."
        }
    
    def _generate_attractions_response(self, info: Dict) -> Dict[str, Any]:
        """Generate attractions list"""
        city = info["city"].title()
        
        attractions = self.api_service.get_google_places(city, "tourist_attraction")
        
        response_text = f"**🎯 Top Attractions in {city}**\n\n"
        
        for i, attraction in enumerate(attractions, 1):
            response_text += f"{i}. **{attraction['name']}** ⭐ {attraction['rating']}\n"
            response_text += f"   🏛️ {attraction['type']}\n"
            response_text += f"   📍 {attraction['address']}\n\n"
        
        response_text += "**💡 Visiting Tips:**\n"
        response_text += "• Check opening hours before visiting\n"
        response_text += "• Consider guided tours for historical sites\n"
        response_text += "• Bring camera for amazing photos\n"
        
        return {
            "type": "attractions",
            "text": response_text,
            "attractions": attractions,
            "city": city
        }
    
    def _generate_general_response(self, query: str) -> Dict[str, Any]:
        """Generate general conversational response"""
        
        # Simple responses for common queries
        simple_responses = {
            "hello": "Hello there! 👋 I'm your friendly Virtual Tour Guide for Sri Lanka! I'm here to help you discover the most amazing places, plan perfect trips, find the best restaurants, and make your Sri Lankan adventure absolutely unforgettable. What would you like to explore today?",
            "hi": "Hi! 🌴 Welcome to Sri Lanka! I'm so excited to help you plan an incredible journey through this beautiful island. Whether you want to explore ancient temples, relax on pristine beaches, or discover hidden gems, I'm here to make it happen! What's on your mind?",
            "help": "I'd be happy to help! 😊 I'm your personal Sri Lankan travel assistant, and I can do quite a lot for you:\n\n🗺️ **Plan amazing trips** - from quick 2-hour tours to multi-day adventures\n🌤️ **Check real-time weather** - so you know what to wear and where to go\n🍽️ **Find incredible restaurants** - from street food to fine dining\n🏨 **Recommend perfect hotels** - for every budget and style\n📍 **Share fascinating info** - about Sri Lanka's amazing places and history\n🎯 **Suggest must-see attractions** - tailored to your interests\n\nJust ask me anything about Sri Lanka - I love talking about this incredible country!",
            "thanks": "You're so welcome! 😊 I absolutely love helping people discover the magic of Sri Lanka. Feel free to ask me anything else - I'm here to make your journey amazing!",
            "thank you": "You're very welcome! 🎉 It makes me so happy to help you explore Sri Lanka. Have an absolutely wonderful time, and don't hesitate to ask if you need anything else!",
            "yes": "Great! I'm excited to help you with that! What would you like to know or plan?",
            "no": "No problem at all! Is there something else I can help you with instead?",
            "ok": "Perfect! What would you like to explore or plan?",
            "okay": "Awesome! I'm here and ready to help you discover Sri Lanka! What's on your mind?"
        }
        
        query_lower = query.lower().strip()
        
        if query_lower in simple_responses:
            return {
                "type": "general",
                "text": simple_responses[query_lower]
            }
        
        # Default response - more natural and ChatGPT-like
        return {
            "type": "general",
            "text": f"I'm your personal Virtual Tour Guide for Sri Lanka! 🇱🇰 I'm absolutely passionate about helping people discover the incredible beauty and culture of this amazing island.\n\nHere's what I can help you with:\n\n🗺️ **Trip Planning** - \"Plan a 3-hour trip to Kandy\" or \"Plan a 2-day adventure in Galle\"\n🌤️ **Weather Updates** - \"What's the weather like in Colombo?\"\n🍽️ **Food Discovery** - \"Best restaurants in Negombo\" or \"Where to eat in Anuradhapura\"\n🏨 **Accommodation** - \"Hotels in Sigiriya\" or \"Where to stay in Trincomalee\"\n📍 **Place Information** - \"Tell me about the Temple of the Tooth\" or \"What's special about Ella?\"\n🎯 **Attractions** - \"Top things to do in Bentota\" or \"Must-see places in Jaffna\"\n\nI love talking about Sri Lanka's rich history, stunning landscapes, delicious food, and warm people. What would you like to explore? I'm here to make your Sri Lankan adventure absolutely amazing! 😊"
        }
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for better matching and spelling correction"""
        query = query.lower().strip()
        
        # Common spelling corrections for Sri Lankan places
        spelling_corrections = {
            "columbo": "colombo",
            "kandi": "kandy", 
            "candy": "kandy",
            "sigiri": "sigiriya",
            "gale": "galle",
            "negambo": "negombo",
            "anuradapura": "anuradhapura",
            "polonnaruwa": "polonnaruwa",
            "trincomalee": "trincomalee",
            "nuwara": "nuwara eliya",
            "nuwara eliya": "nuwara eliya",
            "dambulla": "dambulla",
            "bentota": "bentota",
            "mirissa": "mirissa",
            "unawatuna": "unawatuna",
            "ella": "ella",
            "jaffna": "jaffna",
            "batticaloa": "batticaloa",
            "kurunegala": "kurunegala",
            "ratnapura": "ratnapura"
        }
        
        # Apply spelling corrections
        for misspelling, correction in spelling_corrections.items():
            if misspelling in query:
                query = query.replace(misspelling, correction)
        
        return query
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def _generate_transportation_response(self, info: Dict) -> Dict[str, Any]:
        """Generate transportation information"""
        place = info.get("place", "sri lanka").title()
        
        return {
            "type": "transportation",
            "text": f"**🚌 Transportation to {place}**\n\nHere are the best ways to reach {place}:\n\n**🚗 By Road:**\n• **Bus:** Regular buses from Colombo and major cities\n• **Car:** Rent a car for flexibility and comfort\n• **Taxi:** Private taxi services available\n\n**🚂 By Train:**\n• Scenic train routes available from Colombo\n• Book in advance for popular routes\n\n**✈️ By Air:**\n• Domestic flights available to major cities\n• International airport connections\n\n**💡 Tips:**\n• Book transportation in advance during peak season\n• Consider traffic conditions for road travel\n• Train journeys offer beautiful scenery\n\nNeed specific details about any transportation option? Just ask! 😊"
        }
    
    def _generate_history_response(self, info: Dict) -> Dict[str, Any]:
        """Generate historical information"""
        place = info.get("place", "sri lanka").title()
        
        return {
            "type": "history",
            "text": f"**📜 History of {place}**\n\n{place} has a fascinating historical background:\n\n**🏛️ Ancient Heritage:**\n• Rich cultural traditions dating back centuries\n• Important archaeological sites and monuments\n• UNESCO World Heritage sites\n\n**👑 Royal Connections:**\n• Former royal capitals and kingdoms\n• Ancient palaces and temples\n• Historical artifacts and treasures\n\n**🌍 Colonial Influence:**\n• Portuguese, Dutch, and British colonial periods\n• Architectural influences from different eras\n• Cultural blending and heritage\n\n**📚 Key Historical Events:**\n• Significant events that shaped the region\n• Cultural and religious developments\n• Modern historical importance\n\n**🎯 Must-Visit Historical Sites:**\n• Ancient temples and monuments\n• Museums with rich collections\n• Heritage buildings and structures\n\nWant to know more about specific historical periods or sites? I'd love to share more details! 🏛️"
        }
    
    def _generate_best_time_response(self, info: Dict) -> Dict[str, Any]:
        """Generate best time to visit information"""
        place = info.get("place", "sri lanka").title()
        
        return {
            "type": "best_time",
            "text": f"**📅 Best Time to Visit {place}**\n\n**🌞 Peak Season (December - March):**\n• **Weather:** Dry and pleasant\n• **Temperature:** 25-30°C\n• **Best for:** Sightseeing, beaches, outdoor activities\n• **Note:** Higher prices and crowds\n\n**🌧️ Monsoon Season (May - September):**\n• **Weather:** Rainy but lush green landscapes\n• **Temperature:** 22-28°C\n• **Best for:** Photography, fewer crowds, lower prices\n• **Note:** Some outdoor activities may be limited\n\n**🍂 Shoulder Season (October - November, April):**\n• **Weather:** Mixed conditions\n• **Temperature:** 24-29°C\n• **Best for:** Balanced experience\n• **Note:** Good value for money\n\n**💡 Pro Tips:**\n• Book accommodations in advance for peak season\n• Pack accordingly for weather conditions\n• Consider local festivals and events\n• Check specific regional weather patterns\n\n**🎉 Special Events:**\n• Cultural festivals throughout the year\n• Religious celebrations\n• Local events and traditions\n\nPlanning your trip timing perfectly? I can help you plan the ideal itinerary! 📅"
        }
    
    def _generate_cost_response(self, info: Dict) -> Dict[str, Any]:
        """Generate cost information"""
        place = info.get("place", "sri lanka").title()
        
        return {
            "type": "cost",
            "text": f"**💰 Cost of Visiting {place}**\n\n**🏨 Accommodation:**\n• **Budget:** LKR 2,000-5,000 per night\n• **Mid-range:** LKR 5,000-15,000 per night\n• **Luxury:** LKR 15,000+ per night\n\n**🍽️ Food & Dining:**\n• **Street Food:** LKR 200-500 per meal\n• **Local Restaurants:** LKR 500-1,500 per meal\n• **Fine Dining:** LKR 2,000+ per meal\n\n**🚌 Transportation:**\n• **Bus:** LKR 100-500 per trip\n• **Train:** LKR 200-800 per journey\n• **Taxi:** LKR 1,000-3,000 per day\n• **Car Rental:** LKR 5,000-10,000 per day\n\n**🎯 Attractions & Activities:**\n• **Temples:** LKR 500-2,000 entry\n• **Museums:** LKR 500-1,500 entry\n• **National Parks:** LKR 2,000-5,000 entry\n• **Guided Tours:** LKR 3,000-10,000 per day\n\n**💡 Budget Tips:**\n• Travel during off-peak season\n• Use public transportation\n• Eat at local restaurants\n• Book accommodations in advance\n• Look for package deals\n\n**📊 Daily Budget Estimates:**\n• **Backpacker:** LKR 3,000-5,000\n• **Mid-range:** LKR 8,000-15,000\n• **Luxury:** LKR 20,000+\n\nNeed help planning your budget? I can create a detailed cost breakdown! 💰"
        }
    
    def _generate_distance_response(self, info: Dict) -> Dict[str, Any]:
        """Generate distance information"""
        query = info.get("query", "")
        
        return {
            "type": "distance",
            "text": f"**📏 Distance Information**\n\nHere are the distances from major cities in Sri Lanka:\n\n**🚗 From Colombo:**\n• **To Kandy:** ~115 km (2-3 hours)\n• **To Galle:** ~120 km (2-3 hours)\n• **To Anuradhapura:** ~205 km (4-5 hours)\n• **To Sigiriya:** ~170 km (3-4 hours)\n• **To Trincomalee:** ~260 km (5-6 hours)\n• **To Nuwara Eliya:** ~180 km (4-5 hours)\n• **To Jaffna:** ~400 km (8-10 hours)\n\n**🚂 By Train:**\n• **Colombo to Kandy:** ~3 hours\n• **Colombo to Galle:** ~3 hours\n• **Colombo to Anuradhapura:** ~5 hours\n\n**✈️ By Air:**\n• **Colombo to Jaffna:** ~1 hour\n• **Colombo to Trincomalee:** ~45 minutes\n\n**💡 Travel Tips:**\n• Consider traffic conditions for road travel\n• Book train tickets in advance\n• Domestic flights available for longer distances\n• Factor in rest stops for long drives\n\n**🗺️ Route Planning:**\n• Use GPS navigation apps\n• Check road conditions\n• Plan fuel stops\n• Consider scenic routes\n\nNeed specific directions or route planning? I can help you plan the perfect journey! 🗺️"
        }
    
    def _generate_recommendations_response(self, info: Dict) -> Dict[str, Any]:
        """Generate recommendations"""
        query = info.get("query", "")
        
        return {
            "type": "recommendations",
            "text": f"**⭐ My Top Recommendations for Sri Lanka**\n\n**🏛️ Must-Visit Cultural Sites:**\n• **Temple of the Tooth Relic** (Kandy)\n• **Sigiriya Rock Fortress**\n• **Anuradhapura Ancient City**\n• **Polonnaruwa Archaeological Park**\n• **Galle Fort** (UNESCO World Heritage)\n\n**🏖️ Beautiful Beaches:**\n• **Mirissa Beach** (whale watching)\n• **Unawatuna Beach** (swimming)\n• **Bentota Beach** (water sports)\n• **Trincomalee** (diving)\n• **Negombo Beach** (close to airport)\n\n**🌄 Natural Wonders:**\n• **Ella** (hiking and views)\n• **Nuwara Eliya** (tea plantations)\n• **Yala National Park** (wildlife safari)\n• **Horton Plains** (hiking)\n• **Adam's Peak** (pilgrimage)\n\n**🍽️ Food Experiences:**\n• **Rice and Curry** (traditional)\n• **Hopper** (local breakfast)\n• **Kottu Roti** (street food)\n• **Fresh Seafood** (coastal areas)\n• **Tea Tasting** (tea plantations)\n\n**🏨 Accommodation Types:**\n• **Boutique Hotels** (luxury experience)\n• **Eco Lodges** (nature immersion)\n• **Homestays** (local culture)\n• **Beach Resorts** (relaxation)\n• **City Hotels** (convenience)\n\n**🎯 Activity Recommendations:**\n• **Safari Tours** (wildlife)\n• **Temple Visits** (spiritual)\n• **Beach Relaxation** (wellness)\n• **Cultural Shows** (entertainment)\n• **Adventure Sports** (thrills)\n\nBased on your interests, I can create personalized recommendations! What type of experience are you looking for? ⭐"
        }
    
    def _generate_comparison_response(self, info: Dict) -> Dict[str, Any]:
        """Generate comparison information"""
        query = info.get("query", "")
        
        return {
            "type": "comparison",
            "text": f"**⚖️ Comparison Guide**\n\nI'd love to help you compare different destinations, accommodations, or experiences in Sri Lanka!\n\n**🏙️ Popular City Comparisons:**\n• **Colombo vs Kandy** (modern vs cultural)\n• **Galle vs Negombo** (historic vs beach)\n• **Ella vs Nuwara Eliya** (adventure vs tea country)\n\n**🏨 Accommodation Comparisons:**\n• **Hotels vs Guesthouses** (luxury vs budget)\n• **Beach vs City Hotels** (location preferences)\n• **Boutique vs Chain Hotels** (experience types)\n\n**🍽️ Food Comparisons:**\n• **Street Food vs Restaurants** (authentic vs comfort)\n• **Local vs International Cuisine** (cultural experience)\n• **Budget vs Fine Dining** (price ranges)\n\n**🚌 Transportation Comparisons:**\n• **Bus vs Train vs Taxi** (cost vs comfort vs speed)\n• **Public vs Private Transport** (convenience vs budget)\n• **Car Rental vs Guided Tours** (flexibility vs expertise)\n\n**💡 Comparison Factors:**\n• **Cost** (budget considerations)\n• **Time** (duration and scheduling)\n• **Experience** (cultural vs convenience)\n• **Location** (accessibility and surroundings)\n• **Services** (amenities and facilities)\n\n**🎯 What would you like to compare?**\n• Specific destinations or cities\n• Types of accommodations\n• Transportation options\n• Activities or experiences\n• Budget vs luxury options\n\nTell me what you'd like to compare, and I'll give you a detailed analysis! ⚖️"
        }
    
    def _generate_activities_response(self, info: Dict) -> Dict[str, Any]:
        """Generate activity-specific information"""
        activity = info.get("activity", "")
        place = info.get("place", "sri lanka").title()
        
        return {
            "type": "activities",
            "text": f"**🎯 {activity.title()} in {place}**\n\n**🏔️ Hiking & Nature:**\n• **Ella Rock** (challenging hike with stunning views)\n• **Little Adam's Peak** (easier hike, great for beginners)\n• **Horton Plains** (plateau hiking and World's End)\n• **Knuckles Range** (mountain hiking)\n• **Sinharaja Forest** (rainforest trekking)\n\n**📸 Photography Spots:**\n• **Sigiriya Rock** (iconic fortress)\n• **Tea Plantations** (Nuwara Eliya and Ella)\n• **Temple Complexes** (ancient architecture)\n• **Beach Sunsets** (coastal beauty)\n• **Wildlife Safaris** (animal photography)\n\n**🌙 Nightlife:**\n• **Colombo** (bars, clubs, and restaurants)\n• **Negombo** (beachside nightlife)\n• **Galle** (historic fort area)\n• **Kandy** (cultural evening shows)\n• **Unawatuna** (beach parties)\n\n**🛍️ Shopping:**\n• **Colombo** (modern malls and markets)\n• **Kandy** (cultural souvenirs)\n• **Galle** (antiques and crafts)\n• **Negombo** (beachside shopping)\n• **Local Markets** (authentic experiences)\n\n**🏖️ Beach Activities:**\n• **Mirissa** (whale watching and surfing)\n• **Bentota** (water sports and relaxation)\n• **Trincomalee** (diving and snorkeling)\n• **Unawatuna** (swimming and beach bars)\n• **Arugam Bay** (surfing capital)\n\n**🏛️ Temple Visits:**\n• **Temple of the Tooth** (Kandy)\n• **Dambulla Cave Temple**\n• **Gangaramaya Temple** (Colombo)\n• **Ancient City Temples** (Anuradhapura)\n• **Buddhist Monasteries** (throughout the country)\n\n**💡 Activity Tips:**\n• Book in advance for popular activities\n• Check weather conditions\n• Wear appropriate clothing\n• Respect local customs\n• Bring necessary equipment\n\n**🎯 Specific Recommendations:**\n• Best time of day for activities\n• Required permits or bookings\n• Difficulty levels and requirements\n• Local guides and tour operators\n• Safety considerations\n\nWant more details about any specific activity? I can provide detailed information! 🎯"
        }
    
    def _generate_beaches_list_response(self, info: Dict) -> Dict[str, Any]:
        """Generate beaches list for specific locations"""
        place = info.get("place", "sri lanka").lower()
        
        # Location-specific beach lists
        beach_data = {
            "colombo": [
                {"name": "Mount Lavinia Beach", "description": "Popular beach with restaurants and water sports", "features": "Swimming, dining, beach bars"},
                {"name": "Negombo Beach", "description": "Close to airport, great for first/last day", "features": "Easy access, beach hotels"},
                {"name": "Dehiwala Beach", "description": "Local beach with calm waters", "features": "Family-friendly, less crowded"},
                {"name": "Wellawatta Beach", "description": "Urban beach with good facilities", "features": "Beach volleyball, food stalls"}
            ],
            "galle": [
                {"name": "Unawatuna Beach", "description": "Famous crescent-shaped beach with coral reef", "features": "Snorkeling, diving, beach bars"},
                {"name": "Mirissa Beach", "description": "Whale watching capital with beautiful sunsets", "features": "Whale watching, surfing, beach parties"},
                {"name": "Hikkaduwa Beach", "description": "Popular beach with coral reef and marine life", "features": "Snorkeling, diving, beach resorts"},
                {"name": "Bentota Beach", "description": "Long sandy beach with water sports", "features": "Jet skiing, windsurfing, beach hotels"},
                {"name": "Weligama Beach", "description": "Famous for stilt fishing and surfing", "features": "Surfing, fishing culture, photography"}
            ],
            "trincomalee": [
                {"name": "Nilaveli Beach", "description": "Pristine beach with crystal clear waters", "features": "Swimming, snorkeling, diving"},
                {"name": "Uppuveli Beach", "description": "Beautiful beach with calm waters", "features": "Swimming, beach resorts, fishing"},
                {"name": "Marble Beach", "description": "Unique beach with marble-like rocks", "features": "Photography, swimming, unique landscape"},
                {"name": "Pigeon Island", "description": "Marine national park with coral reef", "features": "Diving, snorkeling, marine life"}
            ],
            "jaffna": [
                {"name": "Casuarina Beach", "description": "Northern beach with unique landscape", "features": "Swimming, beach walks, local culture"},
                {"name": "Point Pedro Beach", "description": "Northernmost beach of Sri Lanka", "features": "Photography, fishing, historical significance"},
                {"name": "Nagadeepa Beach", "description": "Near Nagadeepa temple, peaceful setting", "features": "Religious significance, peaceful atmosphere"}
            ],
            "anuradhapura": [
                {"name": "Kalawewa Beach", "description": "Artificial lake with beach-like areas", "features": "Boating, fishing, picnic spots"},
                {"name": "Nuwarawewa", "description": "Ancient tank with recreational areas", "features": "Historical significance, boating, nature"}
            ]
        }
        
        # Get beaches for the specific place or default to general Sri Lankan beaches
        beaches = beach_data.get(place, [
            {"name": "Mirissa Beach", "description": "Whale watching and surfing paradise", "features": "Whale watching, surfing, beach parties"},
            {"name": "Unawatuna Beach", "description": "Crescent-shaped beach with coral reef", "features": "Snorkeling, diving, beach bars"},
            {"name": "Bentota Beach", "description": "Long sandy beach with water sports", "features": "Jet skiing, windsurfing, beach hotels"},
            {"name": "Hikkaduwa Beach", "description": "Popular beach with marine life", "features": "Snorkeling, diving, beach resorts"},
            {"name": "Negombo Beach", "description": "Close to Colombo airport", "features": "Easy access, beach hotels, fishing"},
            {"name": "Trincomalee Beaches", "description": "Pristine beaches in the east", "features": "Swimming, diving, marine national parks"},
            {"name": "Arugam Bay", "description": "Surfing capital of Sri Lanka", "features": "Surfing, beach parties, wildlife"},
            {"name": "Kalpitiya Beach", "description": "Kite surfing and dolphin watching", "features": "Kite surfing, dolphin watching, fishing"}
        ])
        
        response_text = f"**🏖️ Beaches in {place.title()}**\n\n"
        
        for i, beach in enumerate(beaches, 1):
            response_text += f"**{i}. {beach['name']}** ⭐\n"
            response_text += f"   📍 {beach['description']}\n"
            response_text += f"   🎯 Features: {beach['features']}\n\n"
        
        response_text += "**💡 Beach Tips:**\n"
        response_text += "• Best time: December to March (dry season)\n"
        response_text += "• Bring sunscreen and water\n"
        response_text += "• Check weather conditions\n"
        response_text += "• Respect marine life and coral reefs\n"
        response_text += "• Some beaches have entry fees for facilities\n\n"
        response_text += "Need more details about any specific beach? Just ask! 🏖️"
        
        return {
            "type": "beaches_list",
            "text": response_text
        }
    
    def _generate_temples_list_response(self, info: Dict) -> Dict[str, Any]:
        """Generate temples list for specific locations"""
        place = info.get("place", "sri lanka").lower()
        
        # Location-specific temple lists
        temple_data = {
            "jaffna": [
                {"name": "Nallur Kandaswamy Temple", "description": "Most important Hindu temple in Jaffna", "features": "Daily pujas, annual festival, architecture"},
                {"name": "Nagadeepa Purana Vihara", "description": "Ancient Buddhist temple on Nagadeepa island", "features": "Pilgrimage site, boat access, historical"},
                {"name": "Jaffna Public Library", "description": "Cultural landmark with historical significance", "features": "Architecture, history, cultural importance"},
                {"name": "Mantri Manai", "description": "Traditional Tamil architectural complex", "features": "Traditional architecture, cultural heritage"}
            ],
            "kandy": [
                {"name": "Temple of the Tooth Relic", "description": "Most sacred Buddhist temple in Sri Lanka", "features": "Sacred relic, daily ceremonies, UNESCO site"},
                {"name": "Lankatilaka Vihara", "description": "Ancient Buddhist temple with unique architecture", "features": "Ancient architecture, religious significance"},
                {"name": "Gadaladeniya Temple", "description": "Stone temple with South Indian influence", "features": "Stone architecture, historical importance"},
                {"name": "Embekka Devalaya", "description": "Wooden temple famous for intricate carvings", "features": "Wooden architecture, detailed carvings"}
            ],
            "colombo": [
                {"name": "Gangaramaya Temple", "description": "Famous Buddhist temple with museum", "features": "Museum, library, cultural center"},
                {"name": "Kelaniya Raja Maha Vihara", "description": "Ancient temple with beautiful murals", "features": "Ancient murals, religious ceremonies"},
                {"name": "Sri Ponnambalawaneswaram Temple", "description": "Hindu temple with Dravidian architecture", "features": "Hindu architecture, religious festivals"},
                {"name": "Wolvendaal Church", "description": "Historic Dutch colonial church", "features": "Colonial architecture, historical significance"}
            ],
            "anuradhapura": [
                {"name": "Sri Maha Bodhi", "description": "Sacred Bodhi tree, oldest in the world", "features": "Sacred tree, pilgrimage site, ancient history"},
                {"name": "Ruwanwelisaya", "description": "Great stupa built by King Dutugemunu", "features": "Ancient stupa, architectural marvel"},
                {"name": "Abhayagiri Vihara", "description": "Ancient monastery complex", "features": "Archaeological site, ancient monastery"},
                {"name": "Jetavanaramaya", "description": "Massive ancient stupa", "features": "World's tallest stupa, architectural wonder"}
            ],
            "polonnaruwa": [
                {"name": "Gal Vihara", "description": "Rock temple with four Buddha statues", "features": "Rock carvings, ancient art, UNESCO site"},
                {"name": "Lotus Bath", "description": "Ancient royal bathing pool", "features": "Ancient architecture, royal history"},
                {"name": "Parakrama Samudra", "description": "Ancient reservoir built by King Parakramabahu", "features": "Ancient engineering, water management"},
                {"name": "Rankot Vihara", "description": "Large ancient stupa", "features": "Ancient stupa, archaeological significance"}
            ],
            "dambulla": [
                {"name": "Dambulla Cave Temple", "description": "UNESCO World Heritage site with cave temples", "features": "Cave temples, ancient paintings, UNESCO site"},
                {"name": "Golden Temple", "description": "Modern temple complex with golden Buddha", "features": "Modern architecture, golden Buddha statue"},
                {"name": "Rangiri Dambulla Cave Temple", "description": "Ancient cave temple with Buddha statues", "features": "Cave architecture, ancient statues, paintings"}
            ]
        }
        
        # Get temples for the specific place or default to general Sri Lankan temples
        temples = temple_data.get(place, [
            {"name": "Temple of the Tooth Relic (Kandy)", "description": "Most sacred Buddhist temple", "features": "Sacred relic, UNESCO World Heritage"},
            {"name": "Dambulla Cave Temple", "description": "Ancient cave temple complex", "features": "Cave temples, ancient paintings, UNESCO site"},
            {"name": "Gangaramaya Temple (Colombo)", "description": "Famous Buddhist temple with museum", "features": "Museum, cultural center, architecture"},
            {"name": "Sri Maha Bodhi (Anuradhapura)", "description": "Sacred Bodhi tree", "features": "Sacred tree, pilgrimage site, ancient history"},
            {"name": "Nallur Kandaswamy Temple (Jaffna)", "description": "Important Hindu temple", "features": "Hindu architecture, annual festivals"},
            {"name": "Gal Vihara (Polonnaruwa)", "description": "Rock temple with Buddha statues", "features": "Rock carvings, ancient art, UNESCO site"},
            {"name": "Kelaniya Raja Maha Vihara", "description": "Ancient temple with beautiful murals", "features": "Ancient murals, religious ceremonies"},
            {"name": "Abhayagiri Vihara (Anuradhapura)", "description": "Ancient monastery complex", "features": "Archaeological site, ancient monastery"}
        ])
        
        response_text = f"**🏛️ Temples in {place.title()}**\n\n"
        
        for i, temple in enumerate(temples, 1):
            response_text += f"**{i}. {temple['name']}** ⭐\n"
            response_text += f"   📍 {temple['description']}\n"
            response_text += f"   🎯 Features: {temple['features']}\n\n"
        
        response_text += "**💡 Temple Visit Tips:**\n"
        response_text += "• Dress modestly (cover shoulders and knees)\n"
        response_text += "• Remove shoes before entering\n"
        response_text += "• Respect religious ceremonies\n"
        response_text += "• Check opening hours\n"
        response_text += "• Some temples have entry fees\n"
        response_text += "• Photography may be restricted\n\n"
        response_text += "Need more details about any specific temple? Just ask! 🏛️"
        
        return {
            "type": "temples_list",
            "text": response_text
        }
