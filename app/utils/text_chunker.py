"""
text_chunker.py
Utility for splitting long text into smaller chunks for LLM processing.
"""

from app.utils.config import settings

def chunk_text(text: str, max_chunk_size: int = None) -> list[str]:
    """
    Splits a given text into chunks based on the SUMMARY_CHUNK_SIZE_CHARS limit
    defined in settings, unless a custom max_chunk_size is provided.
    Ensures words are not split in the middle.

    Args:
        text (str): The full text to be chunked.
        max_chunk_size (int, optional): Custom max chunk size. Defaults to settings value.

    Returns:
        list[str]: A list of text chunks, each within the defined size limit.
    """
    chunk_size = max_chunk_size or settings.SUMMARY_CHUNK_SIZE_CHARS
    words = text.split()
    
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        # +1 accounts for space between words
        if current_length + len(word) + 1 > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
