from datetime import datetime

import numpy as np
import pandas as pd

from app.config import (
    HUMIDITY_STEP,
    MAX_HUMIDITY,
    MAX_TEMPERATURE,
    MIN_HUMIDITY,
    MIN_TEMPERATURE,
    TEMPERATURE_STEP,
)
from app.ml.model_service import comfort_model_service
from app.ml.train_model import FEATURE_COLUMNS
from app.schemas.scenario_schema import SensorMeasurement


class ScenarioRecommender:
    def recommend(self, measurement: SensorMeasurement) -> dict:
        timestamp = measurement.timestamp or datetime.utcnow()

        time_features = self._build_time_features(timestamp)
        candidates = self._build_candidates(time_features)

        model_scores = np.array(comfort_model_service.predict_comfort(candidates))
        model_scores = np.clip(model_scores, 1.0, 10.0)

        domain_scores = candidates.apply(
            lambda row: self._domain_comfort_score(
                row["temperature"],
                row["humidity"],
            ),
            axis=1,
        ).to_numpy()

        final_scores = 0.7 * model_scores + 0.3 * domain_scores

        distance_penalty = (
            (candidates["temperature"] - 21.0).abs()
            + (candidates["humidity"] - 50.0).abs() / 10.0
        ).to_numpy()

        ranking_scores = final_scores - 0.001 * distance_penalty

        best_index = int(np.argmax(ranking_scores))
        best_row = candidates.iloc[best_index]
        best_score = final_scores[best_index]

        return {
            "pref_temperature": round(float(best_row["temperature"]), 1),
            "pref_humidity": round(float(best_row["humidity"]), 1),
            "comfort_score": round(float(best_score), 2),
            "current_temperature": measurement.temperature,
            "current_humidity": measurement.humidity,
            **time_features,
        }

    def _build_candidates(self, time_features: dict) -> pd.DataFrame:
        temperatures = np.arange(
            MIN_TEMPERATURE,
            MAX_TEMPERATURE + TEMPERATURE_STEP,
            TEMPERATURE_STEP,
        )

        humidities = np.arange(
            MIN_HUMIDITY,
            MAX_HUMIDITY + HUMIDITY_STEP,
            HUMIDITY_STEP,
        )

        rows = []

        for temperature in temperatures:
            for humidity in humidities:
                rows.append(
                    {
                        "temperature": float(round(temperature, 2)),
                        "humidity": float(round(humidity, 2)),
                        **time_features,
                    }
                )

        df = pd.DataFrame(rows)

        return df[FEATURE_COLUMNS]

    def _build_time_features(self, timestamp: datetime) -> dict:
        return {
            "year": timestamp.year,
            "month": timestamp.month,
            "day_of_week": timestamp.weekday(),
            "hour": timestamp.hour,
            "quarter": (timestamp.month - 1) // 3 + 1,
            "is_weekend": int(timestamp.weekday() in [5, 6]),
        }

    def _domain_comfort_score(self, temperature: float, humidity: float) -> float:
        temperature_score = self._temperature_score(temperature)
        humidity_score = self._humidity_score(humidity)

        raw_score = 0.6 * temperature_score + 0.4 * humidity_score

        return float(round(raw_score * 9 + 1, 4))

    def _temperature_score(self, temperature: float) -> float:
        if 20 <= temperature <= 22:
            return 1.0

        if 16 <= temperature < 20:
            return (temperature - 16) / (20 - 16)

        if 22 < temperature <= 28:
            return (28 - temperature) / (28 - 22)

        return 0.0

    def _humidity_score(self, humidity: float) -> float:
        if 40 <= humidity <= 60:
            return 1.0

        if 20 <= humidity < 40:
            return (humidity - 20) / (40 - 20)

        if 60 < humidity <= 80:
            return (80 - humidity) / (80 - 60)

        return 0.0


scenario_recommender = ScenarioRecommender()