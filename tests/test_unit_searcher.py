"""
Unit tests for agents/searcher.py — no network calls, no credentials required.
conftest.py adds the project root to sys.path.
"""
from config.state import CandidateTrial, ExtractedEntities, ClinicalTrialState
from agents.searcher import _parse_study, searcher_node


# ---------------------------------------------------------------------------
# Canned fixture data
# ---------------------------------------------------------------------------

VALID_STUDY = {
	"protocolSection": {
		"identificationModule": {
			"nctId": "NCT99999999",
			"briefTitle": "A Study of Fixture Drug in Fixture Disease",
		},
		"designModule": {
			"phases": ["PHASE2", "PHASE3"],
		},
		"statusModule": {
			"overallStatus": "RECRUITING",
		},
		"eligibilityModule": {
			"eligibilityCriteria": "Inclusion: age >= 18. Exclusion: prior chemo.",
		},
	}
}

MISSING_NCT_ID_STUDY = {
	"protocolSection": {
		"identificationModule": {
			"briefTitle": "Some Study",
		},
		"designModule": {},
		"statusModule": {},
		"eligibilityModule": {},
	}
}

EMPTY_STUDY: dict = {}


# ---------------------------------------------------------------------------
# Tests for _parse_study
# ---------------------------------------------------------------------------

def test_parse_study_extracts_fields():
	result = _parse_study(VALID_STUDY)

	assert result is not None
	assert result.nct_id == "NCT99999999"
	assert result.title == "A Study of Fixture Drug in Fixture Disease"
	assert result.phase == ["PHASE2", "PHASE3"]
	assert result.status == "RECRUITING"
	assert result.eligibility == "Inclusion: age >= 18. Exclusion: prior chemo."
	assert result.url == "https://clinicaltrials.gov/study/NCT99999999"


def test_parse_study_skips_missing_nct_id():
	result = _parse_study(MISSING_NCT_ID_STUDY)
	assert result is None


def test_parse_study_skips_empty_dict():
	result = _parse_study(EMPTY_STUDY)
	assert result is None


# ---------------------------------------------------------------------------
# FixtureTrialSearchClient
# ---------------------------------------------------------------------------

class FixtureTrialSearchClient:
	"""Returns canned CandidateTrial objects without network I/O."""

	FIXTURE_TRIALS = [
		CandidateTrial(
			nct_id="NCT11111111",
			title="Fixture Trial A",
			phase=["PHASE2"],
			status="RECRUITING",
			eligibility="Inclusion: EGFR positive.",
			url="https://clinicaltrials.gov/study/NCT11111111",
		),
		CandidateTrial(
			nct_id="NCT22222222",
			title="Fixture Trial B",
			phase=["PHASE3"],
			status="RECRUITING",
			eligibility="Inclusion: NSCLC confirmed.",
			url="https://clinicaltrials.gov/study/NCT22222222",
		),
	]

	def search(
		self,
		diseases: list[str],
		medications: list[str],
		page_size: int,
	) -> list[CandidateTrial]:
		return self.FIXTURE_TRIALS


# ---------------------------------------------------------------------------
# Tests for searcher_node with injected client
# ---------------------------------------------------------------------------

def test_searcher_node_with_fixture_client():
	state: ClinicalTrialState = {
		"run_id": "unit-test-searcher",
		"patient_profile": "",
		"extracted_entities": ExtractedEntities(
			diseases=["NSCLC"],
			medications=["osimertinib"],
			genes=["EGFR"],
			age=58,
		),
		"candidate_trials": [],
		"scored_trials": [],
		"final_report": "",
	}

	result = searcher_node(state, client=FixtureTrialSearchClient())

	trials = result["candidate_trials"]
	assert len(trials) == 2
	assert trials[0].nct_id == "NCT11111111"
	assert trials[1].nct_id == "NCT22222222"
	assert isinstance(trials[0], CandidateTrial)


def test_searcher_node_returns_empty_when_no_entities():
	state: ClinicalTrialState = {
		"run_id": "unit-test-no-entities",
		"patient_profile": "",
		"extracted_entities": None,
		"candidate_trials": [],
		"scored_trials": [],
		"final_report": "",
	}

	result = searcher_node(state, client=FixtureTrialSearchClient())
	assert result["candidate_trials"] == []
