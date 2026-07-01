import os
import json
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

CACHE_FILE = "search_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_cache(cache_dict):
    with open(CACHE_FILE, 'w') as file:
        json.dump(cache_dict, file, indent=4)

def standardize_search_query(raw_query: str) -> str:
    """
    Uses Gemini AI as an AI Pre-Processor to clean up misspelled user search queries.
    """
    cache_key = raw_query.lower().strip()
    cache = load_cache()
    
    if cache_key in cache:
        print("Cache Hit! Skipping Gemini API...")
        return cache[cache_key]
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables.")
        return raw_query # Fallback to raw query if no key
        
    # Using the fast gemini-2.5-flash model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = (
        "You are a search query optimizer for an e-commerce bot. "
        "The user will provide a messy, misspelled gadget name. "
        "Your ONLY job is to return the perfectly spelled, standard brand and model name. "
        "Fix typos (e.g., 'reddmi' -> 'Redmi', 'ihpone' -> 'iPhone') and standard specs (e.g., '256gig' -> '256GB'). "
        "DO NOT include any conversational text, markdown formatting, or explanations. "
        "Return ONLY the corrected string. If it is already correct, return it as is.\n\n"
        f"Query: {raw_query}"
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.0, # Zero temperature for deterministic, strictly formatted responses
        }
    }
    
    try:
        # Use verify=False to bypass local Windows SSL/Antivirus interception issues we faced earlier
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, verify=False)
        response.raise_for_status()
        
        data = response.json()
        clean_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Sometimes AI might add quotes or extra spaces, strip them
        clean_text = clean_text.strip('\'" \n')
        
        cache[cache_key] = clean_text
        save_cache(cache)
        
        return clean_text
    except Exception as e:
        logger.error(f"Gemini AI extraction failed: {e}")
        # If AI fails, fallback to raw query seamlessly
        return raw_query
