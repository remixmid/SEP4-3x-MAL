from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SensorMeasurement(BaseModel):
    temperature: float = Field(..., examples=[22.5])
    humidity: float = Field(..., examples=[48.0])
    timestamp: datetime | None = None


class ScenarioOut(BaseModel):
    id: int
    prefTemperature: float
    prefHumidity: float
    comfortScore: float
    source: str
    applied: bool
    createdAt: datetime
    currentTemperature: float | None = None
    currentHumidity: float | None = None

    model_config = ConfigDict(from_attributes=True)


class ScenarioListOut(BaseModel):
    scenarios: list[ScenarioOut]


class FeedbackIn(BaseModel):
    scenarioId: int
    liked: bool


class FeedbackOut(BaseModel):
    id: int
    scenarioId: int
    liked: bool
    savedAt: datetime


class ModelMetricsOut(BaseModel):
    trainRmse: float
    testRmse: float
    trainR2: float
    testR2: float
    rows: int
    features: list[str]