import pytest
from backend.app.services.dda_engine import DynamicDifficultyAdjustmentEngine

def test_dda_baseline_for_new_patient():
    params = DynamicDifficultyAdjustmentEngine.evaluate_next_parameters([])
    assert params["difficulty_level"] == 1
    assert params["sequence_length"] == 3
    assert len(params["sequence"]) == 3
    assert params["display_duration_ms"] >= 3000

def test_dda_step_up_on_high_accuracy():
    # Simulate patient with 5 consecutive fast & accurate games
    history = [
        {"accuracy": 1.0, "reaction_time_ms": 2200, "difficulty_level": 1}
        for _ in range(5)
    ]
    params = DynamicDifficultyAdjustmentEngine.evaluate_next_parameters(history)
    assert params["difficulty_level"] >= 2
    assert params["display_duration_ms"] <= 3000

def test_dda_step_down_on_fatigue():
    # Simulate patient struggling at Level 3
    history = [
        {"accuracy": 0.4, "reaction_time_ms": 6500, "difficulty_level": 3}
        for _ in range(5)
    ]
    params = DynamicDifficultyAdjustmentEngine.evaluate_next_parameters(history)
    assert params["difficulty_level"] == 2 # Gently dialed down to reduce frustration

def test_cognitive_stability_score():
    healthy_history = [
        {"accuracy": 1.0, "reaction_time_ms": 2500} for _ in range(5)
    ]
    score = DynamicDifficultyAdjustmentEngine.calculate_cognitive_stability_score(healthy_history)
    assert score >= 80
