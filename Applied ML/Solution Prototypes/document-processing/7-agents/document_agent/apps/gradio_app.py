import os, json, argparse, mimetypes, base64
import gradio
import dotenv
import utils

# Load environment variables set with agent (.env)
dotenv.load_dotenv(dotenv_path = '.env')

# Set variables
USER_ID = 'gradio_user_123'
SESSION_ID = None

def get_agent_response(message: dict, history: list, mode: str):

    # Process Input
    text_input = message["text"]
    file_paths = message["files"]

    message_parts = []
    if text_input:
        message_parts.append({"text": text_input})
    if file_paths:
        for file_path in file_paths:
            with open(file_path, "rb") as file:
                file_bytes = file.read()
            base64_encoded_data = base64.b64encode(file_bytes).decode('utf-8')
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"
            file_part = {
                "inline_data": { "mime_type": mime_type, "data": base64_encoded_data}
            }
            message_parts.append(file_part)

    # File handling would go here. For now, we use the text input.
    if not text_input:
        return "Please provide a text-based message."

    # Interact With Agent
    if mode == 'local':
        payload = dict(
            appName = 'document_agent',
            userId = USER_ID,
            sessionId = SESSION_ID,
            newMessage = dict(
                role = "user",
                parts = message_parts
            ),
            streaming = False # token level streaming
        )
        response = utils.make_request(payload = payload, mode = mode, suffix = 'run_sse')
        final_text = utils.response_parse(response, mode = mode)
        return final_text

    elif mode == 'remote':
        payload = dict(
            class_method = 'stream_query',
            input = dict(
                user_id = USER_ID,
                session_id = SESSION_ID,
                message = text_input
            )
        )
        response = utils.make_request(payload = payload, mode = mode, suffix = 'streamQuery?alt=sse')
        final_text = utils.response_parse(response, mode = mode)
        return final_text

    else:
        return f"An unknown exectuion mode was requested: mode = '{mode}'"

if __name__ == "__main__":
    # determine if this is running with Vertex Agent Engine or directly with ADK (adk, adk api_server)
    parser = argparse.ArgumentParser(description="Run the Gradio app with a specific configuration.")
    parser.add_argument(
        "--mode",
        type=str,
        default="local",  # This is the default value if the flag isn't provided
        help="Specify the run mode: 'local' (adk web, adk api_server) or 'remote' (Vertex AI Agent Engine)."
    )
    args = parser.parse_args()
    if args.mode == "local":
        SESSION_ID = utils.initialize_adk_session(user_id = USER_ID, mode = args.mode)
        print(f"✅ Starting Gradio service in '{args.mode}' mode which will use the service hosted locally and served by `adk web` or `adk api_server`")
    if args.mode == "remote":
        SESSION_ID = utils.initialize_adk_session(user_id = USER_ID, mode = args.mode)
        print(f"✅ Starting Gradio service in '{args.mode}' mode which will use the service hosted by Vertex AI Agent Engine")    

    # set mode in the function:
    app_function = lambda message, history: get_agent_response(message, history, mode = args.mode)

    # --- Gradio Interface ---
    chat = gradio.ChatInterface(
        fn = app_function, 
        title = "Document Processing Agent",
        description = "Interact with your ADK-powered document agent. You can type a message and/or use the paperclip icon to upload a PDF or PNG file.",
        multimodal = True,
        examples = [
            ["What can you do?"],
            ["Please extract contents from the document at gs://statmike-mlops-349915/applied-ml-solution-prototypes/document-processing/vendor_2/fake_invoices/vendor_2_invoice_10.pdf"]
        ]
    )

    # get a session and start the chat
    if SESSION_ID:
        print(f"Successfully initialized ADK session on startup: {SESSION_ID}")
        print('Starting Gradio service...')
        chat.launch()
    else:
        print("ERROR: Failed to initialize ADK session on startup.")
    
    