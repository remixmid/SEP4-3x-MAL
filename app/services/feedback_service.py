from sqlalchemy.orm import Session

from app.database.models import Feedback
from app.schemas.scenario_schema import (
    FeedbackIn,
    FeedbackOut,
    IndicatorFeedbackOut,
)
from app.services.scenario_service import get_scenario_or_none


def save_feedback(db: Session, payload: FeedbackIn) -> FeedbackOut:
    scenario = get_scenario_or_none(db, payload.scenarioId)

    if scenario is None:
        raise ValueError(f"Scenario with id={payload.scenarioId} was not found")

    saved_items: list[IndicatorFeedbackOut] = []

    for item in payload.feedback:
        existing_feedback = (
            db.query(Feedback)
            .filter(
                Feedback.scenario_id == payload.scenarioId,
                Feedback.indicator == item.type,
            )
            .first()
        )

        if existing_feedback is not None:
            existing_feedback.liked = item.liked
            db.commit()
            db.refresh(existing_feedback)

            saved_items.append(
                IndicatorFeedbackOut(
                    id=existing_feedback.id,
                    type=existing_feedback.indicator,
                    liked=existing_feedback.liked,
                    savedAt=existing_feedback.created_at,
                )
            )

            continue

        feedback = Feedback(
            scenario_id=payload.scenarioId,
            indicator=item.type,
            liked=item.liked,
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        saved_items.append(
            IndicatorFeedbackOut(
                id=feedback.id,
                type=feedback.indicator,
                liked=feedback.liked,
                savedAt=feedback.created_at,
            )
        )

    return FeedbackOut(
        scenarioId=payload.scenarioId,
        feedback=saved_items,
    )