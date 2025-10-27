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
        """Get comprehensive tourism information from Wikipedia API, fallback to Gemini AI"""
        try:
            # Try Wikipedia API first
            wiki_data = self._get_wikipedia_place_info(query)
            if wiki_data:
                return wiki_data
            
            # Fallback to Gemini service if Wikipedia fails
            logger.info(f"Wikipedia API failed for {query}, falling back to Gemini demo data")
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
                    "source": "gemini_ai_fallback",
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
    
    def _get_wikipedia_place_info(self, place_name: str) -> Optional[Dict]:
        """Get Wikipedia information for a specific place"""
        try:
            # Clean the place name for Wikipedia
            clean_name = place_name.replace(" ", "_").title()
            
            # Try different Wikipedia search strategies
            search_terms = [
                f"{place_name}, Sri Lanka",
                f"{place_name} (Sri Lanka)",
                place_name,
                clean_name
            ]
            
            for term in search_terms:
                url = "https://en.wikipedia.org/api/rest_v1/page/summary"
                params = {'q': term}
                
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if it's about Sri Lanka
                    extract = data.get("extract", "").lower()
                    if "sri lanka" in extract or "lanka" in extract or "ceylon" in extract:
                        return {
                            "title": data.get("title", place_name),
                            "extract": data.get("extract", ""),
                            "description": data.get("description", ""),
                            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                            "thumbnail": data.get("thumbnail", {}).get("source", ""),
                            "coordinates": data.get("coordinates", {}),
                            "type": "place_info",
                            "source": "wikipedia_api"
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Wikipedia place info error for {place_name}: {e}")
            return None
    
    def _get_real_weather(self, location: str) -> Dict:
        """Get real weather data from OpenWeatherMap API"""
        try:
            # Map Sri Lankan cities to coordinates for better accuracy
            city_coords = {
                "colombo": {"lat": 6.9271, "lon": 79.8612},
                "kandy": {"lat": 7.2906, "lon": 80.6337},
                "galle": {"lat": 6.0329, "lon": 80.2170},
                "sigiriya": {"lat": 7.9575, "lon": 80.7603},
                "anuradhapura": {"lat": 8.3114, "lon": 80.4037},
                "negombo": {"lat": 7.2086, "lon": 79.8358},
                "jaffna": {"lat": 9.6615, "lon": 80.0255},
                "ella": {"lat": 6.8667, "lon": 81.0500},
                "nuwara eliya": {"lat": 6.9497, "lon": 80.7891},
                "trincomalee": {"lat": 8.5874, "lon": 81.2152}
            }
            
            # Try to get coordinates for the location
            location_lower = location.lower().strip()
            if location_lower in city_coords:
                coords = city_coords[location_lower]
                url = f"https://api.openweathermap.org/data/2.5/weather"
                params = {
                    'lat': coords['lat'],
                    'lon': coords['lon'],
                    'appid': self.openweather_api_key,
                    'units': 'metric'
                }
            else:
                # Use city name search
                url = f"https://api.openweathermap.org/data/2.5/weather"
                params = {
                    'q': f"{location},LK",  # LK = Sri Lanka country code
                    'appid': self.openweather_api_key,
                    'units': 'metric'
                }
            
            response = self.session.get(url, params=params, timeout=10)
            
            # Check for authentication errors
            if response.status_code == 401:
                logger.warning(f"Invalid OpenWeatherMap API key for {location}")
                return self.gemini_service.get_weather_info(location)
            
            response.raise_for_status()
            data = response.json()
            
            # Extract weather information
            main = data.get('main', {})
            weather = data.get('weather', [{}])[0]
            wind = data.get('wind', {})
            
            return {
                "temperature": f"{main.get('temp', 0):.1f}°C",
                "condition": weather.get('description', 'Unknown').title(),
                "humidity": f"{main.get('humidity', 0)}%",
                "wind_speed": f"{wind.get('speed', 0):.1f} km/h",
                "feels_like": f"{main.get('feels_like', 0):.1f}°C",
                "pressure": f"{main.get('pressure', 0)} hPa",
                "description": f"Real-time weather in {location.title()} - {weather.get('description', '')}",
                "source": "openweather_api",
                "last_updated": "Just now"
            }
            
        except Exception as e:
            logger.error(f"Real weather API error for {location}: {e}")
            # Fallback to demo data if real API fails
            return self.gemini_service.get_weather_info(location)
    
    def get_weather_info(self, location: str) -> Optional[Dict]:
        """Get real-time weather information"""
        try:
            # Check if we have a real API key
            if self.openweather_api_key and self.openweather_api_key != 'demo_key':
                # Make real API call to OpenWeatherMap
                return self._get_real_weather(location)
            else:
                # Use Gemini service for demo weather data
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

    def geocode_location(self, query: str) -> Optional[Dict[str, Any]]:
        """Geocode a place or address using Google Geocoding API.

        Returns a dict with latitude, longitude, formatted_address, and maps_url if successful.
        """
        try:
            if not self.google_places_api_key:
                # Fallback: provide a Google Maps search URL without coordinates
                return {
                    "lat": None,
                    "lng": None,
                    "formatted_address": query.title(),
                    "maps_url": f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(query)}",
                    "source": "fallback_no_api_key"
                }

            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {"address": query, "key": self.google_places_api_key}
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results = (data or {}).get("results", [])
            if not results:
                # Fallback to maps search URL if no results
                return {
                    "lat": None,
                    "lng": None,
                    "formatted_address": query.title(),
                    "maps_url": f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(query)}",
                    "source": "fallback_no_results"
                }

            top = results[0]
            geom = (top.get("geometry") or {}).get("location") or {}
            lat = geom.get("lat")
            lng = geom.get("lng")
            formatted = top.get("formatted_address") or query.title()
            maps_url = f"https://www.google.com/maps/search/?api=1&query={lat}%2C{lng}" if lat is not None and lng is not None else f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(query)}"
            return {
                "lat": lat,
                "lng": lng,
                "formatted_address": formatted,
                "maps_url": maps_url,
                "source": "google_geocoding"
            }
        except Exception as e:
            logger.error(f"Geocoding error for {query}: {e}")
            # Fallback to maps search URL
            return {
                "lat": None,
                "lng": None,
                "formatted_address": query.title(),
                "maps_url": f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(query)}",
                "source": "fallback_error"
            }
    
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
