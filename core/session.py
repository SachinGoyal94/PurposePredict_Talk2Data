"""
core/session.py

Stores per-user state:
- The uploaded dataframe
- Conversation history (for follow-up questions)
- Schema metadata
"""
import uuid
import pandas as pd
from datetime import datetime, UTC


class Session:
    def __init__(self, session_id: str):
        self.session_id   = session_id
        self.df: pd.DataFrame | None = None
        self.filename: str            = ""
        self.history: list[dict]      = []   # [{role, content, timestamp}]
        self.db_history: list[dict]   = []   # SQL chat history for /db/chat
        self.last_chart_b64: str | None = None
        self.created_at               = datetime.now(UTC)

    def set_dataframe(self, df: pd.DataFrame, filename: str):
        self.df       = df
        self.filename = filename
        self.last_chart_b64 = None

    def add_message(self, role: str, content: str):
        self.history.append({
            "role":      role,
            "content":   content,
            "timestamp": datetime.now(UTC).isoformat(),
        })

    def get_history_text(self, last_n: int = 6) -> str:
        """Last N messages as a formatted string for the LLM prompt."""
        msgs = self.history[-last_n:]
        return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in msgs)

    def add_db_message(self, role: str, content: str, max_messages: int = 10):
        self.db_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        if len(self.db_history) > max_messages:
            self.db_history = self.db_history[-max_messages:]

    def get_db_history_text(self, last_n: int = 8) -> str:
        msgs = self.db_history[-last_n:]
        return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in msgs)

    def has_data(self) -> bool:
        return self.df is not None


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        sid     = str(uuid.uuid4())
        session = Session(sid)
        self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None) -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create()


# Singleton
_store = None

def get_session_store() -> SessionStore:
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
