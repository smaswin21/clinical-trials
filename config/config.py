from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key:    str
    mongodb_uri:     str
    mongodb_db_name: str = "trial_matcher"

    max_candidate_trials: int = 20
    top_n_trials:         int = 5
    min_match_score:      int = 40

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
