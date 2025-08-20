import pytesseract
from pdf2image import convert_from_path
import logging
from typing import List
from PyPDF2 import PdfReader

from app.utils.text_chunker import chunk_text
from app.utils.llm_client import call_llm_api
from app.utils.config import settings

logger = logging.getLogger(__name__)

MIN_TEXT_LENGTH_FOR_SUMMARY = 50  # Minimum chars before calling LLM
MAX_CHUNK_SIZE = 1500  # Adjust based on your LLM's token/char limit


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Extracted text from the PDF.
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    try:
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            try:
                reader.decrypt("")  # Try to decrypt with an empty password
            except Exception:
                logger.error("PDF is encrypted and cannot be decrypted without a password.")
                raise Exception("PDF is encrypted or password-protected and cannot be processed.")
            if reader.is_encrypted:
                logger.error("PDF is still encrypted after decryption attempt.")
                raise Exception("PDF is encrypted or password-protected and cannot be processed.")
        all_text = ""
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception as page_e:
                logger.error(f"Error extracting text from page {page_num}: {page_e}")
                page_text = ""
            all_text += page_text + "\n"
            logger.debug(f"Extracted page {page_num} text length: {len(page_text)}")
        logger.info(f"Completed text extraction. Total length: {len(all_text)} characters.")
        # If no text found, try OCR fallback
        if not all_text.strip():
            logger.info("No text found with PyPDF2, attempting OCR fallback.")
            try:
                images = convert_from_path(file_path)
                ocr_text = ""
                for i, img in enumerate(images, start=1):
                    page_ocr = pytesseract.image_to_string(img)
                    ocr_text += page_ocr + "\n"
                    logger.debug(f"OCR extracted page {i} text length: {len(page_ocr)}")
                logger.info(f"OCR extraction complete. Total length: {len(ocr_text)} characters.")
                if not ocr_text.strip():
                    raise Exception("No text could be extracted from the PDF, even with OCR.")
                return ocr_text.strip()
            except Exception as ocr_e:
                logger.error(f"OCR extraction failed: {ocr_e}")
                raise Exception(f"Failed to extract text from PDF (OCR fallback also failed): {ocr_e}")
        return all_text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        error_str = str(e).lower()
        if 'encrypted' in error_str or 'password' in error_str:
            raise Exception("PDF is encrypted or password-protected and cannot be processed.")
        elif 'corrupt' in error_str or 'broken' in error_str or 'cannot read' in error_str:
            raise Exception("PDF file is corrupted and cannot be processed.")
        else:
            raise Exception(f"Failed to extract text from PDF: {e}")


def optimal_chunk_text(text: str, max_chunk_size: int = MAX_CHUNK_SIZE) -> List[str]:
    """
    Splits text into optimal chunks for LLM processing.

    Args:
        text (str): The text to split.
        max_chunk_size (int): Maximum size of each chunk.

    Returns:
        List[str]: A list of text chunks.
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word) + 1
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks


async def summarize_text_with_llm(text: str) -> str:
    """
    Summarizes a given text using the LLM API.

    Args:
        text (str): The text to summarize.

    Returns:
        str: The generated summary or the original text if too short.
    """
    logger.info("Starting text summarization with LLM...")

    if len(text) < MIN_TEXT_LENGTH_FOR_SUMMARY:
        logger.info(f"Text length {len(text)} below minimum threshold {MIN_TEXT_LENGTH_FOR_SUMMARY}. Skipping summarization.")
        return {
            "summary": text,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0
        }

    try:
        # Use optimal chunking
        chunks = optimal_chunk_text(text)
        logger.info(f"Text split into {len(chunks)} chunks for processing.")
        for i, chunk in enumerate(chunks):
            logger.info(f"Chunk {i+1} length: {len(chunk)}")

        summaries = []
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        total_cost = 0.0
        for idx, chunk in enumerate(chunks, start=1):
            prompt = (
                "Summarize the following text in a concise, clear way:\n\n"
                f"{chunk}\n\nSummary:"
            )
            try:
                chunk_result = await call_llm_api(prompt)
                summaries.append(chunk_result["summary"])
                # Aggregate token usage and cost
                total_prompt_tokens += chunk_result.get("prompt_tokens") or 0
                total_completion_tokens += chunk_result.get("completion_tokens") or 0
                total_tokens += chunk_result.get("total_tokens") or 0
                total_cost += chunk_result.get("estimated_cost") or 0.0
            except Exception as e:
                logger.error(f"LLM API failed for chunk {idx}: {e}")
                summaries.append("[Summary unavailable for this section]")

        # Combine all chunk summaries into a final summary
        if len(summaries) > 1:
            logger.info("Combining multiple chunk summaries into final summary.")
            combined_prompt = (
                "Combine the following summaries into a single coherent summary:\n\n"
                + "\n".join(summaries)
            )
            final_result = await call_llm_api(combined_prompt)
            final_summary = final_result["summary"]
            total_prompt_tokens += final_result.get("prompt_tokens") or 0
            total_completion_tokens += final_result.get("completion_tokens") or 0
            total_tokens += final_result.get("total_tokens") or 0
            total_cost += final_result.get("estimated_cost") or 0.0
        else:
            final_summary = summaries[0]

        logger.info("Summarization completed successfully.")
        return {
            "summary": final_summary,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": total_cost
        }
    except Exception as e:
        logger.error(f"Error during summarization: {e}")
        raise
