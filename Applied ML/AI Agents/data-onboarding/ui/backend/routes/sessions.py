"""Session management endpoints."""

from fastapi import APIRouter

from ..services import agent_engine, history

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/")
async def create_session(user_id: str = "ui_user"):
    """Create a new chat session on Agent Engine."""
    session = await agent_engine.create_session(user_id=user_id)
    return session


@router.get("/")
async def list_sessions(user_id: str = "ui_user"):
    """List active sessions."""
    sessions = await agent_engine.list_sessions(user_id=user_id)
    return {"sessions": sessions}


@router.delete("/{session_id}")
async def delete_session(session_id: str, user_id: str = "ui_user"):
    """Delete a session."""
    await agent_engine.delete_session(user_id=user_id, session_id=session_id)
    history.clear(session_id)
    return {"deleted": session_id}


@router.get("/{session_id}/history")
async def get_history(session_id: str):
    """Return stored events for backfill when toggling panels."""
    events = history.get_all(session_id)
    return {"events": events}
