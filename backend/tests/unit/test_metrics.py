
import pytest

from app.processing.metrics import calculate_metrics


def test_calculates_accuracy_metrics():
    result = calculate_metrics([
        {"forecast_mw": 110, "actual_mw": 100},
        {"forecast_mw": 180, "actual_mw": 200},
    ])

    assert result["sample_count"] == 2
    assert result["mae_mw"] == 15
    assert result["rmse_mw"] == pytest.approx(15.811388)
    assert result["bias_mw"] == -5


def test_rejects_empty_input():
    with pytest.raises(ValueError):
        calculate_metrics([])
