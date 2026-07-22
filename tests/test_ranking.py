from __future__ import annotations

from shellsense.knowledge.ranking import rank_suggestions, score_suggestion


class TestRanking:
    def test_exact_match_score(self) -> None:
        score = score_suggestion("ls", "ls", "exact")
        assert score > 95.0

    def test_prefix_match_score(self) -> None:
        score = score_suggestion("sys", "systemctl", "prefix")
        assert 75 <= score <= 85

    def test_contains_match_score(self) -> None:
        score = score_suggestion("ctl", "systemctl", "contains")
        assert 35 <= score <= 45

    def test_alias_match_score(self) -> None:
        score = score_suggestion("copy", "cp", "alias")
        assert 65 <= score <= 75

    def test_fuzzy_match_score(self) -> None:
        score = score_suggestion("sytemctl", "systemctl", "fuzzy", fuzzy_score_val=80)
        assert score >= 30

    def test_popularity_boost(self) -> None:
        score_low = score_suggestion("ls", "ls", "exact", popularity=1)
        score_high = score_suggestion("ls", "ls", "exact", popularity=100)
        assert score_high > score_low

    def test_history_freq_boost(self) -> None:
        score_low = score_suggestion("ls", "ls", "exact", history_freq=1)
        score_high = score_suggestion("ls", "ls", "exact", history_freq=50)
        assert score_high > score_low

    def test_category_bonus(self) -> None:
        score_no = score_suggestion("ls", "ls", "exact", category_bonus=False)
        score_yes = score_suggestion("ls", "ls", "exact", category_bonus=True)
        assert score_yes > score_no

    def test_length_penalty(self) -> None:
        score_a = score_suggestion("x", "a", "prefix")
        score_b = score_suggestion("x", "a_very_long_command_name", "prefix")
        assert score_a > score_b

    def test_rank_suggestions_orders_by_score(self) -> None:
        candidates = [
            {
                "name": "zzz_sysctl",
                "_match_type": "prefix",
                "_fuzzy_score": 0,
                "_popularity": 10,
                "_history_freq": 0,
            },
            {
                "name": "aaa_sysctl",
                "_match_type": "prefix",
                "_fuzzy_score": 0,
                "_popularity": 0,
                "_history_freq": 0,
            },
        ]
        ranked = rank_suggestions("sys", candidates)
        assert len(ranked) == 2
        assert ranked[0]["name"] == "zzz_sysctl"

    def test_rank_suggestions_empty(self) -> None:
        ranked = rank_suggestions("sys", [])
        assert ranked == []

    def test_custom_weights(self) -> None:
        weights = {"exact_match": 200.0, "prefix_match": 50.0}
        score = score_suggestion("ls", "ls", "exact", weights=weights)
        assert score >= 195
