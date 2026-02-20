![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FSolutions%2Fmulti-type-parsing-and-vector-search-2&file=readme.md)
<!--- header table --->
<table>
<tr>
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b>
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a>
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a>
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
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
# Multi-Type File Parsing And Vertex Vector Search 2
> You are here: `vertex-ai-mlops/Applied GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md`

## Setup

This project requires the packages listed in [pyproject.toml](pyproject.toml) and prefers the Python version specified there.

**Google Cloud ADC:**

This project uses [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) for Google Cloud APIs. Set up and verify with:
```bash
gcloud auth application-default login
```
Verify ADC is active and check which identity it's using:
```bash
curl -s -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  https://www.googleapis.com/oauth2/v3/userinfo
```

**UV (recommended):**

Run the included [uv_setup.sh](uv_setup.sh) for a one-step setup (environment, packages, Jupyter kernel, and requirements.txt):
```bash
bash uv_setup.sh
```

Or manually:
```bash
uv sync
uv run python -m ipykernel install --user --name=$(basename "$PWD")
```

**Poetry:**
```bash
poetry install
poetry run python -m ipykernel install --user --name=$(basename "$PWD")
```

**pip:**
```bash
pip install -r requirements.txt
python -m ipykernel install --user --name=$(basename "$PWD")
```

### Running Scripts

**UV:** `uv run python <script.py>`

**Poetry:** `poetry run python <script.py>`

**pip:** `python <script.py>` (with your virtual environment activated)

## Generate Data

Three scripts generate synthetic forecasting-themed data in different formats. Each uses Gemini (`gemini-2.5-pro`) via Vertex AI with structured output (Pydantic schemas).

| Script | Output Folder | Format | Description |
|--------|--------------|--------|-------------|
| [generate_reddit.py](generate_reddit.py) | [generated_reddit/](generated_reddit/) | JSON | Synthetic Reddit threads with nested comments (via `comment_id`/`parent_id`). Varying depth and branching levels. |
| [generate_zoom.py](generate_zoom.py) | [generated_zoom/](generated_zoom/) | WebVTT | Synthetic Zoom meeting transcripts with multiple speakers. Varying duration and complexity. |
| [generate_pdf.py](generate_pdf.py) | [generated_pdf/](generated_pdf/) | PDF | Web pages converted to PDF using WeasyPrint. |

**Customization tips:**
- **Reddit/Zoom**: Edit the prompt in the `contents` string to change the topic, tone, or participant mix. Adjust the `configs` list to control the number/complexity of generated files.
- **PDF**: Replace the `urls` list at the top of the script with your own URLs.
