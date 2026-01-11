import numpy as np
import time
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='en')
imgs = [np.zeros((100, 200, 3), dtype=np.uint8)]
res = ocr.predict(imgs)
print("Predict Result Type:", type(res))
# For PaddleX, result is often a generator or a list of result objects
for r in res:
    print("Result Object:", r)
    # Check if it has text patterns
    if hasattr(r, 'json'):
        print("JSON format:", r.json)
