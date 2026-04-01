from google.adk.agents import Context
from root_agent.prompts import WRITER_INSTRUCTION
from root_agent.config import MODEL

def writer_tool(context: Context) -> str:
    from root_agent.models.schema import RFIState
    from root_agent.sub_agents.writer_agent.write_tools import write_docx, write_excel, write_pdf_fallback
    import os
    
    json_state = context.state.get('rfi_state_json', '{}')
    state_str = json_state.strip()
    if state_str.startswith("```json"):
        state_str = state_str[7:]
    if state_str.startswith("```"):
        state_str = state_str[3:]
    if state_str.endswith("```"):
        state_str = state_str[:-3]
    state_str = state_str.strip()
    
    try:
        # Standard strict JSON
        state = RFIState.model_validate_json(state_str)
    except Exception as e:
        # If the LLM still hallucinates single-quotes like {'document': ...} we can fallback to Python AST
        import ast
        try:
            dict_val = ast.literal_eval(state_str)
            state = RFIState.model_validate(dict_val)
        except Exception as e2:
            return f"{{\"error\": \"Failed to parse RFI State either as JSON or dict. First error: {str(e)} Second error: {str(e2)}\"}}"

    base_file = os.path.basename(state.document.path)
    abs_doc_path = os.path.abspath(state.document.path)
    output_path = os.path.join(os.path.dirname(abs_doc_path), "../../data/output", f"completed_{base_file}")
    output_path = os.path.normpath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    state.document.status = "completed"
    if state.document.type == "docx":
        write_docx(state, output_path)
    elif state.document.type == "excel":
        write_excel(state, output_path)
    elif state.document.type == "pdf":
        write_pdf_fallback(state, output_path)
    else:
        return '{"error": "Unsupported file format for writing"}'
        
    for q in state.questions:
        if q.status == "critiqued":
            q.status = "completed"
            
    final_json = state.model_dump_json(indent=2)
    base_no_ext, _ = os.path.splitext(base_file)
    json_output_path = os.path.join(os.path.dirname(output_path), f"completed_{base_no_ext}.json")
    with open(json_output_path, "w") as f:
        f.write(final_json)
        
    return f"Success! RFI workflow complete. Outputs written to {output_path} and JSON state saved to {json_output_path}."

from google.adk.agents.llm_agent import Agent

writer = Agent(
    name="writer_agent",
    model=MODEL,
    description="Your job is to read the finalized RFI JSON state and write the answers back into the original input document.",
    instruction=WRITER_INSTRUCTION,
    tools=[writer_tool]
)
