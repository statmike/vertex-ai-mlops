# UI — Implementation Plan

Custom web interface for `agent_chat`, hosted on Cloud Run, connecting to the deployed chat agent on Vertex AI Agent Engine.

---

## Architecture

```
Browser ──ws──→ Cloud Run (FastAPI) ──SDK──→ Agent Engine (agent_chat)
                      │                              │
                 renders:                     streams events:
                 - question hero              - SchemaMessage (table resolution)
                 - thinking timeline          - DataMessage (SQL + results)
                 - data tables + charts       - TextMessage (THOUGHT, PROGRESS, FINAL_RESPONSE)
                 - insight cards              - ChartMessage (Vega + rendered PNG)
                 - voice transcription        - AnalysisMessage (Python analysis)
                 - persona indicators         - ErrorMessage (recoverable errors)
```

The UI is a **pure client** of Agent Engine — no direct BigQuery access, no ADK dependency, no agent code. All data flows through the deployed `agent_chat` via the Vertex AI SDK.

---

## Phase 1: Text Chat UI ✅

**Goal:** Cloud Run app with the chat/analysis screen — text input, streaming thinking timeline, data tables, charts, and insight cards.

### Backend (FastAPI)

- `backend/app.py` — FastAPI app, mounts static files, includes routers
- `backend/config.py` — env var loading (project, region, Agent Engine resource ID)
- `backend/routes/chat.py` — websocket `/ws/chat` endpoint that proxies to Agent Engine
- `backend/routes/sessions.py` — REST endpoints for session create/list/delete
- `backend/services/agent_engine.py` — SDK client wrapping `async_stream_query`, session management
- `backend/services/event_parser.py` — maps Agent Engine proto events to frontend-friendly JSON

### Frontend (vanilla HTML/CSS/JS)

- `frontend/index.html` — SPA shell with Manrope font
- `frontend/static/css/theme.css` — design system colors, glassmorphism, typography from DESIGN.md
- `frontend/static/css/components.css` — timeline, insight cards, chart container, input bar
- `frontend/static/js/app.js` — main app, manages view state (idle → asking → thinking → results)
- `frontend/static/js/chat.js` — chat mode: question hero display, thinking timeline, result rendering
- `frontend/static/js/ws.js` — websocket client: connect, send messages, handle event types

### Deployment

- `Dockerfile` — Python 3.13 slim, installs deps, runs uvicorn
- `.env.example` — documents required env vars
- Deploy via `gcloud run deploy` with service account that has Agent Engine access

---

## Phase 2: Voice Mode ✅

**Goal:** Add voice interaction — speak questions, hear responses, see thinking steps during processing.

### What was built

**Approach chosen: Delegation architecture** (evolved from the original options below)

Rather than having the voice model call agent_chat's tools directly (Options A/C) or using a STT→TTS sandwich (Option B), we built a **standalone `agent_voice` agent** that delegates to `agent_chat` via a single `ask_data_question` tool:

```
Browser (mic) ──ws /ws/voice──→ FastAPI ──Runner.run_live()──→ agent_voice
                                                                    │
                                                             ask_data_question()
                                                                    │
                                                               agent_chat
                                                             (unchanged)
                                                                    │
                                                             voice summary
                                                               (flash-lite)
```

**Why this approach won:**
- `agent_chat` stays completely untouched — no cloning, no patching, no fragile overrides
- The voice model only needs one tool and short instructions (fits in 32K context)
- Voice summarization produces naturally speakable answers from detailed text responses
- Follow-up context is preserved via persistent text sessions in the bridge tool

**Key discovery:** ADK's async generator tools in live mode return "pending" immediately, causing the model to re-invoke the tool in a loop. Regular async functions (blocking until completion) are the correct pattern for tools that need to wait for results.

### Backend additions

- `backend/routes/voice.py` — websocket `/ws/voice` for bidirectional audio via Gemini Live API
- `backend/services/agent_engine.py` — added `_get_voice_runner()` (creates Runner with `agent_voice`, model overridden to `gemini-live-2.5-flash-native-audio`) and `stream_live()` for live event streaming

### Frontend additions

- `frontend/static/js/voice.js` — voice state machine (idle → listening → speaking), mic control, thinking step display, WebSocket audio streaming
- `frontend/static/js/audio.js` — `AudioCapture` (16kHz PCM from mic) and `AudioPlayback` (chunked audio queue with playback state tracking)
- `frontend/static/css/voice.css` — voice orb visualization, status indicators, mode toggle
- Mode toggle between text and voice in the main UI

### Voice UX

- Voice model says "Let me look that up" → calls `ask_data_question`
- UI shows thinking steps as the pipeline processes (reranker, SQL, etc.)
- Answer is summarized to 2-4 spoken sentences and narrated
- Mic stays muted during playback to prevent echo-triggered interruptions
- Follow-up questions call the tool again with preserved session context

### Agent module (`agent_voice/`)

Lives in the main project directory alongside other agent modules:
- `agent_voice/agent.py` — root agent (model overridden at runtime)
- `agent_voice/prompts.py` — voice-specific instructions with scope awareness
- `agent_voice/tools/function_tool_ask_data.py` — bridge tool with voice summarization, concurrency guards, and repeat detection

### Original options considered (from planning)

- **Option A:** Gemini Live API with function calling — voice model calls agent_chat tools directly. Rejected: voice model's 32K context too small for full agent instructions + tools.
- **Option B:** STT → Agent Engine → TTS sandwich — more control, less natural. Not needed since delegation handles this better.
- **Option C:** Clone agent_chat and patch for voice. Attempted first — proved fragile. Every voice fix created new text-mode regressions.

---

## Phase 3: Persona Voice Handoffs

**Status:** Future — not yet started.

**Goal:** Distinct voice personalities for each agent_chat persona.

### Approach

- Single Gemini Live session with system instruction shifts per persona
- Host voice: warm, conversational — "Let me check with my data analyst on that..."
- Data Analyst voice: precise, numbers-focused — cites specific values
- Data Engineer voice: technical — references pipeline stages, table names
- Catalog Explorer voice: descriptive, definitional — explains concepts
- Color-coded timeline steps match persona (blue = analyst, cyan = engineer, violet = catalog)
- Orb color shifts to match active persona

### Open questions

- Can `agent_voice` pass persona hints through `ask_data_question` results (e.g., which sub-agent answered)?
- Does the Gemini Live API support mid-session voice/personality changes via system instruction updates?
- Alternative: use the live model's natural narration style with persona cues in the answer text ("As a data engineer, I can tell you...")

---

## Design Reference

See `ui/sketch/` for design exports:
- `screen.png` / `code.html` — Voice mode with Intelligence Core orb
- `chat_screen.png` / `chat_code.html` — Chat/analysis mode with timeline and chart
- `DESIGN.md` — Full design system specification (colors, typography, components)
