
import os
import logging
from typing import List
from fastapi import Depends, APIRouter, File, UploadFile, HTTPException
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
from app.services.pdf_service import extract_text_from_pdf, summarize_text_with_llm


# API Key authentication setup
API_KEY = os.getenv("OPENROUTER_API_KEY", "changeme")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

logger = logging.getLogger(__name__)
pdf_router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@pdf_router.post("/compare-pdfs")
async def compare_pdfs(files: List[UploadFile] = File(...), api_key: str = Depends(verify_api_key)):
    """
    Accepts two PDF files, summarizes both, and returns their summaries and a comparison verdict.
    """
    if len(files) != 2:
        raise HTTPException(status_code=400, detail="Exactly two PDF files are required.")

    summaries = []
    filenames = []
    summary_results = []
    for file in files:
        if file.content_type != "application/pdf" or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Invalid file type for {file.filename}. Please upload only PDF files.")
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File {file.filename} too large. Max 10MB allowed.")
        save_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(save_path, "wb") as f:
            f.write(contents)
        logger.info(f"File saved to {save_path}")
        try:
            text = extract_text_from_pdf(save_path)
        except Exception as e:
            logger.error(f"Error processing PDF file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process PDF file {file.filename}.")
        if not text.strip():
            summary_results.append({
                "summary": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0
            })
            summaries.append("")
        else:
            try:
                summary_result = await summarize_text_with_llm(text)
            except Exception as e:
                logger.error(f"Error during text summarization for {file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to generate summary for {file.filename}.")
            summary_results.append(summary_result)
            summaries.append(summary_result["summary"])
        filenames.append(file.filename)

    # Compare the two summaries using the LLM (simple prompt engineering)
    compare_prompt = (
        f"Compare the following two document summaries and decide which is more favorable.\n"
        f"Document 1 Summary:\n{summaries[0]}\n\nDocument 2 Summary:\n{summaries[1]}\n\n"
        "Respond with a verdict: 'Document 1', 'Document 2', or 'Indeterminate', and provide a brief justification."
    )
    try:
        verdict_result = await summarize_text_with_llm(compare_prompt)
    except Exception as e:
        logger.error(f"Error during comparison verdict generation: {e}")
        verdict_result = {"summary": "Unable to generate verdict.", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "estimated_cost": 0.0}

    return JSONResponse(content={
        "file1": filenames[0],
        "file2": filenames[1],
        "summary1": summary_results[0],
        "summary2": summary_results[1],
        "verdict": verdict_result
    })

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@pdf_router.post("/upload-pdf-summary")
async def upload_pdf_and_summarize(file: UploadFile = File(...), api_key: str = Depends(verify_api_key)):
    """
    Endpoint to upload a PDF file, extract its text, summarize it using LLM,
    and return the summary as JSON.
    """
    # File type and extension check
    if file.content_type != "application/pdf" or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    # Read file contents and check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 10MB allowed.")

    # Save to persistent uploads directory
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(contents)
    logger.info(f"File saved to {save_path}")

    # Extract and summarize as before
    try:
        text = extract_text_from_pdf(save_path)
    except Exception as e:
        logger.error(f"Error processing PDF file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process PDF file.")
    finally:
        # No temporary file to clean up since file is saved directly to uploads directory
        pass

    # If text extraction yields empty content, return early
    if not text.strip():
        return JSONResponse(content={"summary": "", "message": "No extractable text found in the PDF."})

    # Summarize extracted text asynchronously
    try:
        summary_result = await summarize_text_with_llm(text)
    except Exception as e:
        logger.error(f"Error during text summarization: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary from text.")

    return JSONResponse(content=summary_result)

