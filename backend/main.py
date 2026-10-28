from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.profile_routes import router as profile_router

app = FastAPI(
    title="RADIX Talent Match - Profile Builder",
    description="Candidate profile creation and management API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    profile_router,
    prefix="/api/profiles",
    tags=["Profiles"],
)


@app.get("/")
def home():
    return {
        "message": "RADIX Profile Builder API is running"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
