from typing import Optional, Dict, Any
import copy
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google import genai

async def process_toolbox_output(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict
) -> str: #Optional[Dict]:
    """
    Inspects/modifies the tool result after execution.
    """

    # get tool response information
    agent_name = tool_context.agent_name
    response = tool_response #.get("result", "")

    if tool.name in ['sum-by-day-overall', 'sum-by-day-stations', 'forecast-sum-by-day-overall', 'forecast-sum-by-day-stations']:

        # save the tool response as an artifact specific to the tool
        artifact_key = f'response-from-{tool.name}'
        artifact = genai.types.Part.from_text(text = str(response))
        version = await tool_context.save_artifact(filename = artifact_key, artifact = artifact)

        # modify response
        mod_response = copy.deepcopy(tool_response)
        mod_response = f"The results of calling the tool {tool.name} are stored as version {version} with artifact_key {artifact_key}."
        #mod_response['changed_by_callback'] = True
        return mod_response

    # passthrough response
    return None
