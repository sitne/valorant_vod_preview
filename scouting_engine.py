import sys
import time
import os
import cv2
from typing import Optional, Callable
from config import Config
from utils import setup_logger
from downloader import VideoDownloader
from frame_extractor import FrameExtractor
from screenshot_manager import ScreenshotManager
from session_manager import SessionManager
from ocr_engine import PaddleOCREngine
from agent_detector import AgentDetector
from position_analyzer import PositionAnalyzer, RoundPositions
from formation_analyzer import FormationAnalyzer
from report_generator import ReportGenerator

logger = setup_logger("ScoutingEngine")


class ScoutingEngine:
    def __init__(
        self, config: Config, use_sessions: bool = True, session_id: str = None
    ):
        self.cfg = config
        self.use_sessions = use_sessions
        self.ocr_engine = None
        self.session_manager = None
        self.screenshot_manager = ScreenshotManager(
            config.output_dir, use_sessions=use_sessions
        )
        self.stop_requested = False

        if self.use_sessions:
            self.session_manager = SessionManager(config.output_dir)
            self.screenshot_manager.set_session_manager(self.session_manager)

    def initialize_ocr(self):
        if self.ocr_engine is None:
            try:
                logger.info("Loading OCR Engine...")
                self.ocr_engine = PaddleOCREngine(self.cfg.ocr_lang, self.cfg.use_gpu)
            except Exception as e:
                logger.critical(f"Failed to initialize OCR Engine: {e}")
                raise e

    def get_refinement_score(self, timer_str: str) -> int:
        """
        1:40に近いほど高スコア（1:40=100, 1:41=99, 1:39=39 ...）
        """
        if not timer_str:
            return -1
        try:
            parts = timer_str.split(":")
            if len(parts) != 2:
                return -1
            m, s = int(parts[0]), int(parts[1])
            if m == 1:
                if s >= 40:
                    return 100 + (40 - s)  # 1:40=100, 1:41=99, etc.
                else:
                    return s  # 1:39=39, 1:38=38, etc.
        except:
            pass
        return -1

    def is_timer_in_130s(self, timer_str: str) -> bool:
        if not timer_str:
            return False
        try:
            parts = timer_str.split(":")
            if len(parts) != 2:
                return False
            m, s = int(parts[0]), int(parts[1])
            return m == 1 and 30 <= s <= 39
        except:
            return False

    def process_video(
        self,
        local_video_path: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        session_id: Optional[str] = None,
    ):
        """
        Main processing loop
        """
        self.initialize_ocr()

        # 1. Video Source
        video_path = local_video_path

        # If the path looks like a URL, force it into config and clear video_path to trigger download
        if video_path and (
            video_path.startswith("http://") or video_path.startswith("https://")
        ):
            self.cfg.video_url = video_path
            video_path = None

        if not video_path and self.cfg.video_url:
            downloader = VideoDownloader("downloads")
            try:
                video_path = downloader.download(self.cfg.video_url)
            except Exception as e:
                logger.critical("Failed to download video.")
                raise e

        if not video_path:
            raise ValueError("No video source provided.")

        # 2. Init Session Manager
        if self.use_sessions and self.session_manager:
            self.session_manager.create_session(
                video_url=self.cfg.video_url, video_id=session_id
            )
            self.session_manager.update_session_status("processing")

        # 3. Init Frame Extractor
        frame_extractor = FrameExtractor(video_path, self.cfg.frame_sample_rate)

        # Apply dynamic scaling
        self.cfg.scale_coords(frame_extractor.width, frame_extractor.height)

        logger.info("Starting coarse-to-fine search...")
        round_count = 0

        # Coarse search settings
        COARSE_STEP = 5.0
        SKIP_AMOUNT = 60.0

        current_time = self.cfg.start_time if self.cfg.start_time is not None else 0.0
        duration = (
            min(self.cfg.end_time, frame_extractor.duration)
            if self.cfg.end_time is not None
            else frame_extractor.duration
        )

        try:
            while current_time < duration:
                if self.stop_requested:
                    logger.info("Processing stopped by user request.")
                    break

                if progress_callback:
                    progress_callback(
                        current_time / duration, f"Scanning at {current_time:.0f}s"
                    )

                # Phase 1: Coarse Search
                result = frame_extractor.get_frame_at_time(current_time)
                if result is None:
                    current_time += COARSE_STEP
                    continue

                frame_idx, timestamp, frame = result

                # OCR Batch Detection
                detections = self.ocr_engine.detect_timer_batch(
                    [frame], [self.cfg.timer_coords]
                )
                detected, confidence, _, det_round, det_timer = detections[0]

                if detected and det_timer and self.is_timer_in_130s(det_timer):
                    logger.info(
                        f"Coarse: 1:3x detected at {timestamp:.2f}s ({det_timer}). Rewinding..."
                    )

                    # Phase 2: Refinement
                    low = max(0.0, timestamp - COARSE_STEP)
                    high = timestamp

                    best_matches = self._refine_search(frame_extractor, low, high)

                    if best_matches:
                        (
                            best_frame,
                            best_timestamp,
                            best_round,
                            best_score,
                            best_timer,
                        ) = best_matches

                        round_count += 1
                        target_round = best_round if best_round else round_count

                        logger.info(
                            f"Round {target_round} saved at {best_timestamp:.2f}s ({best_timer}, score={best_score})"
                        )

                        self.screenshot_manager.save_round(
                            best_frame,
                            target_round,
                            best_timestamp,
                            self.cfg.minimap_coords,
                            self.cfg.full_screenshot,
                        )
                    else:
                        logger.warning(f"Refinement failed near {timestamp:.2f}s")

                    # Phase 3: Skip
                    current_time = timestamp + SKIP_AMOUNT
                else:
                    current_time += COARSE_STEP

        except Exception as e:
            logger.error(f"Error processing video: {e}")
            if self.use_sessions and self.session_manager:
                self.session_manager.update_session_status("failed", round_count)
            raise e
        finally:
            frame_extractor.release()
            logger.info(f"Processing complete. Detected {round_count} rounds.")

            if self.use_sessions and self.session_manager:
                self.session_manager.update_session_status("completed", round_count)

    def _refine_search(self, frame_extractor, low, high):
        """
        Binary search refinement logic
        """
        best_frame = None
        best_timestamp = 0.0
        best_timer = None
        best_round = None
        best_score = -1

        while (high - low) > 0.1:
            mid = (low + high) / 2
            ref_result = frame_extractor.get_frame_at_time(mid)
            if ref_result is None:
                low = mid
                continue

            ref_idx, ref_ts, ref_frame = ref_result
            ref_detections = self.ocr_engine.detect_timer_batch(
                [ref_frame], [self.cfg.timer_coords]
            )
            ref_detected, ref_conf, _, ref_round, ref_timer = ref_detections[0]

            score = self.get_refinement_score(ref_timer)

            if score >= 100:
                low = mid
                if score > best_score or (
                    score == best_score and ref_ts > best_timestamp
                ):
                    best_score = score
                    best_frame = ref_frame
                    best_timestamp = ref_ts
                    best_timer = ref_timer
                    if ref_round:
                        best_round = ref_round
            elif score > 0:
                high = mid
                if score > best_score:
                    best_score = score
                    best_frame = ref_frame
                    best_timestamp = ref_ts
                    best_timer = ref_timer
                    if ref_round:
                        best_round = ref_round
            else:
                low = mid

        if best_frame is not None and best_score >= 35:
            return best_frame, best_timestamp, best_round, best_score, best_timer
        return None

    def run_post_processing(
        self,
        detect_agents=False,
        cluster_formations=False,
        generate_report=False,
        report_format="markdown",
        video_source=None,
    ):
        logger.info("Starting post-processing...")
        position_analyzer = PositionAnalyzer(self.cfg.output_dir)
        positions_data = {}

        if detect_agents:
            self._run_agent_detection(position_analyzer, positions_data)
        else:
            self._load_existing_positions(positions_data)

        clusters = None
        cluster_names = {}
        if cluster_formations and positions_data:
            clusters, cluster_names = self._run_clustering(positions_data)

        if generate_report and positions_data:
            self._generate_report(
                positions_data, clusters, cluster_names, report_format, video_source
            )

    def _run_agent_detection(self, analyzer, positions_data):
        logger.info("Detecting agent positions...")
        agent_detector = AgentDetector(
            icons_dir=self.cfg.agent_icons_dir,
            detection_threshold=self.cfg.detection_threshold,
            nms_iou_threshold=self.cfg.nms_iou_threshold,
            team_color_offset=self.cfg.team_color_offset,
        )

        round_files = sorted(
            [
                f
                for f in os.listdir(self.cfg.output_dir)
                if f.startswith("round_")
                and f.endswith(".png")
                and "_full" not in f
                and "_positions" not in f
            ]
        )

        for round_file in round_files:
            try:
                round_num = int(round_file.replace("round_", "").replace(".png", ""))
            except ValueError:
                continue

            minimap_path = os.path.join(self.cfg.output_dir, round_file)
            minimap_img = cv2.imread(minimap_path)
            if minimap_img is None:
                continue

            # Load metadata
            metadata_file = os.path.join(
                self.cfg.output_dir, f"round_{round_num:02d}_metadata.json"
            )
            timestamp = 0.0
            if os.path.exists(metadata_file):
                import json

                with open(metadata_file, "r") as f:
                    timestamp = json.load(f).get("timestamp", 0.0)

            detections = agent_detector.detect(minimap_img)
            positions = analyzer.analyze_round(
                round_num, timestamp, round_file, detections
            )
            analyzer.save_positions(positions)
            positions_data[round_num] = positions

        analyzer.save_all_positions(positions_data)

    def _load_existing_positions(self, positions_data):
        import json

        all_positions_file = os.path.join(self.cfg.output_dir, "all_positions.json")
        if os.path.exists(all_positions_file):
            with open(all_positions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in data.items():
                    round_num = int(key.replace("round_", ""))
                    positions_data[round_num] = RoundPositions(**value)
            logger.info(f"Loaded {len(positions_data)} rounds.")

    def _run_clustering(self, positions_data):
        logger.info(f"Clustering with threshold {self.cfg.similarity_threshold}...")
        formation_analyzer = FormationAnalyzer(self.cfg.output_dir)
        team = self.cfg.cluster_method

        clusters = formation_analyzer.cluster_formations(
            positions_data, self.cfg.similarity_threshold, team
        )

        cluster_names = {}
        for cid, rounds in clusters.items():
            cluster_names[cid] = formation_analyzer.name_cluster(
                cid, rounds, positions_data, team
            )

        formation_analyzer.save_clusters(clusters, cluster_names, positions_data)
        return clusters, cluster_names

    def _generate_report(
        self, positions_data, clusters, cluster_names, fmt, video_source
    ):
        logger.info("Generating report...")
        generator = ReportGenerator(self.cfg.output_dir)
        content = generator.generate_markdown(
            positions_data, clusters, cluster_names, video_source
        )

        generator.save_report(content, "scouting_report.md")
        if fmt == "html":
            generator.generate_html_report(content, "scouting_report.html")
