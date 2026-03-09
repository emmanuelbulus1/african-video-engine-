"""
main.py — FastAPI application entry point for African Video Engine
"""

import os
import asyncio
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import aiofiles

from config import (
    APP_TITLE,
    APP_VERSION,
    OPENAI_API_KEY,
    ELEVENLABS_API_KEY,
    ASSEMBLYAI_API_KEY,
    TEMP_DIR,
)
from pipeline import run_pipeline

# ── App setup ─────────────────────────────────────────────
app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(TEMP_DIR, exist_ok=True)

# ── In-memory job tracker ─────────────────────────────────
jobs: dict = {}


# ── Request / Response models ─────────────────────────────
class TransformRequest(BaseModel):
    youtube_url: str
    mode: Optional[str] = "guru"   # guru | documentary | story | news


class JobStatus(BaseModel):
    job_id:   str
    status:   str          # pending | running | done | error
    progress: int
    message:  str
    result:   Optional[dict] = None


# ── Health check ──────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "apis": {
            "openai":      "connected" if OPENAI_API_KEY      else "MISSING",
            "elevenlabs":  "connected" if ELEVENLABS_API_KEY  else "MISSING",
            "assemblyai":  "connected" if ASSEMBLYAI_API_KEY  else "MISSING",
        },
    }


# ── Start a transform job ─────────────────────────────────
@app.post("/api/transform")
async def start_transform(req: TransformRequest, background_tasks: BackgroundTasks):
    import uuid
    job_id = str(uuid.uuid4())[:8]

    jobs[job_id] = {
        "status":   "pending",
        "progress": 0,
        "message":  "Job queued",
        "result":   None,
    }

    background_tasks.add_task(_run_job, job_id, req.youtube_url, req.mode)
    return {"job_id": job_id}


async def _run_job(job_id: str, url: str, mode: str):
    """Background task that runs the full pipeline and updates job state."""

    async def progress_cb(percent: int, message: str):
        jobs[job_id]["progress"] = percent
        jobs[job_id]["message"]  = message
        jobs[job_id]["status"]   = "running"

    try:
        result = await run_pipeline(url, mode, progress_cb)
        jobs[job_id].update({
            "status":   "done",
            "progress": 100,
            "message":  "🎉 Video ready!",
            "result":   {
                "title":            result["title"],
                "transcript":       result["transcript"],
                "rewritten_script": result["rewritten_script"],
                "download_url":     f"/api/download/{result['job_id']}",
            },
        })
    except Exception as exc:
        jobs[job_id].update({
            "status":  "error",
            "message": str(exc),
        })


# ── Poll job status ───────────────────────────────────────
@app.get("/api/job/{job_id}")
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, detail="Job not found")
    return jobs[job_id]


# ── SSE progress stream ───────────────────────────────────
@app.get("/api/stream/{job_id}")
async def stream_progress(job_id: str):
    """Server-Sent Events endpoint so the frontend can get live updates."""

    async def event_generator():
        while True:
            if job_id not in jobs:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            job = jobs[job_id]
            yield f"data: {json.dumps(job)}\n\n"
            if job["status"] in ("done", "error"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Download finished video ───────────────────────────────
@app.get("/api/download/{job_id}")
async def download_video(job_id: str):
    # Find the output file for this job_id
    job_dir = os.path.join(TEMP_DIR, job_id)
    output  = os.path.join(job_dir, "output_african.mp4")
    if not os.path.exists(output):
        # fallback: audio only
        output = os.path.join(job_dir, "voiceover.mp3")
    if not os.path.exists(output):
        raise HTTPException(404, detail="Output file not found")
    return FileResponse(output, filename=f"african_engine_{job_id}.mp4")


# ── Serve React frontend (production build) ───────────────
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = os.path.join(frontend_dist, "index.html")
        return FileResponse(index)


# ── Dev entry point ───────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
