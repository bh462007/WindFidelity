
from math import sqrt


def calculate_metrics(matched: list[dict]) -> dict:
    if not matched:
        raise ValueError("Cannot calculate metrics without matched records")

    errors = [
        float(row["forecast_mw"]) - float(row["actual_mw"])
        for row in matched
    ]

    return {
        "sample_count": len(errors),
        "mae_mw": sum(abs(error) for error in errors) / len(errors),
        "rmse_mw": sqrt(sum(error**2 for error in errors) / len(errors)),
        "bias_mw": sum(errors) / len(errors),
    }
