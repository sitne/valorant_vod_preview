import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import glob
from pydantic import BaseModel
from typing import Optional, List
import threading
import uuid
from config import Config
from scouting_engine import ScoutingEngine
from session_manager import SessionManager
from utils import setup_logger

logger = setup_logger("Server")

app = FastAPI(title="Valorant Scouting Tool API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (output directory)
default_output = Config().output_dir
if not os.path.exists(default_output):
    os.makedirs(default_output)

app.mount("/static", StaticFiles(directory=default_output), name="static")

# Session Manager
session_manager = SessionManager(default_output)

# Serve sessions static files
sessions_dir = os.path.join(default_output, "sessions")
if os.path.exists(sessions_dir):
    app.mount("/sessions", StaticFiles(directory=sessions_dir), name="sessions")


# Global State
class JobState:
    id: str = None
    is_running: bool = False
    progress: float = 0.0
    status: str = "idle"
    current_time: float = 0.0


current_job = JobState()
engine_instance: Optional[ScoutingEngine] = None


# Pydantic Models
class AnalyzeRequest(BaseModel):
    video_url: Optional[str] = None
    local_video_path: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    detection_threshold: float = 0.7
    session_id: Optional[str] = None


class JobStatus(BaseModel):
    id: Optional[str]
    is_running: bool
    progress: float
    status: str
    current_time: float


class SessionInfo(BaseModel):
    session_id: str
    video_url: Optional[str]
    created_at: str
    status: str
    round_count: int
    tags: List[str]


# Background Task
def run_analysis_task(job_id: str, req: AnalyzeRequest):
    global current_job, engine_instance

    current_job.id = job_id
    current_job.is_running = True
    current_job.status = "processing"
    current_job.progress = 0.0

    try:
        cfg = Config()
        cfg.start_time = req.start_time
        cfg.end_time = req.end_time
        cfg.detection_threshold = req.detection_threshold
        if req.video_url:
            cfg.video_url = req.video_url

        engine_instance = ScoutingEngine(cfg, use_sessions=True)

        def progress_callback(prog: float, msg: str):
            current_job.progress = prog
            current_job.status = msg

        video_source = req.local_video_path if req.local_video_path else req.video_url
        engine_instance.process_video(
            video_source, progress_callback, session_id=req.session_id
        )

        current_job.status = "completed"
        current_job.progress = 1.0

    except Exception as e:
        logger.error(f"Job failed: {e}")
        current_job.status = f"error: {str(e)}"
    finally:
        current_job.is_running = False


@app.get("/")
def read_root():
    return {"message": "Valorant Scouting Tool API is running"}


@app.get("/sessions", response_model=List[SessionInfo])
def get_sessions():
    """List all sessions"""
    sessions = session_manager.list_sessions()
    return [
        SessionInfo(
            session_id=s.get("session_id", ""),
            video_url=s.get("video_url"),
            created_at=s.get("created_at", ""),
            status=s.get("status", "unknown"),
            round_count=s.get("round_count", 0),
            tags=s.get("tags", []),
        )
        for s in sessions
    ]


@app.get("/sessions/{session_id}", response_model=SessionInfo)
def get_session(session_id: str):
    """Get session details by ID"""
    session = session_manager.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionInfo(
        session_id=session.get("session_id", ""),
        video_url=session.get("video_url"),
        created_at=session.get("created_at", ""),
        status=session.get("status", "unknown"),
        round_count=session.get("round_count", 0),
        tags=session.get("tags", []),
    )


@app.get("/sessions/{session_id}/rounds")
def get_session_rounds(session_id: str):
    """List all rounds for a specific session"""
    session_dir = session_manager.get_session_dir(session_id)

    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session not found")

    rounds = []
    minimaps_dir = os.path.join(session_dir, "minimaps")

    if os.path.exists(minimaps_dir):
        files = glob.glob(os.path.join(minimaps_dir, "round_*.png"))
        for f in files:
            basename = os.path.basename(f)
            try:
                round_num = int(basename.replace("round_", "").replace(".png", ""))
                rounds.append(
                    {
                        "round": round_num,
                        "image_url": f"/sessions/{session_id}/minimaps/{basename}",
                        "full_image_url": f"/sessions/{session_id}/full_screenshots/round_{round_num:02d}_full.png",
                    }
                )
            except:
                continue

    return {
        "session_id": session_id,
        "rounds": sorted(rounds, key=lambda x: x["round"]),
    }


@app.get("/status", response_model=JobStatus)
def get_status():
    return JobStatus(
        id=current_job.id,
        is_running=current_job.is_running,
        progress=current_job.progress,
        status=current_job.status,
        current_time=current_job.current_time,
    )


@app.post("/analyze")
def start_analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    global current_job
    if current_job.is_running:
        raise HTTPException(status_code=400, detail="A job is already running")

    job_id = str(uuid.uuid4())
    background_tasks.add_task(run_analysis_task, job_id, req)
    return {"message": "Analysis started", "job_id": job_id}


@app.post("/stop")
def stop_analyze():
    global engine_instance, current_job
    if current_job.is_running and engine_instance:
        engine_instance.stop_requested = True
        return {"message": "Stop requested"}
    return {"message": "No running job to stop"}


@app.get("/rounds")
def get_rounds():
    """List all detected rounds in the output directory"""
    rounds = []
    # Find all round_*.png files
    # pattern: round_{xx}.png
    default_output = Config().output_dir
    files = glob.glob(os.path.join(default_output, "round_*.png"))
    for f in files:
        basename = os.path.basename(f)
        if "_full" in basename or "_positions" in basename:
            continue

        try:
            # simple parse round_09.png -> 9
            round_num = int(basename.replace("round_", "").replace(".png", ""))
            rounds.append(
                {
                    "round": round_num,
                    "image_url": f"/static/{basename}",
                    "timestamp": 0.0,  # TODO: read from metadata json if available
                }
            )
        except:
            continue

    return {"rounds": sorted(rounds, key=lambda x: x["round"])}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
