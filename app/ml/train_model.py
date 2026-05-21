import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.config import MODEL_DATASET_PATH, MODEL_FILE_PATH, MODEL_METADATA_PATH

FEATURE_COLUMNS = [
    "temperature",
    "humidity",
    "year",
    "month",
    "day_of_week",
    "hour",
    "quarter",
    "is_weekend",
]

TARGET_COLUMN = "comfort"


def load_training_data(dataset_path: str = MODEL_DATASET_PATH) -> pd.DataFrame:
    path = Path(dataset_path)

    if not path.exists():
        raise FileNotFoundError(f"Training dataset was not found: {path}")

    df = pd.read_csv(path)
    validate_training_data(df)

    return df


def validate_training_data(df: pd.DataFrame) -> None:
    required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "preprocessed.csv has wrong structure. "
            f"Missing columns: {missing_columns}. "
            f"Required columns: {required_columns}"
        )

    if df.empty:
        raise ValueError("preprocessed.csv is empty")


def train_and_save_model(
    dataset_path: str = MODEL_DATASET_PATH,
    model_file_path: str = MODEL_FILE_PATH,
    metadata_file_path: str = MODEL_METADATA_PATH,
) -> dict:
    df = load_training_data(dataset_path)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=120,
                    max_depth=12,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    train_predictions = model.predict(X_train)
    test_predictions = model.predict(X_test)

    train_mse = mean_squared_error(y_train, train_predictions)
    test_mse = mean_squared_error(y_test, test_predictions)

    metrics = {
        "train_rmse": float(np.sqrt(train_mse)),
        "test_rmse": float(np.sqrt(test_mse)),
        "train_mae": float(mean_absolute_error(y_train, train_predictions)),
        "test_mae": float(mean_absolute_error(y_test, test_predictions)),
        "train_r2": float(r2_score(y_train, train_predictions)),
        "test_r2": float(r2_score(y_test, test_predictions)),
        "rows": int(len(df)),
        "features": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
    }

    model_path = Path(model_file_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)

    metadata_path = Path(metadata_file_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    return metrics


if __name__ == "__main__":
    result = train_and_save_model()
    print(json.dumps(result, indent=2))