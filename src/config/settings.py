from pydantic import EmailStr, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    Attributes:
        DB_URL (str): Database connection URL.
        JWT_SECRET (str): Secret key for JWT encoding.
        JWT_ALGORITHM (str): Algorithm used for JWT, default "HS256".
        JWT_EXPIRATION_SECONDS (int): JWT token expiration time in seconds.
        JWT_REFRESH_SECRET (str): Secret key for JWT refresh tokens.
        JWT_REFRESH_EXPIRATION_MINUTES (int): Refresh token expiration time in minutes.

        MAIL_USERNAME (str): Username for mail server authentication.
        MAIL_PASSWORD (SecretStr): Password for mail server authentication.
        MAIL_FROM (EmailStr): Email address used as sender.
        MAIL_PORT (int): Port for mail server.
        MAIL_SERVER (str): Mail server address.
        MAIL_FROM_NAME (str): Display name for sender email.
        MAIL_STARTTLS (bool): Enable STARTTLS for mail, default True.
        MAIL_SSL_TLS (bool): Enable SSL/TLS for mail, default False.
        USE_CREDENTIALS (bool): Use credentials for mail server authentication.
        VALIDATE_CERTS (bool): Validate SSL certificates, default True.

        CLD_NAME (str): Cloudinary cloud name.
        CLD_API_KEY (str): Cloudinary API key.
        CLD_API_SECRET (str): Cloudinary API secret.

        REDIS_URL (str): Redis connection URL, default "redis://localhost:6379".

        DENIED_ORIGINS (List[str]): List of denied CORS origins.
        DENIED_USER_AGENTS (List[str]): List of denied user agents.

    Settings are loaded from environment variables or a `.env` file.
    """

    DB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 3600
    JWT_REFRESH_SECRET: str
    JWT_REFRESH_EXPIRATION_MINUTES: int = 10080

    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLD_NAME: str
    CLD_API_KEY: str
    CLD_API_SECRET: str

    REDIS_URL: str = "redis://localhost:6379"

    DENIED_ORIGINS: List[str] = Field(default_factory=list)
    DENIED_USER_AGENTS: List[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
