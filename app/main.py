from dotenv import load_dotenv
import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
import traceback
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pdf_router

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pdf_analyzer_backend")

# Initialize the FastAPI app
app = FastAPI(
    title="PDF Analyzer Backend",
    description="API for uploading PDFs and generating summaries using LLM.",
    version="1.0.0"
)

# CORS configuration (adjust for your frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://v0-document-icon-next-to-header.vercel.app/"],  # Change this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})
    logger.info(f"Response status: {response.status_code}")
    return response

# Global exception handler for validation errors
@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request: Request, exc: FastAPIRequestValidationError):
    logger.error(f"Validation error: {exc.errors()} for request: {request.url}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# Register PDF router
app.include_router(pdf_router.pdf_router, prefix="/pdf")

@app.get("/")
def read_root():
    """
    Simple health check endpoint to verify the API is running.
    """
    return {"status": "OK"}

