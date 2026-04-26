import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, List, Optional

class Settings(BaseSettings):
    """
    Application configuration settings.
    Loads from environment variables, .env file, or Streamlit Secrets (lazy-loaded).
    """
    ai_provider: Literal["gemini", "groq"] = "gemini"
    gemini_api_keys: List[str] = []
    groq_api_keys: List[str] = []
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    cache_dir: str = ".cache"
    cache_expiration_seconds: int = 86400

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        self._load_all_keys()

    def _get_secrets(self) -> dict:
        """Try to get Streamlit secrets dict. Returns {} if not available yet."""
        try:
            import streamlit as st
            # Access .secrets — on Cloud this is always ready during a script run
            return dict(st.secrets)
        except Exception:
            return {}

    def _get(self, key: str, secrets: dict) -> Optional[str]:
        """Read a key from Streamlit Secrets first, then OS environment."""
        val = secrets.get(key)
        if val:
            return str(val).strip()
        return os.getenv(key, "").strip() or None

    def _load_all_keys(self):
        """
        Collects all API keys from every supported secret format:
        Format 1 (numbered):   GEMINI_API_KEY, GEMINI_API_KEY1 ... GEMINI_API_KEY30
        Format 2 (list/csv):   GEMINI_API_KEYS = "key1, key2, key3"
        """
        from dotenv import load_dotenv
        load_dotenv()

        secrets = self._get_secrets()

        # ── GEMINI ──────────────────────────────────────────────────
        self.gemini_api_keys = []

        # Format 2: comma-separated list in one secret
        csv = self._get("GEMINI_API_KEYS", secrets)
        if csv:
            for k in csv.split(","):
                k = k.strip()
                if k and k not in self.gemini_api_keys:
                    self.gemini_api_keys.append(k)

        # Format 1: individual numbered keys
        for suffix in ["", *[str(i) for i in range(1, 31)]]:
            k = self._get(f"GEMINI_API_KEY{suffix}", secrets)
            if k and k not in self.gemini_api_keys:
                self.gemini_api_keys.append(k)

        # Set primary key alias
        if self.gemini_api_keys:
            self.gemini_api_key = self.gemini_api_keys[0]

        # ── GROQ ────────────────────────────────────────────────────
        self.groq_api_keys = []

        csv = self._get("GROQ_API_KEYS", secrets)
        if csv:
            for k in csv.split(","):
                k = k.strip()
                if k and k not in self.groq_api_keys:
                    self.groq_api_keys.append(k)

        for suffix in ["", *[str(i) for i in range(1, 21)]]:
            k = self._get(f"GROQ_API_KEY{suffix}", secrets)
            if k and k not in self.groq_api_keys:
                self.groq_api_keys.append(k)

        if self.groq_api_keys:
            self.groq_api_key = self.groq_api_keys[0]

        # ── AI Provider override ────────────────────────────────────
        prov = self._get("AI_PROVIDER", secrets)
        if prov in ("gemini", "groq"):
            self.ai_provider = prov

        # ── Model overrides ─────────────────────────────────────────
        gm = self._get("GEMINI_MODEL", secrets)
        if gm: self.gemini_model = gm
        gq = self._get("GROQ_MODEL", secrets)
        if gq: self.groq_model = gq

        print(f"📡 KEY_DISCOVERY: {len(self.gemini_api_keys)} Gemini keys | {len(self.groq_api_keys)} Groq keys | Provider: {self.ai_provider}")
        if not self.gemini_api_keys and not self.groq_api_keys:
            print("⚠️  WARNING: No API keys found! Check Streamlit Secrets or your .env file.")

    def refresh(self):
        """Re-load all keys at runtime (call after Streamlit context is ready)."""
        self._load_all_keys()


# Global settings singleton
settings = Settings()
