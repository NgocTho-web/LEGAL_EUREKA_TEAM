# --- Đoạn vá lỗi Self cho Python 3.10 ---
try:
    from typing import Self
except ImportError:
    try:
        from typing_extensions import Self
        import typing
        typing.Self = Self
    except ImportError:
        pass
# ---------------------------------------

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Đổi thành "openai" khi muốn chuyển từ Ollama sang GPT
    LLM_PROVIDER: str = "ollama"

    # --- Cấu hình OLLAMA (Chạy Local hiện tại) ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_NAME: str = "ollama/qwen2.5:7b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_EMBEDDING_DIM: int = 768

    # --- Cấu hình OPENAI (Dùng khi chuyển sang GPT) ---
    OPENAI_API_KEY: str = "sk-proj-xxxxxxxxxxxxxxxx"
    OPENAI_MODEL_NAME: str = "gpt-4o"
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 1536

    # --- Cấu hình Qdrant & Neo4j ---
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "vietnamese_legal_chunks"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()