from dotenv import load_dotenv
import os
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pdf_router

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pdf_analyzer_backend")

# Initialize FastAPI app
app = FastAPI(
    title="PDF Analyzer Backend",
    description="API for uploading PDFs and generating summaries using LLM.",
    version="1.0.0"
)

# CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://v0-document-icon-next-to-header.vercel.app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://v0-document-icon-next-to-header.vercel.app"],
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
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()} for request: {request.url}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# Include PDF router WITHOUT prefix to match frontend calls directly
app.include_router(pdf_router.pdf_router)

# Health check endpoint
@app.get("/")
def read_root():
    return {"status": "OK"}

# Run using uvicorn if executed directly (Render uses PORT)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

