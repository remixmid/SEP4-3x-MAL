from sqlalchemy.orm import Session

from app.database.models import Feedback
from app.schemas.scenario_schema import FeedbackIn, FeedbackOut
from app.services.scenario_service import get_scenario_or_none


def save_feedback(db: Session, payload: FeedbackIn) -> FeedbackOut:
    scenario = get_scenario_or_none(db, payload.scenarioId)

    if scenario is None:
        raise ValueError(f"Scenario with id={payload.scenarioId} was not found")

    existing_feedback = (
        db.query(Feedback)
        .filter(Feedback.scenario_id == payload.scenarioId)
        .first()
    )

    if existing_feedback is not None:
        existing_feedback.liked = payload.liked
        db.commit()
        db.refresh(existing_feedback)

        return FeedbackOut(
            id=existing_feedback.id,
            scenarioId=existing_feedback.scenario_id,
            liked=existing_feedback.liked,
            savedAt=existing_feedback.created_at,
        )

    feedback = Feedback(
        scenario_id=payload.scenarioId,
        liked=payload.liked,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return FeedbackOut(
        id=feedback.id,
        scenarioId=feedback.scenario_id,
        liked=feedback.liked,
        savedAt=feedback.created_at,
    )