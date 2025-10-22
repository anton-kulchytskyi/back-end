# app/config/cors.py

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.config.constants import DEFAULT_CORS_ORIGINS

def setup_cors(app: FastAPI):
    """Attach CORS middleware to the FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEFAULT_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
