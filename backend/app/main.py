import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.core.config import get_settings
from app.routers import auth, reports, notifications, analytics, locations
from app.routers import taxonomy as taxonomy_router

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

# Create uploads dir
os.makedirs(settings.upload_dir, exist_ok=True)

app = FastAPI(
    title="S.O.S. — Spark On-Site Solutions",
    description="AI-powered campus hazard reporting system",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(taxonomy_router.router)
app.include_router(locations.router)


@app.get("/")
def root():
    return {"message": "S.O.S. API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
