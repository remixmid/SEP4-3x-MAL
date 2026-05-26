from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Body, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import check_user, signJWT
from app.database.db import create_tables, get_db
from app.ml.model_service import comfort_model_service
from app.ml.recommender import scenario_recommender
from app.schemas.scenario_schema import (
    ApplyOut,
    DeviceActionResult,
    FeedbackIn,
    FeedbackOut,
    ModelMetricsOut,
    ScenarioListOut,
    ScenarioOut,
    SensorMeasurement,
    UserLoginSchema,
    UserSchema,
)
from app.services.backend_client import backend_client
from app.services.feedback_service import save_feedback
from app.services.scenario_service import (
    create_scenario,
    get_all_scenarios,
    get_latest_scenario,
    get_scenario_or_none,
    to_scenario_out,
)
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.api:app", host="192.168.123.52", port=8081, reload=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    comfort_model_service.load_or_train()
    yield


#protected routes
private_router = APIRouter(
    prefix="/api",
    dependencies=[Depends(JWTBearer())]
)

# Public routes
public_router = APIRouter(prefix="/auth")

app = FastAPI(
    title="SEP4 MAL / ML Service API",
    version="1.0.0",
    description=(
        "ML service for recommending room scenarios based on "
        "temperature, humidity, and time features."
    ),
    lifespan=lifespan,
)

@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your example blog app!"}

@private_router.get("/health")
async def health():
    return {"status": "ok"}


@private_router.get("/model/metrics", response_model=ModelMetricsOut)
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


@private_router.post("/model/retrain", response_model=ModelMetricsOut)
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


@private_router.get("/scenario/current", response_model=ScenarioOut)
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


@private_router.post("/scenario/predict", response_model=ScenarioOut)
async def predict_scenario_from_payload(
    payload: SensorMeasurement,
    db: Session = Depends(get_db),
):
    recommendation = scenario_recommender.recommend(payload)
    scenario = create_scenario(db, recommendation, source="model")

    return to_scenario_out(scenario)


@private_router.get("/scenario/all", response_model=ScenarioListOut)
async def get_scenarios(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
):
    scenarios = get_all_scenarios(db, limit=limit)

    return ScenarioListOut(
        scenarios=[to_scenario_out(scenario) for scenario in scenarios]
    )


def _actions_for_scenario(scenario) -> list[tuple[str, str]]:
    """Derive device actions from the scenario's own preferred vs current values."""
    actions: list[tuple[str, str]] = []

    current_temp = scenario.current_temperature
    current_hum = scenario.current_humidity

    # --- Heater ---
    # If we know current temperature: heat up when room is colder than preferred.
    # Fallback: use preferred temperature against the model's comfort optimum (21°C).
    if current_temp is not None:
        heater_action = "turn on" if current_temp < scenario.pref_temperature else "turn off"
    else:
        heater_action = "turn on" if scenario.pref_temperature < 21.0 else "turn off"
    actions.append(("Heater", heater_action))

    # --- Windows ---
    # Open windows when current humidity exceeds preferred (ventilate to reduce moisture).
    # Fallback: open if preferred humidity is above the comfort optimum (50%).
    if current_hum is not None:
        window_action = "open" if current_hum > scenario.pref_humidity else "close"
    else:
        window_action = "open" if scenario.pref_humidity > 50.0 else "close"
    actions.append(("Windows", window_action))

    # --- Curtain ---
    # Open during daytime hours (stored in the scenario from sensor timestamp).
    if scenario.hour is not None:
        curtain_action = "open" if 8 <= scenario.hour < 20 else "close"
    else:
        curtain_action = "open"
    actions.append(("Curtain", curtain_action))

    return actions


@private_router.post("/scenario/{scenario_id}/apply", response_model=ApplyOut)
async def apply_scenario(scenario_id: int, db: Session = Depends(get_db)):
    """Apply a scenario by sending device actions to the backend."""
    scenario = get_scenario_or_none(db, scenario_id)

    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")

    planned = _actions_for_scenario(scenario)
    results: list[DeviceActionResult] = []

    for device, action in planned:
        try:
            await backend_client.send_device_action(device, action)
            results.append(DeviceActionResult(device=device, action=action, success=True))
        except Exception as exc:
            results.append(
                DeviceActionResult(device=device, action=action, success=False, detail=str(exc))
            )

    # Mark scenario as applied only if all actions succeeded
    if all(r.success for r in results):
        scenario.applied = True
        db.commit()

    return ApplyOut(scenarioId=scenario_id, actions=results)


@private_router.post("/feedback", response_model=FeedbackOut, status_code=201)
async def post_feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    try:
        return save_feedback(db, payload)

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@private_router.post("/TBA_FEEDBACK", response_model=FeedbackOut, status_code=201)
async def post_tba_feedback(
    payload: FeedbackIn,
    db: Session = Depends(get_db),
):
    return await post_feedback(payload, db)

@public_router.post("/user/signup", tags=["user"])
async def create_user(user: UserSchema = Body(...)):
    users.append(user) # replace with db call
    return signJWT(user.email)

@public_router.post("/user/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {
        "error": "Wrong login details!"
    }

app.include_router(private_router)
app.include_router(public_router)