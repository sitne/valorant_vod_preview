import argparse
import sys
import time
import os
import cv2
from config import Config
from utils import setup_logger
from downloader import VideoDownloader
from frame_extractor import FrameExtractor
from screenshot_manager import ScreenshotManager
from ocr_engine import PaddleOCREngine


logger = setup_logger("Main")

def get_refinement_score(timer_str: str) -> int:
    """
    タイマー文字列から品質スコアを計算する
    1:40に近いほど高スコア（1:40=100, 1:41=99, 1:39=39 ...）
    """
    if not timer_str: return -1
    try:
        parts = timer_str.split(":")
        if len(parts) != 2: return -1
        m, s = int(parts[0]), int(parts[1])
        if m == 1:
            if s >= 40: return 100 + (40 - s)  # 1:40=100, 1:41=99, etc.
            else: return s  # 1:39=39, 1:38=38, etc.
    except:
        pass
    return -1

def parse_args():
    parser = argparse.ArgumentParser(description="Valorant Round Screenshot Extractor")
    
    parser.add_argument("--url", help="Video URL to download")
    parser.add_argument("--local-video", help="Path to local video file")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--ocr-lang", default="en", help="Language for PaddleOCR")
    parser.add_argument("--use-gpu", action="store_true", help="Use GPU for OCR")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU for OCR")
    parser.add_argument("--minimap-coords", help="x,y,w,h CSV")
    parser.add_argument("--full-screenshot", action="store_true", help="Save full screenshots too")
    parser.add_argument("--sample-rate", type=float, help="Frames per second to sample")
    parser.add_argument("--debug-ocr", action="store_true", help="Save OCR crop images for debugging")
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Load config from file or defaults
    config_path = args.config if args.config else "config.yaml"
    cfg = Config.load_from_yaml(config_path)
    
    # Override config with CLI args
    if args.url: cfg.video_url = args.url
    if args.output: cfg.output_dir = args.output
    if args.ocr_lang: cfg.ocr_lang = args.ocr_lang
    
    # Handle GPU flag logic
    if args.use_gpu: cfg.use_gpu = True
    elif args.no_gpu: cfg.use_gpu = False
    
    if args.full_screenshot: cfg.full_screenshot = True
    if args.sample_rate: cfg.frame_sample_rate = args.sample_rate
    if args.minimap_coords:
        cfg.minimap_coords = tuple(map(int, args.minimap_coords.split(',')))
        
    logger.info("Initializing Valorant Screenshot Tool...")
    logger.info(f"Config: {cfg}")
    
    # 1. Video Source
    video_path = None
    if args.local_video:
        video_path = args.local_video
    elif cfg.video_url:
        downloader = VideoDownloader("downloads")
        try:
            video_path = downloader.download(cfg.video_url)
        except Exception as e:
            logger.critical("Failed to download video. Exiting.")
            sys.exit(1)
    else:
        logger.error("No video source provided. Use --url or --local-video.")
        sys.exit(1)
        
    # 2. Init OCR Engine
    try:
        logger.info("loading OCR Engine...")
        ocr_engine = PaddleOCREngine(cfg.ocr_lang, cfg.use_gpu)
    except Exception as e:
        logger.critical(f"Failed to initialize OCR Engine: {e}")
        sys.exit(1)
        
    # 3. Init Managers
    screenshot_manager = ScreenshotManager(cfg.output_dir)
    frame_extractor = FrameExtractor(video_path, cfg.frame_sample_rate)
    
    # Apply dynamic scaling based on video resolution
    cfg.scale_coords(frame_extractor.width, frame_extractor.height)
    
    # 4. Coarse-to-Fine Search ベースの処理
    logger.info("Starting coarse-to-fine search...")
    round_count = 0
    
    # Coarse search settings
    COARSE_STEP = 5.0  # 秒
    SKIP_AMOUNT = 60.0  # ラウンド検出後にスキップする秒数 (短縮して短いラウンドに対応)
    
    current_time = 0.0
    duration = frame_extractor.duration
    
    def is_timer_in_130s(timer_str: str) -> bool:
        """タイマーが1:30秒台かどうか判定"""
        if not timer_str: return False
        try:
            parts = timer_str.split(":")
            if len(parts) != 2: return False
            m, s = int(parts[0]), int(parts[1])
            return m == 1 and 30 <= s <= 39
        except:
            return False
    
    def is_timer_at_140(timer_str: str) -> bool:
        """タイマーが1:40かどうか判定"""
        if not timer_str: return False
        try:
            parts = timer_str.split(":")
            if len(parts) != 2: return False
            m, s = int(parts[0]), int(parts[1])
            return m == 1 and s == 40
        except:
            return False
    
    try:
        while current_time < duration:
            # フェーズ1: Coarse Search
            result = frame_extractor.get_frame_at_time(current_time)
            if result is None:
                current_time += COARSE_STEP
                continue
            
            frame_idx, timestamp, frame = result
            
            # OCRで1:3xを検出するか確認
            detections = ocr_engine.detect_timer_batch([frame], [cfg.timer_coords])
            detected, confidence, _, det_round, det_timer = detections[0]
            
            if detected and det_timer and is_timer_in_130s(det_timer):
                # 1:3xが検出された → ラウンドが既に始まっている
                logger.info(f"Coarse: 1:3x detected at {timestamp:.2f}s ({det_timer}). Rewinding to find 1:40...")
                
                # フェーズ2: Refinement (二分探索で精査)
                low = max(0.0, timestamp - COARSE_STEP)
                high = timestamp
                best_frame = None
                best_timestamp = 0.0
                best_timer = None
                best_round = det_round
                best_score = -1
                
                # 最初に見つけた1:3xを候補として記録しておく（念のため）
                best_frame = frame
                best_timestamp = timestamp
                best_timer = det_timer
                best_score = get_refinement_score(det_timer)
                
                logger.info(f"Refinement: Starting binary search in range [{low:.2f}, {high:.2f}]")
                
                while (high - low) > 0.1:
                    mid = (low + high) / 2
                    ref_result = frame_extractor.get_frame_at_time(mid)
                    if ref_result is None:
                        low = mid # 読み込めない場合は進めるしかない
                        continue
                    
                    ref_idx, ref_ts, ref_frame = ref_result
                    ref_detections = ocr_engine.detect_timer_batch([ref_frame], [cfg.timer_coords])
                    ref_detected, ref_conf, _, ref_round, ref_timer = ref_detections[0]
                    
                    score = get_refinement_score(ref_timer)
                    
                    if score >= 100:
                        # 1:40 以上（購入フェーズ中または1:40ちょうど）
                        # より「遅い（1:39に近い）1:40」を探すため、下限を上げる
                        low = mid
                        if score > best_score or (score == best_score and ref_ts > best_timestamp):
                            best_score = score
                            best_frame = ref_frame
                            best_timestamp = ref_ts
                            best_timer = ref_timer
                            if ref_round: best_round = ref_round
                    elif score > 0:
                        # 1:39 以下（ラウンド開始後）
                        # 1:40 よりも後なので、上限を下げる
                        high = mid
                        if score > best_score:
                            best_score = score
                            best_frame = ref_frame
                            best_timestamp = ref_ts
                            best_timer = ref_timer
                            if ref_round: best_round = ref_round
                    else:
                        # タイマーが取れなかった場合
                        # 多分購入フェーズのさらに前か、画面が暗転している等
                        # 暫定的に1:40より前とみなして探索範囲を後ろにずらす
                        low = mid
                
                # 保存
                if best_frame is not None and best_score >= 35:  # 1:35以上なら保存
                    round_count += 1
                    target_round = best_round if best_round else round_count
                    round_str = f"Round {target_round}"
                    logger.info(f"{round_str} saved at {best_timestamp:.2f}s ({best_timer}, score={best_score})")
                    screenshot_manager.save_round(
                        best_frame, 
                        target_round, 
                        best_timestamp, 
                        cfg.minimap_coords, 
                        cfg.full_screenshot
                    )
                else:
                    logger.warning(f"Refinement failed at {timestamp:.2f}s. Best score={best_score}.")
                
                # フェーズ3: Skip (次のラウンドまでジャンプ)
                current_time = timestamp + SKIP_AMOUNT
                logger.info(f"Skipping to {current_time:.2f}s...")
            else:
                # 1:3xが見つからなければ次のステップへ
                current_time += COARSE_STEP
    
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        frame_extractor.release()
        logger.info(f"Processing complete. Total rounds detected: {round_count}")

if __name__ == "__main__":
    main()
