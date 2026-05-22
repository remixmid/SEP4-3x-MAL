import json
from pathlib import Path

import joblib
import pandas as pd

from app.config import MODEL_FILE_PATH, MODEL_METADATA_PATH
from app.ml.train_model import FEATURE_COLUMNS, train_and_save_model


class ComfortModelService:
    def __init__(
        self,
        model_file_path: str = MODEL_FILE_PATH,
        metadata_file_path: str = MODEL_METADATA_PATH,
    ):
        self.model_file_path = Path(model_file_path)
        self.metadata_file_path = Path(metadata_file_path)
        self.model = None
        self.metrics: dict = {}

    def load_or_train(self) -> None:
        if not self.model_file_path.exists() or not self.metadata_file_path.exists():
            self.metrics = train_and_save_model(
                model_file_path=str(self.model_file_path),
                metadata_file_path=str(self.metadata_file_path),
            )

        self.model = joblib.load(self.model_file_path)
        self.metrics = self._load_metadata()

    def predict_comfort(self, rows: pd.DataFrame) -> list[float]:
        if self.model is None:
            self.load_or_train()

        missing_columns = [
            column for column in FEATURE_COLUMNS if column not in rows.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Prediction rows have missing features: {missing_columns}"
            )

        prediction_rows = rows[FEATURE_COLUMNS]
        predictions = self.model.predict(prediction_rows)

        return [float(round(value, 4)) for value in predictions]

    def get_metrics(self) -> dict:
        if self.model is None:
            self.load_or_train()

        return self.metrics

    def retrain(self) -> dict:
        self.metrics = train_and_save_model(
            model_file_path=str(self.model_file_path),
            metadata_file_path=str(self.metadata_file_path),
        )

        self.model = joblib.load(self.model_file_path)

        return self.metrics

    def _load_metadata(self) -> dict:
        if not self.metadata_file_path.exists():
            return {}

        return json.loads(self.metadata_file_path.read_text(encoding="utf-8"))


comfort_model_service = ComfortModelService()