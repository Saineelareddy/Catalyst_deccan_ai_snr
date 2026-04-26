import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, List, Optional


class Settings(BaseSettings):
    """
    Application configuration settings.
    Loads from .env, environment variables, or Streamlit Secrets.

    IMPORTANT: gemini_api_keys and groq_api_keys are NOT pydantic fields.
    They are plain Python attributes set after __init__ to avoid pydantic_settings
    trying to auto-parse List[str] from env vars (which causes SettingsError).
    """
    # ── Simple scalar fields (safe for pydantic_settings to auto-read) ──────
    ai_provider: Literal["gemini", "groq"] = "gemini"
    gemini_api_key: Optional[str] = None   # single primary key (alias)
    groq_api_key: Optional[str] = None     # single primary key (alias)
    gemini_model: str = "gemini-1.5-flash"   # 1500 RPD free tier (vs 20 for 2.5/3.x)
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
        # Declare list attrs as plain Python (NOT pydantic fields)
        # This prevents pydantic_settings from auto-reading GEMINI_API_KEYS
        # as a List[str] and crashing on CSV format.
        object.__setattr__(self, 'gemini_api_keys', [])
        object.__setattr__(self, 'groq_api_keys', [])
        self._load_all_keys()

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _get_secrets(self) -> dict:
        """Try to get Streamlit secrets. Returns {} if not in Streamlit context."""
        try:
            import streamlit as st
            return dict(st.secrets)
        except Exception:
            return {}

    def _get(self, key: str, secrets: dict) -> Optional[str]:
        """Read from Streamlit Secrets first, then OS env."""
        val = secrets.get(key)
        if val:
            return str(val).strip() or None
        return os.getenv(key, "").strip() or None

    def _parse_csv(self, raw: Optional[str]) -> List[str]:
        """Split a comma-separated key string into a list."""
        if not raw:
            return []
        return [k.strip() for k in raw.split(",") if k.strip()]

    # ── Key loading ───────────────────────────────────────────────────────────

    def _load_all_keys(self):
        """
        Collect all API keys from all supported formats:
          Format A (CSV):      GEMINI_API_KEYS = "k1, k2, k3"
          Format B (numbered): GEMINI_API_KEY1 = "k1", GEMINI_API_KEY2 = "k2"
          Format C (single):   GEMINI_API_KEY = "k1"
        """
        from dotenv import load_dotenv
        load_dotenv()

        secrets = self._get_secrets()
        gemini_keys: List[str] = []
        groq_keys: List[str] = []

        # ── GEMINI ──────────────────────────────────────────────────────────
        # Format A
        for k in self._parse_csv(self._get("GEMINI_API_KEYS", secrets)):
            if k not in gemini_keys:
                gemini_keys.append(k)

        # Format B + C  (suffix "" = no number = GEMINI_API_KEY)
        for suffix in ["", *[str(i) for i in range(1, 31)]]:
            k = self._get(f"GEMINI_API_KEY{suffix}", secrets)
            if k and k not in gemini_keys:
                gemini_keys.append(k)

        # ── GROQ ────────────────────────────────────────────────────────────
        for k in self._parse_csv(self._get("GROQ_API_KEYS", secrets)):
            if k not in groq_keys:
                groq_keys.append(k)

        for suffix in ["", *[str(i) for i in range(1, 21)]]:
            k = self._get(f"GROQ_API_KEY{suffix}", secrets)
            if k and k not in groq_keys:
                groq_keys.append(k)

        # ── Write back as plain Python attrs (bypass pydantic validation) ───
        object.__setattr__(self, 'gemini_api_keys', gemini_keys)
        object.__setattr__(self, 'groq_api_keys', groq_keys)

        # Update scalar aliases
        if gemini_keys:
            object.__setattr__(self, 'gemini_api_key', gemini_keys[0])
        if groq_keys:
            object.__setattr__(self, 'groq_api_key', groq_keys[0])

        # ── Provider / model overrides ───────────────────────────────────────
        prov = self._get("AI_PROVIDER", secrets)
        if prov in ("gemini", "groq"):
            object.__setattr__(self, 'ai_provider', prov)

        gm = self._get("GEMINI_MODEL", secrets)
        if gm:
            object.__setattr__(self, 'gemini_model', gm)

        gq = self._get("GROQ_MODEL", secrets)
        if gq:
            object.__setattr__(self, 'groq_model', gq)

        print(
            f"📡 KEY_DISCOVERY: {len(gemini_keys)} Gemini | "
            f"{len(groq_keys)} Groq | Provider: {self.ai_provider}"
        )
        if not gemini_keys and not groq_keys:
            print("⚠️  WARNING: No API keys found! Check Streamlit Secrets or .env")

    def refresh(self):
        """Re-load all keys (call this inside the Streamlit script to get st.secrets)."""
        self._load_all_keys()


# Global singleton
settings = Settings()
