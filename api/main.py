from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# Load env variables before starting
load_dotenv()

from api.routers import assessment, webrtc

app = FastAPI(
    title="AI Skill Assessment API",
    description="Production API for AI-Powered Skill Assessment & Personalized Learning Plan Agent",
    version="1.0.0",
)

# Allow CORS for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assessment.router, prefix="/api/v1/assessment", tags=["Assessment"])
app.include_router(webrtc.router, prefix="/api/v1/live", tags=["Live Session"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
