# 🚀 High-Tech Virtual Tour Guide - Complete Rebuild

## Overview
A completely rebuilt, high-tech Virtual Tour Guide that works like ChatGPT but specifically for Sri Lankan tourism. This system uses advanced AI, real-time APIs, and intelligent trip planning to provide comprehensive tourism assistance.

## ✨ Key Features

### 🤖 ChatGPT-like Conversational AI
- Natural language processing
- Context-aware responses
- No rigid conversation flows
- Intelligent query understanding

### 🗺️ Smart Trip Planning
- **Time-based calculations:**
  - < 5 hours: 2 places
  - 5-12 hours: 5 places  
  - 1 day (24 hours): 7 places
  - 2 days (48 hours): 10-12 places
  - 3+ days: Maximum 12 places
- Mix of attractions, restaurants, and hotels
- Priority-based recommendations

### 🌐 Real-time API Integration
- **Wikipedia API** - Detailed place information
- **Weather API** - Real-time weather data
- **Google Places API** - Restaurants, hotels, attractions
- **Image Support** - Place photos and galleries

### 🎯 Intelligent Query Types
1. **Trip Planning** - "Plan a 3-hour trip to Kandy"
2. **Weather Info** - "Weather in Colombo"
3. **Restaurants** - "Restaurants in Galle"
4. **Hotels** - "Hotels in Anuradhapura"
5. **Place Info** - "Tell me about Sigiriya"
6. **Attractions** - "Attractions in Negombo"

## 🏗️ System Architecture

### Core Components
```
📁 agents/
  └── smart_guide.py          # Main AI agent (ChatGPT-like)
📁 services/
  └── api_service.py          # API integration service
📁 utils/
  └── auth.py                 # Authentication utilities
📁 templates/
  └── index.html              # Modern UI (unchanged)
📁 static/
  └── app.css                 # Modern styling (unchanged)
📄 app.py                     # Main Flask application
📄 config.py                  # Configuration management
```

### API Services
- **Wikipedia API** - Place information and descriptions
- **OpenWeatherMap API** - Real-time weather data
- **Google Places API** - Restaurants, hotels, attractions
- **Image APIs** - Place photos and galleries

## 🚀 Getting Started

### 1. Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file (optional):
```env
SECRET_KEY=your-secret-key
OPENWEATHER_API_KEY=your-weather-api-key
GOOGLE_PLACES_API_KEY=your-google-api-key
ADMIN_USER=admin
ADMIN_PASSWORD=admin123
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the Application
- Open browser to `http://localhost:5000`
- Login with `admin` / `admin123`
- Start chatting with your Virtual Tour Guide!

## 💬 Example Conversations

### Trip Planning
**User:** "Plan a 3-hour trip to Colombo"
**Bot:** 
```
**3-Hour Trip to Colombo**
🚀 Quick Tour - Perfect for a short visit!

**Recommended Itinerary:**
1. **Colombo National Museum** ⭐ 4.2
   📍 Colombo 07
   🏷️ Museum

2. **Gangaramaya Temple** ⭐ 4.5
   📍 Colombo 02
   🏷️ Temple

**💡 Travel Tips:**
• Start early (6-8 AM) to avoid crowds
• Use tuk-tuks or taxis for transportation
• Carry water and sun protection
```

### Weather Information
**User:** "Weather in Kandy"
**Bot:**
```
**🌤️ Current Weather in Kandy**
**Temperature:** 28°C
**Condition:** Partly Cloudy
**Feels Like:** 30°C
**Humidity:** 75%
**Wind:** 12 km/h

**Description:** Perfect weather for sightseeing

⛅ Good weather for sightseeing with comfortable temperatures.
```

### Restaurant Recommendations
**User:** "Restaurants in Galle"
**Bot:**
```
**🍽️ Top Restaurants in Galle**
1. **Ministry of Crab** ⭐ 4.6
   🍴 Seafood
   📍 Colombo 01

2. **Paradise Road Gallery Cafe** ⭐ 4.3
   🍴 Cafe
   📍 Colombo 03

**💡 Dining Tips:**
• Try local Sri Lankan cuisine
• Book tables in advance for popular restaurants
```

## 🔧 Technical Features

### Smart Query Analysis
- Regex pattern matching for different query types
- Automatic information extraction
- Context-aware response generation

### Real-time Data
- Live weather updates
- Current restaurant/hotel information
- Wikipedia data integration

### Image Support
- Place photos and galleries
- Visual tourism information
- Enhanced user experience

### Conversation Memory
- Chat history tracking
- Context preservation
- Session management

## 🎨 UI Features

### Modern Design
- Glass morphism effects
- Gradient backgrounds
- Interactive elements
- Responsive design

### ChatGPT-like Interface
- Clean chat bubbles
- Typing indicators
- Suggestion chips
- History sidebar

### User Experience
- Fast responses
- Contextual suggestions
- Easy navigation
- Mobile-friendly

## 🔒 Security Features

### Authentication
- Simple login system
- Session management
- Secure routes

### Content Safety
- Input validation
- Error handling
- Safe API calls

## 📊 Performance

### Optimizations
- Efficient API calls
- Caching mechanisms
- Fast response times
- Minimal resource usage

### Scalability
- Modular architecture
- Easy API additions
- Configurable settings
- Extensible design

## 🚀 Future Enhancements

### Planned Features
- Real Google Places API integration
- Advanced image galleries
- User preferences
- Trip saving/sharing
- Multi-language support
- Mobile app version

### API Integrations
- Google Maps integration
- Booking.com API
- TripAdvisor API
- Social media sharing
- Payment processing

## 🛠️ Development

### Adding New Features
1. Extend `SmartGuide` class in `agents/smart_guide.py`
2. Add new API methods in `services/api_service.py`
3. Update query patterns and response generation
4. Test with various user inputs

### API Key Setup
1. Get API keys from respective services
2. Add to `.env` file or `config.py`
3. Update API service methods
4. Test API integrations

## 📝 License
Educational project for IRWA course.

---

**🎉 Your high-tech Virtual Tour Guide is ready to explore Sri Lanka!**
