
import json
from datetime import timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from google.adk import tools
from google import genai

async def function_tool_forecast_plot(
        history_data_key: str,
        horizon_data_key: str,
        tool_context: tools.ToolContext) -> str:
    """
    Create a visualization plot of forecast results using historical and horizon data.

    This tool retrieves forecast data from the tool context state and generates an
    interactive HTML plot showing both historical data and forecast predictions.

    Args:
        history_data_key: The key to retrieve historical data from tool_context.state
                         (typically 'forecast_history')
        horizon_data_key: The key to retrieve forecast horizon data from tool_context.state
                         (typically 'forecast_horizon')
        tool_context: The tool execution context containing shared state

    Returns:
        str: A message indicating successful plot generation with artifact details,
             or an error message if the operation fails
    """

    artifact_key = 'forecast_plot'

    try:
        # Retrieve data from tool context state
        forecast_history_data = tool_context.state.get(history_data_key)
        forecast_horizon_data = tool_context.state.get(horizon_data_key)

        if not forecast_history_data or not forecast_horizon_data:
            return f"Error: Required data not found in tool context state. history_key='{history_data_key}', horizon_key='{horizon_data_key}'"

        # Extract column mapping from history data args
        args = forecast_history_data.get('args', {})
        timestamp_col = args.get('timestamp_col')
        data_col = args.get('data_col')
        id_cols = args.get('id_cols', [])  # List of ID columns, empty if single time series

        if not timestamp_col or not data_col:
            return "Error: Missing required column mappings in forecast_history['args'] (timestamp_col or data_col)"

        # Convert history data rows to pandas DataFrame
        history_rows = forecast_history_data.get('rows', [])
        if not history_rows:
            return "Error: No rows found in forecast_history data"

        df_history = pd.DataFrame(history_rows)

        # Convert timestamp column to datetime and ensure timezone awareness
        df_history[timestamp_col] = pd.to_datetime(df_history[timestamp_col])
        # Make timezone-aware if naive (use UTC)
        if df_history[timestamp_col].dt.tz is None:
            df_history[timestamp_col] = df_history[timestamp_col].dt.tz_localize('UTC')
        else:
            df_history[timestamp_col] = df_history[timestamp_col].dt.tz_convert('UTC')

        # Ensure data column is numeric
        df_history[data_col] = pd.to_numeric(df_history[data_col], errors='coerce')

        # Convert horizon data rows to pandas DataFrame
        horizon_rows = forecast_horizon_data.get('rows', [])
        if not horizon_rows:
            return "Error: No rows found in forecast_horizon data"

        df_horizon = pd.DataFrame(horizon_rows)

        # Convert forecast timestamp to datetime and ensure timezone awareness
        df_horizon['forecast_timestamp'] = pd.to_datetime(df_horizon['forecast_timestamp'])
        # Make timezone-aware if naive (use UTC)
        if df_horizon['forecast_timestamp'].dt.tz is None:
            df_horizon['forecast_timestamp'] = df_horizon['forecast_timestamp'].dt.tz_localize('UTC')
        else:
            df_horizon['forecast_timestamp'] = df_horizon['forecast_timestamp'].dt.tz_convert('UTC')

        # Ensure forecast columns are numeric
        numeric_cols = ['forecast_value', 'prediction_interval_lower_bound',
                       'prediction_interval_upper_bound', 'confidence_level']
        for col in numeric_cols:
            if col in df_horizon.columns:
                df_horizon[col] = pd.to_numeric(df_horizon[col], errors='coerce')

        print(f"Successfully loaded data:")
        print(f"  History: {len(df_history)} rows, columns: {list(df_history.columns)}")
        print(f"  Horizon: {len(df_horizon)} rows, columns: {list(df_horizon.columns)}")
        print(f"  Time series ID columns: {id_cols if id_cols else 'None (single time series)'}")

        # Create plotly figure
        fig = go.Figure()

        # Determine if we have multiple time series or a single series
        if id_cols:
            # Multiple time series - get unique combinations
            series_list = df_history[id_cols].drop_duplicates().to_dict('records')
        else:
            # Single time series
            series_list = [{}]

        # Store traces for visibility toggling
        all_traces = []

        for series_id in series_list:
            # Filter data for this series
            if id_cols:
                # Build filter for multiple ID columns
                hist_mask = pd.Series([True] * len(df_history))
                fcst_mask = pd.Series([True] * len(df_horizon))
                for col in id_cols:
                    hist_mask &= (df_history[col] == series_id[col])
                    fcst_mask &= (df_horizon[col] == series_id[col])

                hist_df = df_history[hist_mask].copy()
                fcst_df = df_horizon[fcst_mask].copy()

                # Create series name from ID columns
                series_name = ', '.join([f"{series_id[col]}" for col in id_cols])
            else:
                # Single series - use all data
                hist_df = df_history.copy()
                fcst_df = df_horizon.copy()
                series_name = 'Overall'

            # Sort by timestamp
            hist_df = hist_df.sort_values(by=timestamp_col)
            fcst_df = fcst_df.sort_values(by='forecast_timestamp')

            traces_for_series = []

            # Add confidence interval bounds
            fig.add_trace(go.Scatter(
                x=fcst_df['forecast_timestamp'],
                y=fcst_df['prediction_interval_lower_bound'],
                name='Lower',
                mode='lines',
                line_color='rgba(0,0,0,0)',
                showlegend=False,
                hovertemplate='Lower Bound: %{y:.2f}<extra></extra>'
            ))
            traces_for_series.append(len(fig.data) - 1)

            fig.add_trace(go.Scatter(
                x=fcst_df['forecast_timestamp'],
                y=fcst_df['prediction_interval_upper_bound'],
                name='Upper',
                mode='lines',
                line_color='rgba(0,0,0,0)',
                showlegend=False,
                fill='tonexty',
                fillcolor='rgba(0,100,80,0.2)',
                hovertemplate='Upper Bound: %{y:.2f}<extra></extra>'
            ))
            traces_for_series.append(len(fig.data) - 1)

            # Add forecast line
            fig.add_trace(go.Scatter(
                x=fcst_df['forecast_timestamp'],
                y=fcst_df['forecast_value'],
                name=f'Forecast: {series_name}',
                mode='lines',
                line=dict(color='green', dash='dot'),
                hovertemplate='Forecast: %{y:.2f}<extra></extra>'
            ))
            traces_for_series.append(len(fig.data) - 1)

            # Add history line
            fig.add_trace(go.Scatter(
                x=hist_df[timestamp_col],
                y=hist_df[data_col],
                name=f'History: {series_name}',
                mode='lines+markers',
                line=dict(color='blue'),
                marker={'size': 4},
                hovertemplate=f'{data_col}: %{{y:.2f}}<extra></extra>'
            ))
            traces_for_series.append(len(fig.data) - 1)

            all_traces.append(traces_for_series)

        # Create dropdown buttons for multiple time series
        buttons = []
        for i, series_id in enumerate(series_list):
            visibility = [False] * len(fig.data)
            for trace_index in all_traces[i]:
                visibility[trace_index] = True

            if id_cols:
                label = ', '.join([f"{series_id[col]}" for col in id_cols])
            else:
                label = 'Overall'

            buttons.append(dict(
                label=label,
                method='update',
                args=[{'visible': visibility}]
            ))

        # Set first series visible by default
        if fig.data:
            for trace_index in all_traces[0]:
                fig.data[trace_index].visible = True

        # Calculate date range for initial view
        max_date = df_horizon['forecast_timestamp'].max()
        min_date = df_history[timestamp_col].min()
        min_date_range = max_date - timedelta(days=180)
        if min_date_range < min_date:
            min_date_range = min_date

        # Update layout
        fig.update_layout(
            title_text=f'Time Series Forecast: {data_col}',
            template='plotly_white',
            height=600,
            hovermode="x unified",
            xaxis=dict(
                rangeslider=dict(visible=True),
                type='date',
                range=[min_date_range, max_date]
            ),
            yaxis=dict(title=data_col),
            updatemenus=[dict(
                active=0,
                buttons=buttons,
                direction="down",
                x=1.0,
                y=1.1,
                xanchor="right",
                yanchor="top"
            )] if len(series_list) > 1 else [],
            legend_title_text='Series'
        )

        # Save figure as an HTML artifact
        html_plot = fig.to_html(full_html=True)
        plot_blob = genai.types.Part.from_bytes(
            data=html_plot.encode('utf-8'),
            mime_type='text/html'
        )
        await tool_context.save_artifact(filename=artifact_key, artifact=plot_blob)

        return f"The forecast plot has been successfully generated and saved as the artifact '{artifact_key}'."

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"An unexpected error occurred: {e}"
