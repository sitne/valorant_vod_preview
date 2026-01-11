import logging
import sys
import os
from typing import Optional

def setup_logger(name: str = "ValorantTool", log_file: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File Handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def parse_timestamp(ts_str: Optional[str]) -> Optional[float]:
    """
    Parse timestamp string (hh:mm:ss, mm:ss, or ss) to seconds.
    Returns None if input is None or empty.
    """
    if ts_str is None or not ts_str.strip():
        return None

    try:
        # If it's just a number, return as float
        if ":" not in ts_str:
            return float(ts_str)

        parts = ts_str.split(":")
        if len(parts) == 2:  # mm:ss
            m, s = map(float, parts)
            return m * 60 + s
        elif len(parts) == 3:  # hh:mm:ss
            h, m, s = map(float, parts)
            return h * 3600 + m * 60 + s
        else:
            return float(ts_str)
    except ValueError:
        return None
