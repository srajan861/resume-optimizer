from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from routers import resume, analysis, history
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Resume Optimizer API starting up...")
    yield
    print("🛑 Resume Optimizer API shutting down...")


app = FastAPI(
    title="Dynamic Resume Optimizer API",
    description="ATS + Recruiter Simulation Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router, prefix="/api", tags=["Resume"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(history.router, prefix="/api", tags=["History"])


@app.get("/")
async def root():
    return {"message": "Dynamic Resume Optimizer API", "status": "healthy"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
