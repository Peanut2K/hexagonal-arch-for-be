import os
from typing import List

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

# Email Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD", ""),
    MAIL_FROM=os.environ.get("MAIL_FROM", "noreply@example.com"),
    MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
    MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_email(email: List[EmailStr], subject: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=email,
        body=body,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_forgot_password_email(email: EmailStr, token: str):
    reset_link = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/?reset-password=true&token={token}"

    subject = "Password Reset Request"

    html = f"""
    <html>
        <body>
            <p>Hello,</p>
            <p>You have requested to reset your password.</p>
            <p>Please click the link below to reset your password:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>If you did not request this, please ignore this email.</p>
            <p>This link will expire in 15 minutes.</p>
            <br>
            <p>Best regards,</p>
            <p>Pinup Team</p>
        </body>
    </html>
    """

    await send_email([email], subject, html)


async def send_verification_email(email: EmailStr, token: str):
    verify_link = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/?verify-email=true&token={token}"

    subject = "Verify Your PINUP Account"

    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Welcome to PINUP!</h2>
            <p>Thank you for joining PINUP — the AI-powered platform for architects and property developers.</p>
            <p>Please click the button below to activate your account:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{verify_link}"
                   style="background-color: #1858C0; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Verify My Email
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{verify_link}">{verify_link}</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not create an account, please ignore this email.</p>
            <br>
            <p>Best regards,</p>
            <p>The PINUP Team</p>
        </body>
    </html>
    """

    await send_email([email], subject, html)
