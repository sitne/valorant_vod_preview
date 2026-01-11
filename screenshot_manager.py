import os
import cv2
import json
import numpy as np
from typing import Optional
from utils import setup_logger, ensure_dir
from session_manager import SessionManager

logger = setup_logger("ScreenshotManager")


class ScreenshotManager:
    def __init__(self, output_dir: str, use_sessions: bool = True):
        self.output_dir = output_dir
        self.use_sessions = use_sessions
        self.session_manager: Optional[SessionManager] = None
        ensure_dir(self.output_dir)

    def set_session_manager(self, session_manager: SessionManager):
        """
        Set the session manager for session-based output.

        Args:
            session_manager: SessionManager instance
        """
        self.session_manager = session_manager
        logger.info(f"Session manager set: {session_manager.current_session_id}")

    def save_round(
        self,
        frame: np.ndarray,
        round_num: int,
        timestamp: float,
        minimap_roi: tuple,
        full_screenshot: bool = False,
    ):
        """
        Saves the minimap and optionally full screenshot for a round.
        Uses session-based directory structure if session_manager is set,
        otherwise falls back to legacy flat structure.
        """
        if self.use_sessions and self.session_manager:
            self._save_round_session(
                frame, round_num, timestamp, minimap_roi, full_screenshot
            )
        else:
            self._save_round_legacy(
                frame, round_num, timestamp, minimap_roi, full_screenshot
            )

    def _save_round_session(
        self,
        frame: np.ndarray,
        round_num: int,
        timestamp: float,
        minimap_roi: tuple,
        full_screenshot: bool = False,
    ):
        """
        Save round using session-based directory structure.
        """
        session_dir = self.session_manager.get_session_dir()

        minimaps_dir = os.path.join(session_dir, "minimaps")
        metadata_dir = os.path.join(session_dir, "metadata")
        full_screenshots_dir = os.path.join(session_dir, "full_screenshots")

        ensure_dir(minimaps_dir)
        ensure_dir(metadata_dir)
        ensure_dir(full_screenshots_dir)

        x, y, w, h = minimap_roi
        h_img, w_img = frame.shape[:2]
        x = max(0, min(x, w_img))
        y = max(0, min(y, h_img))
        w = max(1, min(w, w_img - x))
        h = max(1, min(h, h_img - y))

        minimap_img = frame[y : y + h, x : x + w]
        minimap_filename = f"round_{round_num:02d}.png"
        minimap_path = os.path.join(minimaps_dir, minimap_filename)
        cv2.imwrite(minimap_path, minimap_img)
        logger.info(f"Saved minimap: {minimap_path}")

        if full_screenshot:
            full_filename = f"round_{round_num:02d}_full.png"
            full_path = os.path.join(full_screenshots_dir, full_filename)
            cv2.imwrite(full_path, frame)

        metadata = {
            "round": round_num,
            "timestamp": timestamp,
            "minimap_file": os.path.join("minimaps", minimap_filename),
            "minimap_roi": minimap_roi,
            "session_id": self.session_manager.current_session_id,
        }

        meta_filename = f"round_{round_num:02d}_metadata.json"
        meta_path = os.path.join(metadata_dir, meta_filename)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

    def _save_round_legacy(
        self,
        frame: np.ndarray,
        round_num: int,
        timestamp: float,
        minimap_roi: tuple,
        full_screenshot: bool = False,
    ):
        """
        Save round using legacy flat directory structure.
        """
        ensure_dir(self.output_dir)

        x, y, w, h = minimap_roi
        h_img, w_img = frame.shape[:2]
        x = max(0, min(x, w_img))
        y = max(0, min(y, h_img))
        w = max(1, min(w, w_img - x))
        h = max(1, min(h, h_img - y))

        minimap_img = frame[y : y + h, x : x + w]
        minimap_filename = f"round_{round_num:02d}.png"
        minimap_path = os.path.join(self.output_dir, minimap_filename)
        cv2.imwrite(minimap_path, minimap_img)
        logger.info(f"Saved minimap: {minimap_path}")

        if full_screenshot:
            full_filename = f"round_{round_num:02d}_full.png"
            full_path = os.path.join(self.output_dir, full_filename)
            cv2.imwrite(full_path, frame)

        metadata = {
            "round": round_num,
            "timestamp": timestamp,
            "minimap_file": minimap_filename,
            "minimap_roi": minimap_roi,
        }

        meta_filename = f"round_{round_num:02d}_metadata.json"
        with open(
            os.path.join(self.output_dir, meta_filename), "w", encoding="utf-8"
        ) as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
