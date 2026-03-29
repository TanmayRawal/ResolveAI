"""
Email sender utility for ResolveAI.
Sends formatted HTML resolution emails to customers via Gmail SMTP.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os


def send_resolution_email(
    to_email: str,
    customer_name: str,
    ticket_id: str,
    response_text: str,
    citations: list = None,
    support_email: str = None,
    support_password: str = None,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> dict:
    """
    Send a formatted HTML resolution email to the customer.

    Args:
        to_email: Customer's email address.
        customer_name: Customer's first name for personalization.
        ticket_id: The support ticket ID for reference.
        response_text: The agent-generated resolution text.
        citations: List of policy citations used.
        support_email: Sender Gmail address (from .env).
        support_password: Gmail App Password (from .env).
        smtp_host: SMTP server (default: Gmail).
        smtp_port: SMTP port (default: 587 for TLS).

    Returns:
        dict with keys: success (bool), message (str).
    """
    if not support_email or not support_password:
        return {"success": False, "message": "Email credentials not configured in .env"}

    # Format response text as HTML paragraphs
    html_paragraphs = "".join(
        f"<p style='margin: 0 0 14px 0; color: #374151;'>{para.strip()}</p>"
        for para in response_text.split("\n")
        if para.strip()
    )

    # Format citations if present
    citations_html = ""
    if citations:
        citation_items = "".join(
            f"<li style='margin-bottom: 6px; color: #6366f1; font-size: 13px;'>{c}</li>"
            for c in citations
        )
        citations_html = f"""
        <div style='background: #f0f4ff; border-left: 3px solid #6366f1; border-radius: 6px; padding: 16px 20px; margin-top: 20px;'>
            <p style='margin: 0 0 8px 0; font-weight: 600; color: #4338ca; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;'>Policy References</p>
            <ul style='margin: 0; padding-left: 18px;'>{citation_items}</ul>
        </div>
        """

    current_date = datetime.now().strftime("%d %B %Y")

    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Support Resolution — {ticket_id}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">

    <!-- Email Wrapper -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background: #f3f4f6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%;">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); border-radius: 16px 16px 0 0; padding: 36px 40px; text-align: center;">
                            <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,0.6);">Support Resolution</p>
                            <h1 style="margin: 0; font-size: 26px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">Your Issue Has Been Resolved</h1>
                            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.7); font-size: 14px;">Ticket #{ticket_id} &nbsp;|&nbsp; {current_date}</p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="background: #ffffff; padding: 36px 40px;">
                            <p style="margin: 0 0 20px 0; font-size: 16px; color: #111827;">Dear <strong>{customer_name}</strong>,</p>
                            {html_paragraphs}
                            {citations_html}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background: #1f2937; border-radius: 0 0 16px 16px; padding: 24px 40px; text-align: center;">
                            <p style="margin: 0 0 4px 0; font-size: 13px; color: rgba(255,255,255,0.7);">This message was sent by the Customer Support Team.</p>
                            <p style="margin: 0; font-size: 12px; color: rgba(255,255,255,0.4);">Please do not reply to this email. For further assistance, open a new ticket.</p>
                            <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.1);">
                                <p style="margin: 0; font-size: 11px; color: rgba(255,255,255,0.3);">Powered by ResolveAI &nbsp;|&nbsp; Gemini 3.1 Flash Lite ⚡</p>
                            </div>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>

</body>
</html>
"""

    plain_text = f"Dear {customer_name},\n\n{response_text}\n\nTicket ID: {ticket_id}\n\n---\nCustomer Support Team"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Re: Your Support Request — Ticket #{ticket_id}"
        msg["From"] = f"Customer Support <{support_email}>"
        msg["To"] = to_email

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(support_email, support_password)
            server.sendmail(support_email, to_email, msg.as_string())

        return {"success": True, "message": f"Email sent successfully to {to_email}"}

    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Authentication failed. Check your Gmail App Password in .env"}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}
