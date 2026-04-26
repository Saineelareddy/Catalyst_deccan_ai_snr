import httpx
import logging
from typing import Any, Dict

logger = logging.getLogger("WebhookNotifier")

class WebhookNotifier:
    """
    Handles sending interview results and learning plans to external systems (ATS, Slack, etc.).
    """
    def __init__(self, target_url: str):
        self.target_url = target_url

    async def notify_ats(self, candidate_name: str, final_payload: Dict[str, Any]) -> bool:
        """
        Sends an HTTP POST to the configured webhook endpoint.
        """
        if not self.target_url:
            logger.warning("No webhook URL configured. Skipping ATS notification.")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.target_url,
                    json={
                        "event": "interview_completed",
                        "candidate": candidate_name,
                        "data": final_payload
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Successfully notified ATS for candidate {candidate_name}.")
                return True
        except httpx.RequestError as e:
            logger.error(f"Failed to send webhook to ATS: {str(e)}")
            return False
