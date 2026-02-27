"""
Generate the JSON Schema for the BigQuery ARIMA flowchart example.

This script defines Pydantic models matching the structure of the
BQ ARIMA pipeline diagram and exports the schema to schema.json.

Diagram source:
    https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series
Image:
    https://docs.cloud.google.com/static/bigquery/images/BQ_ARIMA_diagram.png
"""

import json
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class ElementType(str, Enum):
    """Types of elements found in the BQ ARIMA pipeline diagram."""
    input = "input"                # Data inputs (cylinder shapes)
    process = "process"            # Processing steps (rectangles)
    intermediate = "intermediate"  # Intermediate data outputs (cylinder shapes)
    component = "component"        # Decomposed time series components (rectangles)
    output = "output"              # Final outputs (cylinder shapes)
    operator = "operator"          # Mathematical operators (e.g., aggregation circle)


class Phase(str, Enum):
    """Pipeline phases shown as labeled sections in the diagram."""
    preprocessing = "Preprocessing"
    modeling = "Modeling"
    decomposed = "Decomposed Time Series"
    output = "Output"


class FlowchartNode(BaseModel):
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display text from the diagram")
    element_type: ElementType = Field(..., description="Type of diagram element")
    phase: Optional[Phase] = Field(None, description="Pipeline phase this node belongs to")
    shape: Optional[str] = Field(None, description="Visual shape: rectangle, cylinder, circle")
    color: Optional[str] = Field(None, description="Fill color: blue, green, yellow, orange, gray")
    bq_function: Optional[str] = Field(None, description="Associated BigQuery ML function (e.g., ML.FORECAST)")
    description: Optional[str] = Field(None, description="Additional context about this node")
    bounding_box: Optional[list[int]] = Field(
        None,
        description="Region coordinates [y_min, x_min, y_max, x_max] normalized 0-1000"
    )


class EdgeType(str, Enum):
    """Types of connections in the diagram."""
    flow = "flow"          # Solid arrow — data flows forward
    feedback = "feedback"  # Dashed arrow — output fed back or referenced


class FlowchartEdge(BaseModel):
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node id")
    target: str = Field(..., description="Target node id")
    label: Optional[str] = Field(None, description="Edge label (e.g., 'Point Forecast')")
    edge_type: EdgeType = Field(EdgeType.flow, description="Arrow style: flow (solid) or feedback (dashed)")


class FlowchartGraph(BaseModel):
    diagram_type: str = Field(..., description="Type of diagram")
    nodes: list[FlowchartNode]
    edges: list[FlowchartEdge]
    metadata: Optional[dict] = None


if __name__ == "__main__":
    schema = FlowchartGraph.model_json_schema()
    with open("schema.json", "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Schema written to schema.json")
    print(f"  Node required fields: {FlowchartNode.model_json_schema().get('required', [])}")
    print(f"  Edge required fields: {FlowchartEdge.model_json_schema().get('required', [])}")
