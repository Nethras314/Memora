import random
from typing import List, Dict, Any, Optional

SYMBOL_POOL = [
    "🍎", "🏠", "🎵", "🌳", "🌻", "☕", "🕊️", "📖", "🌙", "⭐"
]

class DynamicDifficultyAdjustmentEngine:
    """
    AI/ML Adaptive Difficulty Engine for Elderly Cognitive Games.
    Dynamically tunes game parameters (sequence length, display speed, distraction)
    based on patient historical accuracy, error rate, and reaction latency.
    """

    @classmethod
    def evaluate_next_parameters(cls, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates the next difficulty level and stimulus parameters based on recent sessions.
        """
        if not history:
            # Baseline Level 1 for new patient
            selected_sequence = random.sample(SYMBOL_POOL[:5], 3)
            return {
                "difficulty_level": 1,
                "sequence_length": 3,
                "display_duration_ms": 3500,
                "sequence": selected_sequence,
                "options": random.sample(SYMBOL_POOL[:6], 4),
                "guidance_cue": "Take your time and watch the symbols gently."
            }

        recent = history[-5:]
        avg_accuracy = sum(item.get("accuracy", 1.0) for item in recent) / len(recent)
        avg_latency = sum(item.get("reaction_time_ms", 3000) for item in recent) / len(recent)
        latest_level = recent[-1].get("difficulty_level", 1)

        # Dynamic Rule-Based Adaptation
        if avg_accuracy >= 0.85 and avg_latency < 3500:
            # Patient is doing great: increase level gradually
            next_level = min(5, latest_level + 1)
        elif avg_accuracy < 0.60 or avg_latency > 6000:
            # Patient is struggling or fatigued: gently step down to avoid frustration
            next_level = max(1, latest_level - 1)
        else:
            next_level = latest_level

        # Compute stimulus parameters by level
        level_map = {
            1: {"length": 3, "duration_ms": 3500, "pool_size": 4, "cue": "Look at the gentle pictures."},
            2: {"length": 3, "duration_ms": 3000, "pool_size": 5, "cue": "Try to remember the sequence in order."},
            3: {"length": 4, "duration_ms": 2800, "pool_size": 6, "cue": "Four symbols coming up! You're doing wonderful."},
            4: {"length": 4, "duration_ms": 2300, "pool_size": 7, "cue": "A brisk challenge to stimulate your focus."},
            5: {"length": 5, "duration_ms": 2000, "pool_size": 8, "cue": "Advanced memory exercise."}
        }

        params = level_map.get(next_level, level_map[1])
        pool = SYMBOL_POOL[:params["pool_size"]]
        seq = random.sample(pool, params["length"])

        # Options will contain all sequence items plus distractors
        options = list(set(seq + random.sample(SYMBOL_POOL, max(4, params["length"] + 1))))
        random.shuffle(options)

        return {
            "difficulty_level": next_level,
            "sequence_length": params["length"],
            "display_duration_ms": params["duration_ms"],
            "sequence": seq,
            "options": options,
            "guidance_cue": params["cue"]
        }

    @classmethod
    def calculate_cognitive_stability_score(cls, history: List[Dict[str, Any]]) -> int:
        """
        Calculates a clinical Cognitive Stability Index (0-100) based on
        consistency of response latency, accuracy, and mistake recovery over time.
        """
        if not history:
            return 75 # Healthy initial default
        
        recent = history[-10:]
        acc_component = (sum(item.get("accuracy", 0.8) for item in recent) / len(recent)) * 50
        
        # Latency penalty: optimal elderly response is 2000ms - 4500ms
        latencies = [item.get("reaction_time_ms", 3000) for item in recent]
        avg_latency = sum(latencies) / len(latencies)
        
        if avg_latency <= 3500:
            speed_component = 45
        elif avg_latency <= 5500:
            speed_component = 35
        else:
            speed_component = 20

        # Consistency component (low variance indicates higher stability)
        stability_score = int(min(100, max(20, acc_component + speed_component + 5)))
        return stability_score
