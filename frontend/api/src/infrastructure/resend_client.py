from typing import Dict, Any, Optional
import httpx
from src.core.config import get_settings


class ResendClient:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.RESEND_API_KEY
        self.base_url = "https://api.resend.com/emails"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str = "onboarding@resend.dev",
    ) -> Optional[str]:
        if not self.api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(self.base_url, headers=headers, json=payload)
            if res.status_code in (200, 201):
                return res.json().get("id")
            return None
