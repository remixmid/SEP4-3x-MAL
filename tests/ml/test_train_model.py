import json
from pathlib import Path

import pandas as pd
import pytest

from app.ml.train_model import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    train_and_save_model,
    validate_training_data,
)


def test_validate_training_data_accepts_valid_dataframe(sample_training_dataframe):
    validate_training_data(sample_training_dataframe)


def test_validate_training_data_rejects_missing_feature_column(
    sample_training_dataframe,
):
    broken_dataframe = sample_training_dataframe.drop(columns=["humidity"])

    with pytest.raises(ValueError) as error:
        validate_training_data(broken_dataframe)

    assert "Missing columns" in str(error.value)
    assert "humidity" in str(error.value)


def test_validate_training_data_rejects_missing_target_column(
    sample_training_dataframe,
):
    broken_dataframe = sample_training_dataframe.drop(columns=[TARGET_COLUMN])

    with pytest.raises(ValueError) as error:
        validate_training_data(broken_dataframe)

    assert "Missing columns" in str(error.value)
    assert TARGET_COLUMN in str(error.value)


def test_validate_training_data_rejects_empty_dataframe():
    empty_dataframe = pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN])

    with pytest.raises(ValueError) as error:
        validate_training_data(empty_dataframe)

    assert "empty" in str(error.value)


def test_train_and_save_model_creates_model_and_metadata(
    sample_training_csv,
    model_paths,
):
    metrics = train_and_save_model(
        dataset_path=sample_training_csv,
        model_file_path=model_paths["model_file_path"],
        metadata_file_path=model_paths["metadata_file_path"],
    )

    model_path = Path(model_paths["model_file_path"])
    metadata_path = Path(model_paths["metadata_file_path"])

    assert model_path.exists()
    assert metadata_path.exists()

    assert "train_rmse" in metrics
    assert "test_rmse" in metrics
    assert "train_r2" in metrics
    assert "test_r2" in metrics
    assert metrics["rows"] == 8
    assert metrics["features"] == FEATURE_COLUMNS
    assert metrics["target"] == TARGET_COLUMN

    saved_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert saved_metadata["rows"] == 8
    assert saved_metadata["features"] == FEATURE_COLUMNS