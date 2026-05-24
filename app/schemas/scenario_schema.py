from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class IndicatorFeedbackIn(BaseModel):
    type: Literal["temperature", "humidity", "light"]
    liked: bool


class FeedbackIn(BaseModel):
    scenarioId: int
    feedback: list[IndicatorFeedbackIn] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_unique_indicators(self):
        feedback_types = [item.type for item in self.feedback]

        if len(feedback_types) != len(set(feedback_types)):
            raise ValueError("Each scenario value type can appear only once in feedback")

        return self


class IndicatorFeedbackOut(BaseModel):
    id: int
    type: str
    liked: bool
    savedAt: datetime


class FeedbackOut(BaseModel):
    scenarioId: int
    feedback: list[IndicatorFeedbackOut]


class DeviceActionResult(BaseModel):
    device: str
    action: str
    success: bool
    detail: str | None = None


class ApplyOut(BaseModel):
    scenarioId: int
    actions: list[DeviceActionResult]


class ModelMetricsOut(BaseModel):
    trainRmse: float
    testRmse: float
    trainR2: float
    testR2: float
    rows: int
    features: list[str]