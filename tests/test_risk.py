from shellsense.knowledge.risk import (
    RISK_CAUTION,
    RISK_DANGEROUS,
    RISK_SAFE,
    RISK_VERY_DANGEROUS,
    is_dangerous,
    is_safe,
    requires_confirmation,
    risk_level_to_int,
)


class TestRisk:
    def test_risk_level_to_int(self) -> None:
        assert risk_level_to_int(RISK_SAFE) == 0
        assert risk_level_to_int(RISK_CAUTION) == 1
        assert risk_level_to_int(RISK_DANGEROUS) == 2
        assert risk_level_to_int(RISK_VERY_DANGEROUS) == 3

    def test_is_safe(self) -> None:
        assert is_safe(RISK_SAFE)
        assert not is_safe(RISK_DANGEROUS)

    def test_is_dangerous(self) -> None:
        assert is_dangerous(RISK_DANGEROUS)
        assert is_dangerous(RISK_VERY_DANGEROUS)
        assert not is_dangerous(RISK_SAFE)

    def test_requires_confirmation(self) -> None:
        assert requires_confirmation(RISK_DANGEROUS)
        assert requires_confirmation(RISK_VERY_DANGEROUS)
        assert not requires_confirmation(RISK_SAFE)
        assert not requires_confirmation(RISK_CAUTION)
