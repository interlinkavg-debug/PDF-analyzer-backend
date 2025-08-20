from pydantic import BaseModel, Field

# This model defines the expected structure of a request for uploading and analyzing a PDF.
class PDFAnalysisRequest(BaseModel):
    """Request model for uploading and analyzing a PDF."""
    filename: str = Field(..., description="The name of the uploaded PDF file")
    content: str = Field(..., description="The extracted text content of the PDF file")

class PDFSummaryResponse(BaseModel):
    """Response model for the summarized PDF content."""
    filename: str = Field(..., description="The name of the uploaded PDF file")
    summary: str = Field(..., description="The summarized content of the PDF file")
