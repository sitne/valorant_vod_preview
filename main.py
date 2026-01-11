import argparse
import sys
from config import Config
from utils import setup_logger, parse_timestamp
from scouting_engine import ScoutingEngine

logger = setup_logger("Main")


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
    parser.add_argument(
        "--full-screenshot", action="store_true", help="Save full screenshots too"
    )
    parser.add_argument("--sample-rate", type=float, help="Frames per second to sample")
    parser.add_argument(
        "--debug-ocr", action="store_true", help="Save OCR crop images for debugging"
    )
    parser.add_argument("--start-time", help="Start time (hh:mm:ss, mm:ss, or ss)")
    parser.add_argument("--end-time", help="End time (hh:mm:ss, mm:ss, or ss)")

    # Session management arguments
    parser.add_argument(
        "--session-id", help="Custom session ID (default: auto-generated)"
    )
    parser.add_argument(
        "--legacy-output",
        action="store_true",
        help="Use legacy flat output structure (no sessions)",
    )

    # Agent detection arguments
    parser.add_argument(
        "--detect-agents", action="store_true", help="Detect agent positions on minimap"
    )
    parser.add_argument(
        "--detection-threshold",
        type=float,
        help="Agent detection threshold (default: 0.7)",
    )

    # Formation analysis arguments
    parser.add_argument(
        "--cluster-formations", action="store_true", help="Group similar formations"
    )
    parser.add_argument(
        "--similarity",
        type=float,
        default=0.8,
        help="Similarity threshold (default: 0.8)",
    )
    parser.add_argument(
        "--cluster-method",
        choices=["attack", "defend", "both"],
        default="attack",
        help="Which team's formation to use for clustering",
    )

    # Report generation arguments
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate markdown scouting report",
    )
    parser.add_argument(
        "--report-format",
        choices=["markdown", "html"],
        default="markdown",
        help="Report format (default: markdown)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Load config from file or defaults
    config_path = args.config if args.config else "config.yaml"
    cfg = Config.load_from_yaml(config_path)

    # Override config with CLI args
    if args.url:
        cfg.video_url = args.url
    if args.output:
        cfg.output_dir = args.output
    if args.ocr_lang:
        cfg.ocr_lang = args.ocr_lang

    # Handle GPU flag logic
    if args.use_gpu:
        cfg.use_gpu = True
    elif args.no_gpu:
        cfg.use_gpu = False

    if args.full_screenshot:
        cfg.full_screenshot = True
    if args.sample_rate:
        cfg.frame_sample_rate = args.sample_rate
    if args.minimap_coords:
        cfg.minimap_coords = tuple(map(int, args.minimap_coords.split(",")))
    if args.start_time:
        cfg.start_time = parse_timestamp(args.start_time)
    if args.end_time:
        cfg.end_time = parse_timestamp(args.end_time)

    if args.detection_threshold:
        cfg.detection_threshold = args.detection_threshold
    if args.similarity:
        cfg.similarity_threshold = args.similarity
    if args.cluster_method:
        cfg.cluster_method = args.cluster_method

    # Determine if using sessions (default: True unless --legacy-output is specified)
    use_sessions = not hasattr(args, "legacy_output") or not args.legacy_output
    session_id = getattr(args, "session_id", None)

    logger.info("Initializing Valorant Screenshot Tool...")
    logger.info(f"Config: {cfg}")
    if use_sessions:
        logger.info(f"Using session-based output structure")

    engine = ScoutingEngine(cfg, use_sessions=use_sessions)

    # Check if we only need to process existing rounds (no video processing)
    skip_video_processing = (
        args.detect_agents or args.cluster_formations or args.generate_report
    ) and not (args.url or args.local_video)

    if not skip_video_processing:
        video_source = args.local_video if args.local_video else cfg.video_url
        try:
            engine.process_video(local_video_path=video_source, session_id=session_id)
        except Exception as e:
            logger.critical(f"Processing failed: {e}")
            sys.exit(1)

    # Post-processing
    if args.detect_agents or args.cluster_formations or args.generate_report:
        video_source = args.local_video or cfg.video_url
        engine.run_post_processing(
            detect_agents=args.detect_agents,
            cluster_formations=args.cluster_formations,
            generate_report=args.generate_report,
            report_format=args.report_format,
            video_source=video_source,
        )


if __name__ == "__main__":
    main()
