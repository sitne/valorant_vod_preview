import numpy as np
from paddleocr import PaddleOCR
from utils import setup_logger
from typing import Tuple, List, Optional
import os
import cv2
import sys
import logging

logger = setup_logger("PaddleOCREngine")

class PaddleOCREngine:
    def __init__(self, model_path: str = None, device: str = "cuda"):
        # 1. 環境変数の設定
        os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
        
        # 2. 引数の干渉を回避
        argv_backup = sys.argv
        sys.argv = [sys.argv[0]]
        
        # 3. ログレベルの調整
        logging.getLogger("ppocr").setLevel(logging.ERROR)
        
        try:
            # device が "cuda" なら "gpu" に変換（Paddleの慣習）
            target_device = "gpu" if (device == "cuda" or device is True) else "cpu"
            
            logger.info(f"Attempting to initialize PaddleOCR with device={target_device}...")
            
            self.ocr = PaddleOCR(
                device=target_device,
                lang='en'
            )
            
        except TypeError as e:
            logger.warning(f"Failed with 'device' argument, trying no-argument init: {e}")
            self.ocr = PaddleOCR(lang='en')
            
        finally:
            sys.argv = argv_backup
            
        logger.info("PaddleOCR 3.x initialized successfully.")

    def detect_timer(self, image: np.ndarray, roi: Tuple[int, int, int, int] = None) -> Tuple[bool, float]:
        """
        単一フレームのタイマー検出（互換性のために維持）
        """
        res = self.detect_timer_batch([image], [roi] if roi else None)
        if res:
            return res[0][0], res[0][1]
        return False, 0.0

    def detect_timer_batch(self, images: List[np.ndarray], rois: Optional[List[Tuple[int, int, int, int]]] = None) -> List[Tuple[bool, float, int]]:
        """
        複数フレームを一括処理して、タイマーが検出されたインデックスのリストを返す
        """
        processed_imgs = []
        for i, img in enumerate(images):
            roi = rois[i] if rois else None
            if roi:
                x, y, w, h = roi
                h_img, w_img = img.shape[:2]
                x, y = max(0, x), max(0, y)
                w, h = min(w, w_img - x), min(h, h_img - y)
                if w <= 10 or h <= 10:
                    # ダミー画像を入れておく（バッチのインデックスを維持するため）
                    processed_imgs.append(np.zeros((80, 80, 3), dtype=np.uint8))
                    continue
                
                crop_img = img[y:y+h, x:x+w]
                target_h = 80
                scale = target_h / h
                crop_img = cv2.resize(crop_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                processed_imgs.append(crop_img)
            else:
                processed_imgs.append(img)

        if not processed_imgs:
            return []

        # バッチ推論 (PaddleOCR 3.x / PaddleX)
        try:
            results = self.ocr.predict(processed_imgs)
        except Exception as e:
            logger.error(f"Batch inference failed: {e}")
            return [(False, 0.0, i) for i in range(len(images))]
        
        detections = []
        # predict() returns a generator or list of result objects
        for i, res in enumerate(results):
            data = res.json
            found = False
            best_conf = 0.0
            detected_round = None
            
            detected_timer_str = None
            
            if 'res' in data and 'rec_texts' in data['res']:
                texts = data['res']['rec_texts']
                scores = data['res']['rec_scores']
                
                # 1. タイマー（1:XX形式）のチェック
                # Coarse-to-Fine Searchでは、まず1:3x台を見つけて、そこから遡る
                timer_found = False
                for text, confidence in zip(texts, scores):
                    text = str(text).replace(" ", "").upper().replace(".", ":")
                    # 1:数字の形式を探す
                    if ":" in text:
                        parts = text.split(":")
                        if len(parts) == 2:
                            try:
                                m = int(parts[0].replace("O", "0").replace("I", "1"))
                                s_str = parts[1][:2] if len(parts[1]) >= 2 else parts[1]
                                s = int(s_str.replace("O", "0").replace("I", "1"))
                                if m == 1 and 0 <= s <= 59:
                                    timer_found = True
                                    best_conf = max(best_conf, confidence)
                                    detected_timer_str = f"{m}:{s:02d}"
                            except:
                                pass
                
                # 2. "ROUND X" のチェック
                has_round_keyword = False
                for t in texts:
                    t_clean = str(t).replace(" ", "").upper()
                    if "ROUND" in t_clean:
                        has_round_keyword = True
                        num_part = t_clean.replace("ROUND", "")
                        if num_part.isdigit():
                            detected_round = int(num_part)
                    elif t_clean.isdigit() and not detected_round:
                        # "ROUND" の後に別の要素として数字が来ている場合
                        detected_round = int(t_clean)

                # 判定
                if timer_found:
                    found = True
            
            detections.append((found, best_conf, i, detected_round, detected_timer_str))
            
        return detections

    def close(self):
        pass