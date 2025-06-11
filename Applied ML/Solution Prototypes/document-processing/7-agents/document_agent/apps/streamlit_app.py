import json, argparse, base64, mimetypes
import streamlit as st
import dotenv
import utils

# Load environment variables set with agent (.env)
dotenv.load_dotenv(dotenv_path = '.env')

# Set variables
USER_ID = 'streamlit_user_123'

# Determine run mode
parser = argparse.ArgumentParser(description="Run the Streamlit app with a specific configuration.")
parser.add_argument(
    "--mode",
    type=str,
    default="local",
    help="Specify the run mode: 'local' (adk web) or 'remote' (Vertex AI Agent Engine)."
)
args = parser.parse_args()

# Streamlit App UI
st.set_page_config(layout="wide", page_title="Document Processing Agent")
st.title("📄 Document Processing Agent")
st.markdown(f"Interact with your ADK agent (Mode: `{args.mode}`)). Upload a PDF/PNG via the sidebar, type a message, and click Send.")

# setup parameters in the session state
if "user_id" not in st.session_state:
    st.session_state.user_id = USER_ID
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "error" not in st.session_state:
    st.session_state.error = None

# create an active session
if not st.session_state.session_id:
    st.session_state.session_id = utils.initialize_adk_session(user_id = st.session_state.user_id, mode = args.mode)
    if st.session_state.session_id:
        st.success(f"New session created: {st.session_state.session_id}.")
        st.rerun() # Rerun to clear the success message and have a clean slate
    else:
        st.error("Fatal Error: Failed to initialize ADK session. Please check the terminal for logs.")
        st.stop()

# setup sidebar for doucment loading
with st.sidebar:
    st.header("File Upload")
    uploaded_file = st.file_uploader(
        "Upload a PDF or PNG document to include with your next message",
        type=["pdf", "png"],
    )
    if uploaded_file:
        st.success(f"'{uploaded_file.name}' is ready to send.")
        st.caption("The file will be sent when you submit your next message.")

# chat handling
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "text_content" in message and message["text_content"]:
            st.markdown(message["text_content"])
        if "image_content" in message:
            st.image(message["image_content"], caption="Agent Image Response")

# interaction logic
if prompt := st.chat_input("What would you like to do?"):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "text_content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process inputs for the payload
    message_parts = []
    if prompt:
        message_parts.append({"text": prompt})
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        base64_encoded_data = base64.b64encode(file_bytes).decode('utf-8')
        mime_type = uploaded_file.type or "application/octet-stream"
        file_part = {"inline_data": {"mime_type": mime_type, "data": base64_encoded_data}}
        message_parts.append(file_part)

    # Show a thinking spinner while waiting for the response
    with st.spinner("Agent is thinking..."):
        if args.mode == 'local':
            payload = dict(
                appName='document_agent',
                userId=st.session_state.user_id,
                sessionId=st.session_state.session_id,
                newMessage=dict(role="user", parts=message_parts),
                streaming=True
            )
            response = utils.make_request(payload = payload, mode = args.mode, suffix = 'run_sse')
        elif args.mode == 'remote':
            payload = dict(
                class_method='stream_query',
                input=dict(
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id,
                    message=prompt  # Remote endpoint takes the text prompt
                )
            )
            response = utils.make_request(payload = payload, mode = args.mode, suffix = 'streamQuery?alt=sse')

        try:
            final_text = utils.response_parse(response, mode = args.mode)
            if not final_text:
                final_text = "Agent responded, but no text was found."

        except Exception as e:
            st.error(f"An error occurred while parsing the response: {e}")
            final_text = None

    # Display agent response and update history
    if final_text:
        st.session_state.messages.append({"role": "assistant", "text_content": final_text})
        with st.chat_message("assistant"):
            st.markdown(final_text)

    # Rerun to clear the input box implicitly
    st.rerun()
