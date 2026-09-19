"""Turns raw ratios into a 0-100 score per ratio, per bucket, and one
composite score + letter grade — benchmarked against the company's sector
median rather than a single universal bar.
"""
from typing import Any, Dict, Optional

from app.scoring.benchmarks import (
    BUCKET_WEIGHTS,
    BUCKETS,
    HIGHER_IS_BETTER,
    LOWER_IS_BETTER,
    SECTOR_BENCHMARKS,
    score_to_grade,
)


def _ratio_score(ratio_name: str, value: Optional[float], benchmark: float) -> Optional[float]:
    """0-100, where 50 = right at the sector benchmark. Capped so an
    extreme outlier doesn't swing the score more than 2x the benchmark
    would justify."""
    if value is None or benchmark == 0:
        return None

    if ratio_name in HIGHER_IS_BETTER:
        relative_gap = (value - benchmark) / abs(benchmark)
    elif ratio_name in LOWER_IS_BETTER:
        relative_gap = (benchmark - value) / abs(benchmark)
    else:
        return None

    relative_gap = max(-1.0, min(1.0, relative_gap))
    return 50 + 50 * relative_gap


def compute_composite_score(ratios: Dict[str, Optional[float]], sector: str) -> Dict[str, Any]:
    benchmark = SECTOR_BENCHMARKS[sector]

    ratio_scores: Dict[str, Optional[float]] = {}
    for ratio_name, value in ratios.items():
        if ratio_name in benchmark:
            ratio_scores[ratio_name] = _ratio_score(ratio_name, value, benchmark[ratio_name])

    bucket_scores: Dict[str, Optional[float]] = {}
    for bucket_name, ratio_names in BUCKETS.items():
        available = [ratio_scores[r] for r in ratio_names if ratio_scores.get(r) is not None]
        bucket_scores[bucket_name] = sum(available) / len(available) if available else None

    available_buckets = {b: s for b, s in bucket_scores.items() if s is not None}
    total_weight = sum(BUCKET_WEIGHTS[b] for b in available_buckets)
    if total_weight == 0:
        composite_score = 50.0
    else:
        composite_score = sum(
            score * (BUCKET_WEIGHTS[bucket] / total_weight)
            for bucket, score in available_buckets.items()
        )

    return {
        "composite_score": round(composite_score, 1),
        "letter_grade": score_to_grade(composite_score),
        "bucket_scores": {b: (round(s, 1) if s is not None else None) for b, s in bucket_scores.items()},
        "ratio_scores": {r: (round(s, 1) if s is not None else None) for r, s in ratio_scores.items()},
        "sector_benchmark_used": benchmark,
    }
