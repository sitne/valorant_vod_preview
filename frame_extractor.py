import cv2
import math
from typing import Generator, Tuple, Optional
from utils import setup_logger
import numpy as np

logger = setup_logger("FrameExtractor")

class FrameExtractor:
    def __init__(self, video_path: str, sample_rate: float = 2.0):
        self.video_path = video_path
        self.sample_rate = sample_rate
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            raise ValueError(f"Could not open video: {video_path}")
            
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"Video opened: {self.width}x{self.height}, {self.fps} fps, {self.duration:.2f}s")
        
    def extract_frames(self) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        frame_interval = int(self.fps / self.sample_rate)
        if frame_interval < 1: frame_interval = 1
            
        current_frame = 0
        while current_frame < self.total_frames:
            # 1. 目的のフレームへ移動
            # 10フレーム以上離れている場合は set() でジャンプ、そうでなければ grab() で読み飛ばす
            # 一般的に遠い距離の set() は高速ですが、近距離は grab() の方が速い場合があります。
            target_frame = current_frame
            
            # 現在の再生位置を取得
            # 注: cv2 は常に正確な pos_frames を返さないことがあるため、内部カウント(current_frame)を優先します。
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
            # 2. 目的のフレームをデコードして読み込む
            ret, frame = self.cap.read()
            if not ret:
                break
                
            timestamp = target_frame / self.fps
            yield target_frame, timestamp, frame
            
            # 次のサンプリングポイントへ
            current_frame += frame_interval
            
        self.cap.release()
    
    def seek_to_time(self, time_sec: float) -> bool:
        """指定した時間（秒）にシークする"""
        target_frame = int(time_sec * self.fps)
        if target_frame < 0: target_frame = 0
        if target_frame >= self.total_frames: return False
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        return True
    
    def get_frame_at_time(self, time_sec: float) -> Optional[Tuple[int, float, np.ndarray]]:
        """指定した時間（秒）のフレームを取得する"""
        target_frame = int(time_sec * self.fps)
        if target_frame < 0 or target_frame >= self.total_frames:
            return None
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = self.cap.read()
        if not ret:
            return None
        timestamp = target_frame / self.fps
        return (target_frame, timestamp, frame)
    
    def release(self):
        """リソースを解放する"""
        if self.cap.isOpened():
            self.cap.release()
