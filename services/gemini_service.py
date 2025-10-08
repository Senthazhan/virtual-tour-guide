"""
Gemini AI Service for Virtual Tour Guide
Provides real web data and intelligent responses
"""

import os
import re
from typing import Dict, List, Optional, Any
import requests
import json

class GeminiService:
    """Service to interact with Google Gemini AI for tourism data"""
    
    def __init__(self):
        # Get Gemini API key from config
        from config import Config
        self.api_key = Config.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
    def get_tourism_info(self, query: str, location: str = "Sri Lanka") -> Dict[str, Any]:
        """Get comprehensive tourism information using Gemini AI"""
        
        if self.api_key == 'demo_key':
            return self._get_demo_response(query, location)
        
        try:
            # Create prompt for Gemini
            prompt = f"""
            You are a professional tour guide for {location}. Provide detailed, accurate information about: {query}
            
            Please provide:
            1. Brief description (2-3 sentences)
            2. Key highlights/attractions
            3. Best time to visit
            4. Entry fees (if applicable)
            5. Location details
            6. How to get there
            7. Nearby restaurants (2-3 recommendations)
            8. Nearby hotels (2-3 recommendations)
            9. Travel tips
            
            Format the response as JSON with these keys: description, highlights, best_time, entry_fees, location, transportation, restaurants, hotels, tips
            """
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['candidates'][0]['content']['parts'][0]['text']
                
                # Try to parse JSON response
                try:
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        parsed_data = json.loads(json_match.group())
                        return {
                            "success": True,
                            "data": parsed_data,
                            "source": "gemini_api"
                        }
                except json.JSONDecodeError:
                    pass
                
                # If JSON parsing fails, return raw text
                return {
                    "success": True,
                    "data": {"description": content},
                    "source": "gemini_api_text"
                }
            
            else:
                return self._get_demo_response(query, location)
                
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._get_demo_response(query, location)
    
    def _get_demo_response(self, query: str, location: str) -> Dict[str, Any]:
        """Provide demo responses when API key is not available"""
        
        # Comprehensive Sri Lankan tourism database
        tourism_data = {
            # Colombo
            "colombo": {
                "description": "Colombo is the vibrant commercial capital of Sri Lanka, blending modern urban life with rich colonial heritage. The city offers a mix of historic sites, bustling markets, and contemporary attractions. As the economic hub, it's the gateway to exploring the rest of Sri Lanka.",
                "highlights": ["Gangaramaya Temple", "Colombo National Museum", "Galle Face Green", "Pettah Market", "Independence Memorial Hall", "Mount Lavinia Beach", "Lotus Tower", "Viharamahadevi Park"],
                "best_time": "December to March (dry season with pleasant weather)",
                "entry_fees": "Most attractions: LKR 500-2000, Museums: LKR 1000-1500",
                "location": "Western Province, Sri Lanka",
                "transportation": "Tuk-tuks, buses, taxis, Uber/PickMe available",
                "restaurants": ["Ministry of Crab", "Paradise Road Gallery Cafe", "Nuga Gama"],
                "hotels": ["Galle Face Hotel", "Cinnamon Grand", "Shangri-La Colombo"],
                "tips": "Visit early morning to avoid traffic, try local street food, book hotels in advance"
            },
            
            # Jaffna
            "jaffna": {
                "description": "Jaffna is the cultural capital of the Tamil community in Sri Lanka, located in the northernmost part of the island. The city is known for its rich Tamil culture, historic temples, and unique cuisine. It's a fascinating destination that offers a different perspective on Sri Lankan culture.",
                "highlights": ["Jaffna Fort", "Nallur Kandaswamy Temple", "Jaffna Public Library", "Casuarina Beach", "Nagadeepa Purana Vihara", "Jaffna Market"],
                "best_time": "December to March (best weather for northern Sri Lanka)",
                "entry_fees": "Temples: Free, Fort: LKR 500-1000",
                "location": "Northern Province, Sri Lanka",
                "transportation": "Bus from Colombo (8-10 hours), domestic flights available",
                "restaurants": ["Mangos", "Rio Ice Cream", "Cosy Restaurant"],
                "hotels": ["Jetwing Jaffna", "The Thinnai", "Green Grass Hotel"],
                "tips": "Try Jaffna cuisine, visit during festivals, respect local customs"
            },
            
            # Kandy
            "kandy": {
                "description": "Kandy is the cultural capital of Sri Lanka, home to the sacred Temple of the Tooth Relic and surrounded by lush hills. It's a UNESCO World Heritage city with rich Buddhist traditions.",
                "highlights": ["Temple of the Tooth Relic", "Kandy Lake", "Royal Botanical Gardens", "Kandy Cultural Show", "Bahirawakanda Buddha Statue", "Udawattakele Forest"],
                "best_time": "December to April (cooler weather, less rain)",
                "entry_fees": "Temple of Tooth: LKR 2000, Botanical Gardens: LKR 1500",
                "location": "Central Province, Sri Lanka",
                "transportation": "Train from Colombo (scenic route), bus, private car",
                "restaurants": ["Empire Cafe", "Slightly Chilled Lounge Bar", "The Empire Hotel Restaurant"],
                "hotels": ["Earl's Regent", "Queen's Hotel", "Kandy City Hotel"],
                "tips": "Wear modest clothing for temples, visit during Perahera festival (July/August)"
            },
            
            # Sigiriya
            "sigiriya": {
                "description": "Sigiriya is an ancient rock fortress and UNESCO World Heritage Site, often called the 'Eighth Wonder of the World'. It features impressive frescoes and offers panoramic views.",
                "highlights": ["Sigiriya Rock Fortress", "Ancient Frescoes", "Mirror Wall", "Lion's Gate", "Water Gardens", "Archaeological Museum"],
                "best_time": "Early morning (6-8 AM) or late afternoon (4-6 PM) to avoid heat",
                "entry_fees": "Adults: LKR 5000, Children: LKR 2500",
                "location": "Matale District, Central Province",
                "transportation": "Bus from Colombo/Kandy, tuk-tuk from Dambulla",
                "restaurants": ["Sigiriya Village Hotel Restaurant", "Aliya Resort Restaurant", "Hotel Sigiriya Restaurant"],
                "hotels": ["Aliya Resort", "Sigiriya Village", "Jetwing Vil Uyana"],
                "tips": "Start climb early morning, bring water, wear comfortable shoes, camera for frescoes"
            },
            
            # Galle
            "galle": {
                "description": "Galle is a historic coastal city famous for its well-preserved Dutch colonial architecture and UNESCO World Heritage Galle Fort. It offers a perfect blend of history, culture, and beach life.",
                "highlights": ["Galle Fort", "Dutch Reformed Church", "Galle Lighthouse", "National Maritime Museum", "Unawatuna Beach", "Jungle Beach"],
                "best_time": "December to March (best weather for beach activities)",
                "entry_fees": "Fort area: Free, Museums: LKR 500-1000",
                "location": "Southern Province, Sri Lanka",
                "transportation": "Train from Colombo (scenic coastal route), bus, private car",
                "restaurants": ["Heritage Cafe", "Pedlar's Inn Cafe", "Chambers Restaurant"],
                "hotels": ["Galle Fort Hotel", "Jetwing Lighthouse", "Fort Bazaar"],
                "tips": "Walk around Fort walls at sunset, try local seafood, visit Unawatuna Beach"
            },
            
            # Anuradhapura
            "anuradhapura": {
                "description": "Anuradhapura is one of the world's oldest continuously inhabited cities and a UNESCO World Heritage Site. It's the ancient capital with magnificent Buddhist monuments and sacred sites.",
                "highlights": ["Sri Maha Bodhi Tree", "Ruwanwelisaya Stupa", "Abhayagiri Monastery", "Jetavanaramaya", "Isurumuniya Temple", "Archaeological Museum"],
                "best_time": "December to March (cooler, less humid)",
                "entry_fees": "Cultural Triangle ticket: LKR 7500 (valid 30 days)",
                "location": "North Central Province, Sri Lanka",
                "transportation": "Bus from Colombo (4-5 hours), train, private car",
                "restaurants": ["Hotel Alakamanda Restaurant", "Palm Garden Village Restaurant", "Rajaro Hotel Restaurant"],
                "hotels": ["Hotel Alakamanda", "Palm Garden Village", "Rajaro Hotel"],
                "tips": "Hire a bicycle or tuk-tuk for temple tours, dress modestly, visit early morning"
            },
            
            # Negombo
            "negombo": {
                "description": "Negombo is a coastal city near Colombo Airport, known for its fishing industry, beautiful beaches, and colonial churches. It's often the first stop for tourists arriving in Sri Lanka.",
                "highlights": ["Negombo Beach", "Dutch Canal", "St. Mary's Church", "Angurukaramulla Temple", "Fish Market", "Muthurajawela Marsh"],
                "best_time": "December to March (best beach weather)",
                "entry_fees": "Most attractions: Free, Boat tours: LKR 2000-3000",
                "location": "Western Province, Sri Lanka",
                "transportation": "Bus from Colombo (1 hour), tuk-tuk, taxi",
                "restaurants": ["Lord's Restaurant", "Palm Village Restaurant", "Ice Bear Restaurant"],
                "hotels": ["Jetwing Beach", "Heritance Negombo", "Goldi Sands Hotel"],
                "tips": "Great for first/last night, try fresh seafood, visit fish market early morning"
            },
            
            # Ella
            "ella": {
                "description": "Ella is a small mountain town famous for its stunning views, tea plantations, and iconic Nine Arches Bridge. It's a paradise for nature lovers and photographers.",
                "highlights": ["Nine Arches Bridge", "Ella Rock", "Little Adam's Peak", "Ravana Falls", "Ella Spice Garden", "Tea Factory Tours"],
                "best_time": "December to March (clear views, less rain)",
                "entry_fees": "Most attractions: Free, Tea factory tours: LKR 500-1000",
                "location": "Uva Province, Sri Lanka",
                "transportation": "Train from Colombo/Kandy (scenic route), bus, private car",
                "restaurants": ["Cafe Chill", "Ella Flower Garden Restaurant", "Matey Hut"],
                "hotels": ["Ella Jungle Resort", "98 Acres Resort", "Ella Flower Garden Resort"],
                "tips": "Take the famous train journey, hike early morning for best views, bring camera"
            }
        }
        
        # Normalize query for matching
        query_lower = query.lower().strip()
        
        # Try exact matches first
        for place, data in tourism_data.items():
            if place in query_lower or query_lower in place:
                return {
                    "success": True,
                    "data": data,
                    "source": "demo_database"
                }
        
        # Try fuzzy matching for common misspellings
        fuzzy_matches = {
            "colombo": ["colombo", "columbo", "kolombo"],
            "kandy": ["kandy", "kandi", "candy"],
            "sigiriya": ["sigiriya", "sigiri", "sigiriya rock", "lion rock"],
            "galle": ["galle", "gale", "galle fort"],
            "anuradhapura": ["anuradhapura", "anuradapura", "anuradhapura ancient city"],
            "negombo": ["negombo", "negambo", "negombo beach"],
            "ella": ["ella", "ella town", "nine arches bridge"]
        }
        
        for place, variations in fuzzy_matches.items():
            for variation in variations:
                if variation in query_lower:
                    return {
                        "success": True,
                        "data": tourism_data[place],
                        "source": "demo_database_fuzzy"
                    }
        
        # Default response for unknown places
        return {
            "success": True,
            "data": {
                "description": f"I'd be happy to help you with information about {query} in Sri Lanka! While I don't have specific details about this location, Sri Lanka has many amazing places to explore.",
                "highlights": ["Consult local tourism websites", "Ask locals for recommendations", "Visit tourist information centers"],
                "best_time": "Generally December to March for best weather",
                "entry_fees": "Varies by location - check official websites",
                "location": "Sri Lanka",
                "transportation": "Buses, trains, tuk-tuks, and taxis available",
                "restaurants": ["Ask locals for authentic recommendations"],
                "hotels": ["Book in advance, especially during peak season"],
                "tips": "Carry water, wear comfortable shoes, respect local customs"
            },
            "source": "default_response"
        }
    
    def get_weather_info(self, location: str) -> Dict[str, Any]:
        """Get weather information for a location"""
        # Location-specific weather data
        weather_data = {
            "colombo": {
                "temperature": "32°C",
                "condition": "Hot and Humid",
                "feels_like": "36°C",
                "humidity": "85%",
                "wind_speed": "8 km/h",
                "description": "Typical tropical weather in Colombo - hot and humid with occasional sea breeze"
            },
            "kandy": {
                "temperature": "28°C",
                "condition": "Pleasant and Cool",
                "feels_like": "30°C",
                "humidity": "75%",
                "wind_speed": "12 km/h",
                "description": "Comfortable hill station weather - cooler than Colombo with fresh mountain air"
            },
            "galle": {
                "temperature": "30°C",
                "condition": "Coastal Breeze",
                "feels_like": "33°C",
                "humidity": "80%",
                "wind_speed": "15 km/h",
                "description": "Pleasant coastal weather with refreshing sea breeze from the Indian Ocean"
            },
            "ella": {
                "temperature": "22°C",
                "condition": "Cool and Misty",
                "feels_like": "24°C",
                "humidity": "85%",
                "wind_speed": "10 km/h",
                "description": "Cool mountain weather - perfect for hiking and enjoying the scenic views"
            },
            "negombo": {
                "temperature": "31°C",
                "condition": "Tropical Beach Weather",
                "feels_like": "35°C",
                "humidity": "82%",
                "wind_speed": "12 km/h",
                "description": "Ideal beach weather with warm temperatures and gentle coastal winds"
            },
            "anuradhapura": {
                "temperature": "34°C",
                "condition": "Hot and Dry",
                "feels_like": "38°C",
                "humidity": "65%",
                "wind_speed": "6 km/h",
                "description": "Hot dry zone weather - very warm during the day, cooler in the evenings"
            },
            "sigiriya": {
                "temperature": "33°C",
                "condition": "Hot and Sunny",
                "feels_like": "37°C",
                "humidity": "70%",
                "wind_speed": "8 km/h",
                "description": "Hot weather - best to visit early morning or late afternoon to avoid the heat"
            },
            "jaffna": {
                "temperature": "29°C",
                "condition": "Warm and Dry",
                "feels_like": "32°C",
                "humidity": "70%",
                "wind_speed": "10 km/h",
                "description": "Pleasant northern weather - warm but not as humid as the south"
            },
            "trincomalee": {
                "temperature": "30°C",
                "condition": "Coastal and Pleasant",
                "feels_like": "33°C",
                "humidity": "78%",
                "wind_speed": "14 km/h",
                "description": "Beautiful coastal weather with refreshing sea breeze from the Bay of Bengal"
            },
            "nuwara eliya": {
                "temperature": "18°C",
                "condition": "Cool and Misty",
                "feels_like": "20°C",
                "humidity": "90%",
                "wind_speed": "8 km/h",
                "description": "Cool highland weather - often misty and cool, perfect for tea plantation visits"
            }
        }
        
        # Normalize location name
        location_lower = location.lower().strip()
        
        # Try exact match first
        if location_lower in weather_data:
            return weather_data[location_lower]
        
        # Try partial matches
        for city, weather in weather_data.items():
            if city in location_lower or location_lower in city:
                return weather
        
        # Default weather for unknown locations
        return {
            "temperature": "28°C",
            "condition": "Pleasant",
            "feels_like": "30°C",
            "humidity": "75%",
            "wind_speed": "10 km/h",
            "description": f"Pleasant weather in {location.title()} - typical Sri Lankan climate"
        }
    
    def get_trip_suggestions(self, city: str, duration_hours: int) -> List[Dict[str, Any]]:
        """Get trip suggestions based on duration and city"""
        
        # Get city data
        city_data = self.get_tourism_info(city)
        if not city_data.get("success"):
            return []
        
        highlights = city_data["data"].get("highlights", [])
        
        # Calculate number of places based on duration
        if duration_hours < 5:
            num_places = 2
        elif duration_hours <= 12:
            num_places = 5
        elif duration_hours <= 24:
            num_places = 7
        else:
            num_places = min(12, len(highlights))
        
        # Select places for the trip
        selected_places = highlights[:num_places]
        
        suggestions = []
        for i, place in enumerate(selected_places):
            suggestions.append({
                "name": place,
                "rating": "4.5",
                "address": f"{city.title()}, Sri Lanka",
                "type": "Tourist Attraction"
            })
        
        return suggestions
