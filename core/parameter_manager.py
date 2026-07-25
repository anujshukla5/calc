"""Parameter collection helpers."""

DEFAULT_PARAMETERS = ["Dal", "Damaged Seed", "Foreign Material"]


def normalize_parameter_names(names: list[str]) -> list[str]:
    normalized = []
    for name in names:
        clean = name.strip()
        if clean and clean not in normalized:
            normalized.append(clean)
    return normalized
