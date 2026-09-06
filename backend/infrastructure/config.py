from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Aurora PostgreSQL
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # Aplicación
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"

    # Bloqueo temporal de asiento (segundos)
    SEAT_LOCK_TIMEOUT_SECONDS: int = 600  # 10 min — RNF-006

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
