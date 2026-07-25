"""CSV export helpers."""

import csv
from pathlib import Path

from .blend_engine import BlendResult


def export_results(path: str | Path, result: BlendResult) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Parameter", "Low lot %", "Good lot %", "Foreign lot %", "Final %", "Maximum spec %", "Status", "Detail"])
        for item in result.parameters:
            writer.writerow([item.name, item.low_value, item.good_value, item.foreign_value, item.final_value, item.specification, "PASS" if item.meets_specification else "FAIL", item.detail])
