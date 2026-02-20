"""Generate synthetic Reddit threads with Gemini structured output."""

from pydantic import BaseModel
from google import genai
from pathlib import Path
import google.auth
import json

# --- Pydantic schemas for Reddit structure (flat with parent references) ---

class Comment(BaseModel):
    comment_id: str
    parent_id: str | None = None  # None = top-level reply to post
    author: str
    body: str
    score: int
    image_url: str | None = None

class RedditPost(BaseModel):
    title: str
    author: str
    subreddit: str
    body: str
    score: int
    url: str
    image_url: str | None = None
    comments: list[Comment]

# --- Gemini client (Vertex AI + ADC) ---

_, project = google.auth.default()
client = genai.Client(vertexai=True, project=project, location="us-central1")
MODEL = "gemini-2.5-pro"

# --- Output ---

output_dir = Path("generated_reddit")
output_dir.mkdir(exist_ok=True)

# --- Generate threads with varying depth and branching ---

configs = [
    {"name": "shallow", "depth": 1, "branches": 2},
    {"name": "medium", "depth": 3, "branches": 3},
    {"name": "deep", "depth": 5, "branches": 4},
]

for config in configs:
    response = client.models.generate_content(
        model=MODEL,
        contents=f"""Generate a realistic Reddit post about time series forecasting.
The post should be in a data science or statistics subreddit.
Topic should cover forecasting methods, approaches, tools, or real-world use cases
(e.g. ARIMA vs Prophet, ML for demand forecasting, interpreting seasonality, business planning).
Mix commenters: some are knowledgeable statisticians/data scientists giving technical answers,
others are opinionated business people without deep technical skills pushing back or oversimplifying.
Use comment_id and parent_id to represent nesting (parent_id=null for top-level comments).
Comment nesting depth: up to {config['depth']} levels.
Branching: up to {config['branches']} replies per comment.
Include some image_url values using fake URLs like https://i.redd.it/example123abc.jpg
Use realistic usernames and vote scores.""",
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RedditPost,
        ),
    )

    post = json.loads(response.text)
    output_file = output_dir / f"thread_{config['name']}.json"
    output_file.write_text(json.dumps(post, indent=2))
    print(f"Created: {output_file}")
