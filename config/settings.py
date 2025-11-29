# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Base Directories
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = Path(__file__).parent.parent / "data"
    
    # Application
    APP_NAME: str = "SwasthAI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str
    WEBHOOK_URL: str = ""
    
    # Database Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "SwasthAI"
    DATABASE_NAME: str = "swasthai"
    
    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Ollama Configuration (for Triage & Surveillance)
    OLLAMA_MODEL: str = "llama3.2:3b-instruct-q4_K_M"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TEMPERATURE: float = 0.3
    
    # NVIDIA NIM Configuration (for Coordinator & Alert)
    NVIDIA_API_KEY: str = ""
    NVIDIA_MODEL: str = "mistralai/mistral-medium-3-instruct"
    NVIDIA_TEMPERATURE: float = 0.7
    
    # Google Gemini API
    GOOGLE_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_API_KEY: Optional[str] = None
    MAX_RPM: int = 60
    TEMP_FILES_DIR: str = "temp_media"
    MAX_FILE_SIZE_MB: int = 20
    
    # General LLM Settings
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-2.0-flash-exp"
    LLM_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4096
    
    # Surveillance Configuration
    SURVEILLANCE_INTERVAL_MINUTES: int = 15
    ANOMALY_THRESHOLD: int = 5
    SPIKE_WINDOW_HOURS: int = 24
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Sarvam Translation API
    SARVAM_API_KEY: Optional[str] = Field(
        default=None, description="Sarvam translation API key"
    )
    
    # CrewAI
    CREWAI_MEMORY: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
        # ✅ ADD THIS to prevent multiple loads
        env_file_encoding = "utf-8"
    
    @property
    def mongodb_uri(self) -> str:
        """Get MongoDB connection string"""
        return self.MONGODB_URL
    
    @property
    def ollama_config(self) -> dict:
        """LLM config for Ollama (Triage & Surveillance)"""
        return {
            "model": f"ollama/{self.OLLAMA_MODEL}",
            "base_url": self.OLLAMA_BASE_URL,
            "temperature": self.OLLAMA_TEMPERATURE
        }
    
    @property
    def nvidia_config(self) -> dict:
        """LLM config for NVIDIA NIM (Coordinator & Alert)"""
        return {
            "model": f"nvidia_nim/{self.NVIDIA_MODEL}",
            "api_key": self.NVIDIA_API_KEY,
            "base_url": "https://integrate.api.nvidia.com/v1",
            "temperature": self.NVIDIA_TEMPERATURE
        }

# ✅ Singleton pattern - only load once
_settings_instance = None

def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        # Create directories
        _settings_instance.BASE_DIR.joinpath("logs").mkdir(exist_ok=True)
        _settings_instance.DATA_DIR.mkdir(exist_ok=True)
        
        # Log configuration once
        print(f"✅ SwasthAI Settings Loaded (Mixed LLM Strategy)")
        print(f"   - Environment: {_settings_instance.ENVIRONMENT}")
        print(f"   - Database: {_settings_instance.MONGODB_DB_NAME}")
        print(f"   - Ollama (Triage/Surveillance): {_settings_instance.OLLAMA_MODEL}")
        print(f"   - NVIDIA NIM (Coordinator/Alert): {_settings_instance.NVIDIA_MODEL}")
    
    return _settings_instance

# Export singleton
settings = get_settings()
