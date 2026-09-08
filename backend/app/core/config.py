from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _as_list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str
    environment: str
    aws_region: str
    bedrock_model_id: str
    bedrock_max_tokens: int
    bedrock_temperature: float
    history_table_name: str | None
    export_bucket_name: str | None
    use_mock_ai: bool
    enable_fallback: bool
    cors_origins: list[str]
    local_data_dir: Path
    log_level: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AI Data Pipeline Generator"),
        environment=os.getenv("APP_ENV", "local"),
        aws_region=os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or "us-east-1",
        bedrock_model_id=os.getenv(
            "BEDROCK_MODEL_ID",
            "us.anthropic.claude-sonnet-4-6",
        ),
        bedrock_max_tokens=_as_int(os.getenv("BEDROCK_MAX_TOKENS"), 4096),
        bedrock_temperature=float(os.getenv("BEDROCK_TEMPERATURE", "0.2")),
        history_table_name=os.getenv("HISTORY_TABLE_NAME"),
        export_bucket_name=os.getenv("EXPORT_BUCKET_NAME"),
        use_mock_ai=_as_bool(os.getenv("USE_MOCK_AI"), False),
        enable_fallback=_as_bool(os.getenv("ENABLE_FALLBACK"), True),
        cors_origins=_as_list(
            os.getenv("CORS_ORIGINS"),
            ["http://localhost:5173", "http://127.0.0.1:5173"],
        ),
        local_data_dir=Path(os.getenv("LOCAL_DATA_DIR", ".data")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
