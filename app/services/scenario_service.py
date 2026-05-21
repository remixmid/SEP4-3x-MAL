from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.models import Scenario
from app.schemas.scenario_schema import ScenarioOut


def create_scenario(
    db: Session,
    recommendation: dict,
    source: str = "model",
) -> Scenario:
    scenario = Scenario(
        pref_temperature=recommendation["pref_temperature"],
        pref_humidity=recommendation["pref_humidity"],
        comfort_score=recommendation["comfort_score"],
        source=source,
        current_temperature=recommendation.get("current_temperature"),
        current_humidity=recommendation.get("current_humidity"),
        year=recommendation.get("year"),
        month=recommendation.get("month"),
        day_of_week=recommendation.get("day_of_week"),
        hour=recommendation.get("hour"),
        quarter=recommendation.get("quarter"),
        is_weekend=recommendation.get("is_weekend"),
    )

    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    return scenario


def get_scenario_or_none(db: Session, scenario_id: int) -> Scenario | None:
    return db.get(Scenario, scenario_id)


def get_all_scenarios(db: Session, limit: int = 50) -> list[Scenario]:
    return (
        db.query(Scenario)
        .order_by(desc(Scenario.created_at))
        .limit(limit)
        .all()
    )


def get_latest_scenario(db: Session) -> Scenario | None:
    return db.query(Scenario).order_by(desc(Scenario.created_at)).first()


def to_scenario_out(scenario: Scenario) -> ScenarioOut:
    return ScenarioOut(
        id=scenario.id,
        prefTemperature=scenario.pref_temperature,
        prefHumidity=scenario.pref_humidity,
        comfortScore=scenario.comfort_score,
        source=scenario.source,
        applied=scenario.applied,
        createdAt=scenario.created_at,
        currentTemperature=scenario.current_temperature,
        currentHumidity=scenario.current_humidity,
    )