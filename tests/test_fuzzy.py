from shellsense.knowledge.fuzzy import best_match, fuzzy_search, spell_correct


class TestFuzzy:
    def test_spell_correct_finds_match(self) -> None:
        results = spell_correct("sytemctl")
        assert len(results) > 0
        assert results[0][0] == "systemctl"
        assert results[0][1] > 80

    def test_spell_correct_empty(self) -> None:
        assert spell_correct("") == []

    def test_fuzzy_search_finds_similar(self) -> None:
        candidates = ["systemctl", "systemd", "system", "sysctl"]
        results = fuzzy_search("sytem", candidates)
        assert len(results) > 0
        assert results[0][0] in candidates

    def test_best_match_finds_top(self) -> None:
        result = best_match("chmdo", ["chmod", "chown", "chgrp"])
        assert result == "chmod"

    def test_best_match_no_result(self) -> None:
        result = best_match("xyzzy", ["chmod", "chown"], min_score=90)
        assert result is None

    def test_best_match_empty_candidates(self) -> None:
        assert best_match("test", []) is None

    def test_fuzzy_score_high_similarity(self) -> None:
        from shellsense.knowledge.fuzzy import fuzzy_score

        score = fuzzy_score("systemctl", "systemctl")
        assert score >= 100

    def test_fuzzy_score_different(self) -> None:
        from shellsense.knowledge.fuzzy import fuzzy_score

        score = fuzzy_score("abc", "xyz")
        assert score < 50
