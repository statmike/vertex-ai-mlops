import json
from google.adk.agents.llm_agent import Agent
from google.adk.agents import Context

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
    model="gemini-2.5-pro",
    description="Your job is to read the central RFI JSON state and classify each question as 'generic' or 'project_specific'.",
    instruction="""You are an expert RFI Qualification assistant.
    Start by announcing to the user that you are beginning the qualification process. Then review the JSON string representing the 'RFIState' provided below:
    {rfi_state_json}

    Process each question individually:
    
    1. Analyze the question 'text'.
    2. If the question asks about standard policies, compliance, generic company information, or general capabilities (like standard processes, history, financial health), categorize it as "generic".
    3. If the question asks for completely bespoke pricing for a specific user project or highly tailored architectural design, categorize it as "project_specific".
    4. Call `save_qualification_tool` to save the ID, decision, and a concise 1-sentence reasoning.
    
    Do NOT try to save the entire JSON state at once! Call `save_qualification_tool` for EACH question after you process it.
    Do NOT attempt to use tools like `transfer_to_agent` to pass control; the framework will handle that automatically.
    Once you have processed all questions, reply to the user that qualification is complete.
    """,
    tools=[save_qualification_tool]
)
