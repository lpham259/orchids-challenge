# test_hyperbrowser.py
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from hyperbrowser import Hyperbrowser
    api_key = os.getenv("HYPERBROWSER_API_KEY")
    print(f"API Key: {api_key[:8] if api_key else 'None'}...")
    
    client = Hyperbrowser(api_key=api_key)
    print("Client created:", type(client))
    
    session = client.sessions.create()
    print("Session created:", session.id if session else "Failed")
    
except Exception as e:
    print(f"Error: {e}")