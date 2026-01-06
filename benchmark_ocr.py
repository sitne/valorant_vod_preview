import cv2
import numpy as np
import time
from ocr_engine import PaddleOCREngine
from config import Config

def benchmark():
    cfg = Config()
    ocr = PaddleOCREngine(device="gpu")
    
    # Create a dummy image with some text-like noise or use a real sample if available
    # For now, just a black image with a white box where text would be
    img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.putText(img, "1:40", (900, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    roi = cfg.timer_coords
    
    print("Starting benchmark (Single frame, det=True)...")
    start = time.time()
    for _ in range(20):
        ocr.detect_timer(img, roi)
    end = time.time()
    print(f"Average time per frame: {(end - start) / 20:.4f}s")

    # Mocking a recognition-only call if we were to modify it
    print("\nSimulating Recognition-only (det=False)...")
    # We'll need to modify ocr_engine.py to test this properly, 
    # but let's see the current baseline first.

if __name__ == "__main__":
    benchmark()
