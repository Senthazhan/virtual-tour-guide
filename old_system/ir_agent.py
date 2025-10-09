import json, os, difflib, re, requests
from typing import Optional, Dict, List

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "places.json")
with open(DATA_PATH, "r", encoding="utf-8-sig") as f:
    PLACES: Dict[str, dict] = json.load(f)

def list_places() -> List[str]:
    return sorted(list(PLACES.keys()))

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def _best_match(q: str) -> Optional[str]:
    if not q: return None
    qn = _norm(q)
    # exact / substring match on keys and aliases
    for name, data in PLACES.items():
        keys = [name] + data.get("aliases", [])
        for k in keys:
            kn = _norm(k)
            if qn == kn or qn in kn or kn in qn:
                return name
    # fuzzy
    candidates = difflib.get_close_matches(qn, [_norm(k) for k in PLACES.keys()], n=1, cutoff=0.6)
    if candidates:
        # map back to original casing
        lower_to_orig = {_norm(k): k for k in PLACES.keys()}
        return lower_to_orig.get(candidates[0])
    return None

def lookup_place(place: str) -> Optional[dict]:
    name = _best_match(place)
    if not name:
        return None
    e = PLACES[name]
    facts = e.get("facts", [])
    ticket = e.get("ticket", "N/A")
    return {
        "place": name,
        "facts": facts[:6],
        "ticket": ticket,
        "city": e.get("city"),
        "best_time": e.get("best_time"),
        "highlights": e.get("highlights", []),
        "coords": e.get("coords"),
        "opening_hours": e.get("opening_hours"),
        "website": e.get("website"),
        "tags": e.get("tags", []),
        "safety_notes": e.get("safety_notes")
    }

