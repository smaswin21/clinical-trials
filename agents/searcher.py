import httpx
from typing import Optional

from config.state import ClinicalTrialState, ExtractedEntities, CandidateTrial
from config.config import settings
from agents.protocols import TrialSearchClient


# ---------------------------------------------------------------------------
# Pure parsing helper
# ---------------------------------------------------------------------------

def _parse_study(study: dict) -> Optional[CandidateTrial]:
	"""
	Parse a single study dict from the ClinicalTrials.gov v2 API response.
	Returns None if the study is missing its NCT ID.
	"""
	try:
		proto       = study.get("protocolSection", {})
		ident       = proto.get("identificationModule", {})
		design      = proto.get("designModule", {})
		status      = proto.get("statusModule", {})
		eligibility = proto.get("eligibilityModule", {})

		nct_id = ident.get("nctId", "")
		if not nct_id:
			return None

		return CandidateTrial(
			nct_id=nct_id,
			title=ident.get("briefTitle", ""),
			phase=design.get("phases", []),
			status=status.get("overallStatus", ""),
			eligibility=eligibility.get("eligibilityCriteria", ""),
			url=f"https://clinicaltrials.gov/study/{nct_id}",
		)
	except (KeyError, TypeError):
		return None


# ---------------------------------------------------------------------------
# HTTP adapter — real implementation used in production
# ---------------------------------------------------------------------------

class ClinicalTrialsAdapter:
	"""Implements TrialSearchClient using the ClinicalTrials.gov v2 API."""

	def search(
		self,
		diseases: list[str],
		medications: list[str],
		page_size: int,
	) -> list[CandidateTrial]:
		condition_query    = " OR ".join(diseases)    if diseases    else None
		intervention_query = " OR ".join(medications) if medications else None

		if condition_query or intervention_query:
			print(f"\n[Searcher] Querying ClinicalTrials.gov v2")
			if condition_query:
				print(f"  Conditions: {condition_query[:80]}...")
			if intervention_query:
				print(f"  Interventions: {intervention_query[:80]}...")

		params: dict = {
			"pageSize": page_size,
			"format": "json",
			"filter.overallStatus": "RECRUITING",
		}
		if condition_query:
			params["query.cond"] = condition_query
		if intervention_query:
			params["query.intr"] = intervention_query

		try:
			response = httpx.get(
				"https://clinicaltrials.gov/api/v2/studies",
				params=params,
				timeout=15.0,
			)
			response.raise_for_status()
		except httpx.HTTPError as e:
			print(f"[Searcher] API error: {e}")
			return []

		data    = response.json()
		studies = data.get("studies", [])

		return [t for t in (_parse_study(s) for s in studies) if t is not None]


# ---------------------------------------------------------------------------
# Default adapter instance (module-level singleton, matches extractor pattern)
# ---------------------------------------------------------------------------

_default_client: TrialSearchClient = ClinicalTrialsAdapter()


# ---------------------------------------------------------------------------
# LangGraph node
# ---------------------------------------------------------------------------

def searcher_node(
	state: ClinicalTrialState,
	client: TrialSearchClient = _default_client,
) -> dict:
	"""
	Reads: state["extracted_entities"]
	Writes: state["candidate_trials"]
	Queries ClinicalTrials.gov v2 API for recruiting trials matching extracted entities.
	"""
	entities: Optional[ExtractedEntities] = state.get("extracted_entities")

	if not entities:
		return {"candidate_trials": []}

	candidate_trials = client.search(
		diseases=entities.diseases,
		medications=entities.medications,
		page_size=settings.max_candidate_trials,
	)

	print(f"[Searcher] Found {len(candidate_trials)} candidate trials")
	return {"candidate_trials": candidate_trials}
