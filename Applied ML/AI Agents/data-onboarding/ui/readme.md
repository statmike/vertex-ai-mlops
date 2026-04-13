# Data Onboarding UI

Custom web interface for the data-onboarding chat agent with **text chat** and **voice mode**. Connects to `agent_chat` either locally (ADK Runner, in-process) or against a deployed agent on Vertex AI Agent Engine.

For agent architecture details, see the [main project README](../readme.md).

## Quick Start

### Run locally (all local — `AGENT_MODE=local`)

Runs all agents directly via ADK Runner — no deployment needed, fast iteration. Uses the main project's venv which has ADK and all agent dependencies. Both text chat and voice mode run agent_chat in-process.

```bash
cd ui

# Create .env from example
cp .env.example .env
# Edit .env — set GOOGLE_CLOUD_PROJECT, AGENT_MODE=local

# Run using the main project venv
../.venv/bin/uvicorn backend.app:app --port 8080
```

### Run locally (agent on VAE — `AGENT_MODE=agent_engine`)

Text chat and voice mode both call the deployed agent_chat on Vertex AI Agent Engine. Voice audio handling still runs locally (the Gemini Live API requires a direct connection), but `ask_data_question` calls the deployed agent remotely.

```bash
cd ui

# Create .env from example
cp .env.example .env
# Edit .env — set AGENT_MODE=agent_engine, AGENT_ENGINE_RESOURCE_ID

# Run using the main project venv (needed for agent_voice + Live API)
../.venv/bin/uvicorn backend.app:app --port 8080
```

Open `http://localhost:8080`.

### Deploy to Cloud Run

Runs the UI on Cloud Run with agent_chat on Agent Engine. Voice mode requires the main project venv for `agent_voice` and the Live API — Cloud Run deployment currently supports text mode only.

```bash
cd ui

gcloud run deploy data-onboarding-ui \
  --source . \
  --region us-central1 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=your-project,GOOGLE_CLOUD_LOCATION=us-central1,AGENT_ENGINE_RESOURCE_ID=your-resource-id,AGENT_MODE=agent_engine" \
  --allow-unauthenticated
```

For internal-only access, replace `--allow-unauthenticated` with IAP or IAM-based access control.

---

## Architecture

The `AGENT_MODE` environment variable controls where `agent_chat` runs. Both text and voice modes respect this setting.

### Text Mode

```
                         AGENT_MODE=local                  AGENT_MODE=agent_engine
                              │                                     │
Browser ──ws /ws/chat──→ FastAPI ──Runner.run_async()──→ agent_chat (local)
                              │
                              └──async_stream_query()──→ agent_chat (VAE)
                              │
                         renders:                          streams events:
                         - question hero                   - agent transfers
                         - thinking timeline               - tool calls + results
                         - data tables + charts            - text responses
                         - insight cards
```

### Voice Mode

```
Browser (mic) ──ws /ws/voice──→ FastAPI ──Runner.run_live()──→ agent_voice
                                    │                          (always local)
                               renders:                            │
                               - voice orb                  ask_data_question()
                               - thinking steps                    │
                               - transcription       ┌─────────────┴─────────────┐
                                                     │                           │
                                              AGENT_MODE=local         AGENT_MODE=agent_engine
                                                     │                           │
                                              agent_chat (local)       agent_chat (VAE)
                                              Runner.run_async()       async_stream_query()
                                                     │                           │
                                                     └─────────────┬─────────────┘
                                                                   │
                                                            voice summary
                                                              (flash-lite)
                                                                   │
                                                         concise spoken answer
```

Voice mode uses a **delegation architecture**: `agent_voice` is a standalone agent with a single tool (`ask_data_question`) that bridges to `agent_chat`. The voice model handles audio I/O through the Gemini Live API, while data analysis runs through `agent_chat` — either locally or on VAE depending on `AGENT_MODE`.

`agent_voice` itself always runs locally because the Gemini Live API requires a direct WebSocket connection for bidirectional audio streaming. Only the data processing is delegated.

The bridge tool includes a **voice summarization step** — after `agent_chat` returns a detailed text answer (with tables, SQL, markdown), a lightweight model (`gemini-2.5-flash-lite`) condenses it into 2-4 spoken sentences. This keeps the voice model's 32K context window small and produces naturally speakable answers.

### Run Mode Comparison

| | `AGENT_MODE=local` | `AGENT_MODE=agent_engine` |
|---|---|---|
| **Text chat** | agent_chat runs in-process via ADK Runner | agent_chat runs on VAE via Vertex AI SDK |
| **Voice chat** | agent_voice runs locally, calls agent_chat in-process | agent_voice runs locally, calls agent_chat on VAE |
| **Sessions** | In-memory (ephemeral, lost on restart) | Cloud-managed (persistent across restarts) |
| **Observability** | Local logs only | Cloud Monitoring, Logging, Trace |
| **Requirements** | Main project venv with all agent dependencies | Main project venv (for agent_voice + Live API) + deployed agent_chat |
| **Best for** | Development, fast iteration | Production, observability, persistent sessions |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_CLOUD_PROJECT` | *(required)* | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | GCP region |
| `AGENT_MODE` | `local` | `local` (ADK Runner, in-process) or `agent_engine` (deployed on VAE). Controls where agent_chat runs for both text and voice modes. |
| `AGENT_ENGINE_RESOURCE_ID` | — | Agent Engine resource ID (required when `AGENT_MODE=agent_engine`) |
| `CHAT_SCOPE` | *(empty)* | Restrict agent to specific dataset(s) — see [main README](../readme.md#configuration) |
| `CONVO_THINKING_MODE` | `THINKING` | Conversational Analytics API thinking mode — `THINKING` or `FAST` |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8080` | Server port |

