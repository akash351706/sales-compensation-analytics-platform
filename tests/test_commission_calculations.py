import pytest
from modules.commission_engine import (
    calculate_attainment,
    get_commission_rate,
    calculate_payout,
)


# Tier boundary tests: (attainment %, expected rate)
@pytest.mark.parametrize("attainment, expected_rate", [
    (79, 0.02),
    (80, 0.05),
    (99, 0.05),
    (100, 0.08),
    (120, 0.08),
    (121, 0.12),
])
def test_tier_boundaries(attainment, expected_rate):
    assert get_commission_rate(attainment) == expected_rate


def test_attainment_calculation():
    assert calculate_attainment(600000, 500000) == 120.0
    assert calculate_attainment(350000, 400000) == 87.5


def test_zero_target_is_safe():
    assert calculate_attainment(100000, 0) is None
    assert get_commission_rate(None) == 0.0


def test_negative_values_rejected():
    with pytest.raises(ValueError):
        calculate_attainment(-100, 500)
    with pytest.raises(ValueError):
        calculate_attainment(100, -500)


def test_missing_values_rejected():
    with pytest.raises(ValueError):
        calculate_attainment(float("nan"), 500)


def test_payout_calculation():
    assert calculate_payout(600000, 0.08) == 48000.0
    assert calculate_payout(240000, 0.05) == 12000.0