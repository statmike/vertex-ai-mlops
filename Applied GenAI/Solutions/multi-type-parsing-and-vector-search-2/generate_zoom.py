"""Generate synthetic WebVTT transcripts with Gemini structured output."""

from pydantic import BaseModel
from google import genai
from pathlib import Path
from config import PROJECT_ID, REGION, GEMINI_MODEL
import json

# --- Pydantic schemas for transcript structure ---

class Cue(BaseModel):
    start: str  # HH:MM:SS.mmm
    end: str    # HH:MM:SS.mmm
    speaker: str
    text: str

class Transcript(BaseModel):
    meeting_title: str
    speakers: list[str]
    cues: list[Cue]

# --- Gemini client (Vertex AI + ADC) ---

client = genai.Client(vertexai=True, project=PROJECT_ID, location=REGION)

# --- Output ---

output_dir = Path("generated_zoom")
output_dir.mkdir(exist_ok=True)

# --- Format structured data as WebVTT ---

def to_vtt(transcript: dict) -> str:
    lines = ["WEBVTT", ""]
    for cue in transcript["cues"]:
        lines.append(f"{cue['start']} --> {cue['end']}")
        lines.append(f"{cue['speaker']}: {cue['text']}")
        lines.append("")
    return "\n".join(lines)

# --- Generate transcripts with varying length and complexity ---

configs = [
    {"name": "data_review", "speakers": 2, "minutes": 5,
     "topic": "a data engineer and data scientist reviewing incoming sales data quality before building a forecast model"},
    {"name": "model_planning", "speakers": 4, "minutes": 20,
     "topic": "a forecasting team (statistician, ML engineer, analyst, project lead) debating which modeling approaches to use for demand forecasting — ARIMA, Prophet, gradient boosting — and how to handle seasonality and holidays"},
    {"name": "business_readout", "speakers": 6, "minutes": 45,
     "topic": "a cross-functional meeting where the data science team presents quarterly forecast results to business stakeholders (VP of Sales, Finance Director, Supply Chain Manager) who question accuracy, push back on methodology, and discuss how to act on the predictions"},
]

for config in configs:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"""Generate a realistic Zoom meeting transcript about time series forecasting.
Speakers: {config['speakers']} participants with realistic names and distinct roles.
Duration: approximately {config['minutes']} minutes.
Scenario: {config['topic']}.
Use timestamps in HH:MM:SS.mmm format with realistic pacing.
Make the conversation natural with back-and-forth, technical discussion, agreements, disagreements, and clarifying questions.""",
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Transcript,
        ),
    )

    transcript = json.loads(response.text)
    output_file = output_dir / f"meeting_{config['name']}.vtt"
    output_file.write_text(to_vtt(transcript))
    print(f"Created: {output_file}")
