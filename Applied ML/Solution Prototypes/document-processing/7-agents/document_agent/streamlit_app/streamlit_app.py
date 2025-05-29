import streamlit as st
import requests
import json
import uuid
import base64
import mimetypes
from PIL import Image
import io
import os

# --- Configuration for your ADK Web server ---
ADK_SESSION_CREATE_URL = "http://localhost:8000/apps/document_agent/users/user/sessions"
# CORRECTED: Point to the non-streaming /run endpoint
ADK_RUN_URL = "http://localhost:8000/run"

# --- ADK Communication Logic ---

def initialize_adk_session():
    """
    Calls the ADK endpoint to create an official session.
    Stores the session ID in Streamlit's session_state.
    """
    try:
        response = requests.post(ADK_SESSION_CREATE_URL, json={}, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        session_id = response_data.get("id")
        
        if session_id:
            st.session_state.adk_session_id = session_id
            print(f"Streamlit App: Successfully initialized ADK session: {session_id}")
        else:
            st.session_state.error = "Failed to get session ID from ADK server."
            print(f"Streamlit App ERROR: Session ID key 'id' not found in response: {response_data}")
            
    except Exception as e:
        st.session_state.error = f"Could not connect to ADK server to initialize session: {e}"
        print(f"Streamlit App ERROR: Exception during session initialization: {e}")

def call_adk_agent(prompt: str, file_bytes: bytes | None, mime_type: str | None):
    """
    CORRECTED: Sends the user's message to the ADK agent's non-streaming
    /run endpoint and processes the returned list of events.
    """
    message_parts = []
    if prompt:
        message_parts.append({"text": prompt})
    if file_bytes and mime_type:
        base64_encoded_data = base64.b64encode(file_bytes).decode('utf-8')
        file_part = {
            "inline_data": {"mime_type": mime_type, "data": base64_encoded_data}
        }
        message_parts.append(file_part)

    payload = {
        "app_name": "document_agent",
        "user_id": "user",
        "session_id": st.session_state.adk_session_id,
        "new_message": {"role": "user", "parts": message_parts},
        # You can even remove "streaming": False, as /run is non-streaming by default
    }

    try:
        # 1. Call the new /run endpoint
        response = requests.post(ADK_RUN_URL, json=payload, timeout=180)
        response.raise_for_status()
        
        # 2. The /run endpoint returns a LIST of event objects
        list_of_events = response.json()
        
        final_text_reply = ""
        final_image_reply = None
        
        # 3. Iterate through the list of events to gather all parts
        for event in list_of_events:
            # Check if the event is from the agent and has content
            if event.get("author") != "user" and event.get("content") and isinstance(event["content"].get("parts"), list):
                # Gather all text parts from the event
                text_parts = [part["text"] for part in event["content"]["parts"] if "text" in part and part["text"]]
                if text_parts:
                    final_text_reply += "\n".join(text_parts)

                # Find the first image part in the event
                if not final_image_reply: # Only take the first image found
                    for part in event["content"]["parts"]:
                        if "inline_data" in part and part["inline_data"].get("mime_type", "").startswith("image/"):
                            img_b64 = part["inline_data"]["data"]
                            img_bytes = base64.b64decode(img_b64)
                            final_image_reply = Image.open(io.BytesIO(img_bytes))
                            break # Found an image, stop looking in this event
        
        if not final_text_reply and not final_image_reply:
             final_text_reply = "Agent responded, but no displayable content was found."

        return {"text": final_text_reply.strip(), "image": final_image_reply}

    except requests.exceptions.JSONDecodeError:
        return {"text": f"Error: The server's response was not valid JSON. Response text: {response.text}"}
    except requests.exceptions.HTTPError as e:
        return {"text": f"Error calling ADK agent (HTTP {e.response.status_code}): {e.response.text}"}
    except Exception as e:
        return {"text": f"An unexpected error occurred: {str(e)}"}

# --- Streamlit App UI (No changes needed below this line) ---

st.set_page_config(layout="wide", page_title="Document Agent")

st.title("📄 Document Processing Agent (Streamlit UI)")
st.markdown("Interact with your ADK agent. Upload a PDF/PNG via the sidebar, type a message, and click Send.")

if "adk_session_id" not in st.session_state:
    st.session_state.adk_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "error" not in st.session_state:
    st.session_state.error = None

if not st.session_state.adk_session_id:
    initialize_adk_session()

if st.session_state.error:
    st.error(st.session_state.error)
    st.stop()

with st.sidebar:
    st.header("File Upload")
    uploaded_file = st.file_uploader(
        "Upload a PDF or PNG document to include with your next message",
        type=["pdf", "png"],
    )
    if uploaded_file:
        st.success(f"'{uploaded_file.name}' is ready to send.")
        st.caption("The file will be sent when you submit your next message.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "text_content" in message and message["text_content"]:
            st.markdown(message["text_content"])
        if "image_content" in message:
            st.image(message["image_content"], caption="Agent Image Response")

if prompt := st.chat_input("What would you like to do?"):
    file_bytes_data = None
    mime_type_data = None
    user_message_text = prompt
    if uploaded_file is not None:
        file_bytes_data = uploaded_file.getvalue()
        mime_type_data = uploaded_file.type
        user_message_text += f"\n\n*(File attached: `{uploaded_file.name}`)*"

    st.session_state.messages.append({"role": "user", "text_content": user_message_text})
    with st.chat_message("user"):
        st.markdown(user_message_text)
    
    with st.spinner("Agent is thinking..."):
        response_dict = call_adk_agent(prompt, file_bytes_data, mime_type_data)

    with st.chat_message("assistant"):
        final_text = response_dict.get("text")
        final_image = response_dict.get("image")
        
        if final_text:
            st.markdown(final_text)
        if final_image:
            st.image(final_image, caption="Agent Image Response")

    assistant_message = {"role": "assistant"}
    if final_text:
        assistant_message["text_content"] = final_text
    if final_image:
        assistant_message["image_content"] = final_image
    
    if final_text or final_image:
        st.session_state.messages.append(assistant_message)
    
    st.rerun()