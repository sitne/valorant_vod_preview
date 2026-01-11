import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from utils import setup_logger, ensure_dir

logger = setup_logger("SessionManager")


def generate_session_id(video_url: str = None) -> str:
    """
    Generate a unique session ID based on video URL and timestamp.
    Format: vlr_{YYYYMMDD}_{12_char_hash}
    """
    date_str = datetime.now().strftime("%Y%m%d")

    if video_url:
        url_hash = hashlib.md5(video_url.encode()).hexdigest()[:12]
    else:
        import uuid

        url_hash = str(uuid.uuid4()).replace("-", "")[:12]

    return f"vlr_{date_str}_{url_hash}"


class SessionManager:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.sessions_dir = os.path.join(output_dir, "sessions")
        ensure_dir(self.output_dir)
        ensure_dir(self.sessions_dir)
        self.current_session_id: Optional[str] = None
        self.current_session_dir: Optional[str] = None

    def create_session(
        self, video_url: str = None, video_id: str = None, tags: List[str] = None
    ) -> str:
        """
        Create a new session and return session_id.

        Args:
            video_url: Video URL (optional)
            video_id: Custom session ID (optional, overrides auto-generation)
            tags: List of tags for the session (optional)

        Returns:
            session_id: Unique session identifier
        """
        session_id = video_id if video_id else generate_session_id(video_url)
        self.current_session_id = session_id
        self.current_session_dir = os.path.join(self.sessions_dir, session_id)

        ensure_dir(self.current_session_dir)
        ensure_dir(os.path.join(self.current_session_dir, "minimaps"))
        ensure_dir(os.path.join(self.current_session_dir, "full_screenshots"))
        ensure_dir(os.path.join(self.current_session_dir, "metadata"))
        ensure_dir(os.path.join(self.current_session_dir, "analysis"))

        session_metadata = {
            "session_id": session_id,
            "video_url": video_url,
            "created_at": datetime.now().isoformat(),
            "tags": tags or [],
            "round_count": 0,
            "status": "initialized",
        }

        self.save_session_metadata(session_metadata)
        self._update_index(session_id, session_metadata)

        logger.info(f"Created session: {session_id}")
        return session_id

    def get_session_dir(self, session_id: str = None) -> str:
        """
        Get session directory path.

        Args:
            session_id: Session ID (uses current session if None)

        Returns:
            Path to session directory
        """
        sid = session_id if session_id else self.current_session_id
        if not sid:
            raise ValueError(
                "No session ID provided or current session not initialized"
            )

        return os.path.join(self.sessions_dir, sid)

    def save_session_metadata(self, metadata: Dict, session_id: str = None):
        """
        Save session metadata to session.json.

        Args:
            metadata: Session metadata dictionary
            session_id: Session ID (uses current session if None)
        """
        sid = session_id if session_id else self.current_session_id
        if not sid:
            raise ValueError(
                "No session ID provided or current session not initialized"
            )

        session_file = os.path.join(self.get_session_dir(sid), "session.json")
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

        logger.debug(f"Saved session metadata: {session_file}")

    def save_video_info(self, video_info: Dict, session_id: str = None):
        """
        Save video information to video_info.json.

        Args:
            video_info: Video information dictionary
            session_id: Session ID (uses current session if None)
        """
        sid = session_id if session_id else self.current_session_id
        if not sid:
            raise ValueError(
                "No session ID provided or current session not initialized"
            )

        video_file = os.path.join(self.get_session_dir(sid), "video_info.json")
        with open(video_file, "w", encoding="utf-8") as f:
            json.dump(video_info, f, indent=4, ensure_ascii=False)

        logger.debug(f"Saved video info: {video_file}")

    def update_session_status(
        self, status: str, round_count: int = None, session_id: str = None
    ):
        """
        Update session status in metadata.

        Args:
            status: New status (e.g., "processing", "completed", "failed")
            round_count: Number of rounds detected (optional)
            session_id: Session ID (uses current session if None)
        """
        sid = session_id if session_id else self.current_session_id
        if not sid:
            return

        session_file = os.path.join(self.get_session_dir(sid), "session.json")
        if os.path.exists(session_file):
            with open(session_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            metadata["status"] = status
            if round_count is not None:
                metadata["round_count"] = round_count
            metadata["updated_at"] = datetime.now().isoformat()

            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)

            self._update_index(sid, metadata)
            logger.debug(f"Updated session status: {status}")

    def list_sessions(self) -> List[Dict]:
        """
        List all sessions with metadata.

        Returns:
            List of session metadata dictionaries
        """
        sessions = []
        if not os.path.exists(self.sessions_dir):
            return sessions

        for session_id in os.listdir(self.sessions_dir):
            session_file = os.path.join(self.sessions_dir, session_id, "session.json")
            if os.path.exists(session_file):
                with open(session_file, "r", encoding="utf-8") as f:
                    sessions.append(json.load(f))

        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions

    def load_session(self, session_id: str) -> Optional[Dict]:
        """
        Load session metadata by session_id.

        Args:
            session_id: Session ID to load

        Returns:
            Session metadata dictionary or None if not found
        """
        session_file = os.path.join(self.sessions_dir, session_id, "session.json")
        if os.path.exists(session_file):
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _update_index(self, session_id: str, metadata: Dict):
        """
        Update the global sessions index file.

        Args:
            session_id: Session ID
            metadata: Session metadata
        """
        index_file = os.path.join(self.sessions_dir, "index.json")

        index = {}
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)

        index[session_id] = {
            "session_id": metadata.get("session_id"),
            "video_url": metadata.get("video_url"),
            "created_at": metadata.get("created_at"),
            "status": metadata.get("status"),
            "round_count": metadata.get("round_count", 0),
            "tags": metadata.get("tags", []),
        }

        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=4, ensure_ascii=False)
