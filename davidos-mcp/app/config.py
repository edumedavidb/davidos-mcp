"""Configuration for DavidOS MCP Server."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server configuration."""
    
    # Paths
    davidos_root: Path = Path("/app/davidos")
    
    # Server
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", os.getenv("DAVIDOS_PORT", "8000")))
    log_level: str = "info"
    
    # Security
    allow_write: bool = True
    
    # Google OAuth
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_allowed_domain: str = os.getenv("GOOGLE_ALLOWED_DOMAIN", "")
    session_secret: str = os.getenv("SESSION_SECRET", "dev-secret-change-in-production")
    
    class Config:
        env_prefix = "DAVIDOS_"
        env_file = ".env"


# Initialize settings
settings = Settings()

# Allowed files for reading (relative to davidos_root)
ALLOWED_READ_FILES = {
    "context.md",
    "index.md",
    "strategy/product-vision.md",
    "strategy/strategic-bets.md",
    "strategy/risks.md",
    "strategy/open-questions.md",
    "organisation/product-org.md",
    "execution/decision-log.md",
    "execution/weekly-notes.md",
}

# Allowed files for writing (subset of read files)
ALLOWED_WRITE_FILES = {
    "strategy/open-questions.md",
    "execution/decision-log.md",
    "execution/weekly-notes.md",
    "strategy/risks.md",
    "strategy/strategic-bets.md",
    "strategy/product-vision.md",
}

# Resource URIs mapping
RESOURCE_URIS = {
    "davidos://context": "context.md",
    "davidos://index": "index.md",
    "davidos://strategy/vision": "strategy/product-vision.md",
    "davidos://strategy/bets": "strategy/strategic-bets.md",
    "davidos://strategy/risks": "strategy/risks.md",
    "davidos://strategy/questions": "strategy/open-questions.md",
    "davidos://org/product": "organisation/product-org.md",
    "davidos://execution/decisions": "execution/decision-log.md",
    "davidos://execution/weekly": "execution/weekly-notes.md",
}
