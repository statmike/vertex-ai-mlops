import json
from google.adk.agents.llm_agent import Agent
from google.adk.agents import Context
from root_agent.prompts import CRITIQUE_INSTRUCTION
from root_agent.config import MODEL

def save_critique_tool(context: Context, question_id: str, passed_quality_check: bool, feedback: str, retry: bool) -> str:
    """Saves the critique decision for a specific question ID to the RFIState JSON in session state."""
    if 'rfi_state_json' not in context.state:
        return "Error: RFI State not found in session."
        
    try:
        rfi_state = json.loads(context.state['rfi_state_json'])
        questions = rfi_state.get('questions', [])
        
        updated = False
        for q in questions:
            if q.get('id') == question_id:
                if 'critique' not in q:
                    q['critique'] = {}
                q['critique']['passed_quality_check'] = passed_quality_check
                q['critique']['feedback'] = feedback
                
                if retry:
                    q['critique']['retry_count'] = q['critique'].get('retry_count', 0) + 1
                    q['status'] = 'qualified' # Loop back to answering
                else:
                    q['status'] = 'critiqued' # Move forward to writing
                
                updated = True
                break
                
        if updated:
            context.state['rfi_state_json'] = json.dumps(rfi_state)
            return f"Critique for {question_id} saved successfully."
        else:
            return f"Error: Question ID {question_id} not found in state."
            
    except Exception as e:
        return f"Error parsing/saving RFI state: {e}"

critique = Agent(
    name="critique_agent",
    model=MODEL,
    description="Your job is to read the RFI JSON and evaluate the quality of the answers in it. Flag poor answers for retry.",
    instruction=CRITIQUE_INSTRUCTION,
    tools=[save_critique_tool]
)
