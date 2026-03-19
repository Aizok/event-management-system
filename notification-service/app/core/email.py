import logging
import smtplib
from email.mime.text import MIMEText
from typing import Optional
from .config import settings

logger=logging.getLogger(__name__)

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Отправка email через SMTP"""
    msg=MIMEText(body, 'plain', 'utf-8')
    msg['Subject']=subject
    msg['From']=settings.SENDER_EMAIL
    msg['To']=to_email

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
            server.sendmail(settings.SENDER_EMAIL, to_email, msg.as_string())
        logger.info(f"Email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Email failed to {to_email}: {e}")
        return False
