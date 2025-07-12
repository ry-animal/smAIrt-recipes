import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
    DEFAULT_LLM_MODEL = "gemini-2.0-flash"
    DEFAULT_VISION_MODEL = "gemini-2.0-flash"
    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp"]
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"