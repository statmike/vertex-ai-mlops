# utils.py
import os, json
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

def response_parse(response, mode: str):
    # Parse Response and Send Back
    try:
        final_text = 'ERROR: No final response from agent found.'
        for line in response.iter_lines(decode_unicode = True):
            if line:
                if mode == 'local':
                    event = json.loads(line.split(':', 1)[1])
                elif mode == 'remote':
                    event = json.loads(line)
                if type(event) == list:
                    for message in event:
                        final_text = message.get("content", {}).get("parts", [{}])[0].get("text")
                else:
                    final_text = event.get('content').get('parts')[0].get('text')
        return final_text
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def make_request(mode: str, payload: dict, stream: bool = True, suffix: str = ""):

    if mode == 'local':
        URL = 'http://localhost:8000/'
        URL += suffix
        headers = {'Content-Type': 'application/json'}
    elif mode == 'remote':
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

def initialize_adk_session(user_id: str, mode: str):
    try:
        if mode == 'remote':
            payload = dict(
                class_method = 'create_session',
                input = dict(user_id = user_id)
            )
            response = make_request(mode = mode, payload = payload, stream = False, suffix = 'query')
            SESSION_ID = response.get('output').get('id')
            return SESSION_ID
        elif mode == 'local':
            payload = dict()
            response = make_request(mode = mode, payload = payload, stream = False, suffix = f'/apps/document_agent/users/{user_id}/sessions')
            SESSION_ID = response.get("id")
            return SESSION_ID
    except Exception as e:
        print(f"ERROR: Exception during session initialization: {e}")
        return None