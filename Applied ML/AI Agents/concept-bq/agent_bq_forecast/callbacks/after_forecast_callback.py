from typing import Optional, Dict, Any
from google.adk import tools


async def after_forecast_callback(tool: tools.BaseTool, args: Dict[str, Any], tool_response: Dict, tool_context: tools.ToolContext) -> Optional[Dict]:
    """
    Callback executed after the forecast tool runs.

    This callback captures the forecast results and stores them in the tool context
    state for later use. It also modifies the response to provide structured keys
    indicating where the forecast data can be found in the state.

    Args:
        tool: The tool that was called (only processes 'forecast' tool)
        args: The arguments passed to the forecast tool
        tool_response: The response returned by the forecast tool
        tool_context: The tool execution context containing shared state

    Returns:
        Optional[Dict]: A modified response with success status and data keys,
                       or None if not processing the forecast tool
    """
    if tool.name != 'forecast':
        return

    try:
        print(f"Forecast completed. Storing results in state.")

        # Store the forecast results in the tool context state
        tool_context.state['forecast_horizon'] = tool_response
        print(f"Forecast results saved to state['forecast_horizon']")

        # modify the response
        new_response = dict(
            result = dict(
                success = True,
                horizon_data_key = 'forecast_horizon',
                history_data_key = 'forecast_history'
            )
        )
        return new_response

    except Exception as e:
        print(f"Error storing forecast results: {e}")
        import traceback
        traceback.print_exc()