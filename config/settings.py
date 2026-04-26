import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    """
    Application configuration settings.
    Loads from environment variables or a .env file.
    """
    # AI Provider configuration
    ai_provider: Literal["gemini", "groq"] = "gemini"
    
    # API Keys (collected as lists for rotation)
    gemini_api_keys: list[str] = []
    groq_api_keys: list[str] = []
    
    # Primary keys (fallback for legacy code)
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    
    # Default Models
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Cache settings
    cache_dir: str = ".cache"
    cache_expiration_seconds: int = 86400  # 24 hours
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        # Collect all numbered keys from environment
        import os
        from dotenv import load_dotenv
        load_dotenv() # Ensure we have latest from .env
        
        # Collect Gemini keys
        self.gemini_api_keys = []
        if self.gemini_api_key:
            self.gemini_api_keys.append(self.gemini_api_key)
        
        for i in range(1, 20): # Check up to 20 keys
            key = os.getenv(f"GEMINI_API_KEY{i}")
            if key and key not in self.gemini_api_keys:
                self.gemini_api_keys.append(key)
                
        # Collect Groq keys
        self.groq_api_keys = []
        if self.groq_api_key:
            self.groq_api_keys.append(self.groq_api_key)
            
        for i in range(1, 20):
            key = os.getenv(f"GROQ_API_KEY{i}")
            if key and key not in self.groq_api_keys:
                self.groq_api_keys.append(key)

# Global settings instance
settings = Settings()

# Ensure we have the necessary API keys depending on the provider
if settings.ai_provider == "gemini" and not settings.gemini_api_key:
    # We warn rather than raise immediately, as they might provide it in runtime
    pass
