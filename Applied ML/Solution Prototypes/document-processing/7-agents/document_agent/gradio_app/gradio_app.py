import gradio as gr
import requests
import json
import uuid

# Configuration for your ADK Web server
ADK_SESSION_CREATE_URL = "http://localhost:8000/apps/document_agent/users/user/sessions"
ADK_RUN_SSE_URL = "http://localhost:8000/run_sse"

SERVER_SESSION_ID = None

def initialize_adk_session():
    global SERVER_SESSION_ID
    if SERVER_SESSION_ID:
        return SERVER_SESSION_ID
    try:
        session_payload = {}
        response = requests.post(ADK_SESSION_CREATE_URL, json=session_payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        created_session_id = response_data.get("id")
        if created_session_id:
            SERVER_SESSION_ID = str(created_session_id)
            return SERVER_SESSION_ID
        else:
            print(f"ERROR in Gradio app: Session ID key 'id' not found in session creation response. Full response: {json.dumps(response_data)}")
            return None
    except Exception as e: # Simplified exception handling for brevity in this example
        print(f"ERROR in Gradio app: Exception during session initialization: {e}")
        return None

def call_adk_agent(message: str, history: list):
    global SERVER_SESSION_ID
    
    if not SERVER_SESSION_ID:
        initialize_adk_session()
        if not SERVER_SESSION_ID:
            return "Error: Could not initialize session with ADK agent. Please check Gradio app console/server logs for details on session creation failure."

    payload = {
        "appName": "document_agent",
        "userId": "user", 
        "sessionId": SERVER_SESSION_ID, 
        "newMessage": {
            "role": "user",
            "parts": [{"text": message}]
        },
        "streaming": False # Set to true if you want to test actual streaming behavior from ADK
                           # and make this function a generator. For now, false is fine for single message.
    }
    
    # print(f"Sending payload to ADK (/run_sse): {json.dumps(payload, indent=2)}")

    try:
        # For SSE, the request should be made with stream=True to handle the stream properly
        response = requests.post(ADK_RUN_SSE_URL, json=payload, timeout=180, stream=True)
        response.raise_for_status()
        
        agent_reply_parts = []
        
        # SSE streams are typically 'text/event-stream'
        if 'text/event-stream' in response.headers.get('Content-Type', '').lower():
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data:'):
                    data_content = line[len('data:'):].strip()
                    if not data_content: # Skip empty data lines like 'data: '
                        continue
                    try:
                        event_json = json.loads(data_content)
                        # ----- THIS IS THE CORRECTED PARSING LOGIC -----
                        if "content" in event_json and \
                           isinstance(event_json["content"].get("parts"), list) and \
                           len(event_json["content"]["parts"]) > 0 and \
                           "text" in event_json["content"]["parts"][0]:
                            agent_reply_parts.append(event_json["content"]["parts"][0]["text"])
                        # You can add other 'elif' conditions here if the SSE event structure varies
                        # for different types of messages (e.g., tool calls vs. final text).
                        
                    except json.JSONDecodeError:
                        # If data is not JSON, but is a non-empty string, append it (less common for ADK)
                        # print(f"SSE data is not JSON: {data_content}") # For debugging
                        if data_content: 
                           agent_reply_parts.append(data_content)
                    except Exception as e_parse: # Catch other potential errors during parsing
                        # print(f"Error parsing SSE event_json: {e_parse}, data: {data_content}") # For debugging
                        pass # Or append an error message part

        else: # Fallback if not an event-stream (e.g., an error response might be plain JSON)
            try:
                response_data = response.json()
                # Standard ADK reply structure for non-streaming or errors
                agent_reply = response_data.get("reply", {}).get("text_output", None)
                if agent_reply is None: 
                    # A simpler direct text field
                    agent_reply = response_data.get("text") 
                    if agent_reply is None:
                        # Try to get it from a parts structure if present
                        parts = response_data.get("parts")
                        if isinstance(parts, list) and parts and "text" in parts[0]:
                             agent_reply = parts[0]["text"]
                        else: # If no known text field is found in a single JSON response
                            agent_reply = f"Received successful single JSON, but couldn't find parsable text output. Data: {json.dumps(response_data, indent=2)}"
                agent_reply_parts.append(agent_reply)
            except json.JSONDecodeError:
                 agent_reply_parts.append(f"Received non-SSE response that was not valid JSON: {response.text[:500]}...")
        
        # Construct final reply
        final_reply = "\n".join(filter(None, agent_reply_parts))
        if not final_reply and response.ok : # If no text was extracted but request was okay
            final_reply = "Agent responded, but no displayable text was found in the event stream."
            # print(f"No parsable text found in SSE stream. Full response text for debugging: {response.text}")

        return final_reply

    except requests.exceptions.Timeout:
        return "Error: The request to the ADK agent timed out."
    except requests.exceptions.ConnectionError:
        return f"Error: Could not connect to the ADK agent at {ADK_AGENT_URL}. Is 'adk web' running?"
    except requests.exceptions.HTTPError as e:
        error_detail = str(e)
        try:
            error_json = e.response.json()
            error_detail = json.dumps(error_json, indent=2)
        except json.JSONDecodeError:
            error_detail = e.response.text 
        return f"Error calling ADK agent (HTTP {e.response.status_code}):\n{error_detail}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# Create the Gradio Chat Interface (no changes to this part)
chat_interface = gr.ChatInterface(
    fn=call_adk_agent,
    title="Document Processing Agent",
    # ... rest of ChatInterface setup ...
    description="Interact with your ADK-powered document agent. \n" \
                "For file operations: \n" \
                "1. Provide a GCS URI directly (e.g., 'Load gs://my-bucket/my-doc.pdf'). \n" \
                "2. Or, if you've uploaded a file through another ADK interface, " \
                "mention that you've uploaded a file for the 'get_user_file' tool to process.",
    examples=[
        ["Hello"],
        ["Please classify the document at gs://statmike-mlops-349915/applied-ml-solution-prototypes/document-processing/documents/mortgage_statement_20231101_1_page.pdf"],
        ["I uploaded a new invoice, can you process it and tell me the total amount?"],
    ]
)

if __name__ == "__main__":
    if initialize_adk_session():
        print(f"Successfully initialized ADK session on startup: {SERVER_SESSION_ID}")
    else:
        print("Warning: Failed to initialize ADK session on startup. Gradio will attempt to initialize on the first message. Check Gradio app console for errors if issues persist.")
    
    chat_interface.launch()