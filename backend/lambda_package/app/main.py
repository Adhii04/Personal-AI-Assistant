from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, chat, google_auth, gmail, calendar
from app.config import get_settings
from mangum import Mangum


settings = get_settings()

# Initialize app
app = FastAPI(
    title="Personal AI Assistant API",
    version="1.0.0",
    description="Phase 2: Google OAuth Integration"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(google_auth.router)
app.include_router(gmail.router)  
app.include_router(calendar.router)


@app.get("/")
def root():
    return {
        "message": "Personal AI Assistant API",
        "status": "running",
        "version": "1.0.1",
        "phase": "2 - Google OAuth"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

handler = Mangum(app)