from typing import Optional, Dict, Any
from google.adk import tools


async def after_forecast_callback(tool: tools.BaseTool, args: Dict[str, Any], tool_response: Dict, tool_context: tools.ToolContext) -> Optional[Dict]:
    """
    Callback executed after the forecast tool runs.

    This callback captures the forecast results and stores them in the tool context
    state for later use.

    Args:
        tool: The tool that was called
        result: The result returned by the tool
        tool_context: The tool execution context
    """
    if tool.name != 'forecast':
        return

    try:
        print(f"Forecast completed. Storing results in state.")

        # Store the forecast results in the tool context state
        tool_context.state['forecast_horizon'] = tool_response
        print(f"Forecast results saved to state['forecast_horizon']")

    except Exception as e:
        print(f"Error storing forecast results: {e}")
        import traceback
        traceback.print_exc()