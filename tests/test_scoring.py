"""Unit tests for the MCDA scoring engine: correctness + 'never fabricate missing data'."""
from __future__ import annotations

from src.core.indicators import OFFICIAL_INDICATORS
from src.core.scoring import (
    safety_flag, score_category_map, score_density_ratio, score_infrastructure_ratio,
    score_linear_scale, score_modification_extent, score_threshold_bands,
)


def test_category_map_known_value():
    rubric = {"map": {"متوسط": 50, "متهالك": 90}}
    r = score_category_map("متوسط", rubric)
    assert r.score == 50
    assert r.status == "validated"


def test_category_map_missing_value_not_fabricated():
    rubric = {"map": {"متوسط": 50}}
    r = score_category_map(None, rubric)
    assert r.score is None
    assert r.status == "insufficient"


def test_category_map_unmapped_value_not_fabricated():
    rubric = {"map": {"متوسط": 50}}
    r = score_category_map("قيمة غريبة", rubric)
    assert r.score is None
    assert r.status == "insufficient"


def test_linear_scale_strategic_importance():
    r = score_linear_scale(10.5, {"max_raw": 15})
    assert abs(r.score - 70.0) < 0.01
    assert r.status == "validated"


def test_linear_scale_missing_not_zero():
    r = score_linear_scale(None, {"max_raw": 15})
    assert r.score is None  # must NOT silently become 0
    assert r.status == "insufficient"


def test_threshold_bands_age():
    bands = {"bands": [{"min": 0, "max": 20, "score": 20}, {"min": 20, "max": 40, "score": 50},
                        {"min": 40, "max": 60, "score": 75}, {"min": 60, "max": 1000, "score": 100}]}
    assert score_threshold_bands(10, bands).score == 20
    assert score_threshold_bands(45, bands).score == 75
    assert score_threshold_bands(80, bands).score == 100
    r = score_threshold_bands(None, bands)
    assert r.score is None and r.status == "insufficient"


def test_density_ratio_relative_normalization():
    rubric = {"ratio": "units_per_feddan", "mode": "minmax"}
    ctx = {
        "density_units": {"min": 10, "max": 110},
        "density_buildings": {"min": 1, "max": 11},
    }
    r = score_density_ratio(60, 6, 1.0, rubric, ctx)
    assert abs(r.score - 50.0) < 0.01  # both normalized components are at midpoint


def test_density_uses_units_only_not_building_count_fallback():
    r = score_density_ratio(None, 5, 1.0, {}, {"density_units": {"min": 10, "max": 100}})
    assert r.score is None and r.status == "insufficient"


def test_density_equal_range_uses_neutral_score():
    ctx = {
        "density_units": {"min": 50, "max": 50},
        "density_buildings": {"min": 5, "max": 5},
    }
    r = score_density_ratio(50, 5, 1.0, {}, ctx)
    assert r.score == 50 and r.status == "validated"
    assert "محايدة 50" in r.explanation


def test_official_scorecard_weights_sum_to_100():
    assert len(OFFICIAL_INDICATORS) == 6
    assert sum(item["weight"] for item in OFFICIAL_INDICATORS) == 100
    assert {item["code"]: item["weight"] for item in OFFICIAL_INDICATORS} == {
        "structural": 35, "strategic": 20, "age": 15,
        "density": 10, "modifications": 10, "infrastructure": 10,
    }


def test_density_ratio_missing_area_not_fabricated():
    r = score_density_ratio(60, 5, None, {}, {})
    assert r.score is None and r.status == "insufficient"


def test_composite_density_requires_both_inputs():
    ctx = {
        "density_units": {"min": 10, "max": 100},
        "density_buildings": {"min": 1, "max": 10},
    }
    r = score_density_ratio(None, 5, 1.0, {}, ctx)
    assert r.score is None and r.status == "insufficient"


def test_composite_density_uses_equal_weight_components():
    ctx = {
        "density_units": {"min": 0, "max": 100},
        "density_buildings": {"min": 0, "max": 10},
    }
    r = score_density_ratio(25, 8, 1.0, {}, ctx)
    # Unit density normalizes to 25; building density normalizes to 80.
    assert abs(r.score - 52.5) < 0.01
    assert "25.00 وحدة/فدان" in r.raw_value
    assert "8.00 عمارة/فدان" in r.raw_value


def test_modification_presence_map_matches_official_scorecard():
    rubric = {"presence_map": {"يوجد": 100, "لا يوجد": 0}}
    yes = score_modification_extent("يوجد", None, None, rubric)
    no = score_modification_extent("لا يوجد", None, None, rubric)
    missing = score_modification_extent("مفقود أو غير واضح", None, None, rubric)
    assert yes.score == 100 and yes.status == "provisional"
    assert no.score == 0 and no.status == "provisional"
    assert missing.score is None and missing.status == "insufficient"


def test_infrastructure_connection_not_quality():
    rubric = {"connected_values": ["متصل"], "utilities": 4}
    r = score_infrastructure_ratio("متصل", "متصل", "متصل", "متصل", rubric)
    assert r.score == 100
    assert r.status == "provisional"  # connection presence only, not verified service quality
    assert "جودة" in r.explanation or "كفاءة" in r.explanation


def test_infrastructure_missing_values_are_not_counted_as_disconnected():
    r = score_infrastructure_ratio("متصل", None, "متصل", "غير متصل",
                                   {"connected_values": ["متصل"], "utilities": 4})
    assert r.score is None
    assert r.status == "insufficient"


def test_safety_flag_critical_for_removal_decision():
    assert safety_flag("ازالة ")["level"] == "critical"
    assert safety_flag("ترميم وإزالة")["level"] == "critical"


def test_safety_flag_warning_for_renovation_only():
    assert safety_flag("ترميم")["level"] == "warning"


def test_safety_flag_none_when_blank():
    assert safety_flag(None)["level"] == "none"
    assert safety_flag("لا يوجد")["level"] == "none"
