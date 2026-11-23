from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    web_origin: str = "http://localhost:3000"
    agent_max_loops: int = 2
    agent_max_steps: int = 8
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
