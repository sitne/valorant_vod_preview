import cv2
import sys
from ocr_engine import PaddleOCREngine
from config import Config
from frame_extractor import FrameExtractor

def test_ocr():
    video_path = "downloads/video.mp4"
    if not video_path:
        print("Usage: python test_ocr.py <video_path>")
        return

    cfg = Config()
    fe = FrameExtractor(video_path)
    cfg.scale_coords(fe.width, fe.height)
    
    ocr = PaddleOCREngine(device="gpu")
    
    # Get frames from 5 minutes onwards
    print("Skipping first 300 seconds...")
    for _ in range(int(300 / (1.0 / fe.sample_rate))):
        if not fe.cap.grab(): break
    
    for i, (idx, ts, frame) in enumerate(fe.extract_frames()):
        print(f"Testing Frame at {ts:.2f}s...")
        detected, confidence = ocr.detect_timer(frame, cfg.timer_coords)
        if detected:
            print(f"SUCCESS: Timer detected at {ts:.2f}s with confidence {confidence:.2f}")
            # Save the crop for visual verification
            x, y, w, h = cfg.timer_coords
            crop = frame[y:y+h, x:x+w]
            cv2.imwrite("test_timer_crop.png", crop)
        else:
            print("FAILED: Timer not detected.")
            # Save the crop anyway to see what we are looking at
            x, y, w, h = cfg.timer_coords
            crop = frame[y:y+h, x:x+w]
            cv2.imwrite("test_timer_crop_failed.png", crop)
        
        if i >= 5: # Test first 5 frames
            break

if __name__ == "__main__":
    test_ocr()
