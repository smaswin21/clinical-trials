"""
Unit tests for agents/matcher.py — no Groq API calls required.
conftest.py adds the project root to sys.path.
"""
from config.state import ScoredTrial
from agents.matcher import _select_top_trials


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_scored_trial(nct_id: str, score: int) -> ScoredTrial:
	return ScoredTrial(
		nct_id=nct_id,
		title=f"Trial {nct_id}",
		phase="PHASE2",
		score=score,
		matching_criteria=["EGFR positive"],
		exclusion_flags=[],
		trial_url=f"https://clinicaltrials.gov/study/{nct_id}",
	)


# ---------------------------------------------------------------------------
# Tests for _select_top_trials
# ---------------------------------------------------------------------------

def test_matcher_filters_below_min_score():
	scored = [
		_make_scored_trial("NCT00000001", score=80),
		_make_scored_trial("NCT00000002", score=39),  # below threshold
		_make_scored_trial("NCT00000003", score=40),  # exactly at threshold — include
		_make_scored_trial("NCT00000004", score=10),  # below threshold
	]

	result = _select_top_trials(scored, min_score=40, top_n=10)

	nct_ids = [t.nct_id for t in result]
	assert "NCT00000001" in nct_ids
	assert "NCT00000003" in nct_ids
	assert "NCT00000002" not in nct_ids
	assert "NCT00000004" not in nct_ids


def test_matcher_returns_top_n():
	scored = [
		_make_scored_trial("NCT00000010", score=90),
		_make_scored_trial("NCT00000011", score=85),
		_make_scored_trial("NCT00000012", score=70),
		_make_scored_trial("NCT00000013", score=60),
		_make_scored_trial("NCT00000014", score=55),
	]

	result = _select_top_trials(scored, min_score=0, top_n=3)

	assert len(result) == 3
	assert result[0].nct_id == "NCT00000010"
	assert result[1].nct_id == "NCT00000011"
	assert result[2].nct_id == "NCT00000012"


def test_matcher_sorts_descending():
	scored = [
		_make_scored_trial("NCT00000020", score=55),
		_make_scored_trial("NCT00000021", score=90),
		_make_scored_trial("NCT00000022", score=70),
	]

	result = _select_top_trials(scored, min_score=0, top_n=10)

	assert result[0].score == 90
	assert result[1].score == 70
	assert result[2].score == 55


def test_matcher_returns_empty_when_all_below_threshold():
	scored = [
		_make_scored_trial("NCT00000030", score=30),
		_make_scored_trial("NCT00000031", score=20),
	]

	result = _select_top_trials(scored, min_score=40, top_n=10)
	assert result == []
