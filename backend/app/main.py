import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Path resolution
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.api.routes import router as api_router

app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="Multilingual, RAG-grounded IPR and Regulatory Assistant for Ayurveda & Traditional Knowledge",
    version="1.0.0",
)

# CORS middleware for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local hackathon development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to IP-SAKTI Sahayak API. Navigate to /docs for interactive Swagger UI."
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
