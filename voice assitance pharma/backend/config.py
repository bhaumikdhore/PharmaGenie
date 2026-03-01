"""PharmaGenie configuration."""
import os

from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

# LLM: "ollama" (free, local) or "openai" (needs API key)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
