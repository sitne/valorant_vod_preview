import os
import subprocess
import logging
import time # 追加
from utils import setup_logger

logger = setup_logger("VideoDownloader")

class VideoDownloader:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def download(self, url: str) -> str:
        """
        Downloads video from URL using yt-dlp CLI.
        Returns the path to the downloaded video file.
        """
        logger.info(f"Starting download for: {url}")
        
        # 【修正ポイント】
        # ファイル名をタイトルに依存させず、タイムスタンプなどを用いた固定名にする。
        # こうすることで、OpenCVが確実にファイルを見つけられるようになります。
        safe_filename = f"video_{int(time.time())}.mp4"
        output_path = os.path.join(self.output_dir, safe_filename)
        
        # ダウンロード用コマンド
        # --restrict-filenames を付けると、スペースをアンダースコアに置換してくれるのでより安全です
        cmd_download = [
            "yt-dlp",
            "-o", output_path, # 出力パスを直接指定
            "--format", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
            "--no-warnings",
            "--restrict-filenames", # ファイル名を安全な文字のみにする
            url
        ]
        
        try:
            logger.info(f"Executing yt-dlp...")
            subprocess.run(cmd_download, check=True)
            
            # 実際にファイルが存在するか最終確認
            if os.path.exists(output_path):
                logger.info(f"Download completed: {output_path}")
                return output_path
            else:
                # 稀に拡張子が .mkv などになる場合があるためのフォールバック
                logger.error(f"Expected file not found: {output_path}")
                raise FileNotFoundError(f"Download failed for {url}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Download failed with exit code {e.returncode}")
            raise