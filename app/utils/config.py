from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Configuration settings for the PDF Analyzer backend.
    Loads critical environment variables with validation and defaults.
    """

    # API key for OpenAI or other LLM provider to enable summarization and analysis
    OPENROUTER_API_KEY: str = Field(..., env='OPENROUTER_API_KEY')

    # Maximum number of characters per text chunk to feed into LLM summarization
    SUMMARY_CHUNK_SIZE_CHARS: int = Field(3000, env='SUMMARY_CHUNK_SIZE_CHARS')

    # Timeout in seconds for API calls to the LLM (to avoid hanging requests)
    LLM_TIMEOUT_SECONDS: int = Field(30, env='LLM_TIMEOUT_SECONDS')

    # Maximum retry attempts for LLM API calls upon failure
    LLM_MAX_RETRIES: int = Field(3, env='LLM_MAX_RETRIES')

    # Logging level (DEBUG, INFO, WARNING, ERROR) - default is INFO
    LOG_LEVEL: str = Field('INFO', env='LOG_LEVEL')

    # LLM_MODEL_NAME
    LLM_MODEL_NAME: str = Field('tngtech/deepseek-r1t2-chimera:free', env='LLM_MODEL_NAME')

    def masked(self) -> dict:
        """
        Returns a dict of settings with sensitive info masked for safe logging.
        Masks API keys by showing only first and last 4 chars with middle replaced by stars.
        """

        def mask_secret(value: Optional[str]) -> str:
            if not value or len(value) < 8:
                return "****"  # Not enough length to mask properly
            return f"{value[:4]}****{value[-4:]}"  # Show first 4 and last 4 characters only

        return {
            "OPENROUTER_API_KEY": mask_secret(self.OPENROUTER_API_KEY),
            "SUMMARY_CHUNK_SIZE_CHARS": self.SUMMARY_CHUNK_SIZE_CHARS,
            "LLM_TIMEOUT_SECONDS": self.LLM_TIMEOUT_SECONDS,
            "LLM_MAX_RETRIES": self.LLM_MAX_RETRIES,
            "LOG_LEVEL": self.LOG_LEVEL,
        }

    class Config:
        """
        Pydantic config class to specify .env file location and encoding.
        """
        env_file = ".env"  # Auto-load environment variables from this file
        env_file_encoding = "utf-8"

# Create a single shared settings instance
settings = Settings()