def search(query: str) -> List[dict]:
    """Lightweight search across name, city, highlights."""
    qn = _norm(query)
    results = []
    for name, data in PLACES.items():
        score = 0
        fields = [
            name,
            data.get("city", ""),
            " ".join(data.get("highlights", [])),
            " ".join(data.get("facts", [])),
        ]
        joined = " ".join(fields).lower()
        if qn in joined:
            score += 3
        # token overlap
        tokens = set(qn.split())
        if tokens and any(tok in joined for tok in tokens):
            score += len(tokens)
        if score:
            results.append({
                "name": name,
                "city": data.get("city", ""),
                "best_time": data.get("best_time", ""),
                "score": score
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]

def fetch_wikipedia_data(place_name: str) -> Optional[Dict]:
    """
    Fetch Wikipedia data for a place using Wikipedia API.
    Returns additional information that can enhance the existing data.
    """
    try:
        # Wikipedia API endpoint
        base_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
        
        # Clean the place name for Wikipedia search
        clean_name = place_name.replace(" ", "_")
        
        # Make request to Wikipedia API with proper headers
        headers = {
            'User-Agent': 'VirtualTourGuide/1.0 (Educational Tourism App; https://github.com/your-repo)'
        }
        response = requests.get(f"{base_url}/{clean_name}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant information
            wikipedia_info = {
                "wikipedia_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "extract": data.get("extract", ""),
                "description": data.get("description", ""),
                "thumbnail": data.get("thumbnail", {}).get("source", "") if data.get("thumbnail") else "",
                "coordinates": data.get("coordinates", {}),
                "page_id": data.get("pageid"),
                "title": data.get("title", place_name)
            }
            
            return wikipedia_info
            
    except requests.exceptions.RequestException as e:
        # Log error but don't break the application
        print(f"Wikipedia API error for {place_name}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching Wikipedia data for {place_name}: {e}")
        return None
    
    return None

def get_enhanced_place_info(place: str) -> Optional[dict]:
    """
    Get enhanced place information by combining local data with Wikipedia data.
    This function extends the existing lookup_place function with Wikipedia data.
    """
    # Get the original place data
    original_data = lookup_place(place)
    
    # Try to get Wikipedia data
    wikipedia_data = fetch_wikipedia_data(place)
    
    # If we have Wikipedia data, enhance the original data
    if wikipedia_data:
        # If we have local data, enhance it with Wikipedia
        if original_data:
            original_data.update({
                "wikipedia_url": wikipedia_data.get("wikipedia_url", ""),
                "wikipedia_extract": wikipedia_data.get("extract", ""),
                "wikipedia_description": wikipedia_data.get("description", ""),
                "wikipedia_thumbnail": wikipedia_data.get("thumbnail", ""),
                "wikipedia_coordinates": wikipedia_data.get("coordinates", {}),
                "has_wikipedia_data": True
            })
            
            # If we don't have local facts but have Wikipedia extract, use it
            if not original_data.get("facts") and wikipedia_data.get("extract"):
                # Split the extract into sentences and take first few as facts
                extract = wikipedia_data.get("extract", "")
                sentences = [s.strip() for s in extract.split('.') if s.strip()]
                original_data["facts"] = sentences[:3]  # Take first 3 sentences as facts
        else:
            # No local data, create from Wikipedia data
            original_data = {
                "place": wikipedia_data.get("title", place),
                "facts": [wikipedia_data.get("extract", "")] if wikipedia_data.get("extract") else [],
                "ticket": "Check official website for current prices",
                "city": "Sri Lanka",
                "wikipedia_url": wikipedia_data.get("wikipedia_url", ""),
                "wikipedia_description": wikipedia_data.get("description", ""),
                "wikipedia_thumbnail": wikipedia_data.get("thumbnail", ""),
                "wikipedia_coordinates": wikipedia_data.get("coordinates", {}),
                "has_wikipedia_data": True,
                "source": "wikipedia"
            }
    
    return original_data

def search_wikipedia_places(query: str) -> List[Dict]:
    """
    Search for places using Wikipedia's search API.
    This can help find places that might not be in the local database.
    """
    try:
        # Wikipedia search API
        search_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
        
        # Clean query for Wikipedia
        clean_query = query.replace(" ", "_")
        
        # Try to get the page directly with proper headers
        headers = {
            'User-Agent': 'VirtualTourGuide/1.0 (Educational Tourism App; https://github.com/your-repo)'
        }
        response = requests.get(f"{search_url}/{clean_query}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if this is a disambiguation page or redirect
            if data.get("type") == "disambiguation":
                return []
            
            # Return the found place
            return [{
                "name": data.get("title", query),
                "description": data.get("description", ""),
                "extract": data.get("extract", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "thumbnail": data.get("thumbnail", {}).get("source", "") if data.get("thumbnail") else "",
                "source": "wikipedia"
            }]
            
    except requests.exceptions.RequestException as e:
        print(f"Wikipedia search error for {query}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error searching Wikipedia for {query}: {e}")
        return []
    
    return []

def fetch_additional_sources(place_name: str) -> Optional[Dict]:
    """
    Fetch additional information from other sources.
    This can be extended to include more APIs in the future.
    """
    try:
        # For now, we'll use Wikipedia as the primary external source
        # In the future, you can add:
        # - Google Places API
        # - TripAdvisor API
        # - OpenStreetMap API
        # - Other tourism APIs
        
        wikipedia_data = fetch_wikipedia_data(place_name)
        if wikipedia_data:
            return {
                "source": "wikipedia",
                "data": wikipedia_data
            }
        
        return None
        
    except Exception as e:
        print(f"Error fetching additional sources for {place_name}: {e}")
        return None

def comprehensive_place_search(query: str) -> Optional[Dict]:
    """
    Comprehensive search that tries multiple sources to find place information.
    Priority: Local database -> Wikipedia -> Other sources
    """
    # Clean the query
    clean_query = query.strip()
    
    # Try local database first
    local_data = lookup_place(clean_query)
    if local_data:
        # Enhance with Wikipedia data
        wikipedia_data = fetch_wikipedia_data(clean_query)
        if wikipedia_data:
            local_data.update({
                "wikipedia_url": wikipedia_data.get("wikipedia_url", ""),
                "wikipedia_extract": wikipedia_data.get("extract", ""),
                "wikipedia_description": wikipedia_data.get("description", ""),
                "wikipedia_thumbnail": wikipedia_data.get("thumbnail", ""),
                "wikipedia_coordinates": wikipedia_data.get("coordinates", {}),
                "has_wikipedia_data": True
            })
        return local_data
    
    # If not found locally, try Wikipedia
    wikipedia_data = fetch_wikipedia_data(clean_query)
    if wikipedia_data:
        return {
            "place": wikipedia_data.get("title", clean_query),
            "facts": [wikipedia_data.get("extract", "")] if wikipedia_data.get("extract") else [],
            "ticket": "Check official website for current prices",
            "city": "Sri Lanka",
            "wikipedia_url": wikipedia_data.get("wikipedia_url", ""),
            "wikipedia_description": wikipedia_data.get("description", ""),
            "wikipedia_thumbnail": wikipedia_data.get("thumbnail", ""),
            "wikipedia_coordinates": wikipedia_data.get("coordinates", {}),
            "has_wikipedia_data": True,
            "source": "wikipedia"
        }
    
    # Try alternative search terms
    alternative_terms = [
        f"{clean_query} Sri Lanka",
        f"{clean_query} temple",
        f"{clean_query} fort",
        f"{clean_query} city"
    ]
    
    for term in alternative_terms:
        alt_data = fetch_wikipedia_data(term)
        if alt_data:
            return {
                "place": alt_data.get("title", clean_query),
                "facts": [alt_data.get("extract", "")] if alt_data.get("extract") else [],
                "ticket": "Check official website for current prices",
                "city": "Sri Lanka",
                "wikipedia_url": alt_data.get("wikipedia_url", ""),
                "wikipedia_description": alt_data.get("description", ""),
                "wikipedia_thumbnail": alt_data.get("thumbnail", ""),
                "wikipedia_coordinates": alt_data.get("coordinates", {}),
                "has_wikipedia_data": True,
                "source": "wikipedia",
                "search_term": term
            }
    
    return None

def search_list_queries(query: str) -> Optional[Dict]:
    """
    Handle list queries like 'beaches in Colombo', 'temples in Kandy', etc.
    Uses Wikipedia to find comprehensive lists of places.
    """
    try:
        # Clean the query
        clean_query = query.strip().lower()
        
        # Check if it's a list query
        list_indicators = [
            "list of", "beaches in", "temples in", "forts in", "mountains in",
            "waterfalls in", "parks in", "attractions in", "places in",
            "things to do in", "what to see in", "where to go in"
        ]
        
        is_list_query = any(indicator in clean_query for indicator in list_indicators)
        
        # Also check for specific patterns
        if not is_list_query:
            # Check for "X in Y" pattern
            if " in " in clean_query:
                parts = clean_query.split(" in ")
                if len(parts) == 2:
                    first_part = parts[0].strip()
                    second_part = parts[1].strip()
                    # If first part is a category and second part is a place
                    category_words = ["beaches", "temples", "forts", "mountains", "waterfalls", 
                                    "parks", "attractions", "places", "restaurants", "hotels",
                                    "shops", "markets", "museums", "galleries"]
                    if any(word in first_part for word in category_words):
                        is_list_query = True
        
        if not is_list_query:
            return None
        
        # Try to get Wikipedia data for the list query
        wikipedia_data = fetch_wikipedia_data(query)
        
        if wikipedia_data:
            return {
                "place": query.title(),
                "facts": [wikipedia_data.get("extract", "")] if wikipedia_data.get("extract") else [],
                "ticket": "Varies by location - check individual sites",
                "city": "Sri Lanka",
                "wikipedia_url": wikipedia_data.get("wikipedia_url", ""),
                "wikipedia_description": wikipedia_data.get("description", ""),
                "wikipedia_thumbnail": wikipedia_data.get("thumbnail", ""),
                "wikipedia_coordinates": wikipedia_data.get("coordinates", {}),
                "has_wikipedia_data": True,
                "source": "wikipedia",
                "is_list_query": True
            }
        
        # Try alternative search terms for list queries
        alternative_terms = [
            f"{query} Sri Lanka",
            f"Tourism in {query}",
            f"Attractions in {query}",
            f"Places to visit in {query}",
            f"Things to do in {query}",
            f"Best {query}",
            f"Top {query}",
            f"Popular {query}",
            f"List of {query}",
            f"{query} attractions",
            f"{query} tourism",
            f"{query} places"
        ]
        
        for term in alternative_terms:
            alt_data = fetch_wikipedia_data(term)
            if alt_data:
                return {
                    "place": alt_data.get("title", query.title()),
                    "facts": [alt_data.get("extract", "")] if alt_data.get("extract") else [],
                    "ticket": "Varies by location - check individual sites",
                    "city": "Sri Lanka",
                    "wikipedia_url": alt_data.get("wikipedia_url", ""),
                    "wikipedia_description": alt_data.get("description", ""),
                    "wikipedia_thumbnail": alt_data.get("thumbnail", ""),
                    "wikipedia_coordinates": alt_data.get("coordinates", {}),
                    "has_wikipedia_data": True,
                    "source": "wikipedia",
                    "is_list_query": True,
                    "search_term": term
                }
        
        # If no Wikipedia data found, create a basic response with known information
        return create_fallback_list_response(query)
        
    except Exception as e:
        print(f"Error searching list queries for {query}: {e}")
        return None

def create_fallback_list_response(query: str) -> Optional[Dict]:
    """
    Create a fallback response for list queries when Wikipedia data is not available.
    """
    try:
        clean_query = query.strip().lower()
        
        # Extract the category and location
        if " in " in clean_query:
            parts = clean_query.split(" in ")
            category = parts[0].strip()
            location = parts[1].strip()
        else:
            return None
        
        # Create responses based on known information - providing clear lists
        responses = {
            "beaches in colombo": {
                "facts": [
                    "🏖️ **Mount Lavinia Beach** - Most popular beach with golden sand and calm waters",
                    "🌅 **Dehiwala Beach** - Great for sunset watching with Indian Ocean views", 
                    "👨‍👩‍👧‍👦 **Wellawatta Beach** - Family-friendly with shallow waters and beach restaurants",
                    "🏊‍♂️ **Bambalapitiya Beach** - Popular for swimming and water sports",
                    "🌊 **Kollupitiya Beach** - Urban beach perfect for evening walks"
                ],
                "description": "Beautiful beaches in Colombo with golden sand and calm waters"
            },
            "temples in kandy": {
                "facts": [
                    "🦷 **Temple of the Tooth Relic (Sri Dalada Maligawa)** - UNESCO World Heritage site, most sacred Buddhist temple",
                    "🏛️ **Embekka Devalaya** - Famous for its intricate wood carvings and architecture",
                    "⛩️ **Lankatilaka Vihara** - Ancient temple with impressive architecture",
                    "🕉️ **Gadaladeniya Temple** - Unique architectural style blending Sinhalese and South Indian influences",
                    "🌺 **Kataragama Devalaya** - Hindu temple dedicated to Lord Kataragama"
                ],
                "description": "Sacred Buddhist temples including the famous Temple of the Tooth Relic"
            },
            "attractions in galle": {
                "facts": [
                    "🏰 **Galle Fort** - UNESCO World Heritage site with Dutch colonial architecture",
                    "🗼 **Galle Lighthouse** - Historic lighthouse with panoramic Indian Ocean views",
                    "⛪ **Dutch Reformed Church** - Beautiful colonial-era church",
                    "⛪ **All Saints' Church** - Anglican church showcasing colonial architecture",
                    "🏛️ **National Maritime Museum** - Located in the fort, showcases maritime history"
                ],
                "description": "Historic Galle Fort and colonial architecture attractions"
            },
            "places to visit in anuradhapura": {
                "facts": [
                    "🌳 **Sacred Bodhi Tree** - Ancient tree with great religious significance",
                    "🏛️ **Ruwanwelisaya Stupa** - Massive white stupa, symbol of the city",
                    "🗿 **Jetavanaramaya Stupa** - One of the largest stupas in the world",
                    "🏛️ **Abhayagiri Monastery** - Ancient monastery ruins",
                    "🪨 **Isurumuniya Rock Temple** - Rock temple with famous carvings"
                ],
                "description": "Ancient capital with archaeological sites and Buddhist temples"
            },
            "beaches in sri lanka": {
                "facts": [
                    "🏖️ **Unawatuna Beach** - Popular crescent-shaped beach with calm waters",
                    "🏄‍♂️ **Arugam Bay** - World-famous surfing destination on the east coast",
                    "🌊 **Mirissa Beach** - Perfect for whale watching and beach relaxation",
                    "🏖️ **Bentota Beach** - Resort area with water sports and luxury hotels",
                    "🌅 **Hikkaduwa Beach** - Great for snorkeling and coral reef exploration"
                ],
                "description": "Beautiful beaches across Sri Lanka"
            },
            "temples in sri lanka": {
                "facts": [
                    "🦷 **Temple of the Tooth (Kandy)** - Most sacred Buddhist temple",
                    "🗿 **Dambulla Cave Temple** - UNESCO site with ancient cave paintings",
                    "🌳 **Mihintale** - Birthplace of Buddhism in Sri Lanka",
                    "🏛️ **Polonnaruwa Ancient City** - UNESCO World Heritage archaeological site",
                    "⛩️ **Kelaniya Raja Maha Viharaya** - Ancient temple near Colombo"
                ],
                "description": "Sacred temples and religious sites across Sri Lanka"
            }
        }
        
        # Check for exact match first
        if clean_query in responses:
            response_data = responses[clean_query]
            return {
                "place": query.title(),
                "facts": response_data["facts"],
                "ticket": "Varies by location - check individual sites",
                "city": "Sri Lanka",
                "wikipedia_url": "",
                "wikipedia_description": response_data["description"],
                "wikipedia_thumbnail": "",
                "wikipedia_coordinates": {},
                "has_wikipedia_data": False,
                "source": "local_knowledge",
                "is_list_query": True
            }
        
        # Try partial matches with better logic
        for key, response_data in responses.items():
            key_parts = key.split(" in ")
            if len(key_parts) == 2:
                key_category = key_parts[0].strip()
                key_location = key_parts[1].strip()
                
                # Check if both category and location match
                if (category == key_category or key_category in category) and (location == key_location or key_location in location):
                    return {
                        "place": query.title(),
                        "facts": response_data["facts"],
                        "ticket": "Varies by location - check individual sites",
                        "city": "Sri Lanka",
                        "wikipedia_url": "",
                        "wikipedia_description": response_data["description"],
                        "wikipedia_thumbnail": "",
                        "wikipedia_coordinates": {},
                        "has_wikipedia_data": False,
                        "source": "local_knowledge",
                        "is_list_query": True
                    }
        
        return None
        
    except Exception as e:
        print(f"Error creating fallback response for {query}: {e}")
        return None

def plan_multi_day_trip(city: str, days: int) -> Optional[Dict]:
    """
    Plan a multi-day trip to a specific city with detailed itinerary.
    """
    try:
        # Enhanced place data for comprehensive trip planning
        enhanced_places = {
            "kandy": {
                "places": [
                    {"name": "Temple of the Sacred Tooth Relic", "duration": "2-3 hours", "type": "Cultural", "priority": "Must Visit"},
                    {"name": "Kandy Lake", "duration": "1-2 hours", "type": "Scenic", "priority": "High"},
                    {"name": "Royal Botanical Gardens", "duration": "3-4 hours", "type": "Nature", "priority": "High"},
                    {"name": "Kandy Cultural Show", "duration": "1 hour", "type": "Cultural", "priority": "Medium"},
                    {"name": "Bahirawakanda Buddha Statue", "duration": "1 hour", "type": "Religious", "priority": "Medium"},
                    {"name": "Udawattakele Forest Reserve", "duration": "2-3 hours", "type": "Nature", "priority": "Medium"},
                    {"name": "Kandy Market", "duration": "1-2 hours", "type": "Shopping", "priority": "Low"},
                    {"name": "Commonwealth War Cemetery", "duration": "30 minutes", "type": "Historical", "priority": "Low"}
                ],
                "description": f"Kandy, the cultural capital of Sri Lanka, offers a perfect blend of history, culture, and natural beauty for a {days}-day trip."
            },
            "colombo": {
                "places": [
                    {"name": "Gangaramaya Temple", "duration": "1-2 hours", "type": "Cultural", "priority": "Must Visit"},
                    {"name": "Independence Memorial Hall", "duration": "1 hour", "type": "Historical", "priority": "High"},
                    {"name": "Colombo National Museum", "duration": "2-3 hours", "type": "Museum", "priority": "High"},
                    {"name": "Mount Lavinia Beach", "duration": "2-3 hours", "type": "Beach", "priority": "High"},
                    {"name": "Galle Face Green", "duration": "1-2 hours", "type": "Recreation", "priority": "Medium"},
                    {"name": "Red Mosque (Jami Ul-Alfar)", "duration": "30 minutes", "type": "Architecture", "priority": "Medium"},
                    {"name": "Colombo Fort", "duration": "2-3 hours", "type": "Historical", "priority": "Medium"},
                    {"name": "Pettah Market", "duration": "1-2 hours", "type": "Shopping", "priority": "Low"}
                ],
                "description": f"Colombo, Sri Lanka's commercial capital, offers diverse attractions from temples to beaches for a {days}-day exploration."
            },
            "galle": {
                "places": [
                    {"name": "Galle Fort", "duration": "3-4 hours", "type": "Historical", "priority": "Must Visit"},
                    {"name": "Galle Lighthouse", "duration": "30 minutes", "type": "Landmark", "priority": "High"},
                    {"name": "Dutch Reformed Church", "duration": "30 minutes", "type": "Historical", "priority": "High"},
                    {"name": "Galle Maritime Museum", "duration": "1-2 hours", "type": "Museum", "priority": "Medium"},
                    {"name": "Unawatuna Beach", "duration": "2-3 hours", "type": "Beach", "priority": "High"},
                    {"name": "Japanese Peace Pagoda", "duration": "1 hour", "type": "Religious", "priority": "Medium"},
                    {"name": "Rumassala Sanctuary", "duration": "2-3 hours", "type": "Nature", "priority": "Medium"},
                    {"name": "Stilt Fishing", "duration": "1-2 hours", "type": "Cultural", "priority": "Medium"}
                ],
                "description": f"Galle, with its UNESCO World Heritage Fort and beautiful beaches, is perfect for a {days}-day coastal getaway."
            },
            "anuradhapura": {
                "places": [
                    {"name": "Sacred Bodhi Tree", "duration": "1 hour", "type": "Religious", "priority": "Must Visit"},
                    {"name": "Ruwanwelisaya Stupa", "duration": "1-2 hours", "type": "Religious", "priority": "Must Visit"},
                    {"name": "Jetavanaramaya", "duration": "1 hour", "type": "Religious", "priority": "High"},
                    {"name": "Abhayagiri Monastery", "duration": "2-3 hours", "type": "Historical", "priority": "High"},
                    {"name": "Anuradhapura Archaeological Museum", "duration": "1-2 hours", "type": "Museum", "priority": "Medium"},
                    {"name": "Isurumuniya Rock Temple", "duration": "1 hour", "type": "Religious", "priority": "Medium"},
                    {"name": "Mihintale", "duration": "3-4 hours", "type": "Religious", "priority": "High"},
                    {"name": "Kuttam Pokuna (Twin Ponds)", "duration": "30 minutes", "type": "Historical", "priority": "Low"}
                ],
                "description": f"Anuradhapura, the ancient capital, offers incredible archaeological sites and spiritual significance for a {days}-day journey through history."
            },
            "sigiriya": {
                "places": [
                    {"name": "Sigiriya Rock Fortress", "duration": "4-5 hours", "type": "Historical", "priority": "Must Visit"},
                    {"name": "Sigiriya Museum", "duration": "1 hour", "type": "Museum", "priority": "High"},
                    {"name": "Pidurangala Rock", "duration": "2-3 hours", "type": "Hiking", "priority": "High"},
                    {"name": "Minneriya National Park", "duration": "4-6 hours", "type": "Wildlife", "priority": "High"},
                    {"name": "Dambulla Cave Temple", "duration": "2-3 hours", "type": "Religious", "priority": "High"},
                    {"name": "Kaudulla National Park", "duration": "4-6 hours", "type": "Wildlife", "priority": "Medium"},
                    {"name": "Hurulu Eco Park", "duration": "3-4 hours", "type": "Nature", "priority": "Medium"},
                    {"name": "Polonnaruwa Ancient City", "duration": "4-5 hours", "type": "Historical", "priority": "High"}
                ],
                "description": f"Sigiriya region offers the iconic rock fortress, ancient cities, and wildlife safaris for an unforgettable {days}-day adventure."
            }
        }
        
        city_lower = city.lower()
        if city_lower in enhanced_places:
            city_data = enhanced_places[city_lower]
            places = city_data["places"]
            
            # Calculate optimal itinerary based on days
            if days == 1:
                # Must-visit and high priority only
                selected_places = [p for p in places if p["priority"] in ["Must Visit", "High"]][:4]
            elif days == 2:
                # Must-visit, high, and some medium priority
                selected_places = [p for p in places if p["priority"] in ["Must Visit", "High", "Medium"]][:6]
            elif days == 3:
                # Include more places but still prioritize
                selected_places = places[:8]
            else:
                # 4+ days - include all places
                selected_places = places
            
            # Format the itinerary
            itinerary = []
            for i, place in enumerate(selected_places, 1):
                itinerary.append(f"**Day {min((i-1)//2 + 1, days)}:** {place['name']} ({place['duration']}) - {place['type']} | Priority: {place['priority']}")
            
            # Add practical information
            practical_info = [
                f"**Best Time to Visit:** Early morning (6-9 AM) to avoid crowds and heat",
                f"**Transportation:** Tuk-tuk, car rental, or guided tours recommended",
                f"**Accommodation:** Stay in {city.title()} city center for easy access to all attractions",
                f"**Tips:** Book tickets in advance for popular sites, carry water and sun protection"
            ]
            
            return {
                "place": f"{days}-Day Trip to {city.title()}",
                "facts": [city_data["description"]] + itinerary + practical_info,
                "ticket": "Varies by attraction - check individual sites",
                "city": city.title(),
                "wikipedia_url": "",
                "wikipedia_description": f"Comprehensive {days}-day itinerary for {city.title()}",
                "wikipedia_thumbnail": "",
                "wikipedia_coordinates": {},
                "has_wikipedia_data": False,
                "source": "enhanced_trip_planner",
                "is_list_query": True
            }
        
        return None
        
    except Exception as e:
        print(f"Error planning multi-day trip for {city}: {e}")
        return None

def fetch_weather_data(location: str) -> Optional[Dict]:
    """
    Fetch weather data for a location using OpenWeatherMap API.
    """
    try:
        # Using a free weather API (OpenWeatherMap)
        # You'll need to get a free API key from openweathermap.org
        api_key = "your_api_key_here"  # Replace with actual API key
        
        if api_key == "your_api_key_here":
            # Return mock weather data for demonstration
            return {
                "temperature": "28°C",
                "condition": "Partly Cloudy",
                "humidity": "75%",
                "description": "Perfect weather for sightseeing",
                "source": "mock_data"
            }
        
        # Real API call (when you have an API key)
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": f"{location}, Sri Lanka",
            "appid": api_key,
            "units": "metric"
        }
        
        headers = {
            'User-Agent': 'VirtualTourGuide/1.0 (Educational Tourism App; https://github.com/your-repo)'
        }
        
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            weather_info = {
                "temperature": f"{data['main']['temp']}°C",
                "condition": data['weather'][0]['main'],
                "humidity": f"{data['main']['humidity']}%",
                "description": data['weather'][0]['description'],
                "source": "openweathermap"
            }
            
            return weather_info
            
    except requests.exceptions.RequestException as e:
        print(f"Weather API error for {location}: {e}")
        # Return mock data on error
        return {
            "temperature": "28°C",
            "condition": "Partly Cloudy",
            "humidity": "75%",
            "description": "Good weather for tourism",
            "source": "fallback_data"
        }
    except Exception as e:
        print(f"Unexpected error fetching weather for {location}: {e}")
        return None
    
    return None

def get_comprehensive_information(query: str) -> Optional[Dict]:
    """
    Get comprehensive information for any query - specific places, general topics, or lists.
    This is the main function that handles all types of queries.
    """
    # Clean the query
    clean_query = query.strip()
    
    # Handle simple responses first (yes, no, ok, etc.)
    simple_responses = ["yes", "no", "ok", "okay", "sure", "maybe", "thanks", "thank you"]
    if clean_query.lower().strip() in simple_responses:
        return {
            "place": "Simple Response",
            "facts": ["Got it!"],
            "ticket": "N/A",
            "city": "Sri Lanka",
            "wikipedia_url": "",
            "wikipedia_description": "Simple acknowledgment",
            "wikipedia_thumbnail": "",
            "wikipedia_coordinates": {},
            "has_wikipedia_data": False,
            "source": "simple_response"
        }
    
    # Check for multi-day trip planning first
    import re
    trip_pattern = r'plan\s+a\s+(\d+)\s+day\s+trip\s+to\s+(\w+)'
    match = re.search(trip_pattern, clean_query.lower())
    if match:
        days = int(match.group(1))
        city = match.group(2)
        trip_result = plan_multi_day_trip(city, days)
        if trip_result:
            return trip_result
    
    # Try local database first (no Wikipedia)
    local_result = lookup_place(clean_query)
    if local_result:
        # Only add weather data if specifically requested
        if "weather" in clean_query.lower():
            weather_data = fetch_weather_data(clean_query)
            if weather_data:
                local_result["weather"] = weather_data
        return local_result
    
    # Check if it's a list query and handle it accordingly (local only)
    list_result = search_list_queries(clean_query)
    if list_result and list_result.get("source") == "local_knowledge":
        # Only add weather data if specifically requested
        if "weather" in clean_query.lower():
            if " in " in clean_query.lower():
                location = clean_query.split(" in ")[-1].strip()
                weather_data = fetch_weather_data(location)
                if weather_data:
                    list_result["weather"] = weather_data
        return list_result
    
    # Only use Wikipedia for specific requests or when local data fails completely
    should_use_wikipedia = (
        "wikipedia" in clean_query.lower() or 
        "more information" in clean_query.lower() or
        "detailed" in clean_query.lower() or
        "comprehensive" in clean_query.lower()
    )
    
    if should_use_wikipedia:
        # Try comprehensive place search (includes Wikipedia)
        place_result = comprehensive_place_search(clean_query)
        if place_result:
            # Only add weather data if specifically requested
            if "weather" in clean_query.lower():
                weather_data = fetch_weather_data(clean_query)
                if weather_data:
                    place_result["weather"] = weather_data
            return place_result
        
        # Try list query with Wikipedia
        wikipedia_list = search_list_queries(clean_query)
        if wikipedia_list:
            # Only add weather data if specifically requested
            if "weather" in clean_query.lower():
                if " in " in clean_query.lower():
                    location = clean_query.split(" in ")[-1].strip()
                    weather_data = fetch_weather_data(location)
                    if weather_data:
                        wikipedia_list["weather"] = weather_data
            return wikipedia_list
    
    # Special handling for weather queries that don't match any place
    if "weather" in clean_query.lower() or "weathe" in clean_query.lower():
        # Extract location from weather query
        location = None
        
        # Handle various weather query patterns
        if " in " in clean_query.lower():
            location = clean_query.split(" in ")[-1].strip()
        elif " at " in clean_query.lower():
            location = clean_query.split(" at ")[-1].strip()
        else:
            # Try to extract location from the query
            words = clean_query.split()
            for i, word in enumerate(words):
                if (word == "weather" or word == "weathe") and i < len(words) - 1:
                    location = " ".join(words[i+1:]).strip()
                    break
        
        # Clean up the location (remove common suffixes)
        if location:
            location = location.replace(" today", "").replace("?", "").replace("!", "").strip()
        
        if location:
            weather_data = fetch_weather_data(location)
            if weather_data:
                return {
                    "place": f"Weather in {location.title()}",
                    "facts": [f"Weather information for {location.title()}"],
                    "ticket": "N/A",
                    "city": location.title(),
                    "wikipedia_url": "",
                    "wikipedia_description": f"Current weather conditions for {location.title()}",
                    "wikipedia_thumbnail": "",
                    "wikipedia_coordinates": {},
                    "has_wikipedia_data": False,
                    "source": "weather_api",
                    "weather": weather_data
                }
    
    return None
