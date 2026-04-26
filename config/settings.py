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
        import os
        from dotenv import load_dotenv
        load_dotenv() 
        
        # Streamlit Secrets Support
        st_secrets = {}
        try:
            import streamlit as st
            st_secrets = st.secrets
        except:
            pass

        def get_sec(key, default=None):
            # Try Streamlit Secrets first, then OS Env
            val = st_secrets.get(key)
            if val is not None: return val
            return os.getenv(key, default)

        # Collect Gemini keys
        self.gemini_api_keys = []
        # Check primary key
        pk = get_sec("GEMINI_API_KEY")
        if pk: 
            self.gemini_api_key = pk
            self.gemini_api_keys.append(pk)
        
        for i in range(1, 30): # Check up to 30 keys
            key = get_sec(f"GEMINI_API_KEY{i}")
            if key and key not in self.gemini_api_keys:
                self.gemini_api_keys.append(key)
        
        print(f"📡 KEY_DISCOVERY: Found {len(self.gemini_api_keys)} Gemini keys.")
                
        # Collect Groq keys
        self.groq_api_keys = []
        pk_groq = get_sec("GROQ_API_KEY")
        if pk_groq:
            self.groq_api_key = pk_groq
            self.groq_api_keys.append(pk_groq)
            
        for i in range(1, 20):
            key = get_sec(f"GROQ_API_KEY{i}")
            if key and key not in self.groq_api_keys:
                self.groq_api_keys.append(key)
        
        print(f"📡 KEY_DISCOVERY: Found {len(self.groq_api_keys)} Groq keys.")

        if not self.gemini_api_keys and not self.groq_api_keys:
            print("⚠️ WARNING: No API keys found in Environment or Streamlit Secrets!")

# Global settings instance
settings = Settings()

# Ensure we have the necessary API keys depending on the provider
if settings.ai_provider == "gemini" and not settings.gemini_api_key:
    # We warn rather than raise immediately, as they might provide it in runtime
    pass
