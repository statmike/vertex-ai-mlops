import os, json, time, base64, mimetypes
import mesop as me
import mesop.labs as mel
from dataclasses import field
import dotenv
import utils

# Load environment variables set with agent (.env)
dotenv.load_dotenv(dotenv_path = '.env')

# Set variables
USER_ID = 'mesop_user_123'

@me.stateclass
class State:
    user_id: str | None = None
    session_id: str | None = None
    mode: str = ""
    chat_history: list[mel.ChatMessage] = field(default_factory=list)
    staged_file: me.UploadedFile | None = None
    is_processing: bool = False
    error_message: str | None = None
    notification: str | None = None
    input_key: int = 0

def set_notification(message: str):
    state = me.state(State)
    state.notification = message
    yield
    time.sleep(3)
    state.notification = None
    yield

def on_load(e: me.LoadEvent):
    state = me.state(State)
    state.mode = os.getenv("APP_MODE", "local") # defaults to local if not set
    print(f"✅ Mesop App starting in '{state.mode}' mode.")
    state.user_id = USER_ID
    state.session_id = utils.initialize_adk_session(user_id = state.user_id, mode = state.mode)  
    if not state.chat_history:
        state.chat_history.append(
            mel.ChatMessage(role = "assistant", content = "Welcome! Ask a question or upload a document.")
        )

def on_file_upload(event: me.UploadEvent):
    state = me.state(State)
    state.staged_file = event.file
    yield from set_notification(f"Staged file: {event.file.name}")

def on_chat_submit(event: me.InputEvent):
    state = me.state(State)
    user_input = event.value
    
    if not user_input and not state.staged_file:
        yield from set_notification("Please type a message or upload a file first.")
        return
        
    state.is_processing = True
    state.error_message = None
    yield

    if user_input:
        state.chat_history.append(mel.ChatMessage(role = "user", content = user_input))
    elif state.staged_file:
        state.chat_history.append(mel.ChatMessage(role = "user", content = f"Processing file: {state.staged_file.name}"))
    
    # After adding the message to history, increment the key to reset the input
    state.input_key += 1
    state.chat_history.append(mel.ChatMessage(role = "assistant", content = "..."))
    yield

    if not state.session_id:
        state.chat_history[-1].content = "Error: Session not initialized."
        state.is_processing = False
        yield
        return

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
            state.chat_history[-1].content = f"Error processing file: {e}"; state.is_processing = False
            yield
            return

    # Interact With Agent
    try:
        if state.mode == 'local':
            payload = dict(
                appName = 'document_agent',
                userId = state.user_id,
                sessionId = state.session_id,
                newMessage = dict(
                    role = "user",
                    parts = message_parts
                ),
                streaming = False # token level streaming
            )
            response = utils.make_request(payload = payload, mode = state.mode, suffix = 'run_sse')

        elif state.mode == 'remote':
            payload = dict(
                class_method = 'stream_query',
                input = dict(
                    user_id = state.user_id,
                    session_id = state.session_id,
                    message = user_input
                )
            )
            response = utils.make_request(payload = payload, mode = state.mode, suffix = 'streamQuery?alt=sse')

        else:
            state.chat_history[-1].content = f"An unknown exectuion mode was requested: mode = '{mode}'"
            state.is_processing = False
            yield
            return
    
        final_text = utils.response_parse(response, mode = state.mode)
        state.chat_history[-1].content = final_text if final_text else "Agent responded, but no text was found."

    except Exception as e:
        import traceback
        traceback.print_exc()
        state.chat_history[-1].content = f"An unexpected error occurred: {str(e)}"       
    finally:
        state.is_processing = False
        yield

@me.page(
    path="/",
    title = "Document Processing Agent",
    on_load = on_load,
    security_policy = me.SecurityPolicy(dangerously_disable_trusted_types=True)
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
        me.text(f"Interact with your ADK agent (Mode: {state.mode}). Type a message and/or upload a document.", style=me.Style(margin=me.Margin(bottom=16)))
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

            me.input(
                key=str(state.input_key),
                label="Send a message",
                on_enter=on_chat_submit,
                disabled=state.is_processing,
                style=me.Style(width="100%", margin=me.Margin(top=16))
            )