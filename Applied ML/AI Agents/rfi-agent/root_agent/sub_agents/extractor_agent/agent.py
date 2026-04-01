from google.adk.agents.llm_agent import Agent
from google.adk.agents import Context

def extractor_tool(context: Context, file_path: str) -> str:
    from root_agent.sub_agents.extractor_agent.doc_tools import parse_docx, parse_excel, parse_pdf
    from root_agent.models.schema import RFIState, DocumentMetadata
    import os
    
    # Gracefully handle relative filenames from the chat UI
    if not os.path.exists(file_path):
        attempt_path = os.path.join(os.getcwd(), "data/input", file_path)
        if os.path.exists(attempt_path):
            file_path = attempt_path
            
    if file_path.endswith(".docx"):
        doc_type = "docx"
        questions = parse_docx(file_path)
    elif file_path.endswith(".xlsx"):
        doc_type = "excel"
        questions = parse_excel(file_path)
    elif file_path.endswith(".pdf"):
        doc_type = "pdf"
        questions = parse_pdf(file_path)
    else:
        return '{"error": "Unsupported file format. Please provide .docx, .xlsx, or .pdf"}'
        
    filename = os.path.basename(file_path)
    state = RFIState(
        document=DocumentMetadata(
            filename=filename,
            type=doc_type,
            path=file_path,
            status="processing"
        ),
        questions=questions
    )
    context.state['rfi_state_json'] = state.model_dump_json()
    return f"Successfully extracted questions from {filename}. The central state has been updated. You can now pass control to the qualification agent."

extractor = Agent(
    name="extractor_agent",
    model="gemini-2.5-pro",
    description="Your job is to read DOCX, Excel, or PDF files from the raw input and extract all RFI questions into the central RFIState JSON. Use the extracting tool provided.",
    instruction="Execute the extractor tool to parse the file. When it completes, just reply with a text summary of your work. Do NOT attempt to use tools like `transfer_to_agent` to pass control; the framework will handle that automatically.",
    tools=[extractor_tool]
)
