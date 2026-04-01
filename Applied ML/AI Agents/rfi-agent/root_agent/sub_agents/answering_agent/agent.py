import os
import json
from google.adk.agents.llm_agent import Agent

def google_search(query: str) -> str:
    """Searches the open web for facts, standard service definitions, and regulatory compliance."""
    # In production, this uses the native Vertex Search Grounding module.
    # For standard testing without billing access, this mocks a successful retrieval.
    return f"Search result for '{query}': Our platform complies with SOC2 Type II, ISO 27001, and provides 99.9% uptime SLAs."

from google.adk.agents import Context

def save_answer_tool(context: Context, question_id: str, answer_text: str, confidence_score: float) -> str:
    """Saves the answer for a specific question ID to the RFIState JSON in session state."""
    if 'rfi_state_json' not in context.state:
        return "Error: RFI State not found in session."
        
    try:
        rfi_state = json.loads(context.state['rfi_state_json'])
        questions = rfi_state.get('questions', [])
        
        updated = False
        for q in questions:
            if q.get('id') == question_id:
                if 'answer' not in q:
                    q['answer'] = {}
                q['answer']['text'] = answer_text
                q['answer']['confidence_score'] = confidence_score
                q['status'] = 'answered'
                updated = True
                break
                
        if updated:
            context.state['rfi_state_json'] = json.dumps(rfi_state)
            return f"Answer for {question_id} saved successfully."
        else:
            return f"Error: Question ID {question_id} not found in state."
            
    except Exception as e:
        return f"Error parsing/saving RFI state: {e}"

answering = Agent(
    name="answering_agent",
    model="gemini-2.5-pro",
    description="Your job is to generate answers for questions in the RFI state using your Google Search engine.",
    instruction="""You are an expert RFI Answering assistant.
    Start by announcing to the user that you are beginning the answering process. Then review the JSON string representing the 'RFIState' provided below:
    {rfi_state_json}

    Process each question individually:
    
    1. For questions where "qualification.question_type" is "generic":
       - Call `google_search` to find internal or external information.
       - **Fallback Rule**: If `google_search` returns a generic mock snippet that does not help answer the specific question, DO NOT give up! Instead, use your own internal knowledge to provide a professional, standard industry answer.
       - Call `save_answer_tool` to save the ID, the answer text, and a confidence score (0.0 to 1.0).
       
    2. For questions where "qualification.question_type" is "project_specific":
       - Call `save_answer_tool` with the text "Requires Human SE Architecture Review" and confidence `0.0`.
       
    Do NOT try to save the entire JSON state at once! Call `save_answer_tool` for EACH question after you generate its answer.
    Do NOT attempt to use tools like `transfer_to_agent` to pass control; the framework will handle that automatically.
    Once you have processed all questions, reply to the user that answering is complete.
    """,
    tools=[google_search, save_answer_tool]
)
