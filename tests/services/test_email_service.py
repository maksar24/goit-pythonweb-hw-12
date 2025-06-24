import pytest
from unittest.mock import patch, AsyncMock
from fastapi_mail.errors import ConnectionErrors

from src.services.email import send_email, send_password_reset_email


@pytest.mark.asyncio
@patch("src.services.email.FastMail.send_message", new_callable=AsyncMock)
@patch("src.services.email.create_email_token", return_value="test_token")
async def test_send_email_success(mock_token, mock_send):
    email = "user@example.com"
    username = "testuser"
    host = "http://localhost:8000"

    await send_email(email, username, host)

    mock_send.assert_called_once()
    args, kwargs = mock_send.call_args

    # Перевіримо, що шаблон правильний
    assert kwargs["template_name"] == "verify_email.html"
    # Перевіримо, що в тілі повідомлення є потрібні ключі
    body = args[0].template_body
    assert body["host"] == host
    assert body["username"] == username
    assert body["token"] == "test_token"


@pytest.mark.asyncio
@patch("src.services.email.FastMail.send_message", new_callable=AsyncMock)
async def test_send_password_reset_email_success(mock_send):
    email = "user@example.com"
    username = "testuser"
    reset_link = "http://localhost:8000/reset?token=abc123"

    await send_password_reset_email(email, username, reset_link)

    mock_send.assert_called_once()
    args, kwargs = mock_send.call_args

    assert kwargs["template_name"] == "reset_password.html"
    body = args[0].template_body
    assert body["username"] == username
    assert body["reset_link"] == reset_link


@pytest.mark.asyncio
@patch(
    "src.services.email.FastMail.send_message",
    side_effect=ConnectionErrors("SMTP Error"),
)
@patch("src.services.email.create_email_token", return_value="test_token")
async def test_send_email_failure_logs_error(mock_token, mock_send, caplog):
    email = "user@example.com"
    username = "testuser"
    host = "http://localhost:8000"

    with caplog.at_level("ERROR"):
        await send_email(email, username, host)
        assert "Email sending failed" in caplog.text


@pytest.mark.asyncio
@patch(
    "src.services.email.FastMail.send_message",
    side_effect=ConnectionErrors("SMTP Error"),
)
async def test_send_password_reset_email_failure_logs_error(mock_send, caplog):
    email = "user@example.com"
    username = "testuser"
    reset_link = "http://localhost/reset"

    with caplog.at_level("ERROR"):
        await send_password_reset_email(email, username, reset_link)
        assert "Email sending failed" in caplog.text
