import os
from pathlib import Path
from pydantic_settings import BaseSettings
import torch

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Base paths
    BASE_DIR: Path = BASE_DIR
    MODELS_DIR: Path = BASE_DIR / "models"
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma_db"

    # batch size for embedding model
    BATCH_SIZE: int = 4
    
    # Device setup
    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
    COMPUTE_TYPE: str = "float16" if torch.cuda.is_available() else "int8"
    
    # Whisper (ASR)
    WHISPER_MODEL_NAME: str = "base"  # options: "base", "small", "medium", "distil-small.en"
    WHISPER_MODEL_DIR: Path = BASE_DIR / "models" / "whisper-base"
    
    # Silero VAD
    VAD_SAMPLING_RATE: int = 16000
    VAD_THRESHOLD: float = 0.5
    
    # Embeddings & Reranker
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_MODEL_DIR: Path = BASE_DIR / "models" / "bge-small-en-v1.5"
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-base"
    RERANKER_MODEL_DIR: Path = BASE_DIR / "models" / "bge-reranker-base"
    
    # Kokoro (TTS)
    KOKORO_MODEL_NAME: str = "hexgrad/Kokoro-82M"
    KOKORO_MODEL_DIR: Path = BASE_DIR / "models" / "kokoro-82m"
    KOKORO_VOICE: str = "af_heart"
    TTS_SAMPLE_RATE: int = 24000
    
    # LLM 
    OLLAMA_MODEL_NAME: str = "qwen3:4b"
    OLLAMA_TEMPERATURE: float = 0.2


    # External API Keys (optional for cloud LLMs like Groq / Gemini / OpenAI)
    # GROQ_API_KEY: str = ""
    # OPENAI_API_KEY: str = ""
    # GEMINI_API_KEY: str = ""

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "extra": "ignore"
    }

settings = Settings()
