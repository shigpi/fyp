"""
AWS Lambda entry point for VoiceScribe FastAPI backend.

Uses Mangum to adapt the ASGI FastAPI application to AWS Lambda's
event/context handler interface behind API Gateway.
"""

from app.main import app
from mangum import Mangum

handler = Mangum(app, lifespan="off", api_gateway_base_path="/prod")
