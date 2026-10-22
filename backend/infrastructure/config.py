from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ROOT_DIR = _BACKEND_DIR.parent


class Settings(BaseSettings):
    # Aurora PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"

    # Aplicación
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"

    # Bloqueo temporal de asiento (segundos)
    SEAT_LOCK_TIMEOUT_SECONDS: int = 600  # 10 min — RNF-006

    # AWS Athena / Analytics (R7)
    AWS_REGION: str = "us-east-1"
    ATHENA_DATABASE: str = "vuelos_db"
    ATHENA_S3_OUTPUT: str = "s3://s3vuelosparcial/results/"
    ATHENA_WORKGROUP: str = "primary"

    model_config = SettingsConfigDict(
        env_file=[
            str(_BACKEND_DIR / ".env"),
            str(_ROOT_DIR / ".env"),
            ".env",
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
