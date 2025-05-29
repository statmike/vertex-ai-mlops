import mesop as me
import mesop.labs as mel
from dataclasses import field
import requests
import json
import uuid
import base64
import mimetypes
import time

# --- Configuration for your ADK Web server ---
ADK_SESSION_CREATE_URL = "http://localhost:8000/apps/document_agent/users/user/sessions"
ADK_RUN_URL = "http://localhost:8000/run"


@me.stateclass
class State:
    session_id: str | None = None
    chat_history: list[mel.ChatMessage] = field(default_factory=list)
    staged_file: me.UploadedFile | None = None
    is_processing: bool = False
    error_message: str | None = None
    notification: str | None = None
    # CHANGE 1: Remove input_text, add input_key
    input_key: int = 0


# All helper functions and other event handlers remain the same.
def set_notification(message: str):
    state = me.state(State)
    state.notification = message
    yield
    time.sleep(3)
    state.notification = None
    yield

def initialize_adk_session(state: State):
    if state.session_id: return True
    try:
        response = requests.post(ADK_SESSION_CREATE_URL, json={}, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        created_session_id = response_data.get("id")
        if created_session_id:
            state.session_id = str(created_session_id)
            print(f"Successfully initialized ADK session: {state.session_id}")
            return True
        else:
            state.error_message = f"Error: Session ID key 'id' not found."
            return False
    except requests.exceptions.RequestException as e:
        state.error_message = f"Error connecting to ADK server. Is it running? Details: {e}"
        return False

def on_load(e: me.LoadEvent):
    state = me.state(State)
    if not initialize_adk_session(state): pass
    if not state.chat_history:
        state.chat_history.append(
            mel.ChatMessage(role="assistant", content="Welcome! Ask a question or upload a document.")
        )

def on_file_upload(event: me.UploadEvent):
    state = me.state(State)
    state.staged_file = event.file
    yield from set_notification(f"Staged file: {event.file.name}")

# CHANGE 2: The on_input function is no longer needed and has been deleted.

def on_chat_submit(event: me.InputEvent):
    state = me.state(State)
    # CHANGE 3: Get input value directly from the event, not from state.
    user_input = event.value
    
    if not user_input and not state.staged_file:
        yield from set_notification("Please type a message or upload a file first.")
        return
        
    state.is_processing = True
    state.error_message = None
    yield

    if user_input:
        state.chat_history.append(mel.ChatMessage(role="user", content=user_input))
    elif state.staged_file:
        state.chat_history.append(mel.ChatMessage(role="user", content=f"Processing file: {state.staged_file.name}"))
    
    # After adding the message to history, increment the key to reset the input
    state.input_key += 1
    state.chat_history.append(mel.ChatMessage(role="assistant", content="..."))
    yield

    if not state.session_id and not initialize_adk_session(state):
        state.chat_history[-1].content = state.error_message; state.is_processing = False; yield; return

    message_parts = []
    if user_input:
        message_parts.append({"text": user_input})
    if state.staged_file:
        try:
            file_bytes = state.staged_file.getvalue()
            base64_encoded_data = base64.b64encode(file_bytes).decode('utf-8')
            mime_type, _ = mimetypes.guess_type(state.staged_file.name)
            message_parts.append({
                "inline_data": { "mime_type": mime_type or "application/octet-stream", "data": base64_encoded_data }
            })
            state.staged_file = None
        except Exception as e:
            state.chat_history[-1].content = f"Error processing file: {e}"; state.is_processing = False; yield; return
            
    payload = {
        "appName": "document_agent", "userId": "user", "sessionId": state.session_id,
        "newMessage": {"role": "user", "parts": message_parts},
        "streaming": False 
    }

    try:
        response = requests.post(ADK_RUN_URL, json=payload, timeout=180)
        response.raise_for_status()
        response_data = response.json()
        
        final_text = "Error: No final response from assistant found."
        if isinstance(response_data, list):
            for message in reversed(response_data):
                content = message.get("content", {})
                if isinstance(content, dict) and content.get("role") == "model":
                    parts = content.get("parts", [])
                    if parts and isinstance(parts, list):
                        first_part = parts[0]
                        if isinstance(first_part, dict):
                            text_part = first_part.get("text")
                            if text_part:
                                final_text = text_part
                            else:
                                final_text = f"Agent returned a structured response: `{json.dumps(first_part)}`"
                        else:
                            final_text = f"Agent returned an unknown part: `{str(first_part)}`"
                        break
        
        state.chat_history[-1].content = final_text

    except requests.exceptions.RequestException as e:
        state.chat_history[-1].content = f"An unexpected error occurred: {e}"
    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        state.chat_history[-1].content = f"Error parsing response from server: {e}"
    finally:
        state.is_processing = False
        yield


@me.page(
    path="/",
    title="Document Processing Agent",
    on_load=on_load,
    security_policy=me.SecurityPolicy(dangerously_disable_trusted_types=True)
)
def app():
    state = me.state(State)

    if state.notification:
        with me.box(style=me.Style(
            position="fixed", bottom="24px", left="50%", transform="translateX(-50%)",
            background="#333", color="white", padding=me.Padding(top=10, bottom=10, left=16, right=16),
            border_radius=8, z_index=1000,
        )):
            me.text(state.notification)

    with me.box(style=me.Style(display="flex", flex_direction="column", height="95vh", padding=me.Padding.all(16))):
        me.text("Document Processing Agent", type="headline-4")
        me.text("Interact with your ADK agent. Type a message and/or upload a document.", style=me.Style(margin=me.Margin(bottom=16)))
        if state.error_message:
            me.text(state.error_message, style=me.Style(color="red", font_weight="bold"))

        with me.box(style=me.Style(flex_grow=1, overflow_y="auto", display="flex", flex_direction="column")):
            for message in state.chat_history:
                if message.role == "user":
                    with me.box(style=me.Style(display="flex", justify_content="flex-start", margin=me.Margin(bottom=12))):
                        with me.box(style=me.Style(
                            background="#dcf8c6", color="black", padding=me.Padding.all(12), 
                            border_radius=16, max_width="70%"
                        )):
                            me.text(message.content)
                else: 
                    with me.box(style=me.Style(display="flex", justify_content="flex-end", margin=me.Margin(bottom=12))):
                         with me.box(style=me.Style(
                            background="#f1f0f0", color="black", padding=me.Padding.all(12),
                            border_radius=16, max_width="70%",
                         )):
                            me.markdown(message.content)

        with me.box(style=me.Style(margin=me.Margin(top=16))):
            with me.box(style=me.Style(display="flex", align_items="center", gap=16)):
                me.uploader(
                    label="Upload PDF or PNG",
                    accepted_file_types=["application/pdf", "image/png"],
                    on_upload=on_file_upload,
                    type="stroked",
                )
                if state.staged_file:
                    me.text(f"Ready to send: {state.staged_file.name}")

            # CHANGE 4: The input is now uncontrolled. It has no `value` or `on_input`.
            # It has a `key` that forces a reset when it changes.
            me.input(
                key=str(state.input_key),
                label="Send a message",
                on_enter=on_chat_submit,
                disabled=state.is_processing,
                style=me.Style(width="100%", margin=me.Margin(top=16))
            )