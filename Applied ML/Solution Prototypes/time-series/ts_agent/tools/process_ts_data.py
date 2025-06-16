import json
from datetime import timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from google.adk import tools
from google import genai


from google.adk import tools

async def process_ts_data(
    artifact_key: str,
    tool_context: tools.ToolContext
) -> str:
    """
    Processes time-series data from an artifact, creates an interactive plot,
    and saves the plot as a new HTML artifact.

    This tool handles both historical data and forecast data. If forecast data
    is detected (via a 'type' column), it plots the historical trend, the
    forecasted values, and a shaded confidence interval.

    Args:
        artifact_key: The unique identifier for the artifact that was created
            by the `process_toolbox_output` callback. This key is typically
            provided to the agent in the modified response from the callback.
        tool_context: The execution context for the tool, automatically provided
            by the ADK framework. It is used here to access the `load_artifact`
            method.

    Returns:
        A success message confirming that the specified artifact was loaded
        and successfully converted into a Pandas DataFrame, including a list
    of the DataFrame's columns.
    """

    try:

        artifact = await tool_context.load_artifact(filename = artifact_key)
        data_string = artifact.text
        data = json.loads(data_string)
        df = pd.DataFrame(data)
        df['starttime'] = pd.to_datetime(df['starttime'])
        df.sort_values(by='starttime', inplace=True)
        df = df.fillna(np.nan).replace([np.nan], [None])

        # create plotly figure
        fig = go.Figure()

        # is this a forecast plot?
        is_forecast = 'type' in df.columns

        # Handle either a single overall series or multiple station series
        if 'start_station_name' not in df.columns:
            df['start_station_name'] = 'Overall'
        series_list = df['start_station_name'].unique().tolist()
        series_list.sort()

        # Store traces for visibility toggling
        all_traces = []

        for s_name in series_list:
            series_df = df[df['start_station_name'] == s_name].copy()
            traces_for_series = []

            # --- Plotting Logic ---
            if is_forecast:
                hist_df = series_df[series_df['type'] == 'history']
                fcst_df = series_df[series_df['type'] == 'forecast']

                # 1. Lower confidence bound (invisible, for filling)
                fig.add_trace(go.Scatter(
                    x=fcst_df['starttime'], y=fcst_df['pred_low'],
                    mode='lines', line_color='rgba(0,0,0,0)', showlegend=False
                ))
                traces_for_series.append(len(fig.data) - 1)

                # 2. Upper confidence bound (fills to lower bound)
                fig.add_trace(go.Scatter(
                    x=fcst_df['starttime'], y=fcst_df['pred_high'],
                    mode='lines', line_color='rgba(0,0,0,0)', showlegend=False,
                    fill='tonexty', fillcolor='rgba(0,100,80,0.2)'
                ))
                traces_for_series.append(len(fig.data) - 1)

                # 3. Forecast line
                fig.add_trace(go.Scatter(
                    x=fcst_df['starttime'], y=fcst_df['num_trips'],
                    name='Forecast', mode='lines', line=dict(color='green', dash='dot')
                ))
                traces_for_series.append(len(fig.data) - 1)
                
                # 4. Historical line
                fig.add_trace(go.Scatter(
                    x=hist_df['starttime'], y=hist_df['num_trips'],
                    name='History', mode='lines+markers', line=dict(color='blue'), marker={'size': 4}
                ))
                traces_for_series.append(len(fig.data) - 1)

            else: # Not a forecast, plot as before
                fig.add_trace(go.Scatter(
                    x=series_df['starttime'], y=series_df['num_trips'], name='num_trips',
                    mode='lines+markers', line={'width': 2}, marker={'size': 5}
                ))
                traces_for_series.append(len(fig.data) - 1)
            
            all_traces.append(traces_for_series)

        # --- Dropdown Button Logic ---
        buttons = []
        for i, s_name in enumerate(series_list):
            visibility = [False] * len(fig.data)
            for trace_index in all_traces[i]:
                visibility[trace_index] = True
            buttons.append(dict(label=s_name, method='update', args=[{'visible': visibility}]))

        # Set first series to be visible by default
        for trace_index in all_traces[0]:
            fig.data[trace_index].visible = True

        # --- Layout Updates ---
        max_date = df['starttime'].max()
        # Extend visible range to 180 days for forecasts
        min_date_range = max_date - timedelta(days=180 if is_forecast else 90)
        fig.update_layout(
            title_text='Daily Bike Trips' + (' with Forecast' if is_forecast else ''),
            template='plotly_white', height=600, hovermode="x unified",
            xaxis=dict(
                rangeslider=dict(visible=True), type='date', range=[min_date_range, max_date]
            ),
            yaxis=dict(title='Number of Trips'),
            updatemenus=[dict(
                active=0, buttons=buttons, direction="down",
                x=1.0, y=1.1, xanchor="right", yanchor="top"
            )],
            showlegend=is_forecast # Only show legend if there's a forecast
        )

        # buttons = []
        # # Add a trace for each series
        # for i, s_name in enumerate(series_list):
        #     series_df = df[df['start_station_name'] == s_name]
        #     fig.add_trace(
        #         go.Scatter(
        #             x=series_df['starttime'],
        #             y=series_df['num_trips'],
        #             name='num_trips',
        #             text=series_df['num_trips'],
        #             hoverinfo='name+x+text',
        #             mode='lines+markers',
        #             line={'width': 2},
        #             marker={'size': 5},
        #             visible=(i == 0) # Make first series visible by default
        #         )
        #     )

        # # Create a dropdown button for each series
        # for i, s_name in enumerate(series_list):
        #     visibility = [False] * len(series_list)
        #     visibility[i] = True
        #     button = dict(
        #         label=s_name,
        #         method='update',
        #         args=[{'visible': visibility}]
        #     )
        #     buttons.append(button)

        # # Update layout with dropdown, rangeslider, and styling
        # max_date = df['starttime'].max()
        # min_date_range = max_date - timedelta(days=90)
        # fig.update_layout(
        #     title_text='Daily Bike Trips',
        #     template='plotly_white',
        #     height=600,
        #     hovermode="x unified",
        #     xaxis=dict(
        #         rangeslider=dict(visible=True),
        #         type='date',
        #         range = [min_date_range, max_date]
        #     ),
        #     yaxis=dict(title='Number of Trips'),
        #     updatemenus=[dict(
        #         active=0,
        #         buttons=buttons,
        #         direction="down",
        #         x=1.0,
        #         y=1.1,
        #         xanchor="right",
        #         yanchor="top"
        #     )]
        # )

        # --- Save figure as an HTML artifact ---
        html_plot = fig.to_html(full_html = True)
        plot_artifact_key = f"plot-from-{artifact_key}"
        plot_blob = genai.types.Part.from_bytes(data = html_plot.encode('utf-8'), mime_type = 'text/html')
        await tool_context.save_artifact(filename = plot_artifact_key, artifact = plot_blob)

        return f"Successfully processed artifact '{artifact_key}'. A plot has been generated and saved as the artifact '{plot_artifact_key}'."

    except Exception as e:
        return f"An unexpected error occurred: {e}"