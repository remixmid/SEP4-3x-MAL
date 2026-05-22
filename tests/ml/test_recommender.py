from datetime import datetime

import pandas as pd

from app.ml.recommender import ScenarioRecommender
from app.schemas.scenario_schema import SensorMeasurement


class DummyComfortModelService:
    def predict_comfort(self, rows: pd.DataFrame) -> list[float]:
        scores = []

        for _, row in rows.iterrows():
            temperature = row["temperature"]
            humidity = row["humidity"]

            temperature_penalty = abs(temperature - 21.0) * 0.7
            humidity_penalty = abs(humidity - 50.0) * 0.05

            score = 10.0 - temperature_penalty - humidity_penalty
            score = max(1.0, min(10.0, score))

            scores.append(float(score))

        return scores


def test_recommender_returns_valid_scenario(monkeypatch):
    monkeypatch.setattr(
        "app.ml.recommender.comfort_model_service",
        DummyComfortModelService(),
    )

    recommender = ScenarioRecommender()

    measurement = SensorMeasurement(
        temperature=24.5,
        humidity=65.0,
        timestamp=datetime(2026, 5, 21, 14, 30),
    )

    recommendation = recommender.recommend(measurement)

    assert "pref_temperature" in recommendation
    assert "pref_humidity" in recommendation
    assert "comfort_score" in recommendation

    assert 18.0 <= recommendation["pref_temperature"] <= 26.0
    assert 35.0 <= recommendation["pref_humidity"] <= 65.0
    assert 1.0 <= recommendation["comfort_score"] <= 10.0

    assert recommendation["current_temperature"] == 24.5
    assert recommendation["current_humidity"] == 65.0


def test_recommender_builds_correct_time_features(monkeypatch):
    monkeypatch.setattr(
        "app.ml.recommender.comfort_model_service",
        DummyComfortModelService(),
    )

    recommender = ScenarioRecommender()

    measurement = SensorMeasurement(
        temperature=23.0,
        humidity=55.0,
        timestamp=datetime(2026, 5, 23, 9, 0),
    )

    recommendation = recommender.recommend(measurement)

    assert recommendation["year"] == 2026
    assert recommendation["month"] == 5
    assert recommendation["day_of_week"] == 5
    assert recommendation["hour"] == 9
    assert recommendation["quarter"] == 2
    assert recommendation["is_weekend"] == 1


def test_recommender_does_not_use_light(monkeypatch):
    monkeypatch.setattr(
        "app.ml.recommender.comfort_model_service",
        DummyComfortModelService(),
    )

    recommender = ScenarioRecommender()

    measurement = SensorMeasurement(
        temperature=22.0,
        humidity=50.0,
        timestamp=datetime(2026, 5, 21, 12, 0),
    )

    recommendation = recommender.recommend(measurement)

    assert "pref_light" not in recommendation
    assert "prefLight" not in recommendation
    assert "light" not in recommendation