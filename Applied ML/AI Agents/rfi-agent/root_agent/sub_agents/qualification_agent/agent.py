import json
from google.adk.agents.llm_agent import Agent
from google.adk.agents import Context
from root_agent.prompts import QUALIFICATION_INSTRUCTION
from root_agent.config import MODEL

def save_qualification_tool(context: Context, question_id: str, question_type: str, reasoning: str) -> str:
    """Saves the qualification decision for a specific question ID to the RFIState JSON in session state."""
    if 'rfi_state_json' not in context.state:
        return "Error: RFI State not found in session."
        
    try:
        rfi_state = json.loads(context.state['rfi_state_json'])
        questions = rfi_state.get('questions', [])
        
        updated = False
        for q in questions:
            if q.get('id') == question_id:
                if 'qualification' not in q:
                    q['qualification'] = {}
                q['qualification']['question_type'] = question_type
                q['qualification']['reasoning'] = reasoning
                q['status'] = 'qualified'
                updated = True
                break
                
        if updated:
            context.state['rfi_state_json'] = json.dumps(rfi_state)
            return f"Qualification for {question_id} saved successfully."
        else:
            return f"Error: Question ID {question_id} not found in state."
            
    except Exception as e:
        return f"Error parsing/saving RFI state: {e}"

qualification = Agent(
    name="qualification_agent",
    model=MODEL,
    description="Your job is to read the central RFI JSON state and classify each question as 'generic' or 'project_specific'.",
    instruction=QUALIFICATION_INSTRUCTION,
    tools=[save_qualification_tool]
)
