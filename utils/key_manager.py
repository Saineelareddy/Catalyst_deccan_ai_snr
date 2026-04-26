import time
import logging
from typing import List, Dict
from config.settings import settings

logger = logging.getLogger("KeyManager")

class KeyManager:
    """
    Manages multiple API keys for different providers.
    Handles rotation, health tracking, and rate-limit cooling down.
    """
    def __init__(self):
        # Initialize key tracking structures
        self.keys: Dict[str, List[Dict]] = {
            "gemini": [{"key": k, "last_used": 0, "cooldown_until": 0, "failures": 0} for k in settings.gemini_api_keys],
            "groq": [{"key": k, "last_used": 0, "cooldown_until": 0, "failures": 0} for k in settings.groq_api_keys]
        }
        
        # Ensure we have at least one key if the lists were empty but single keys were provided
        if not self.keys["gemini"] and settings.gemini_api_key:
            self.keys["gemini"] = [{"key": settings.gemini_api_key, "last_used": 0, "cooldown_until": 0, "failures": 0}]
        if not self.keys["groq"] and settings.groq_api_key:
            self.keys["groq"] = [{"key": settings.groq_api_key, "last_used": 0, "cooldown_until": 0, "failures": 0}]

        logger.info(f"KeyManager initialized: {len(self.keys['gemini'])} Gemini keys, {len(self.keys['groq'])} Groq keys.")

    def refresh_keys(self, provider: str):
        """Reloads keys from settings (re-reads Streamlit Secrets if needed)."""
        settings.refresh()  # Re-load from secrets/env at runtime
        if provider == "gemini":
            self.keys["gemini"] = [{"key": k, "last_used": 0, "cooldown_until": 0, "failures": 0} for k in settings.gemini_api_keys]
        elif provider == "groq":
            self.keys["groq"] = [{"key": k, "last_used": 0, "cooldown_until": 0, "failures": 0} for k in settings.groq_api_keys]
        logger.info(f"KeyManager refreshed: {len(self.keys.get(provider, []))} {provider} keys loaded.")

    def get_best_keys(self, provider: str, count: int = 3) -> List[str]:
        """
        Returns the N best available keys for a provider, sorted by least recently used.
        Skips keys currently in cooldown.
        """
        if provider not in self.keys:
            return []
            
        # Try a refresh if empty — handles Streamlit Cloud lazy-secret loading
        if not self.keys[provider]:
            logger.warning(f"No keys for '{provider}'. Attempting runtime refresh from secrets...")
            self.refresh_keys(provider)

        now = time.time()
        available = [k for k in self.keys[provider] if k["cooldown_until"] <= now]
        
        # If all keys are in cooldown, just take the one that expires soonest
        if not available:
            logger.warning(f"All {provider} keys are in cooldown. Forcing use of soonest available.")
            available = sorted(self.keys[provider], key=lambda x: x["cooldown_until"])
            
        # Sort by last_used to ensure fair rotation
        available.sort(key=lambda x: x["last_used"])
        
        best_keys = [k["key"] for k in available[:count]]
        return best_keys

    def report_failure(self, provider: str, key: str, error_msg: str = ""):
        """
        Reports a failure for a specific key.
        If it looks like a rate limit (429), it cools down for longer.
        """
        if provider not in self.keys:
            return

        now = time.time()
        for k in self.keys[provider]:
            if k["key"] == key:
                k["failures"] += 1
                
                # Check for rate limit indicators in error message
                is_rate_limit = any(x in error_msg.lower() for x in ["429", "rate limit", "quota", "exhausted"])
                
                if is_rate_limit:
                    cooldown = 60 # 1 minute for rate limit
                    logger.warning(f"Key {key[:8]}... rate limited. Cooling down for {cooldown}s.")
                else:
                    cooldown = 10 # 10s for random failures
                    logger.warning(f"Key {key[:8]}... failed ({error_msg}). Cooling down for {cooldown}s.")
                    
                k["cooldown_until"] = now + cooldown
                break

    def report_success(self, provider: str, key: str):
        """
        Reports a successful call for a key, updating its last_used timestamp.
        """
        if provider not in self.keys:
            return
            
        now = time.time()
        for k in self.keys[provider]:
            if k["key"] == key:
                k["last_used"] = now
                k["cooldown_until"] = 0
                k["failures"] = 0 # Reset failures on success
                break

# Global singleton
key_manager = KeyManager()
