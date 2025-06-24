from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import create_email_token
from src.config.settings import settings
from src.core.logger import logger

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    Send a verification email to the specified user email address.

    Args:
        email (EmailStr): Recipient's email address.
        username (str): Username of the recipient.
        host (str): Host URL used to build verification link.

    Raises:
        Logs an error if sending email fails due to connection issues.
    """
    try:
        token_verification = create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        logger.error(f"Email sending failed: {err}")


async def send_password_reset_email(email: str, username: str, reset_link: str):
    """
    Send a password reset email to the specified user email address.

    Args:
        email (str): Recipient's email address.
        username (str): Username of the recipient.
        reset_link (str): Link for resetting the password.

    Raises:
        Logs an error if sending email fails due to connection issues.
    """
    try:
        message = MessageSchema(
            subject="Reset password",
            recipients=[email],
            template_body={
                "username": username,
                "reset_link": reset_link,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password.html")
    except ConnectionErrors as err:
        logger.error(f"Email sending failed: {err}")
