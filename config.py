"""
Configuration for Virtual Tour Guide
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # API Keys
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '66982acfea538d30203e2f317d820f90')
    GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', 'demo_key')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'demo_key')
    
    # Authentication
    ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Application Settings
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