### Voice-Specific Variables

These are set in the main project `.env` and apply when running in local mode:

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_SUMMARY_MODEL` | `gemini-2.5-flash-lite` | Model for condensing answers into voice-friendly summaries |
| `SHORTLIST_MODEL` | `gemini-2.5-flash-lite` | Model for the reranker shortlist pass (lightweight screening) |

---

## File Structure

### Backend

| File | Purpose |
|------|---------|
| `backend/app.py` | FastAPI app — mounts routes + static files |
| `backend/routes/chat.py` | WebSocket `/ws/chat` — text mode chat proxy |
| `backend/routes/voice.py` | WebSocket `/ws/voice` — voice mode with Gemini Live API |
| `backend/routes/sessions.py` | REST session management (create, list, delete) |
| `backend/services/agent_engine.py` | Agent runner management — text Runner, voice Runner, Live API streaming |
| `backend/services/event_parser.py` | Maps agent events → frontend event types (thinking steps, data, charts) |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/index.html` | SPA shell with mode toggle (text/voice) |
| `frontend/static/css/theme.css` | Design system — colors, glassmorphism, typography |
| `frontend/static/css/components.css` | Timeline, cards, input bar, data tables |
| `frontend/static/css/voice.css` | Voice mode — orb visualization, status indicators |
| `frontend/static/js/app.js` | Main app — input handling, WebSocket init, mode switching |
| `frontend/static/js/chat.js` | Text mode — question hero, thinking timeline, response rendering |
| `frontend/static/js/voice.js` | Voice mode — mic capture, audio playback, state machine, thinking steps |
| `frontend/static/js/audio.js` | Audio utilities — PCM capture (AudioCapture) and playback (AudioPlayback) |
| `frontend/static/js/ws.js` | WebSocket client with reconnection |

### Voice Agent (`agent_voice/`)

The voice agent lives in the main project directory (not under `ui/`) since it's an agent module like the others. See the [main README's Voice Agent section](../readme.md#voice-agent-agent_voice) for details.

| File | Purpose |
|------|---------|
| `agent_voice/agent.py` | Agent definition — model overridden to live audio model at runtime |
| `agent_voice/prompts.py` | Voice instructions — always call tool, narrate naturally, scope awareness |
| `agent_voice/tools/function_tool_ask_data.py` | Bridge tool — delegates to agent_chat (local or VAE), summarizes for voice |

---

## Voice Mode Details

### How It Works

1. User clicks the voice toggle in the UI → browser opens WebSocket to `/ws/voice`
2. Backend creates a Gemini Live API session with `agent_voice` via `Runner.run_live()`
3. Browser captures microphone audio (16kHz PCM) and sends it over the WebSocket
4. The live model (`gemini-live-2.5-flash-native-audio`) processes speech and decides to call `ask_data_question`
5. The tool calls `agent_chat` — locally via `Runner.run_async()` or on VAE via `async_stream_query()`, depending on `AGENT_MODE`
6. The raw answer is summarized into 2-4 spoken sentences by `gemini-2.5-flash-lite`
7. The summary is returned to the live model, which narrates it as audio
8. Audio chunks stream back through the WebSocket to the browser for playback

### Audio Timing

The voice UI handles a subtle timing issue: the Gemini Live API sends a `turn_complete` signal before all audio chunks finish playing. If the mic re-enables immediately, the speaker output gets picked up by the mic, triggering an interruption that cuts off the answer. The UI waits for `AudioPlayback.isPlaying()` to return false before re-enabling the microphone.

### Thinking Steps in Voice Mode

While `ask_data_question` is processing, the UI displays thinking steps based on tool calls observed in the pipeline:

| Tool Call | Display Label |
|-----------|--------------|
| `ask_data_question` | "Querying the data system..." |
| `transfer_to_agent` | "Routing to {agent}..." |
| `conversational_chat` | "Analyzing data..." |
| `meta_chat` | "Checking pipeline metadata..." |
| `search_context` | "Searching documentation..." |

---

## Phases

See [PLANS.md](PLANS.md) for the full implementation plan:
- **Phase 1** (complete): Text chat with streaming timeline and data rendering
- **Phase 2** (complete): Voice mode with Gemini Live API via agent_voice delegation
- **Phase 3** (future): Persona voice handoffs with distinct personalities

## Prerequisites

- Python 3.11+ with the main project venv (for local mode)
- A deployed chat agent on Agent Engine (for agent_engine mode) — see [deploy/readme.md](../deploy/readme.md)
- Microphone access in the browser (for voice mode)
