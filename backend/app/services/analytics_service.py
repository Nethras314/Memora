"""Cognitive tracking metric spine.

Pure computation helpers over already-loaded rows (cognitive sessions, tasks,
reminders, mood logs, clinical notes). The route layer is responsible for
loading rows from Supabase (or the demo fallback) and calling into here.

Design note: the multi-domain *composite* index is a current snapshot
(games + routine + medication + mood). Longitudinal *trend* / *delta* /
*velocity* are computed from cognitive-session history, which is the only
time-series signal we persist. Domain *breakdown* is a finer-grained
diagnostic view for the clinical portal.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GAME_DOMAIN: Dict[str, str] = {
    "sequence_memory": "memory",
    "photo_recognition": "memory",
    "odd_one_out": "attention",
    "general_knowledge": "semantic",
}

# Fixed composite weights, shown transparently in the UI.
COMPOSITE_WEIGHTS: Dict[str, float] = {
    "games": 0.50,
    "adl": 0.20,
    "medication": 0.15,
    "mood": 0.15,
}

# Coarse groups the domain breakdown rolls into (for display weight).
DOMAIN_GROUP_WEIGHT: Dict[str, float] = {
    "memory": 0.50,
    "attention": 0.50,
    "semantic": 0.50,
    "speed": 0.50,
    "adl": 0.20,
    "medication": 0.15,
    "mood": 0.15,
}

MOOD_VALENCE: Dict[str, int] = {
    "Happy": 95,
    "Calm": 85,
    "Irritable": 50,
    "Anxious": 45,
    "Confused": 40,
    "Sad": 35,
    "Agitated": 30,
}

RAG_GREEN = 75
RAG_AMBER = 60


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _naive(ts: datetime) -> datetime:
    return ts.replace(tzinfo=None) if ts.tzinfo is not None else ts


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _avg(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


# ---------------------------------------------------------------------------
# Domain scores
# ---------------------------------------------------------------------------
def games_stability(sessions: List[Dict[str, Any]]) -> Optional[int]:
    """0-100 games-only stability from the DDA engine. None when no sessions."""
    if not sessions:
        return None
    from backend.app.services.dda_engine import DynamicDifficultyAdjustmentEngine

    return DynamicDifficultyAdjustmentEngine.calculate_cognitive_stability_score(sessions)


def adl_score(tasks: List[Dict[str, Any]]) -> Optional[float]:
    if not tasks:
        return None
    done = sum(1 for t in tasks if t.get("done"))
    return round(done / len(tasks) * 100, 1)


def medication_score(reminders: List[Dict[str, Any]]) -> Optional[float]:
    meds = [r for r in reminders if (r.get("category") or "").lower() == "medicine"]
    if not meds:
        return None
    done = sum(1 for r in meds if r.get("done"))
    return round(done / len(meds) * 100, 1)


def mood_score(moods: List[Dict[str, Any]]) -> Optional[float]:
    if not moods:
        return None
    vals = [MOOD_VALENCE.get(m.get("mood"), 70) for m in moods]
    return round(sum(vals) / len(vals), 1)


def _speed_score(avg_latency_ms: float) -> float:
    """2000ms -> 100, 8000ms -> 0, linear clamp."""
    return round(max(0.0, min(100.0, (8000 - avg_latency_ms) / 60.0)), 1)


# ---------------------------------------------------------------------------
# Composite index
# ---------------------------------------------------------------------------
def composite_index(
    games: Optional[float],
    adl: Optional[float],
    medication: Optional[float],
    mood: Optional[float],
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[Optional[float], bool, Dict[str, float]]:
    """Weighted mean over available domains, renormalized to the available set.

    Returns (index, insufficient_data, normalized_weights). ``insufficient_data``
    is True when fewer than two domains have data; a single-domain patient still
    receives that domain's score (games, usually) so the headline is never blank.
    """
    weights = weights or COMPOSITE_WEIGHTS
    available: Dict[str, float] = {}
    if games is not None:
        available["games"] = float(games)
    if adl is not None:
        available["adl"] = float(adl)
    if medication is not None:
        available["medication"] = float(medication)
    if mood is not None:
        available["mood"] = float(mood)

    normalized = {k: 0.0 for k in weights}
    if not available:
        return None, True, normalized

    total_weight = sum(weights.get(k, 0.0) for k in available)
    for k in available:
        normalized[k] = weights.get(k, 0.0) / total_weight if total_weight else 0.0

    index = sum(available[k] * normalized[k] for k in available)
    return round(index, 1), len(available) < 2, normalized


# ---------------------------------------------------------------------------
# Domain breakdown (diagnostic)
# ---------------------------------------------------------------------------
def domain_breakdown(
    sessions: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    reminders: List[Dict[str, Any]],
    moods: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    by_domain: Dict[str, List[float]] = {}
    for s in sessions:
        dom = GAME_DOMAIN.get(s.get("game_type"))
        if dom:
            by_domain.setdefault(dom, []).append(_as_float(s.get("accuracy"), 0.0))

    items: List[Dict[str, Any]] = []
    for dom in ("memory", "attention", "semantic"):
        vals = by_domain.get(dom, [])
        items.append({
            "domain": dom,
            "score": _avg(vals) * 100 if vals else None,
            "weight": DOMAIN_GROUP_WEIGHT[dom],
            "sample_count": len(vals),
        })

    latencies = [_as_float(s.get("reaction_time_ms"), 0.0) for s in sessions if s.get("reaction_time_ms")]
    if latencies:
        items.append({
            "domain": "speed",
            "score": _speed_score(sum(latencies) / len(latencies)),
            "weight": DOMAIN_GROUP_WEIGHT["speed"],
            "sample_count": len(latencies),
        })
    else:
        items.append({"domain": "speed", "score": None, "weight": DOMAIN_GROUP_WEIGHT["speed"], "sample_count": 0})

    items.append({"domain": "adl", "score": adl_score(tasks), "weight": DOMAIN_GROUP_WEIGHT["adl"],
                  "sample_count": len(tasks)})
    meds = [r for r in reminders if (r.get("category") or "").lower() == "medicine"]
    items.append({"domain": "medication", "score": medication_score(reminders), "weight": DOMAIN_GROUP_WEIGHT["medication"],
                  "sample_count": len(meds)})
    items.append({"domain": "mood", "score": mood_score(moods), "weight": DOMAIN_GROUP_WEIGHT["mood"],
                  "sample_count": len(moods)})
    return items


# ---------------------------------------------------------------------------
# Longitudinal trend (cognitive sessions only)
# ---------------------------------------------------------------------------
def daily_series(
    sessions: List[Dict[str, Any]],
    window_days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Daily-bucketed cognitive series, ascending.

    Each entry: {date: datetime.date, score, latency_ms, index}. ``index`` is the
    games-only stability score for that day's sessions.
    """
    from collections import OrderedDict

    from backend.app.services.dda_engine import DynamicDifficultyAdjustmentEngine

    points: List[Tuple[datetime, Dict[str, Any]]] = []
    for s in sessions:
        ts = _ts(s.get("created_at"))
        if ts is None:
            continue
        points.append((_naive(ts), s))
    points.sort(key=lambda p: p[0])

    if window_days is not None:
        cutoff = datetime.now() - timedelta(days=window_days)
        points = [(ts, s) for ts, s in points if ts >= cutoff]

    buckets: "OrderedDict[Any, List[Dict[str, Any]]]" = OrderedDict()
    for ts, s in points:
        buckets.setdefault(ts.date(), []).append(s)

    out: List[Dict[str, Any]] = []
    for day, day_sessions in buckets.items():
        scores = [_as_float(s.get("score"), 0.0) for s in day_sessions if s.get("score") is not None]
        latencies = [_as_float(s.get("reaction_time_ms"), 0.0) for s in day_sessions if s.get("reaction_time_ms")]
        out.append({
            "date": day,
            "score": _avg(scores),
            "latency_ms": _avg(latencies),
            "index": DynamicDifficultyAdjustmentEngine.calculate_cognitive_stability_score(day_sessions),
        })
    return out


