import yaml
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

@dataclass
class Config:
    # Default Configuration
    video_url: Optional[str] = None
    output_dir: str = "output"
    
    # Minimap ROI (x, y, w, h) - Default approximate for 1080p
    # Adjust based on resolution if needed. 
    # Usually minimap is top left.
    minimap_coords: Tuple[int, int, int, int] = (40, 40, 400, 400)
    
    # Timer ROI (x, y, w, h) - Default approximate for 1080p centered top
    # "1:40" appears at top center.
    timer_coords: Tuple[int, int, int, int] = (880, 10, 160, 80)
    
    # OCR settings
    ocr_lang: str = "en"  # 'en' or 'japan'
    use_gpu: bool = True
    
    # Processing settings
    frame_sample_rate: float = 0.2 # frames per second
    confidence_threshold: float = 0.5
    full_screenshot: bool = True
    
    def scale_coords(self, width: int, height: int):
        """
        Scale coordinates if the video is not 1920x1080.
        This assumes default coords are for 1080p.
        """
        if width == 1920 and height == 1080:
            return

        scale_x = width / 1920.0
        scale_y = height / 1080.0
        
        self.minimap_coords = (
            int(self.minimap_coords[0] * scale_x),
            int(self.minimap_coords[1] * scale_y),
            int(self.minimap_coords[2] * scale_x),
            int(self.minimap_coords[3] * scale_y)
        )
        self.timer_coords = (
            int(self.timer_coords[0] * scale_x),
            int(self.timer_coords[1] * scale_y),
            int(self.timer_coords[2] * scale_x),
            int(self.timer_coords[3] * scale_y)
        )

    @staticmethod
    def load_from_yaml(path: str) -> 'Config':
        if not os.path.exists(path):
            return Config()
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        config = Config()
        if not data:
            return config

        if 'video_url' in data: config.video_url = data['video_url']
        if 'output_dir' in data: config.output_dir = data['output_dir']
        if 'minimap_coords' in data: config.minimap_coords = tuple(data['minimap_coords'])
        if 'timer_coords' in data: config.timer_coords = tuple(data['timer_coords'])
        if 'model_path' in data: config.model_path = data['model_path']
        if 'device' in data: config.device = data['device']
        if 'frame_sample_rate' in data: config.frame_sample_rate = data['frame_sample_rate']
        if 'confidence_threshold' in data: config.confidence_threshold = data['confidence_threshold']
        if 'full_screenshot' in data: config.full_screenshot = data['full_screenshot']
        
        return config
