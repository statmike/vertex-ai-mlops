import json
from google.adk.agents.llm_agent import Agent
from root_agent.prompts import ANSWERING_INSTRUCTION
from root_agent.config import MODEL

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
    model=MODEL,
    description="Your job is to generate answers for questions in the RFI state using your Google Search engine.",
    instruction=ANSWERING_INSTRUCTION,
    tools=[google_search, save_answer_tool]
)
