from src.infrastructure.resend_client import ResendClient


class NotificationService:
    def __init__(self, resend_client: ResendClient = None):
        self.resend = resend_client or ResendClient()

    async def send_audit_summary(self, recipient: str, document_name: str, summary: str):
        subject = f"FDIS Audit Summary: {document_name}"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 8px;">
            <h2 style="color: #0f172a; margin-bottom: 8px;">Financial Document Analysis Report</h2>
            <p style="color: #64748b; font-size: 14px;">Target Filing: <strong>{document_name}</strong></p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 16px 0;" />
            <div style="background-color: #f8fafc; padding: 16px; border-radius: 6px; line-height: 1.6; color: #334155;">
                {summary}
            </div>
            <p style="color: #94a3b8; font-size: 12px; margin-top: 24px;">Generated autonomously by Financial Document Intelligence System (FDIS).</p>
        </div>
        """
        msg_id = await self.resend.send_email(
            to_email=recipient,
            subject=subject,
            html_content=html,
        )
        return msg_id