def serialize_series(series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "date": p["date"].isoformat(),
            "score": p["score"],
            "latency_ms": p["latency_ms"],
            "index": p["index"],
        }
        for p in series
    ]


def index_delta(series: List[Dict[str, Any]], recent_days: int = 7, prior_days: int = 21) -> Optional[float]:
    """Mean index of the last ``recent_days`` days minus the prior ``prior_days``."""
    if not series:
        return None
    latest = series[-1]["date"]
    recent = [p["index"] for p in series
              if p.get("index") is not None and (latest - p["date"]).days < recent_days]
    prior = [p["index"] for p in series
             if p.get("index") is not None
             and recent_days <= (latest - p["date"]).days < recent_days + prior_days]
    if not recent or not prior:
        return None
    return round(sum(recent) / len(recent) - sum(prior) / len(prior), 1)


def decline_velocity(series: List[Dict[str, Any]]) -> Optional[float]:
    """Least-squares slope of index over time, expressed in points per week."""
    pts = [(p["date"].toordinal(), p["index"]) for p in series if p.get("index") is not None]
    if len(pts) < 3:
        return None
    n = len(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xm = sum(xs) / n
    ym = sum(ys) / n
    num = sum((x - xm) * (y - ym) for x, y in pts)
    den = sum((x - xm) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return round(num / den * 7.0, 2)


# ---------------------------------------------------------------------------
# Status + plain-language messaging
# ---------------------------------------------------------------------------
def rag_status(index: Optional[float]) -> str:
    if index is None:
        return "amber"
    if index >= RAG_GREEN:
        return "green"
    if index >= RAG_AMBER:
        return "amber"
    return "red"


def _rolling_declining(series: List[Dict[str, Any]], days: int = 3) -> bool:
    tail = [p["index"] for p in series[-days:] if p.get("index") is not None]
    return len(tail) >= days and all(tail[i] > tail[i + 1] for i in range(len(tail) - 1))


def plain_language_flag(
    index: Optional[float],
    delta: Optional[float],
    status: str,
    series: Optional[List[Dict[str, Any]]] = None,
) -> str:
    if status == "red":
        return "Recent sessions suggest increased difficulty with memory. A check-in may help."
    if _rolling_declining(series or []):
        return "Memory scores dipped for a few days running. Extra rest may help."
    if delta is not None and delta < -5:
        return "Memory scores dipped this week. Familiar routines can help steady things."
    if delta is not None and delta > 5:
        return "Doing well — memory scores are improving this week."
    return "Steady this week. Daily activities are helping."


def recommended_action(status: str, domains: Optional[List[Dict[str, Any]]] = None) -> str:
    if status == "red":
        return "Book a clinical review and keep routines gentle and familiar."
    if status == "amber":
        return "Add a short daily memory game and encourage hydration and rest."
    return "Maintain the current routine and daily memory stimulation."


# ---------------------------------------------------------------------------
# "Since last visit" (doctor review marker = latest clinical note)
# ---------------------------------------------------------------------------
def _sess_ts(s: Dict[str, Any]) -> datetime:
    ts = _ts(s.get("created_at"))
    return _naive(ts) if ts else datetime.min


def since_last_visit(
    notes: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not notes:
        return {"last_visit": None, "sessions_since": len(sessions), "delta": None}

    last_ts = max((_ts(n.get("created_at")) or datetime.min) for n in notes)
    last_ts = _naive(last_ts)
    since = [s for s in sessions if _sess_ts(s) >= last_ts]
    before = [s for s in sessions if _sess_ts(s) < last_ts]

    now_score = games_stability(sessions)
    prior_score = games_stability(before) if before else None
    delta = None
    if now_score is not None and prior_score is not None:
        delta = round(now_score - prior_score, 1)

    return {"last_visit": last_ts, "sessions_since": len(since), "delta": delta}
