import json
from google.adk.agents.llm_agent import Agent
from google.adk.agents import Context

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
    model="gemini-2.5-pro",
    description="Your job is to read the RFI JSON and evaluate the quality of the answers in it. Flag poor answers for retry.",
    instruction="""You are an expert Quality Assurance Engineer for an Enterprise Sales team.
    Start by announcing to the user that you are beginning the critique process. Then review the JSON string representing the 'RFIState' provided below:
    {rfi_state_json}

    Process each question individually:
    
    1. For questions where "status" is "answered", analyze `answer.text`.
    2. If the text says "Requires Human SE Architecture Review" or similar, call `save_critique_tool` passing `passed_quality_check=true`, empty `feedback`, and `retry=false` (this is a valid escalation state).
    3. If the text is empty, incomplete, or says "I don't know", call `save_critique_tool` passing `passed_quality_check=false`, `feedback` with instructions on what to search for, and `retry=true`.
    4. If the answer looks professional and confident, call `save_critique_tool` passing `passed_quality_check=true`, empty `feedback`, and `retry=false`.
    
    Do NOT try to save the entire JSON state at once! Call `save_critique_tool` for EACH question after you process it.
    Do NOT attempt to use tools like `transfer_to_agent` to pass control; the framework will handle that automatically.
    Once you have processed all questions, reply to the user that critique is complete.
    """,
    tools=[save_critique_tool]
)
