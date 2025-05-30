import gradio as gr
import requests
import json
import uuid
import base64
import mimetypes

# --- Configuration for your ADK Web server ---
from config import ADK_SESSION_CREATE_URL, ADK_RUN_SSE_URL

# Global variable to store the session ID obtained from the server.
# In a production multi-user app, this would require more robust state management.
SERVER_SESSION_ID = None

def initialize_adk_session():
    """
    Calls the ADK endpoint to create an official session and get a session ID.
    This is a mandatory first step before sending messages.
    Returns the session ID if successful, None otherwise.
    """
    global SERVER_SESSION_ID
    if SERVER_SESSION_ID:  # Don't re-initialize if we already have a session
        return SERVER_SESSION_ID

    try:
        # This endpoint might not require a payload, or might need an empty one.
        session_payload = {}
        
        response = requests.post(ADK_SESSION_CREATE_URL, json=session_payload, timeout=30)
        response.raise_for_status()  # Will raise an exception for HTTP errors
        response_data = response.json()
        
        # The key for the session ID was found to be "id" from inspecting the response.
        created_session_id = response_data.get("id")
        
        if created_session_id:
            SERVER_SESSION_ID = str(created_session_id)
            return SERVER_SESSION_ID
        else:
            print(f"ERROR in Gradio app: Session ID key 'id' not found in session creation response: {json.dumps(response_data)}")
            return None
            
    except Exception as e:
        print(f"ERROR in Gradio app: Exception during session initialization: {e}")
        return None

# Replace the existing call_adk_agent function with this instrumented version

def call_adk_agent(message: dict, history: list):
    """
    Handles input from the multimodal gr.ChatInterface and communicates with the ADK agent.
    Includes debugging print statements to trace file handling.
    """
    global SERVER_SESSION_ID
    
    if not SERVER_SESSION_ID:
        initialize_adk_session()
        if not SERVER_SESSION_ID:
            return "Error: Could not initialize session with ADK agent. Please check Gradio app console for details."

    print("\n--- New Request ---")
    print(f"DEBUG: Received raw message object from Gradio: {message}")

    # Extract text and file paths from the message dictionary
    text_input = message["text"]
    file_paths = message["files"]

    message_parts = []

    # Add text part if text_input is provided
    if text_input:
        message_parts.append({"text": text_input})

    # Add file part if a file was uploaded
    if file_paths:
        print(f"DEBUG: Found {len(file_paths)} file(s) in Gradio input.")
        try:
            # Process the first uploaded file from the list
            file_path = file_paths[0]
            print(f"DEBUG: Processing file path: {file_path}")
            
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            print(f"DEBUG: Read {len(file_bytes)} bytes from file.")
            
            base64_encoded_data = base64.b64encode(file_bytes).decode('utf-8')
            
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"
            print(f"DEBUG: Guessed MIME type: {mime_type}")
            
            file_part = {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64_encoded_data
                }
            }
            message_parts.append(file_part)
            print("DEBUG: Successfully created file part for payload.")

        except Exception as e:
            print(f"DEBUG ERROR: An exception occurred while processing the uploaded file: {str(e)}")
            return f"Error processing uploaded file: {str(e)}"
    else:
        print("DEBUG: No files found in Gradio input.")

    if not message_parts:
        return "Please provide a message or upload a file."

    payload = {
        "appName": "document_agent",
        "userId": "user", 
        "sessionId": SERVER_SESSION_ID, 
        "newMessage": {
            "role": "user",
            "parts": message_parts
        },
        "streaming": False 
    }
    
    # Create a version of the payload for logging that doesn't print the huge base64 string
    payload_for_logging = json.loads(json.dumps(payload)) # Deep copy
    for part in payload_for_logging["newMessage"]["parts"]:
        if "inline_data" in part:
            part["inline_data"]["data"] = f"<base64_data_omitted; length={len(payload['newMessage']['parts'][-1]['inline_data']['data'])}>"
    print(f"DEBUG: Sending final payload to ADK: {json.dumps(payload_for_logging, indent=2)}")


    try:
        # The rest of this function (requests call and response parsing) remains the same
        response = requests.post(ADK_RUN_SSE_URL, json=payload, timeout=180, stream=True)
        response.raise_for_status()
        
        agent_reply_parts = []
        # ... (rest of your successful response handling logic) ...
        # This simplified block is just for structure, use your full working version
        if 'text/event-stream' in response.headers.get('Content-Type', '').lower():
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data:'):
                    data_content = line[len('data:'):].strip()
                    if not data_content: continue
                    try:
                        event_json = json.loads(data_content)
                        if "content" in event_json and isinstance(event_json["content"].get("parts"), list) and len(event_json["content"]["parts"]) > 0 and "text" in event_json["content"]["parts"][0]:
                            agent_reply_parts.append(event_json["content"]["parts"][0]["text"])
                    except:
                        if data_content: agent_reply_parts.append(data_content)
        else: 
            # Simplified fallback, use your full working version
            agent_reply_parts.append(f"Received non-SSE response: {response.text[:500]}")
        
        final_reply = "\n".join(filter(None, agent_reply_parts))
        return final_reply if final_reply else "Agent responded, but no displayable text was found."

    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# --- 4. Create and launch the Gradio UI ---
chat_interface = gr.ChatInterface(
    fn=call_adk_agent,
    title="Document Processing Agent",
    description="Interact with your ADK-powered document agent. You can type a message and/or use the paperclip icon to upload a PDF or PNG file.",
    multimodal=True,
    examples=[
        ["What can you do?"],
        ["Please classify the document at gs://statmike-mlops-349915/applied-ml-solution-prototypes/document-processing/documents/mortgage_statement_20231101_1_page.pdf"],
    ]
)

if __name__ == "__main__":
    if initialize_adk_session():
        print(f"Successfully initialized ADK session on startup: {SERVER_SESSION_ID}")
    else:
        print("Warning: Failed to initialize ADK session on startup. Gradio will attempt to initialize on the first message.")
    
    chat_interface.launch()