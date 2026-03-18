![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fimage-to-graph&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/image-to-graph/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/image-to-graph/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/image-to-graph/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/image-to-graph/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/image-to-graph/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
</table><br/><br/>

---
# Image to Graph

An [ADK](https://google.github.io/adk-docs/) agent that converts complex diagram images (flowcharts, electrical schematics, building plans, network diagrams, UML, etc.) into structured graph representations with nodes, edges, and attributes — then lets you ask questions about the results.

> **Why do this?** Diagrams encode rich structural information — components, connections, hierarchies, flows — but this information is trapped in pixels. By converting diagrams to structured graphs, you unlock programmatic analysis, comparison, validation, and integration with downstream systems. The agent uses an **iterative visual thinking approach**: analyze the full image, identify regions with bounding boxes, crop and re-examine at detail, then accumulate a graph incrementally.

The agent uses:
- **Gemini Vision API** — for image analysis and region examination via `google.genai`
- **OpenCV** — for deterministic CV preprocessing (shape detection, contour analysis) via `agent_cv_preprocess` subagent
- **Pillow** — for bounding box-based image cropping
- **PyMuPDF** — for PDF page rendering at high resolution
- **Pydantic** — for dynamic JSON Schema generation and validation
- **ADK Tool Context State** — for incremental graph accumulation across tool calls

Input sources: local file paths, `https://` URLs, `gs://` GCS paths, and PDF files (renders a selected page). See [Example Usage](#example-usage) for all three.

<table>
<tr>
<td align="center" width="33%"><b>Diagram Image</b></td>
<td align="center" width="34%"><b>Extracted Graph + Visualization</b></td>
<td align="center" width="33%"><b>Q&A Over Results</b></td>
</tr>
<tr>
<td align="center">
<a href="examples/bq-arima-flowchart/diagram.png"><img src="examples/bq-arima-flowchart/diagram.png" alt="Input diagram: BigQuery ARIMA pipeline flowchart" width="100%"></a>
</td>
<td align="center">
<a href="examples/bq-arima-flowchart/screenshots/image_to_graph.png"><img src="examples/bq-arima-flowchart/screenshots/image_to_graph.png" alt="Interactive visualization with linked image and graph panels" width="100%"></a>
</td>
<td align="center">
<a href="examples/bq-arima-flowchart/screenshots/graph_qa.png"><img src="examples/bq-arima-flowchart/screenshots/graph_qa.png" alt="Q&A agent answering questions about the extracted graph" width="100%"></a>
</td>
</tr>
<tr>
<td align="center"><sub>Input: any diagram image</sub></td>
<td align="center"><sub>agent_image_to_graph → interactive HTML with linked highlights</sub></td>
<td align="center"><sub>agent_graph_qa → ask about nodes, paths, and meaning</sub></td>
</tr>
</table>

> *Click any image to enlarge. Example uses the [BigQuery ARIMA_PLUS pipeline](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series) diagram.*

---
## Architecture

```
User provides image (local path, URL, or gs://...) + optional schema path
         │
         ▼
    ┌─────────────┐     ┌──────────────┐
    │  load_image  │     │ load_schema  │  (optional) Load target schema
    └──────┬──────┘     └──────┬───────┘
           │ Accepts: local files, https:// URLs,
           │ gs:// GCS paths, and PDF files (renders selected page)
           ▼                   │
    ┌───────────────────┐      │
    │ agent_cv_preprocess│  (optional) OpenCV contour detection + Gemini OCR
    └────────┬──────────┘  Assesses image → detects shapes → finds connections
             │             → labels elements → reports back. Results stored in
             ▼             state as context for semantic analysis tools.
    ┌──────────────┐
    │ analyze_image │  Full image → Gemini (TOOL_MODEL) → regions + bounding boxes
    └──────┬───────┘  Also detects: legend blocks, title/metadata panels,
           │          and multi-flow clusters
           │
           ├─── Flowcharts: Gemini's semantic regions used as-is
           │
           ├─── Schematics/circuits: Gemini's regions replaced with
           │    systematic grid cells (4×3 landscape / 3×4 portrait,
           │    5% overlap) for complete spatial coverage
           │
           ▼
    ┌───────────────────────────────┐
    │  For each region:             │  If legend/page_info regions found:
    │   crop_and_examine            │    → set_metadata(key="legend", ...)
    │   update_graph (batch nodes)  │    → set_metadata(key="page_info", ...)
    │   (adaptive zoom if complex)  │
    │   (detect groups if present)  │  Crop + Gemini → elements + confidence
    │   (schematic: exhaustive      │  (schema hints if input schema loaded)
    │    component enumeration)     │
    └──────────┬────────────────────┘
               ▼
    ┌──────────────────────────┐
    │  trace_connections       │  Full image + node positions → Gemini → edges + confidence
    │  update_graph            │  Also detects semantic cross-references:
    └──────────┬───────────────┘  same labels across flow clusters → reference edges
               ▼
    ┌──────────────────┐
    │ generate_schema  │  Infer JSON Schema (skipped if input schema loaded)
    │ validate_graph   │  Check structure + schema conformance + auto-correct bboxes
    └────────┬─────────┘  + detect flows (connected components via union-find)
             │            + auto-detect label-based cross-references
             ▼
    ┌────────────────────────┐
    │ generate_description   │  Gemini (TOOL_MODEL) → narrative description
    └────────┬───────────────┘  Flow-aware, metadata-aware, legend-aware
             ▼
    ┌────────────────────────┐
    │ generate_visualization │  Interactive HTML: description + image + graph
    └────────┬───────────────┘  + flow subgraphs + legend panel + page metadata
             ▼                  + cross-reference edge styling
    ┌────────────────┐
    │ export_result  │  Saves graph.json + schema.json + description.md as artifacts
    └────────┬───────┘       + writes all files to disk under examples/
             ▼
    examples/<source-folder>/
    ├── results-with-schema/     ← when input schema was loaded
    └── results-without-schema/  ← when no schema was provided
             │
             ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  Q&A handoff → agent_graph_qa                               │
    │  Agent suggests example questions, then transfers            │
    │  to the Q&A sub-agent on user request.                      │
    │  Shared session state — no file reload needed.              │
    └─────────────────────────────────────────────────────────────┘

    ── OR (standalone) ──

    User selects agent_graph_qa from the ADK dropdown
         │
         ▼
    ┌────────────────┐
    │ load_results   │  Reads graph.json + schema.json + description.md from a directory
    └────────┬───────┘
             ▼
    ┌────────────────┐
    │  get_context   │  Formats full graph data for Q&A
    └────────┬───────┘
             ▼
    Answer questions about nodes, edges, paths, schema, and diagram meaning
```

---
## Getting Started

### Google Cloud APIs

Enable the following APIs in your GCP project:

```bash
gcloud services enable \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    bigquerystorage.googleapis.com \
    storage.googleapis.com
```

| API | Purpose |
|-----|---------|
| [Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com) (`aiplatform.googleapis.com`) | Gemini model access via Vertex AI |
| [BigQuery API](https://console.cloud.google.com/apis/library/bigquery.googleapis.com) (`bigquery.googleapis.com`) | Agent analytics logging (bq_plugin) |
| [BigQuery Storage API](https://console.cloud.google.com/apis/library/bigquerystorage.googleapis.com) (`bigquerystorage.googleapis.com`) | Streaming writes for analytics |
| [Cloud Storage API](https://console.cloud.google.com/apis/library/storage.googleapis.com) (`storage.googleapis.com`) | GCS offloading for multimodal content |

### Authentication

```bash
# Login and set application default credentials
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### Other Requirements

- [Git](https://github.com/git-guides/install-git)
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (initialized via `gcloud init`)
- Python 3.13.3 (via [pyenv](https://github.com/pyenv/pyenv) or [uv](https://docs.astral.sh/uv/))
- A GCP project with billing enabled

### Installation

Clone the repo and install dependencies:

```bash
cd ~/repos  # Or your preferred location
git clone https://github.com/statmike/vertex-ai-mlops.git
cd 'vertex-ai-mlops/Applied ML/AI Agents/image-to-graph'
```

Set the Python version:

```bash
pyenv install --skip-existing 3.13.3
pyenv local 3.13.3
```

Install with [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended):

```bash
uv sync
```

<details>
<summary>Alternative: Poetry</summary>

```bash
poetry env use 3.13.3
poetry install
```

</details>

<details>
<summary>Alternative: pip with venv</summary>

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install google-adk google-genai google-cloud-storage pydantic pillow pymupdf opencv-python-headless python-dotenv
```

</details>

### Configuration

Edit the `.env` file with your GCP project details:

```bash
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STORAGE_BUCKET=gs://your-bucket

# Model Configuration
#AGENT_MODEL=gemini-2.5-flash
AGENT_MODEL=gemini-3-flash-preview
AGENT_MODEL_LOCATION=global  # Uncomment for preview models; overrides GOOGLE_CLOUD_LOCATION for the agent
#TOOL_MODEL=gemini-2.5-pro
TOOL_MODEL=gemini-3.1-pro-preview
TOOL_MODEL_LOCATION=global  # Uncomment for preview models; overrides GOOGLE_CLOUD_LOCATION for tool calls

# BigQuery Agent Analytics Plugin
BQ_DATASET_LOCATION=US
BQ_ANALYTICS_DATASET=applied_ml_image_to_graph
BQ_ANALYTICS_TABLE=agent_events
BQ_ANALYTICS_GCS_BUCKET=your-bucket-name
BQ_ANALYTICS_GCS_PATH=applied-ml/ai-agents/image-to-graph/bq_plugin
```

| Variable | Purpose | Code Default |
|----------|---------|--------------|
| `AGENT_MODEL` | Gemini model for the ADK agent (orchestration, tool selection) | `gemini-2.5-flash` |
| `AGENT_MODEL_LOCATION` | API endpoint location for `AGENT_MODEL`; overrides `GOOGLE_CLOUD_LOCATION` for the agent. Set for preview models (e.g., `global`). | *(unset)* |
| `TOOL_MODEL` | Gemini model for vision tools (`analyze_image`, `crop_and_examine`, `trace_connections`, `generate_description`) | `gemini-2.5-flash` |
| `TOOL_MODEL_LOCATION` | API endpoint location for `TOOL_MODEL`; overrides `GOOGLE_CLOUD_LOCATION` for tool calls. Set for preview models (e.g., `global`). | *(unset)* |

The `.env` file overrides these defaults. The example `.env` above shows preview models (`gemini-3-flash-preview`, `gemini-3.1-pro-preview`) with `global` endpoints — adjust to whichever models are available in your project.

### Running the Agent

Start the ADK web interface:

```bash
uv run adk web --reload
```

<details>
<summary>Alternative: Poetry / pip</summary>

```bash
# Poetry:
poetry run adk web --reload

# pip/venv (with .venv activated):
adk web --reload
```

</details>

Then open `http://localhost:8000` in your browser. Three agents appear in the agent dropdown:

| Agent | Purpose |
|-------|---------|
| `agent_image_to_graph` | Convert a diagram image into a structured graph. Accepts local files, URLs, GCS paths, and PDFs. Optionally delegates to `agent_cv_preprocess` for OpenCV-based shape detection. After export, suggests Q&A and can transfer to `agent_graph_qa`. |
| `agent_cv_preprocess` | CV preprocessing subagent — uses OpenCV to detect shapes, connections, and labels in structured diagrams. Called automatically by the main agent when appropriate; results enrich the semantic analysis. |
| `agent_graph_qa` | Ask questions about previously extracted graph results. Can load results from a directory on disk, or receive them via shared session state when transferred from `agent_image_to_graph`. |

---
## Example Usage

Examples are included in `examples/`. Results are always written to the `examples/` directory — for local files already under `examples/`, results go next to the source file; for URLs, GCS paths, or local files outside `examples/`, a new folder is created under `examples/` with a name derived from the source (e.g., `url-www-raspberrypi-org-raspberry-pi-schematics-r1-0` for a URL, `gcs-my-bucket-diagram` for GCS).

**BigQuery ARIMA Flowchart** (`examples/bq-arima-flowchart/`) — the BigQuery ML ARIMA pipeline diagram:

```
examples/bq-arima-flowchart/
├── diagram.png         # The ARIMA pipeline flowchart
├── schema.json         # Pydantic-generated JSON Schema
└── create_schema.py    # Script that defines models and generates schema.json
```

> **Image source:** [BigQuery ML `CREATE TIME SERIES` documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series) — diagram showing the ARIMA_PLUS pipeline stages from preprocessing through decomposition to forecasting.

**XKCD Flowcharts** (`examples/xkcd-flowchart/`) — the humorous "Flowcharts" comic that parodies decision-making diagrams with self-referential loops, electrical schematics, and a hidden golden spiral:

```
examples/xkcd-flowchart/
└── flowcharts.png      # The XKCD "Flowcharts" comic
```

> **Image source:** [XKCD #1488 "Flowcharts"](https://xkcd.com/1488/) by [Randall Munroe](https://xkcd.com), licensed under [CC BY-NC 2.5](https://creativecommons.org/licenses/by-nc/2.5/).

**Raspberry Pi Schematic** (URL-based PDF) — the original Raspberry Pi Model B Rev 1.0 hardware schematic, loaded directly from a URL as a PDF:

> **Image source:** [Raspberry Pi Schematics R1.0](https://www.raspberrypi.org/app/uploads/2012/04/Raspberry-Pi-Schematics-R1.0.pdf) — the official schematic for the original Raspberry Pi board.

> **Note:** Only attach **image files** through the ADK web UI. Schema files (`.json`) should be referenced by **file path** in your message text — the agent's `load_schema` tool reads them from disk. Gemini does not accept `application/json` as a file upload.

### Without a Schema (auto-generated)

The agent analyzes the image freely, builds the graph, and auto-generates a JSON Schema from the observed structure.

Copy/paste this prompt into the ADK web chat:

```
Analyze this flowchart: examples/bq-arima-flowchart/diagram.png
```

or

```
Analyze this chart: examples/xkcd-flowchart/flowcharts.png
```

Or try a **URL-based PDF** — the agent downloads the file, renders the specified page, and processes it like any other image:

```
Analyze this schematic: https://www.raspberrypi.org/app/uploads/2012/04/Raspberry-Pi-Schematics-R1.0.pdf
```

The agent will:
1. Load and validate the image (from local path, URL, or GCS — renders PDF pages at high resolution)
2. Optionally delegate to `agent_cv_preprocess` for OpenCV-based shape/contour detection on clean, structured diagrams
3. Analyze the full image to detect regions, bounding boxes, legend blocks, title/metadata panels, and multi-flow clusters. For schematics/circuits, Gemini's regions are replaced with systematic grid cells for complete spatial coverage.
4. Crop and examine each region in detail (with confidence scoring, adaptive zoom for dense areas, and group detection for visual boundaries). For schematics, all grid cells are examined with exhaustive component enumeration guidance.
5. Extract page-level metadata (legend, title, author, date, version) via `set_metadata` — these are stored in `graph.metadata`, not as nodes
6. Build a graph with nodes and bounding boxes (including confidence levels and parent/child grouping). Duplicate nodes (same label + overlapping bbox) and duplicate edges (same source/target pair) are automatically skipped.
7. Trace connections across the full image for edge detection with confidence, including semantic cross-references between flow clusters
8. Auto-generate a JSON Schema from the graph structure
9. Validate the graph — auto-correct bounding boxes (inversion, axis swap, oversized, schematic-specific normalization), detect multi-flow diagrams (connected components), suggest label-based cross-references, flag low-confidence elements
10. Generate a comprehensive narrative description (flow-aware, metadata-aware, legend-aware)
11. Generate an interactive `visualization.html` with description, flow subgraphs, legend panel, page metadata, cross-reference edge styling, and searchable graph JSON
12. Export `graph.json` + `schema.json` + `description.md` as artifacts and write all files to `examples/<source-folder>/results-without-schema/`
13. Suggest example Q&A questions about the diagram — if you ask one, the agent transfers to `agent_graph_qa` which answers using the shared session state

### With a Schema (user-provided)

Provide a JSON Schema by file path and the agent will ensure the graph conforms to it — including domain-specific fields like `phase`, `element_type`, and `bq_function` for every node.

Copy/paste this prompt into the ADK web chat:

```
Analyze this flowchart: examples/bq-arima-flowchart/diagram.png
Use this schema: examples/bq-arima-flowchart/schema.json
```

The agent will:
1. Load and validate the image (from local path, URL, or GCS — renders PDF pages at high resolution)
2. Load the target schema and report its required fields (`id`, `label`, `element_type` for nodes)
3. Optionally delegate to `agent_cv_preprocess` for OpenCV-based shape/contour detection
4. Analyze the image, detecting regions, legend blocks, metadata panels, and multi-flow clusters. For schematics/circuits, systematic grid cells replace Gemini's regions.
5. Build the graph conforming to the schema (with bounding boxes, confidence, parent/child grouping, and page metadata via `set_metadata`). Duplicate nodes and edges are automatically skipped.
6. `update_graph` will hint at any missing required/optional fields from the schema
7. Trace connections across the full image for edge detection with confidence, including semantic cross-references
8. Validate the graph against the schema — auto-correct bounding boxes (inversion, axis swap, oversized, schematic-specific normalization), detect multi-flow diagrams, compute group bounding boxes, report missing fields, type mismatches, low-confidence warnings
9. Generate a comprehensive narrative description (flow-aware, metadata-aware, legend-aware)
10. Generate an interactive `visualization.html` with description, flow subgraphs, legend panel, page metadata, cross-reference styling, confidence indicators, and searchable graph JSON
11. Export `graph.json` + `schema.json` (the user-provided schema) + `description.md` as artifacts and write all files to `examples/<source-folder>/results-with-schema/`
12. Suggest example Q&A questions about the diagram — if you ask one, the agent transfers to `agent_graph_qa` which answers using the shared session state

The included schema defines domain-specific enums and fields tailored to this diagram:
- **`element_type`**: `input`, `process`, `intermediate`, `component`, `output`, `operator`, `group`
- **`phase`**: `Preprocessing`, `Modeling`, `Decomposed Time Series`, `Output`
- **`edge_type`**: `flow` (solid arrow), `feedback` (dashed arrow)
- **`bq_function`**: associated BigQuery ML function (e.g., `ML.FORECAST`)
- **`parent_id`**: links a node to its parent group node (for nesting)

### Creating Your Own Schema with Pydantic

The example schema was generated by `examples/bq-arima-flowchart/create_schema.py`. To create your own, define Pydantic models for your diagram type, then export the JSON Schema. Required fields use `...` (Ellipsis), optional fields use `None` as default:

```python
import json
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

class ElementType(str, Enum):
    input = "input"                # Data inputs (cylinder shapes)
    process = "process"            # Processing steps (rectangles)
    intermediate = "intermediate"  # Intermediate data outputs
    component = "component"        # Decomposed components
    output = "output"              # Final outputs
    operator = "operator"          # Mathematical operators (e.g., aggregation circle)
    group = "group"                # Visual grouping boundary (dashed boxes, labeled sections)

class Phase(str, Enum):
    preprocessing = "Preprocessing"
    modeling = "Modeling"
    decomposed = "Decomposed Time Series"
    output = "Output"

class FlowchartNode(BaseModel):
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display text from the diagram")
    element_type: ElementType = Field(..., description="Type of diagram element")
    phase: Optional[Phase] = Field(None, description="Pipeline phase this node belongs to")
    shape: Optional[str] = Field(None, description="Visual shape: rectangle, cylinder, circle, group_rectangle")
    color: Optional[str] = Field(None, description="Fill color: blue, green, yellow, orange, gray")
    bq_function: Optional[str] = Field(None, description="Associated BigQuery ML function (e.g., ML.FORECAST)")
    description: Optional[str] = Field(None, description="Additional context about this node")
    bounding_box: Optional[list[int]] = Field(None, description="[y_min, x_min, y_max, x_max] normalized 0-1000")
    parent_id: Optional[str] = Field(None, description="ID of the parent group node (for nesting)")

class EdgeType(str, Enum):
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

# Generate and save the schema
schema = FlowchartGraph.model_json_schema()
with open("schema.json", "w") as f:
    json.dump(schema, f, indent=2)
```

Pydantic's `model_json_schema()` produces a standard JSON Schema with `$defs` and `$ref` references — fully supported by the agent's tools. Run with:

```bash
uv run python examples/bq-arima-flowchart/create_schema.py
```

### Example Results

Running the agent on `examples/bq-arima-flowchart/diagram.png` — once without a schema and once with the included `schema.json` — produces the following result directories:

```
examples/bq-arima-flowchart/
├── diagram.png
├── schema.json
├── create_schema.py
├── results-without-schema/
│   ├── graph.json
│   ├── schema.json          ← auto-generated from graph structure
│   ├── description.md
│   └── visualization.html
└── results-with-schema/
    ├── graph.json
    ├── schema.json           ← copy of the user-provided input schema
    ├── description.md
    └── visualization.html
```

Running the agent on the Raspberry Pi schematic URL creates a new folder under `examples/`:

```
examples/url-www-raspberrypi-org-raspberry-pi-schematics-r1-0/
└── results-without-schema/
    ├── graph.json
    ├── schema.json
    ├── description.md
    └── visualization.html
```

Files are replaced on each run (no accumulation). The same artifacts are also saved via the ADK artifact system.

**Output directory resolution:**
- **Local files under `examples/`** — results go next to the source file (e.g., `examples/bq-arima-flowchart/results-without-schema/`)
- **URLs** — `examples/url-{hostname}-{filename}/` (e.g., `url-www-raspberrypi-org-raspberry-pi-schematics-r1-0`)
- **GCS paths** — `examples/gcs-{bucket}-{filename}/` (e.g., `gcs-my-bucket-diagram`)
- **Local files outside `examples/`** — `examples/local-{filename}/`

**View the interactive visualizations directly in your browser:**

| Run | Visualization | Graph | Description |
|-----|---------------|-------|-------------|
| BQ ARIMA (without schema) | [**visualization.html**](https://htmlpreview.github.io/?https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/image-to-graph/examples/bq-arima-flowchart/results-without-schema/visualization.html) | [graph.json](examples/bq-arima-flowchart/results-without-schema/graph.json) | [description.md](examples/bq-arima-flowchart/results-without-schema/description.md) |
| BQ ARIMA (with schema) | [**visualization.html**](https://htmlpreview.github.io/?https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/image-to-graph/examples/bq-arima-flowchart/results-with-schema/visualization.html) | [graph.json](examples/bq-arima-flowchart/results-with-schema/graph.json) | [description.md](examples/bq-arima-flowchart/results-with-schema/description.md) |
| XKCD (without schema) | [**visualization.html**](https://htmlpreview.github.io/?https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/image-to-graph/examples/xkcd-flowchart/results-without-schema/visualization.html) | [graph.json](examples/xkcd-flowchart/results-without-schema/graph.json) | [description.md](examples/xkcd-flowchart/results-without-schema/description.md) |
| Raspberry Pi schematic (URL, PDF) | [**visualization.html**](https://htmlpreview.github.io/?https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/image-to-graph/examples/url-www-raspberrypi-org-raspberry-pi-schematics-r1-0/results-without-schema/visualization.html) | [graph.json](examples/url-www-raspberrypi-org-raspberry-pi-schematics-r1-0/results-without-schema/graph.json) | [description.md](examples/url-www-raspberrypi-org-raspberry-pi-schematics-r1-0/results-without-schema/description.md) |

> The visualization links use [htmlpreview.github.io](https://htmlpreview.github.io) to render the self-contained HTML files directly from GitHub — no setup required. Each visualization embeds the source image as base64, includes interactive hover/click highlighting, group bounding boxes, flow subgraphs, a searchable graph JSON viewer, a recreated Mermaid diagram (with subgraphs for groups and flows), legend and page metadata panels, and the schema.

**What's different between the two runs?**

- **Without schema**: the agent freely discovers diagram elements and auto-generates a generic schema from the observed structure. Node attributes reflect what was visually detected.
- **With schema**: the agent conforms to the provided schema's field definitions (`element_type`, `phase`, `bq_function`, `edge_type`, etc.), producing richer domain-specific annotations and validated output.

### Q&A: Asking Questions About Results

After `agent_image_to_graph` finishes exporting, it suggests example questions about the diagram and offers to hand off to the Q&A agent. You can also use `agent_graph_qa` directly by selecting it from the ADK dropdown — useful for exploring results from a previous session without re-running the extraction pipeline.

**As a sub-agent** (continued session — no prompt needed, the agent transfers automatically):

After export completes, the agent suggests questions like:
- "What processing steps happen between the input time series and the modeling phase?"
- "Which nodes feed into the Aggregation operator?"
- "What is the path from Input Time Series to Forecasted Time Series?"

Ask any question and the agent transfers to `agent_graph_qa`, which answers using the graph, schema, and description already in session state.

**Standalone** (select `agent_graph_qa` from the dropdown):

Copy/paste this prompt into the ADK web chat:

```
Load results from: examples/bq-arima-flowchart/results-with-schema
```

The agent will:
1. Load `graph.json`, `schema.json`, and `description.md` from the directory
2. Suggest 3-5 example questions based on the actual graph content
3. Answer structural questions (paths, neighbors, connectivity) by reasoning over the edges
4. Answer semantic questions (purpose, meaning) using the description and node attributes
5. Answer schema questions (required fields, allowed types) from the schema

---
## Graph Output Format

The exported `graph.json` follows this structure:

```json
{
  "diagram_type": "flowchart",
  "nodes": [
    {
      "id": "node_1",
      "label": "Start",
      "element_type": "terminal",
      "shape": "oval",
      "bounding_box": [50, 400, 120, 600],
      "confidence": "high",
      "flow_id": "flow_1"
    },
    {
      "id": "node_2",
      "label": "Process Data",
      "element_type": "process",
      "shape": "rectangle",
      "bounding_box": [200, 350, 300, 650],
      "confidence": "medium",
      "description": "Transforms input data",
      "flow_id": "flow_1"
    },
    {
      "id": "group_preprocessing",
      "label": "Preprocessing",
      "element_type": "group",
      "shape": "group_rectangle",
      "bounding_box": [30, 330, 320, 670],
      "confidence": "high",
      "flow_id": "flow_1"
    },
    {
      "id": "node_3",
      "label": "Clean Data",
      "element_type": "process",
      "shape": "rectangle",
      "bounding_box": [150, 380, 220, 620],
      "confidence": "high",
      "parent_id": "group_preprocessing",
      "flow_id": "flow_1"
    },
    {
      "id": "node_4",
      "label": "Subsystem Detail",
      "element_type": "process",
      "shape": "rectangle",
      "bounding_box": [600, 100, 700, 300],
      "confidence": "high",
      "flow_id": "flow_2"
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "label": null,
      "edge_type": "flow",
      "confidence": "high"
    },
    {
      "id": "edge_ref_1",
      "source": "node_2",
      "target": "node_4",
      "label": "cross-reference",
      "edge_type": "reference",
      "confidence": "medium"
    }
  ],
  "flows": [
    {
      "id": "flow_1",
      "label": "Flow 1",
      "node_ids": ["group_preprocessing", "node_1", "node_2", "node_3"]
    },
    {
      "id": "flow_2",
      "label": "Flow 2",
      "node_ids": ["node_4"]
    }
  ],
  "metadata": {
    "source_file": "/path/to/image.png",
    "image_width": 1920,
    "image_height": 1080,
    "status": "complete",
    "page_info": {
      "title": "Data Processing Pipeline v2.1",
      "author": "Jane Doe",
      "date": "2025-03-15",
      "version": "2.1"
    },
    "legend": [
      {"symbol": "dashed line", "meaning": "optional dependency"},
      {"symbol": "red fill", "meaning": "critical path"}
    ]
  }
}
```

Key fields:
- **`bounding_box`**: `[y_min, x_min, y_max, x_max]` on a normalized 0–1000 scale. Required for visualization overlays.
- **`parent_id`**: Links a node to its parent group node for hierarchical nesting.
- **`confidence`**: `high`, `medium`, or `low` — set during extraction by Gemini.
- **`shape: "group_rectangle"`**: Marks a node as a visual grouping boundary (dashed box, labeled section).
- **`flow_id`**: Assigned automatically by `validate_graph` when multiple disconnected flows are detected. Each node belongs to exactly one flow.
- **`flows`**: Array of connected components, each with an `id`, `label`, and list of `node_ids`. Only present when 2+ flows are detected.
- **`edge_type: "reference"`**: Cross-reference edges linking the same logical entity across different flows. Rendered with dashed purple styling in the visualization.
- **`metadata.page_info`**: Page-level metadata (title, author, date, version) extracted from title blocks or metadata panels in the diagram. Displayed in the visualization header.
- **`metadata.legend`**: Legend entries mapping symbols to meanings, extracted from legend blocks in the diagram. Displayed as a legend panel in the visualization.

A `schema.json` is **always** exported alongside the graph — either the user-provided input schema or an auto-generated schema inferred from the graph structure. A `description.md` is also exported when a description has been generated. All files are saved both as ADK artifacts and written to disk under the `examples/` directory (see [Output directory resolution](#example-results)).

---
## Interactive Visualization

The agent generates an interactive HTML visualization (`visualization.html` artifact) that lets you visually verify the extracted graph against the source image.

**Features:**
- **Two-panel layout**: source image on the left, graph details on the right
- **Page metadata header**: if page-level metadata was extracted (title, author, date, version), it's displayed in the header bar alongside the diagram type badge
- **Generated description**: comprehensive narrative description of the diagram shown at the top of the graph panel — flow-aware, metadata-aware, and legend-aware
- **Legend panel**: if legend entries were extracted from the diagram, they're rendered as a styled section between the description and the node list
- **Linked highlighting**: hover or click a node in either panel to highlight its bounding box on the image AND its card in the graph panel. Hover also highlights the corresponding schema section.
- **Edge tracing**: hover an edge to highlight both its source and target nodes on the image
- **Cross-reference edges**: edges with `edge_type: "reference"` are rendered with dashed purple styling in both the edge card list and the Mermaid diagram, visually distinguishing them from regular flow edges
- **Group bounding boxes**: group nodes render as dashed purple outlines behind regular nodes, showing visual containment
- **Flow subgraphs**: when multiple independent flows are detected, the Mermaid diagram wraps each flow's nodes in a `subgraph` block. Groups within flows are nested subgraphs.
- **Schema viewer**: collapsible section with split Node Definition and Edge Definition blocks, linked to node/edge highlighting
- **Graph JSON viewer**: collapsible, searchable section showing the full graph data. Type to search with match highlighting, Enter/Shift+Enter to cycle through matches.
- **Mermaid diagram**: recreated flowchart with `subgraph` blocks for group nodes and flow clusters, rendered via Mermaid.js
- **Resizable panels**: drag the divider between panels to adjust the layout
- **Self-contained**: the HTML file embeds the image as base64 — no external dependencies, works offline

For the visualization to work, nodes must include a `bounding_box` field with `[y_min, x_min, y_max, x_max]` coordinates (normalized 0–1000 scale). The agent is instructed to always include this when adding nodes.

### Confidence Scoring

All Gemini-backed tools (`crop_and_examine`, `trace_connections`) return per-element confidence levels (`high`, `medium`, `low`). Confidence is carried through the pipeline:

- **Extraction**: Each node and edge gets a confidence level during examination and edge tracing
- **Graph storage**: Confidence is stored as a field on each node/edge via `update_graph`
- **Validation**: `validate_graph` flags low-confidence nodes and edges as warnings
- **Visualization**: Confidence-aware indicators on node and edge cards — green (high), yellow (medium), red (low). Low-confidence edges get a dashed border

### Adaptive Zoom

When `crop_and_examine` detects a high-complexity region (many overlapping elements, small text), it returns suggested sub-regions for closer examination. The agent can then re-examine those sub-regions at finer granularity (limited to 3 additional calls for flowcharts) to improve extraction quality in dense areas.

### Schematic-Specific Workflow

When `analyze_image` detects a schematic or circuit diagram, the agent switches to a grid-based extraction workflow designed for dense, spatially uniform diagrams:

1. **Grid generation**: Gemini's semantic regions are replaced with systematic grid cells — 4 columns x 3 rows for landscape images, 3 x 4 for portrait — in the normalized 0-1000 coordinate space. Each cell has 5% overlap with its neighbors to catch components at cell boundaries.

2. **Exhaustive examination**: The agent examines **all** grid cells (the 3-call sub-region budget does not apply to grid cells). Each `crop_and_examine` call receives `SCHEMATIC_CROP_GUIDANCE` (from `prompts.py`) instructing Gemini to enumerate every component symbol, use reference designators as element IDs, provide tight bounding boxes around component symbols (not wire traces), and extract component values.

3. **Automatic deduplication**: Components appearing in overlapping grid cells produce duplicate node IDs. `update_graph` handles this automatically:
   - **ID dedup**: Nodes with an existing ID are silently skipped.
   - **Label + bbox dedup**: Nodes with the same label and overlapping bounding box (IoU > 0.5) are skipped even if the ID differs.
   - **Grid suffix stripping**: For schematics, `normalize_node_id()` (from `util_diagram_type.py`) strips `_r\d+_c\d+` suffixes that the agent may append (e.g., `C92_r1_c2` → `C92`), ensuring the base reference designator is used for dedup.
   - **Edge dedup**: Edges with the same `(source, target)` pair as an existing edge are skipped.

4. **Schematic-specific validation**: `validate_graph` uses a tighter oversized bbox threshold for schematics (5% vs 10% for other types, configured via `DIAGRAM_TYPE_CONFIG` in `config.py`) and normalizes extreme aspect-ratio bboxes (wire-trace bboxes where Gemini followed a connection path instead of the component footprint).

This approach typically extracts 50-70+ nodes from a single schematic page, compared to ~9 conceptual nodes from the non-grid workflow.

### Duplicate Detection

`update_graph` automatically prevents duplicate entries:

- **Node ID dedup**: If a node with the same `id` already exists, the new node is skipped.
- **Node label + bbox dedup**: If a node with the same label (case-insensitive) and overlapping bounding box (IoU > 0.5) exists under a different ID, the new node is skipped. This catches cases where the same component is identified with different IDs from adjacent grid cells or repeated examinations.
- **Edge source/target dedup**: If an edge with the same `(source, target)` pair already exists, the new edge is skipped (regardless of edge ID). Reverse direction (`target → source`) is treated as a different connection.

### Node Grouping and Nesting

Diagrams often contain visual groupings — dashed boundary boxes, labeled sections, swim lanes — that represent logical containment. The agent detects these and represents them as group nodes:

- **Group nodes** have `shape: "group_rectangle"` and `element_type: "group"` with a label (the section title).
- **Child nodes** set `parent_id` pointing to their group node's `id`.
- **Group bounding boxes** are auto-computed from children during validation (with padding), so the agent doesn't need to get them exactly right.
- **Visualization** renders groups as dashed purple outlines behind regular nodes.
- **Mermaid diagrams** use `subgraph` blocks for groups, nesting children inside.

Groups don't require edges unless there are explicit connections between group boundaries.

### Bounding Box Auto-Correction

Four levels of bounding box correction run automatically during `validate_graph`:

1. **Coordinate inversion** (`normalize_bbox` in `util_bbox.py`): Gemini sometimes returns coordinates with min > max on one or both axes (e.g., `{"top": 500, "bottom": 100}`). `normalize_bbox()` swaps each axis pair so that min ≤ max, and clamps all values to the valid 0-1000 range. This runs at every storage and usage boundary (add/update node, crop, analyze), so all downstream code always receives valid boxes. Corrections are detected by `detect_bbox_corrections()` (also in `util_bbox.py`) which compares raw vs normalized values and records which axes were inverted and whether clamping was needed. Corrections are tracked in `tool_context.state["bbox_corrections"]` and captured as `STATE_DELTA` events for BQ analytics observability (see `bq_analytics.ipynb`).

2. **Axis swap detection** (`validate_graph`): Gemini sometimes returns bounding box coordinates with x and y axes swapped. The validator detects and corrects this using three complementary signals:
   - **Element aspect ratios**: For each non-group node, computes the pixel-space aspect ratio under both interpretations (`[y,x,y,x]` vs `[x,y,x,y]`). If the swapped interpretation produces ratios measurably closer to 1.0 (>20% improvement in median), swap is triggered.
   - **Group extreme ratios**: Group nodes span multiple children and have large x/y differences. When ≥2 groups have physically implausible pixel ratios (>7:1) under normal interpretation but reasonable ones after swap, this triggers correction even when individual elements are nearly square. This catches the common case where the LLM confuses `top/left` semantics on landscape images. A false-positive guard ensures the group signal only fires when the element signal at least leans toward swap — preventing incorrect swaps on diagrams with legitimately wide horizontal groups.
   - **Content-based verification**: When the heuristic signals are inconclusive (e.g., schematics with small near-square components on non-square images), the validator samples actual pixel content from the source image as ground truth. For up to 12 bbox centers, it compares darkness at the normal vs swapped pixel positions — if ≥70% of samples find more diagram content (non-white pixels) at the swapped position, swap is triggered. This signal is blocked when elements strongly oppose swap, preventing false positives on correctly oriented diagrams.
   - Swap corrections are tracked in `bbox_corrections` state alongside individual inversions.

3. **Schematic aspect-ratio normalization** (`validate_graph` → `fix_schematic_bboxes` in `util_bbox.py`): For schematics, Gemini sometimes follows wire traces instead of component footprints, producing extremely elongated bboxes (aspect ratio > 8:1). These are shrunk to component-sized square regions centered on the bbox centroid, using the geometric mean of the original dimensions.

4. **Oversized bbox guard** (`validate_graph` → `fix_oversized_bboxes` in `util_bbox.py`): Non-group nodes with problematic bboxes are shrunk to the median size of normal components. Three independent conditions trigger the fix:
   - **Excessive area**: covering more than a threshold fraction of the image area (5% for schematics, 10% for other types, configured via `DIAGRAM_TYPE_CONFIG` in `config.py`).
   - **Extreme aspect ratio**: ratio > 8:1 — catches extremely elongated bboxes (e.g., a wire trace) that may have small area but are clearly wrong for a node.
   - **Outlier single dimension**: `max(height, width) > min(350, 4 × median_side)` — catches nodes spanning >35% of the image on a single axis even when area and ratio pass.

Level 1 runs before levels 2-4, ensuring all subsequent corrections operate on valid (non-inverted) boxes. Levels 2-4 run in order during validation, before group bounding box auto-computation, so group boxes inherit fully corrected child coordinates.

### Validation Checks

Beyond auto-correction, `validate_graph` runs several quality checks that produce warnings:

- **Degenerate bboxes**: Nodes with zero height (`y_min == y_max`) or zero width (`x_min == x_max`) are flagged. Near-zero area bboxes (width or height < 3 units in 0-1000 scale) are also warned about.
- **Overlapping bboxes**: For each pair of non-group nodes, if one bbox contains >70% of the other (by area), a warning is emitted. This catches cases where the LLM places two components at the same position.
- **Child containment**: Child nodes with `parent_id` set to a group are checked to ensure their bbox falls inside the parent group's bbox. Children entirely outside their parent are warned about.
- **Self-loop edges**: Edges where `source == target` are flagged as warnings.
- **Disconnected nodes**: Nodes with no incoming or outgoing edges are warned about.

### Description Artifact

`export_result` saves a `description.md` artifact alongside `graph.json` and `schema.json`. This contains the narrative description generated by `generate_description`, providing a human-readable summary of the diagram's structure and content.

### CV Preprocessing (`agent_cv_preprocess`)

For clean, structured diagrams (flowcharts, schematics with distinct shapes and straight-line connections), the main agent can optionally delegate to `agent_cv_preprocess` before semantic analysis. This subagent uses deterministic OpenCV techniques — contour detection, line finding, shape classification — to detect visual elements, then labels them with Gemini OCR. The results are stored in state as context that enriches the subsequent `analyze_image`, `crop_and_examine`, and `trace_connections` calls. During validation, CV elements can also be matched to graph nodes (via label similarity + IoU + centroid proximity scoring in `util_bbox.py`) to nudge bounding boxes to pixel-precise positions.

The CV subagent workflow:
1. **`assess_image`** — Computes contrast ratio, edge density, noise level, and color distribution. Returns suitability level (`high`, `medium`, `low`) and recommended detection parameters.
2. **`detect_elements`** — Applies adaptive thresholding, morphological closing, and contour detection. Classifies shapes (triangle, rectangle, pentagon, hexagon, circle) and returns normalized bounding boxes.
3. **`detect_connections`** — Finds lines and arrows between detected elements.
4. **`label_elements`** — Sends image + bounding boxes to Gemini for OCR text extraction and semantic labeling.
5. **`report_results`** — Reports back to the main agent with status (`complete`, `partial`, or `skipped`).

If suitability is `low` (hand-drawn, photographic, or artistic diagrams), the subagent skips detection and reports back immediately — the main agent falls back to pure Gemini-based analysis.

### Multi-Flow Awareness

Diagrams often contain **multiple independent flows** on a single page (e.g., a main pipeline and a subsystem detail), **page-level metadata** (title, author, date, version), and **legends** (symbol-to-meaning mappings). The agent recognizes and represents all of these:

**Flow detection**: `validate_graph` computes connected components using a union-find algorithm. Nodes connected by edges or by `parent_id` grouping are unified into the same flow. When 2+ flows are detected:
- Each flow is stored in `graph.flows` with an `id`, `label`, and list of `node_ids`
- Each node gets a `flow_id` attribute
- The "Disconnected nodes" warning is replaced with an informational "Diagram contains N distinct flows" note

**Cross-reference detection**: The validator scans for nodes in different flows that share identical labels, suggesting they represent the same logical entity. A warning prompts the agent to add `reference` edges. The `trace_connections` prompt also instructs Gemini to look for semantic cross-references (shared labels, off-page connectors, "see subsystem X" annotations) and emit edges with `edge_type: "reference"`.

**Page metadata and legends**: The `analyze_image` prompt instructs Gemini to detect legend blocks (`element_type: "legend"`) and title/metadata panels (`element_type: "page_info"`). The agent stores these via `update_graph`'s `set_metadata` operation rather than adding them as diagram nodes. This metadata flows through to the description, visualization, and exported graph JSON.

---
## Tools Reference

| Tool | Purpose |
|------|---------|
| `load_image` | Load image from local path, URL (`https://`), or GCS (`gs://`). Validates with Pillow. Renders PDF pages at high resolution via PyMuPDF. |
| `load_schema` | Load a JSON Schema from file to use as the target structure for graph construction |
| `analyze_image` | Full image analysis via Gemini (`TOOL_MODEL`) — diagram type, regions, bounding boxes. Detects legend blocks, title/metadata panels, and multi-flow clusters. For schematics/circuits, replaces Gemini's regions with systematic grid cells (4x3 landscape, 3x4 portrait, 5% overlap) for complete spatial coverage. |
| `crop_and_examine` | Crop a region and examine it in one call via Gemini (`TOOL_MODEL`) — labels, symbols, attributes, external labels, complexity, confidence; detects group boundaries; suggests sub-regions for adaptive zoom. For schematics, injects exhaustive component enumeration guidance (`SCHEMATIC_CROP_GUIDANCE` from `prompts.py`). |
| `trace_connections` | Dedicated edge detection — sends full image + all node positions to Gemini (`TOOL_MODEL`) for a cross-region edge-finding pass with confidence. Also detects semantic cross-references (shared labels, off-page connectors) as `reference` edges. |
| `update_graph` | Batch add/update nodes and edges in one call (with schema conformance hints). Automatically skips duplicate nodes (same ID, or same label + overlapping bbox via IoU > 0.5) and duplicate edges (same source/target pair). For schematics, strips grid-cell suffixes from node IDs (e.g., `C92_r1_c2` → `C92`) via `normalize_node_id()`. Also supports `set_metadata` for storing page info and legend entries. |
| `get_graph` | Retrieve current graph state for progress review |
| `generate_schema` | Infer JSON Schema from observed graph attributes — includes `flows`, structured `metadata` (page_info, legend) properties (skipped if input schema loaded) |
| `validate_graph` | Validate graph structure and schema conformance. Auto-corrects bounding boxes (inversion, axis swap, schematic aspect-ratio normalization, oversized guard with diagram-type-specific thresholds from `DIAGRAM_TYPE_CONFIG`). Computes group bounding boxes, detects multi-flow diagrams (connected components via union-find), assigns `flow_id` to nodes, suggests label-based cross-references. Optionally refines bboxes from CV preprocessing data. |
| `generate_description` | Generate a narrative description via Gemini (`TOOL_MODEL`) — flow-aware, metadata-aware, legend-aware |
| `generate_visualization` | Create interactive HTML with description + image + graph, flow subgraphs, legend panel, page metadata header, cross-reference edge styling, confidence indicators, schema viewer, searchable graph JSON, Mermaid recreation; writes to disk |
| `export_result` | Save final `graph.json` + `schema.json` + `description.md` as artifacts; writes all files to disk under `examples/` |

### CV Preprocessing Tools (`agent_cv_preprocess`)

| Tool | Purpose |
|------|---------|
| `assess_image` | Assess image suitability for CV preprocessing — contrast ratio, edge density, noise level, color distribution → suitability level and recommended parameters |
| `detect_elements` | OpenCV contour detection — adaptive thresholding, morphological closing, shape classification (triangle, rectangle, pentagon, hexagon, circle), normalized bounding boxes |
| `detect_connections` | Find lines and arrows between detected elements using line detection |
| `label_elements` | Send image + bounding boxes to Gemini for OCR text extraction and semantic labeling |
| `report_results` | Report detection results back to the main agent with status (`complete`, `partial`, `skipped`) |

### Q&A Tools (`agent_graph_qa`)

| Tool | Purpose |
|------|---------|
| `load_results` | Load `graph.json`, `schema.json`, and `description.md` from a results directory into session state (standalone mode) |
| `get_context` | Retrieve the full graph context — nodes, edges, schema, description — formatted for Q&A reasoning |

---
## Agent Analytics

This agent logs events to BigQuery using the [BigQuery Agent Analytics Plugin](https://google.github.io/adk-docs/observability/bigquery-agent-analytics/). The plugin is built into the agent at `agent_image_to_graph/bq_plugin.py`.

### Auto-Setup

**No manual setup required.** The agent automatically checks for and creates the BigQuery dataset and table on first run. Just configure your `.env` and start the agent — the BQ resources are provisioned automatically.

### Configuration

Analytics settings in `.env`:

```bash
BQ_DATASET_LOCATION=US
BQ_ANALYTICS_DATASET=applied_ml_image_to_graph
BQ_ANALYTICS_TABLE=agent_events
BQ_ANALYTICS_GCS_BUCKET=your-bucket-name
BQ_ANALYTICS_GCS_PATH=applied-ml/ai-agents/image-to-graph/bq_plugin
```

### Dual-Model Token Tracking

The agent uses two models with different tracking mechanisms:

| Model Role | Config | Tracking |
|---|---|---|
| **Agent (orchestration)** | `AGENT_MODEL` | Captured automatically via `LLM_RESPONSE` events |
| **Tool (vision/analysis)** | `TOOL_MODEL` | Tracked via `tool_context.state["tool_llm_usage"]` → `STATE_DELTA` events |

Tool-level Gemini calls (the expensive Pro model calls for image analysis) are instrumented in `util_gemini.generate_content()`. Each call appends a usage entry to `tool_context.state["tool_llm_usage"]` with:
- `tool` — which tool made the call (e.g. `analyze_image`, `crop_and_examine`)
- `model` — the model version used
- `prompt_tokens`, `completion_tokens`, `total_tokens`

The BQ Analytics Plugin automatically captures these state changes as `STATE_DELTA` events after each tool completes — no callbacks or direct BQ writes needed.

### Session Cost Profile

Each session (one image → one graph) uses both models. The analytics notebook (`bq_analytics.ipynb`) provides per-session breakdowns with input/output splits for cost estimation. From the initial 2-session dataset:

| | Input | Output | Total |
|---|---|---|---|
| **Agent LLM** (Flash) | ~143K | ~3K | ~147K |
| **Tool LLM** (Pro) | ~16K | ~11K | ~33K |
| **Session total** | ~158K | ~14K | ~180K |

Key observations:
- **Agent LLM dominates input tokens** — context grows over ~17 orchestration calls as the graph state accumulates
- **Tool LLM has a higher output ratio** — vision analysis calls (Pro model) produce substantial structured output relative to their input
- **Thinking tokens** — `total` may exceed `input + output`; the difference is reasoning tokens (visible in `usage_metadata.thoughts_token_count`), which can be significant for some tools (e.g. `trace_connections` used ~9.8K thinking tokens in one session)
- **Most expensive tools** — `generate_description` and `trace_connections` consume the most tool LLM tokens per call

With more sessions, the statistics (avg, min, max, median) become more reliable for predicting batch costs.

### Querying Analytics

Use `bq_analytics.ipynb` to query and analyze agent behavior:
- Event type distribution
- Token usage analysis (agent + tool LLM)
- Latency analysis (LLM & tools)
- Tool usage statistics
- Error analysis
- Conversation tracing by `invocation_id`
- Span hierarchy & duration
- Multimodal content queries (GCS references)
- Daily activity summaries
- **Per-session usage** — combined agent LLM + tool LLM token consumption per session per model, with input/output split for cost estimation (one session = one image evaluated into one graph)
- **Session statistics** — avg, min, max, median input/output/total tokens per session per model for predicting costs across batches
- **Tool LLM by tool** — per-tool token breakdown showing which vision tools are most expensive
- **Usage visualizations** — per-session stacked bars (input/output by model+source), input vs output grouped bars by model, and per-tool input/output breakdown
- **Bounding box corrections** — per-session breakdown of auto-corrections: axis swaps (x/y confusion) and per-node inversions (min > max), tracked from `STATE_DELTA` events

### Disabling Analytics

Comment out the plugin section at the end of `agent_image_to_graph/agent.py`:

```python
# from .bq_plugin import bq_analytics_plugin
# from google.adk.apps import App
# app = App(name="agent_image_to_graph", root_agent=root_agent, plugins=[bq_analytics_plugin])
```

---
## Where This Can Go

The agent works end-to-end for local images, URLs, GCS paths, and PDFs, with optional CV preprocessing and multi-flow awareness. The architecture is designed to extend naturally into broader workflows. Here are directions this can grow.

### Broader Image Input Support

**Natively handled today:** Pillow supports JPEG, PNG, GIF, BMP, TIFF, and WEBP. `load_image` also accepts `https://` URLs, `gs://` GCS paths, and PDF files (renders a selected page at configurable DPI via PyMuPDF).

**Additional formats to support:**
- **SVG** — vector diagrams are everywhere (architecture docs, design tools, web exports). Render to raster via `cairosvg` or `librsvg` before passing to Gemini, preserving the original SVG as metadata.
- **HEIF/HEIC** — common on iOS. Pillow supports these via `pillow-heif`.
- **DICOM / medical imaging** — specialized formats where flowcharts appear in clinical pathway diagrams.
- **Multi-frame inputs** — animated GIFs or multi-page TIFFs where each frame is a separate diagram.

### Remote and Inline File Sources

**Implemented today:** `load_image` supports local file paths, `https://` URLs (with 30-second timeout and size validation), and `gs://` GCS paths (via `google-cloud-storage` with pre-download size checks). Results from remote sources are written to `examples/` under a folder derived from the source (e.g., `url-example-com-diagram/`, `gcs-my-bucket-arch/`).

**Additional sources to support:**
- **Inline base64 / byte streams** — accept image data passed directly in the message (e.g., from another agent, an API call, or a pipeline step) rather than requiring a file on disk.
- **Google Drive** — pull diagrams from shared drives using the Drive API, common in enterprise doc workflows.

### Hosting on Vertex AI Agent Engine

The agent is built with [ADK](https://google.github.io/adk-docs/), which deploys directly to [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview). Hosting there unlocks:

- **API endpoint** — the agent becomes a managed service callable from any system via REST, gRPC, or client libraries. No local runtime needed.
- **Event-driven triggers** — wire Pub/Sub, Cloud Scheduler, Eventarc, or GCS object notifications to invoke the agent automatically. Example: a new diagram image lands in a GCS bucket → Pub/Sub triggers the agent → graph + schema + visualization are written back to the bucket.
- **Pipeline integration** — call the hosted agent as a step in Vertex AI Pipelines, Cloud Workflows, or Dataform pipelines for batch processing of diagram collections.
- **Scaling and auth** — Agent Engine handles autoscaling, IAM-based access control, and audit logging without additional infrastructure.

### Surfacing in Gemini for Google Cloud

Agents hosted on Vertex AI Agent Engine can be surfaced in [Gemini for Google Cloud](https://cloud.google.com/gemini/docs/overview) (available with Gemini Enterprise). This means:

- **Chat-based interaction** — users interact with the agent through the Gemini side panel in the Google Cloud Console, asking it to analyze diagrams and explore results conversationally.
- **Context-aware assistance** — Gemini can pull context from the user's GCP project (storage buckets, BigQuery datasets) and pass it to the agent, enabling prompts like "analyze the architecture diagram in my project's docs bucket."
- **Enterprise access controls** — no separate deployment; the agent inherits the organization's IAM policies and data residency settings.

### Document Parsing Integration

Diagrams rarely exist in isolation — they're embedded in PDFs, slide decks, and technical documents. Integrating with document parsing pipelines:

- **Diagram detection as a trigger** — tools like [Document AI](https://cloud.google.com/document-ai/docs/overview), [Layout Parser](https://github.com/Layout-Parser/layout-parser), or Gemini's own document understanding can classify page regions as diagrams. When a diagram is detected (flowchart, network diagram, electrical schematic, UML class/sequence/state/activity diagram, entity-relationship diagram, building/floor plan, P&ID, circuit/wiring diagram, BPMN process model, swim lane diagram, mind map, Gantt chart, data flow diagram, pipeline diagram, org chart, architecture diagram), it gets routed to this agent for structured extraction.
- **Multi-diagram documents** — a single PDF may contain dozens of diagrams across pages. The parsing pipeline extracts each one, invokes the agent per diagram, and collects all graphs into a unified output.
- **Metadata linkage** — the extracted graph can carry metadata from the source document (page number, section title, document ID), linking the structured graph back to its origin for provenance tracking.

### BigQuery as a Graph and Metadata Store

The agent already logs analytics to BigQuery. Extending BigQuery to store the extracted graphs themselves opens up powerful capabilities:

- **Structured graph storage** — store `graph.json` contents as native JSON columns in BigQuery. Nodes and edges become queryable with SQL — `SELECT * FROM graphs, UNNEST(nodes) WHERE element_type = 'process'`.
- **Schema registry** — maintain a BigQuery table of all schemas used across runs. Link each graph to its schema for cross-diagram conformance analysis.
- **Metadata enrichment** — augment each graph record with source metadata: file origin, document context, extraction timestamp, confidence statistics, agent session ID. This builds a searchable catalog of every diagram ever processed.
- **Cross-diagram analytics** — query patterns across thousands of extracted graphs. Which diagram types appear most? Which schemas have the highest conformance rates? Which node types are most common across all flowcharts in a document corpus?
- **Search and discovery** — combine graph metadata with [BigQuery vector search](https://cloud.google.com/bigquery/docs/vector-search-intro) over diagram descriptions and node labels. Find all diagrams that contain a "database" node connected to an "API gateway," across an entire organization's document library.
- **Object table integration** — use [BigQuery object tables](https://cloud.google.com/bigquery/docs/object-table-introduction) to reference source images in GCS directly from BigQuery, keeping the image, graph, schema, and description linked in a single queryable layer.

### And More

- **Batch processing** — process entire directories or buckets of diagrams in parallel, collecting all results into a unified dataset.
- **Comparison and diffing** — compare graphs extracted from two versions of the same diagram to detect structural changes (added nodes, removed edges, modified labels).
- **Graph database export** — export to Neo4j, Apache TinkerPop, or Property Graph formats for native graph traversal and pattern matching.
- **CI/CD documentation validation** — run the agent on architecture diagrams in a repo and validate that the extracted graph matches expected structure (e.g., "every service node must have an edge to the monitoring node").
- **Multi-agent orchestration** — chain with other specialized agents: a document parsing agent extracts diagrams, this agent converts them to graphs, a compliance agent validates them against policy schemas, and a reporting agent summarizes findings.
- **Fine-tuned extraction models** — for domain-specific diagram types (electrical schematics, P&IDs), fine-tune Gemini on labeled examples to improve extraction accuracy beyond general-purpose vision.

---
## Development

### Project Structure

```
image-to-graph/
├── agent_image_to_graph/              # Main agent package
│   ├── agent.py                       # Agent definition and ADK App
│   ├── config.py                      # Centralized configuration constants + DIAGRAM_TYPE_CONFIG
│   ├── bq_plugin.py                   # BigQuery analytics plugin
│   ├── prompts.py                     # Agent instructions + SCHEMATIC_CROP_GUIDANCE constant
│   ├── tools/
│   │   ├── util_common.py             # Shared utilities (JSON fence stripping, error logging)
│   │   ├── util_bbox.py               # Bounding box utilities (normalization, IoU, CV matching, schematic detection, correction tracking)
│   │   ├── util_diagram_type.py       # Diagram type detection (is_schematic), node ID normalization, schematic grid generation
│   │   ├── util_schema.py             # JSON Schema $ref resolution
│   │   ├── util_gemini.py             # Gemini API client
│   │   ├── util_output.py             # Output directory resolution (examples/ routing)
│   │   └── function_tool_*.py         # Individual tool implementations (12 tools)
│   └── tests/
│       ├── conftest.py                # Shared fixtures
│       ├── unit/                      # Pure function tests (no I/O)
│       │   ├── test_util_bbox.py
│       │   ├── test_util_common.py
│       │   ├── test_util_schema.py
│       │   ├── test_validate_helpers.py
│       │   ├── test_config.py
│       │   └── test_schematic_grid.py # Grid generation tests (coverage, overlap, aspect ratio)
│       └── tools/                     # Tool tests (mocked ToolContext)
│           ├── test_load_image.py
│           ├── test_load_schema.py
│           ├── test_validate_graph.py
│           ├── test_validate_flows.py # Multi-flow detection tests
│           ├── test_update_graph.py   # Includes set_metadata, node/edge dedup tests
│           ├── test_util_bbox.py      # IoU, CV matching, schematic detection tests
│           └── test_get_graph.py
├── agent_cv_preprocess/               # CV preprocessing sub-agent package
│   ├── agent.py                       # Subagent definition
│   ├── prompts.py                     # CV workflow instructions
│   ├── tools/
│   │   ├── util_common.py             # Shared CV utilities
│   │   ├── util_gemini.py             # Gemini client for OCR labeling
│   │   ├── function_tool_assess_image.py
│   │   ├── function_tool_detect_elements.py
│   │   ├── function_tool_detect_connections.py
│   │   ├── function_tool_label_elements.py
│   │   └── function_tool_report_results.py
│   └── tests/
├── agent_graph_qa/                    # Q&A sub-agent package
│   ├── agent.py
│   ├── prompts.py
│   ├── tools/
│   │   ├── function_tool_get_context.py   # Get graph context from parent agent state
│   │   └── function_tool_load_results.py  # Load results from disk for standalone mode
│   └── tests/
│       ├── conftest.py                # Q&A-specific fixtures
│       └── tools/
│           └── test_load_results.py
├── examples/                          # Example diagrams, schemas, and results
│   ├── bq-arima-flowchart/            # BQ ARIMA pipeline diagram + schema + screenshots
│   ├── xkcd-flowchart/                # XKCD "Flowcharts" comic
│   └── url-www-raspberrypi-org.../    # Raspberry Pi schematic (URL source)
├── bq_analytics.ipynb                 # BigQuery analytics notebook (token usage, latency, costs)
├── pyproject.toml                     # Project config, dev deps, tool settings
└── Makefile                           # Dev command shortcuts
```

### Dev Environment Setup

```bash
uv sync --extra dev
```

This installs `pytest`, `pytest-asyncio`, `pytest-cov`, and `ruff` alongside the main project dependencies. `make install` is a shortcut for the same command.

### Running Tests

```bash
uv run pytest                                  # All tests with coverage
uv run pytest agent_image_to_graph/tests/unit -v   # Unit tests only
uv run pytest --cov-report=html                # HTML coverage report (htmlcov/index.html)
```

Makefile shortcuts: `make test`, `make test-unit`, `make test-cov`.

### Linting & Formatting

```bash
uv run ruff check .       # Lint
uv run ruff format .      # Auto-format
uv run ruff check --fix --select I .   # Sort imports
```

Makefile shortcuts: `make lint`, `make format`.

### Makefile Shortcut Reference

| Target | Command | Purpose |
|--------|---------|---------|
| `make install` | `uv sync --extra dev` | Install project with dev dependencies |
| `make test` | `uv run pytest` | Run all tests with coverage |
| `make test-unit` | `uv run pytest agent_image_to_graph/tests/unit -v` | Run unit tests only |
| `make test-cov` | `uv run pytest --cov-report=html` | Tests with HTML coverage report |
| `make lint` | `uv run ruff check .` | Run linter |
| `make format` | `uv run ruff format . && uv run ruff check --fix --select I .` | Auto-format and sort imports |
| `make check` | `make lint && make test` | Lint then test (CI equivalent) |

### Configuration & Security

Input validation is centralized in `agent_image_to_graph/config.py`. All limits are configurable via environment variables:

| Constant | Default | Env Var | Purpose |
|----------|---------|---------|---------|
| `MAX_IMAGE_SIZE_BYTES` | 50 MB | `MAX_IMAGE_SIZE_BYTES` | Maximum image file size for `load_image` |
| `MAX_SCHEMA_SIZE_BYTES` | 10 MB | `MAX_SCHEMA_SIZE_BYTES` | Maximum schema file size for `load_schema` |
| `PIL_MAX_IMAGE_PIXELS` | 200 MP | `PIL_MAX_IMAGE_PIXELS` | Pillow decompression bomb limit |
| `ALLOWED_IMAGE_FORMATS` | JPEG, PNG, GIF, BMP, TIFF, WEBP | — | Accepted image formats (whitelist) |
| `PDF_RENDER_DPI` | 300 | `PDF_RENDER_DPI` | DPI for PDF page rendering via PyMuPDF |
| `DIAGRAM_TYPE_CONFIG` | see below | — | Diagram-type-specific thresholds (not env-configurable) |

`DIAGRAM_TYPE_CONFIG` provides per-diagram-type settings. Currently used by `validate_graph` for the oversized bbox threshold:

```python
DIAGRAM_TYPE_CONFIG = {
    "schematic": {"oversized_bbox_threshold": 0.05},  # 5% of image area
    "default":   {"oversized_bbox_threshold": 0.10},  # 10% of image area
}
```

### Conventions

- **One tool per file**, prefixed `function_tool_` (e.g., `function_tool_load_image.py`)
- **Utils shared across tools** get their own file, prefixed `util_` (e.g., `util_bbox.py`)
- **Utils used by only one tool** stay inline at the top of that tool file
- **Tests co-located per agent** — each agent package has its own `tests/` directory with `conftest.py`, so a developer exploring one agent sees everything together

### Extending the Agent

**Add a new tool:**
1. Create `agent_image_to_graph/tools/function_tool_your_tool.py` with an `async def your_tool(tool_context: tools.ToolContext) -> str:` function
2. Import `log_tool_error` from `util_common` for consistent error handling
3. Register it in `agent_image_to_graph/tools/__init__.py` (import + add to `TOOLS` list)
4. Add tests in `agent_image_to_graph/tests/tools/test_your_tool.py`

**Add a new util:**
1. If used by 2+ tools, create `agent_image_to_graph/tools/util_your_util.py`
2. If used by only one tool, define it inline in that tool file
3. Add unit tests in `agent_image_to_graph/tests/unit/test_util_your_util.py`

---
