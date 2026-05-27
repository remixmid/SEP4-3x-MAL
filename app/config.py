import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or value.strip() == "":
        raise RuntimeError(f"Required environment variable {name} is not set")

    return value


ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

if ENVIRONMENT == "local":
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
else:
    DATABASE_URL = get_required_env("DATABASE_URL")

BACKEND_BASE_URL = get_required_env("BACKEND_BASE_URL")
IOT_JWT_TOKEN = get_required_env("IOT_JWT_TOKEN")

MODEL_DATASET_PATH = os.getenv(
    "MODEL_DATASET_PATH",
    str(BASE_DIR / "preprocessed.csv"),
)

MODEL_FILE_PATH = os.getenv(
    "MODEL_FILE_PATH",
    str(BASE_DIR / "models" / "comfort_model.joblib"),
)

MODEL_METADATA_PATH = os.getenv(
    "MODEL_METADATA_PATH",
    str(BASE_DIR / "models" / "model_metadata.json"),
)

MIN_TEMPERATURE = float(os.getenv("MIN_TEMPERATURE", "18.0"))
MAX_TEMPERATURE = float(os.getenv("MAX_TEMPERATURE", "26.0"))
TEMPERATURE_STEP = float(os.getenv("TEMPERATURE_STEP", "0.5"))

MIN_HUMIDITY = float(os.getenv("MIN_HUMIDITY", "35.0"))
MAX_HUMIDITY = float(os.getenv("MAX_HUMIDITY", "65.0"))
HUMIDITY_STEP = float(os.getenv("HUMIDITY_STEP", "2.5"))