import os
import cv2
import json
import numpy as np
from utils import setup_logger, ensure_dir

logger = setup_logger("ScreenshotManager")

class ScreenshotManager:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        ensure_dir(self.output_dir)

    def save_round(self, frame: np.ndarray, round_num: int, timestamp: float, 
                  minimap_roi: tuple, full_screenshot: bool = False):
        """
        Saves the minimap and optionally full screenshot for a round.
        """
        ensure_dir(self.output_dir)
        
        # Save Minimap
        x, y, w, h = minimap_roi
        # Clamp ROI
        h_img, w_img = frame.shape[:2]
        x = max(0, min(x, w_img))
        y = max(0, min(y, h_img))
        w = max(1, min(w, w_img - x))
        h = max(1, min(h, h_img - y))
        
        minimap_img = frame[y:y+h, x:x+w]
        minimap_filename = f"round_{round_num:02d}.png"
        minimap_path = os.path.join(self.output_dir, minimap_filename)
        cv2.imwrite(minimap_path, minimap_img)
        logger.info(f"Saved minimap: {minimap_path}")
        
        # Save Full Screenshot if requested
        if full_screenshot:
            full_filename = f"round_{round_num:02d}_full.png"
            full_path = os.path.join(self.output_dir, full_filename)
            cv2.imwrite(full_path, frame)
        
        # Save Metadata
        metadata = {
            "round": round_num,
            "timestamp": timestamp,
            "minimap_file": minimap_filename,
            "minimap_roi": minimap_roi
        }
        
        meta_filename = f"round_{round_num:02d}_metadata.json"
        with open(os.path.join(self.output_dir, meta_filename), 'w') as f:
            json.dump(metadata, f, indent=4)
