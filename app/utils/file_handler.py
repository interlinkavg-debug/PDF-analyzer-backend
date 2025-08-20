# app/utils/file_handler.py

# Import necessary libraries
import os                     # For working with environment variables and file paths
import shutil                 # For saving uploaded files
from pathlib import Path       # For cleaner path handling in Python
from fastapi import UploadFile # For handling file uploads in FastAPI
from dotenv import load_dotenv # For loading environment variables from .env

# ------------------------------
# Step 1: Load environment variables
# ------------------------------
load_dotenv()  # Reads the .env file and loads variables into the environment

# ------------------------------
# Step 2: Retrieve the upload directory from environment variables
# ------------------------------
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")  # Default to "uploads" if not set in .env

# ------------------------------
# Step 3: Ensure upload directory exists
# ------------------------------
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)  # Create the folder if it doesn't exist

# ------------------------------
# Step 4: Function to save uploaded files to disk
# ------------------------------
def save_upload_file(upload_file: UploadFile) -> Path:
    """
    Saves an uploaded file to the configured upload directory.
    
    Args:
        upload_file (UploadFile): The uploaded file from a FastAPI endpoint.

    Returns:
        Path: The path to the saved file.
    """
    # Construct full file path
    file_path = Path(UPLOAD_DIR) / upload_file.filename

    # Open file in binary write mode and copy contents
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    # Return the saved file path
    return file_path

# ------------------------------
# Step 5: Function to delete a file
# ------------------------------
def delete_file(file_path: Path) -> None:
    """
    Deletes a file from the file system if it exists.

    Args:
        file_path (Path): Path to the file to delete.
    """
    if file_path.exists():
        file_path.unlink()  # Remove the file from disk
