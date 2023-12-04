def smooth_value(
    current_value: float, previous_value: float, smoothing_factor: float = 0.3
) -> float:
    return smoothing_factor * current_value + (1 - smoothing_factor) * previous_value
