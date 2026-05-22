import pandas as pd

from app.ml.model_service import ComfortModelService
from app.ml.train_model import FEATURE_COLUMNS, train_and_save_model


def test_model_service_loads_existing_model_and_predicts(
    sample_training_csv,
    model_paths,
):
    train_and_save_model(
        dataset_path=sample_training_csv,
        model_file_path=model_paths["model_file_path"],
        metadata_file_path=model_paths["metadata_file_path"],
    )

    service = ComfortModelService(
        model_file_path=model_paths["model_file_path"],
        metadata_file_path=model_paths["metadata_file_path"],
    )

    service.load_or_train()

    input_rows = pd.DataFrame(
        [
            {
                "temperature": 21.0,
                "humidity": 50.0,
                "year": 2026,
                "month": 5,
                "day_of_week": 2,
                "hour": 14,
                "quarter": 2,
                "is_weekend": 0,
            }
        ]
    )

    predictions = service.predict_comfort(input_rows)

    assert len(predictions) == 1
    assert isinstance(predictions[0], float)
    assert 1.0 <= predictions[0] <= 10.0


def test_model_service_returns_metrics_after_loading_model(
    sample_training_csv,
    model_paths,
):
    train_and_save_model(
        dataset_path=sample_training_csv,
        model_file_path=model_paths["model_file_path"],
        metadata_file_path=model_paths["metadata_file_path"],
    )

    service = ComfortModelService(
        model_file_path=model_paths["model_file_path"],
        metadata_file_path=model_paths["metadata_file_path"],
    )

    service.load_or_train()

    metrics = service.get_metrics()

    assert "train_rmse" in metrics
    assert "test_rmse" in metrics
    assert "train_r2" in metrics
    assert "test_r2" in metrics
    assert metrics["features"] == FEATURE_COLUMNS


def test_model_service_rejects_prediction_with_missing_features(
    sample_training_csv,
    model_paths,
):
    train_and_save_model(
        dataset_path=sample_training_csv,
        model_file_path=model_paths["model_file_path"],
        metadata_file_path=model_paths["metadata_file_path"],
    )

    service = ComfortModelService(
        model_file_path=model_paths["model_file_path"],
        metadata_file_path=model_paths["metadata_file_path"],
    )

    service.load_or_train()

    broken_input = pd.DataFrame(
        [
            {
                "temperature": 21.0,
                "humidity": 50.0,
            }
        ]
    )

    try:
        service.predict_comfort(broken_input)
        assert False, "Expected ValueError because required features are missing"

    except ValueError as error:
        assert "missing features" in str(error)