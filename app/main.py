from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.db import create_tables, get_db
from app.ml.model_service import comfort_model_service
from app.ml.recommender import scenario_recommender
from app.schemas.scenario_schema import (
    FeedbackIn,
    FeedbackOut,
    ModelMetricsOut,
    ScenarioListOut,
    ScenarioOut,
    SensorMeasurement,
)
from app.services.backend_client import backend_client
from app.services.feedback_service import save_feedback
from app.services.scenario_service import (
    create_scenario,
    get_all_scenarios,
    get_latest_scenario,
    to_scenario_out,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    comfort_model_service.load_or_train()
    yield


app = FastAPI(
    title="SEP4 MAL / ML Service API",
    version="1.0.0",
    description=(
        "ML service for recommending room scenarios based on "
        "temperature, humidity, and time features."
    ),
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/model/metrics", response_model=ModelMetricsOut)
async def get_model_metrics():
    metrics = comfort_model_service.get_metrics()

    return ModelMetricsOut(
        trainRmse=metrics["train_rmse"],
        testRmse=metrics["test_rmse"],
        trainR2=metrics["train_r2"],
        testR2=metrics["test_r2"],
        rows=metrics["rows"],
        features=metrics["features"],
    )


@app.post("/model/retrain", response_model=ModelMetricsOut)
async def retrain_model():
    metrics = comfort_model_service.retrain()

    return ModelMetricsOut(
        trainRmse=metrics["train_rmse"],
        testRmse=metrics["test_rmse"],
        trainR2=metrics["train_r2"],
        testR2=metrics["test_r2"],
        rows=metrics["rows"],
        features=metrics["features"],
    )


@app.get("/scenario/current", response_model=ScenarioOut)
async def get_current_scenario(db: Session = Depends(get_db)):
    try:
        measurement = await backend_client.get_current_sensor_data()
        recommendation = scenario_recommender.recommend(measurement)

    except Exception as error:
        latest_scenario = get_latest_scenario(db)

        if latest_scenario is not None:
            return to_scenario_out(latest_scenario)

        raise HTTPException(
            status_code=503,
            detail=(
                "Could not get current sensor data from backend and "
                f"no saved scenario exists. Reason: {error}"
            ),
        ) from error

    scenario = create_scenario(db, recommendation, source="model")

    return to_scenario_out(scenario)


@app.post("/scenario/predict", response_model=ScenarioOut)
async def predict_scenario_from_payload(
    payload: SensorMeasurement,
    db: Session = Depends(get_db),
):
    recommendation = scenario_recommender.recommend(payload)
    scenario = create_scenario(db, recommendation, source="model")

    return to_scenario_out(scenario)


@app.get("/scenario/all", response_model=ScenarioListOut)
async def get_scenarios(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
):
    scenarios = get_all_scenarios(db, limit=limit)

    return ScenarioListOut(
        scenarios=[to_scenario_out(scenario) for scenario in scenarios]
    )


@app.post("/feedback", response_model=FeedbackOut, status_code=201)
async def post_feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    try:
        return save_feedback(db, payload)

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/TBA_FEEDBACK", response_model=FeedbackOut, status_code=201)
async def post_tba_feedback(
    payload: FeedbackIn,
    db: Session = Depends(get_db),
):
    return await post_feedback(payload, db)