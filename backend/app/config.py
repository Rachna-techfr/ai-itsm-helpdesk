from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env", override=False)
load_dotenv(BACKEND_ROOT.parent / ".env", override=False)


@dataclass
class Settings:
    mongodb_uri: str
    mongodb_db: str
    mongodb_vector_index: str
    hf_token: str
    hf_model: str
    ollama_base_url: str
    ollama_model: str
    embedding_backend: str
    servicenow_instance: str
    servicenow_user: str
    servicenow_password: str
    servicenow_token: str
    data_dir: Path
    groq_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    auto_resolve_threshold: float = 0.85
    escalate_below: float = 0.62
    rag_threshold: float = 0.18
    sync_provision: bool = False


def load_settings() -> Settings:
    data = os.getenv("DATA_DIR", "").strip()
    data_dir = Path(data) if data else BACKEND_ROOT / "data"
    return Settings(
        mongodb_uri=os.getenv("MONGODB_URI", "").strip(),
        mongodb_db=os.getenv("MONGODB_DB", "northline_itsm").strip() or "northline_itsm",
        mongodb_vector_index=os.getenv("MONGODB_VECTOR_INDEX", "").strip(),
        hf_token=os.getenv("HF_TOKEN", "").strip(),
        hf_model=os.getenv("HF_MODEL", "Qwen/Qwen2.5-3B-Instruct").strip()
        or "Qwen/Qwen2.5-3B-Instruct",
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "").strip().rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2").strip() or "llama3.2",
        embedding_backend=os.getenv("EMBEDDING_BACKEND", "auto").strip().lower() or "auto",
        servicenow_instance=os.getenv("SERVICENOW_INSTANCE", "").strip().replace(".service-now.com", ""),
        servicenow_user=os.getenv("SERVICENOW_USER", "").strip(),
        servicenow_password=os.getenv("SERVICENOW_PASSWORD", "").strip(),
        servicenow_token=os.getenv("SERVICENOW_TOKEN", "").strip(),
        data_dir=data_dir,
        sync_provision=os.getenv("DEMO_SYNC_PROVISION", "").strip() == "1",
    )
