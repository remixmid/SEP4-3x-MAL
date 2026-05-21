import os

import pandas as pd
import pytest


os.environ.setdefault("ENVIRONMENT", "local")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_scenario.db")
os.environ.setdefault("BACKEND_BASE_URL", "http://localhost:8080")
os.environ.setdefault("MODEL_DATASET_PATH", "./preprocessed.csv")
os.environ.setdefault("MODEL_FILE_PATH", "./models/comfort_model.joblib")
os.environ.setdefault("MODEL_METADATA_PATH", "./models/model_metadata.json")


@pytest.fixture
def sample_training_dataframe() -> pd.DataFrame:
    rows = []

    temperatures = [18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0]
    humidities = [35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 62.5, 65.0]

    for index, temperature in enumerate(temperatures):
        humidity = humidities[index]

        temperature_penalty = abs(temperature - 21.5) * 0.7
        humidity_penalty = abs(humidity - 50.0) * 0.05

        comfort = 10.0 - temperature_penalty - humidity_penalty
        comfort = max(1.0, min(10.0, comfort))

        rows.append(
            {
                "temperature": temperature,
                "humidity": humidity,
                "year": 2026,
                "month": 5,
                "day_of_week": index % 7,
                "hour": 10 + index,
                "quarter": 2,
                "is_weekend": 1 if index % 7 in [5, 6] else 0,
                "comfort": comfort,
            }
        )

    return pd.DataFrame(rows)


@pytest.fixture
def sample_training_csv(tmp_path, sample_training_dataframe) -> str:
    csv_path = tmp_path / "preprocessed.csv"
    sample_training_dataframe.to_csv(csv_path, index=False)

    return str(csv_path)


@pytest.fixture
def model_paths(tmp_path) -> dict:
    return {
        "model_file_path": str(tmp_path / "models" / "comfort_model.joblib"),
        "metadata_file_path": str(tmp_path / "models" / "model_metadata.json"),
    }