import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"
BACKEND_ENV_FILE = BACKEND_DIR / ".env"
SUPPORTED_OPENAI_MODELS = [
    "hunyuan-pro",
    "hunyuan-standard",
    "hunyuan-large",
    "hunyuan-turbos-latest",
]


load_dotenv(ENV_FILE, override=False)
load_dotenv(BACKEND_ENV_FILE, override=False)


def _parse_origins(raw: str) -> List[str]:
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items or ["http://127.0.0.1:5173", "http://localhost:5173"]


@dataclass(frozen=True)
class Settings:
    project_name: str = "Smart Inspect Agent"
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", "").strip())
    openai_api_base: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_BASE", "").strip() or None
    )
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "").strip())
    llm_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    )
    llm_fallback_to_mock: bool = field(
        default_factory=lambda: os.getenv("LLM_FALLBACK_TO_MOCK", "true").strip().lower() != "false"
    )
    cors_origins: List[str] = field(
        default_factory=lambda: _parse_origins(os.getenv("CORS_ORIGINS", ""))
    )
    frontend_dist: Path = field(default_factory=lambda: ROOT_DIR / "frontend" / "dist")
    delilegal_api_base: str = field(
        default_factory=lambda: (
            os.getenv("DELILEGAL_API_BASE", "https://openapi.delilegal.com").strip().rstrip("/")
            or "https://openapi.delilegal.com"
        )
    )
    delilegal_appid: str = field(default_factory=lambda: os.getenv("DELILEGAL_APPID", "").strip())
    delilegal_secret: str = field(default_factory=lambda: os.getenv("DELILEGAL_SECRET", "").strip())
    delilegal_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("DELILEGAL_TIMEOUT_SECONDS", "20"))
    )
    delilegal_max_risks: int = field(
        default_factory=lambda: max(1, int(os.getenv("DELILEGAL_MAX_RISKS", "8")))
    )
    delilegal_fetch_detail_in_review: bool = field(
        default_factory=lambda: os.getenv("DELILEGAL_FETCH_DETAIL_IN_REVIEW", "").strip().lower()
        in ("1", "true", "yes")
    )
    delilegal_excerpt_max_chars: int = field(
        default_factory=lambda: max(200, int(os.getenv("DELILEGAL_EXCERPT_MAX_CHARS", "1500")))
    )

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key and self.openai_model)

    @property
    def delilegal_enabled(self) -> bool:
        return bool(self.delilegal_appid and self.delilegal_secret)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_supported_models() -> List[str]:
    return list(SUPPORTED_OPENAI_MODELS)


def _upsert_env_value(env_file: Path, key: str, value: str) -> None:
    lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
    updated_lines: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(f"{key}="):
            updated_lines.append(f"{key}={value}")
            replaced = True
        else:
            updated_lines.append(line)
    if not replaced:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        updated_lines.append(f"{key}={value}")
    env_file.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")


def set_openai_model(model_name: str) -> Settings:
    normalized_model = (model_name or "").strip()
    if normalized_model not in SUPPORTED_OPENAI_MODELS:
        raise ValueError(f"不支持的模型：{normalized_model}")
    try:
        _upsert_env_value(ENV_FILE, "OPENAI_MODEL", normalized_model)
    except OSError as exc:
        logger.warning(
            "无法写入 %s（例如只读部署目录），已仅在进程内更新 OPENAI_MODEL：%s",
            ENV_FILE,
            exc,
        )
    os.environ["OPENAI_MODEL"] = normalized_model
    get_settings.cache_clear()
    return get_settings()
