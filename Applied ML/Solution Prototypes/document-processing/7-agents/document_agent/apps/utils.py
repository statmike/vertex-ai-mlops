# utils.py
import os
import requests
import dotenv
from google import auth as google_auth
from google.auth.transport import requests as google_requests

# Load environment variables from .env file
dotenv.load_dotenv(dotenv_path='.env')

# --- AUTHENTICATION SETUP ---
# These objects are created once when the module is imported, making it efficient.
credentials, _ = google_auth.default()
auth_req = google_requests.Request()

def make_request(suffix: str, payload: dict, stream = False):
    URL = f"https://{os.getenv('GOOGLE_CLOUD_LOCATION')}-aiplatform.googleapis.com/v1/{os.getenv('ADK_DEPLOY_RESOURCE_ID')}:"
    URL += suffix
    credentials.refresh(auth_req)
    headers = {'Authorization': f'Bearer {credentials.token}'}
    response = requests.post(URL, headers = headers, json = payload, stream = stream)    
    response.raise_for_status()
    if stream:
        return response
    else:
        return response.json()

def initialize_adk_session(user_id: str):
    try:
        payload = dict(
            class_method = 'create_session',
            input = dict(user_id = user_id)
        )
        response = make_request(suffix = 'query', payload = payload)
        SESSION_ID = response.get('output').get('id')
        return SESSION_ID
    except Exception as e:
        print(f"ERROR: Exception during session initialization: {e}")
        return None