import streamlit as st
import base64
import mimetypes
import json
from PIL import Image
import dotenv
import utils

# Load environment variables set with agent (.env)
dotenv.load_dotenv(dotenv_path = '.env')

# Set variables
USER_ID = 'streamlit_user_123'

# Streamlit App UI
st.set_page_config(layout="wide", page_title="Document Processing Agent")
st.title("📄 Document Processing Agent")
st.markdown("Interact with your ADK agent. Upload a PDF/PNG via the sidebar, type a message, and click Send.")

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
    st.session_state.session_id = utils.initialize_adk_session(user_id = st.session_state.user_id)
if not st.session_state.session_id:
    st.session_state.error = f"Failed to initialize ADK session."
    st.error(st.session_state.error)
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

# handle user input: text and possible file
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
    
    # Interact with agent 
    with st.spinner("Agent is thinking..."):
        payload = dict(
            class_method = 'stream_query',
            input = dict(
                user_id = st.session_state.user_id,
                session_id = st.session_state.session_id,
                message = prompt
            )
        )
        response = utils.make_request(suffix = 'streamQuery?alt=sse', payload = payload, stream = True)
        # parse response
        #response_dict = call_adk_agent(prompt, file_bytes_data, mime_type_data)
        try:
            final_text = 'ERROR: No final response from agent found.'
            for line in response.iter_lines(decode_unicode = True):
                event = json.loads(line)
                final_text = event.get('content').get('parts')[0].get('text')
            #return final_text
        except Exception as e:
            final_text = f"An unexpected error occurred: {str(e)}"
        # for use by the app
        response_dict = {"text": final_text, "image": None}

    # return to user
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