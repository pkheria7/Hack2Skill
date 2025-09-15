"""
LegalSimplifier – unified FastAPI launcher
Compatible with the HACK2SKILL contract-spec PDF
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# load env first
load_dotenv()

# import routers
from app.api.v1 import (
    upload,
    result,
    clause,
    insert_ghost,
    negotiate,
    chat,
    timeline,
    export,
)

def create_app() -> FastAPI:
    app = FastAPI(
        title="LegalSimplifier API",
        description="Back-end for HACK2SKILL contract analyser",
        version="1.0.0",
    )

    # CORS – adjust origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # register sub-routers
    app.include_router(upload.router, prefix="/api/v1")
    app.include_router(result.router, prefix="/api/v1")
    app.include_router(clause.router, prefix="/api/v1")
    app.include_router(insert_ghost.router, prefix="/api/v1")
    app.include_router(negotiate.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(timeline.router, prefix="/api/v1")
    app.include_router(export.router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )