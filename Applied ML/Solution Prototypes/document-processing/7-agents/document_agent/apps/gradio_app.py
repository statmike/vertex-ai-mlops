import os, json
import gradio
import dotenv
import utils

# Load environment variables set with agent (.env)
dotenv.load_dotenv(dotenv_path = '.env')

# Set variables
USER_ID = 'gradio_user_123'

def get_agent_response(message: dict, history: list):

    # Process Input
    text_input = message["text"]
    # File handling would go here. For now, we use the text input.
    if not text_input:
        return "Please provide a text-based message."

    # Interact With Agent
    payload = dict(
        class_method = 'stream_query',
        input = dict(
            user_id = USER_ID,
            session_id = SESSION_ID,
            message = text_input
        )
    )
    response = utils.make_request(suffix = 'streamQuery?alt=sse', payload = payload, stream = True)

    # Parse Response and Send Back
    try:
        final_text = 'ERROR: No final response from agent found.'
        for line in response.iter_lines(decode_unicode = True):
            event = json.loads(line)
            final_text = event.get('content').get('parts')[0].get('text')
        return final_text
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# --- Gradio Interface ---
chat = gradio.ChatInterface(
    fn = get_agent_response, 
    title = "Document Processing Agent",
    description = "Interact with your ADK-powered document agent. You can type a message and/or use the paperclip icon to upload a PDF or PNG file.",
    multimodal = True,
    examples = [
        ["What can you do?"],
        ["Please extract contents from the document at gs://statmike-mlops-349915/applied-ml-solution-prototypes/document-processing/documents/mortgage_statement_20231101_1_page.pdf"]
    ]
)

if __name__ == "__main__":
    global SESSION_ID
    SESSION_ID = utils.initialize_adk_session(user_id = USER_ID)
    if SESSION_ID:
        print(f"Successfully initialized ADK session on startup: {SESSION_ID}")
        print('Starting Gradio service...')
        chat.launch()
    else:
        print("ERROR: Failed to initialize ADK session on startup.")
    
    