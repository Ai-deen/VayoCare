import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import (
    auth, routine, companion, medications, audit, emergency, alerts
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="ArogyaMitra: Smart Elderly Care & Routine-Anchored Medication Management Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(routine.router)
app.include_router(companion.router)
app.include_router(medications.router)
app.include_router(audit.router)
app.include_router(emergency.router)
app.include_router(alerts.router)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }

@app.get("/", response_class=HTMLResponse, tags=["PWA"])
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>ArogyaMitra Backend API Active</h1><p>Visit <a href='/docs'>/docs</a></p>")

@app.get("/emergency/{patient_id}", response_class=HTMLResponse, tags=["Zero-App Emergency View"])
def serve_emergency_view(patient_id: str):
    emergency_file = os.path.join(static_dir, "emergency.html")
    if os.path.exists(emergency_file):
        return FileResponse(emergency_file)
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/manifest.json", tags=["PWA"])
def serve_manifest():
    return FileResponse(os.path.join(static_dir, "manifest.json"), media_type="application/manifest+json")

@app.get("/sw.js", tags=["PWA"])
def serve_sw():
    return FileResponse(os.path.join(static_dir, "sw.js"), media_type="application/javascript")
