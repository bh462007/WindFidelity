
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


def test_metrics_match_hand_computed_three_rows():
    # errors (forecast - actual): +10, -20, +30
    result = calculate_metrics([
        {"forecast_mw": 110, "actual_mw": 100},
        {"forecast_mw": 80, "actual_mw": 100},
        {"forecast_mw": 130, "actual_mw": 100},
    ])

    assert result["sample_count"] == 3
    assert result["mae_mw"] == 20          # (10+20+30)/3
    assert result["bias_mw"] == pytest.approx(20 / 3)   # (10-20+30)/3
    assert result["rmse_mw"] == pytest.approx(((100 + 400 + 900) / 3) ** 0.5)