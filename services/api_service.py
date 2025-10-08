"""
High-tech API service for Virtual Tour Guide
Integrates multiple APIs for real-time tourism data
"""

import requests
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import sys

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from services.gemini_service import GeminiService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIService:
    """High-tech API service for tourism data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VirtualTourGuide/2.0 (Educational Tourism App; https://github.com/tourism-app)'
        })
        
        # API Keys from config
        self.openweather_api_key = Config.OPENWEATHER_API_KEY
        self.google_places_api_key = Config.GOOGLE_PLACES_API_KEY
        
        # Initialize Gemini service
        self.gemini_service = GeminiService()
        
    def get_wikipedia_info(self, query: str) -> Optional[Dict]:
        """Get comprehensive tourism information using Gemini AI"""
        try:
            # Use Gemini service for comprehensive tourism data
            result = self.gemini_service.get_tourism_info(query)
            
            if result.get("success"):
                data = result["data"]
                return {
                    "title": query.title(),
                    "extract": data.get("description", ""),
                    "description": f"Tourist destination in Sri Lanka",
                    "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                    "thumbnail": "",
                    "coordinates": {},
                    "type": "tourist_attraction",
                    "source": "gemini_ai",
                    "highlights": data.get("highlights", []),
                    "best_time": data.get("best_time", ""),
                    "entry_fees": data.get("entry_fees", ""),
                    "location": data.get("location", ""),
                    "transportation": data.get("transportation", ""),
                    "restaurants": data.get("restaurants", []),
                    "hotels": data.get("hotels", []),
                    "tips": data.get("tips", "")
                }
        except Exception as e:
            logger.error(f"Tourism info error for {query}: {e}")
        
        return None
    
    def get_weather_info(self, location: str) -> Optional[Dict]:
        """Get real-time weather information"""
        try:
            # Use Gemini service for location-specific weather data
            return self.gemini_service.get_weather_info(location)
                
        except Exception as e:
            logger.error(f"Weather API error for {location}: {e}")
            # Return fallback data on error
            return {
                "temperature": "28°C",
                "condition": "Pleasant",
                "humidity": "75%",
                "description": f"Good weather for tourism in {location.title()}",
                "wind_speed": "10 km/h",
                "feels_like": "30°C",
                "source": "fallback_data"
            }
    
    def get_google_places(self, location: str, place_type: str = "tourist_attraction") -> Optional[List[Dict]]:
        """Get places from comprehensive tourism database"""
        try:
            # Use Gemini service for comprehensive place data
            result = self.gemini_service.get_tourism_info(location)
            
            if result.get("success"):
                data = result["data"]
                
                if place_type == "restaurant":
                    restaurants = data.get("restaurants", [])
                    return [{"name": name, "rating": 4.5, "type": "Restaurant", "address": f"{location.title()}, Sri Lanka"} for name in restaurants]
                
                elif place_type == "lodging":
                    hotels = data.get("hotels", [])
                    return [{"name": name, "rating": 4.4, "type": "Hotel", "address": f"{location.title()}, Sri Lanka"} for name in hotels]
                
                elif place_type == "tourist_attraction":
                    highlights = data.get("highlights", [])
                    return [{"name": name, "rating": 4.5, "type": "Attraction", "address": f"{location.title()}, Sri Lanka"} for name in highlights]
            
            return []
            
        except Exception as e:
            logger.error(f"Places API error for {location}: {e}")
            return []
    
    def get_place_images(self, place_name: str) -> List[str]:
        """Get images for a place (mock implementation)"""
        # In a real implementation, this would use Google Images API or similar
        mock_images = {
            "colombo": ["https://example.com/colombo1.jpg", "https://example.com/colombo2.jpg"],
            "kandy": ["https://example.com/kandy1.jpg", "https://example.com/kandy2.jpg"],
            "galle": ["https://example.com/galle1.jpg", "https://example.com/galle2.jpg"],
            "sigiriya": ["https://example.com/sigiriya1.jpg", "https://example.com/sigiriya2.jpg"]
        }
        
        place_key = place_name.lower().replace(" ", "_")
        return mock_images.get(place_key, [])
    
    def calculate_trip_places(self, duration_hours: int) -> int:
        """Calculate number of places based on trip duration"""
        if duration_hours < 5:
            return 2
        elif duration_hours <= 12:
            return 5
        elif duration_hours <= 24:
            return 7
        elif duration_hours <= 48:
            return 10
        else:
            return 12
    
    def get_trip_suggestions(self, city: str, duration_hours: int) -> List[Dict]:
        """Get trip suggestions based on duration"""
        try:
            # Use Gemini service for comprehensive trip suggestions
            return self.gemini_service.get_trip_suggestions(city, duration_hours)
            
        except Exception as e:
            logger.error(f"Error getting trip suggestions for {city}: {e}")
            return []
