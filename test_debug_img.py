from ocr_engine import PaddleOCREngine
import cv2
import numpy as np

def test_debug_image():
    ocr = PaddleOCREngine(device="gpu")
    img = cv2.imread("output/ocr_debug/debug_batch_277.7s.png")
    if img is None:
        print("Image not found")
        return

    # detect_timer_batch returns (found, best_conf, index, det_round)
    results = ocr.detect_timer_batch([img])
    for found, conf, idx, det_round in results:
        print(f"Index {idx}: Found={found}, Conf={conf:.2f}, Round={det_round}")

if __name__ == "__main__":
    test_debug_image()
