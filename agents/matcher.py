from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from config.config import settings
from config.state import ClinicalTrialState, ScoredTrial, ExtractedEntities, CandidateTrial


class TrialScore(BaseModel):
	"""LLM output schema for trial scoring."""
	score: int
	matching_criteria: list[str]
	exclusion_flags: list[str]


_llm = ChatGroq(api_key=settings.groq_api_key, model="llama-3.3-70b-versatile")

_prompt = ChatPromptTemplate.from_messages([
	("system", """You are a clinical trial matching expert. Your task is to score how well a trial matches a patient's profile.

Scoring rubric:
- 0–20: No match or severe contraindications
- 21–40: Poor match; significant misalignment
- 41–60: Moderate match; some alignment but notable gaps
- 61–80: Good match; mostly aligned with minor concerns
- 81–100: Excellent match; strong alignment across criteria

For each trial, provide:
1. A numeric score (0–100 integer)
2. List of matching criteria (e.g., "EGFR mutation positive", "Age 58 within range")
3. List of exclusion flags or concerns (e.g., "Prior chemotherapy may be a concern", "Phase 2 trial, not Phase 3")

Be concrete and clinical. Base scores on eligibility text and patient profile."""),
	("human", """Patient Profile:
- Diseases: {diseases}
- Medications: {medications}
- Genes: {genes}
- Age: {age}

Trial: {trial_title}
Phase: {trial_phase}
Eligibility Criteria:
{eligibility_text}

Score this trial for the patient."""),
])

_chain = _prompt | _llm.with_structured_output(TrialScore)


def _select_top_trials(
	scored: list[ScoredTrial],
	min_score: int,
	top_n: int,
) -> list[ScoredTrial]:
	"""Pure filter+sort+slice logic; testable without LLM."""
	filtered = [t for t in scored if t.score >= min_score]
	return sorted(filtered, key=lambda t: t.score, reverse=True)[:top_n]


def matcher_node(state: ClinicalTrialState) -> dict:
	"""
	Reads: state["extracted_entities"], state["candidate_trials"]
	Writes: state["scored_trials"]
	Scores each candidate trial against the patient profile using Groq LLM.
	"""
	entities = state.get("extracted_entities")
	candidates = state.get("candidate_trials", [])

	if not entities or not candidates:
		return {"scored_trials": []}

	print(f"\n[Matcher] Scoring {len(candidates)} candidate trials...")

	scored = []

	for trial in candidates:
		try:
			nct_id      = trial.nct_id
			title       = trial.title
			phase       = trial.phase
			eligibility = trial.eligibility
			url         = trial.url

			# Format phase: list[str] -> str
			phase_str = ", ".join(phase) if phase else "N/A"

			result = _chain.invoke({
				"diseases": ", ".join(entities.diseases) if entities.diseases else "None",
				"medications": ", ".join(entities.medications) if entities.medications else "None",
				"genes": ", ".join(entities.genes) if entities.genes else "None",
				"age": entities.age or "N/A",
				"trial_title": title,
				"trial_phase": phase_str,
				"eligibility_text": eligibility[:2000],  # Limit to avoid token overflow
			})

			scored_trial = ScoredTrial(
				nct_id=nct_id,
				title=title,
				phase=phase_str,
				score=result.score,
				matching_criteria=result.matching_criteria,
				exclusion_flags=result.exclusion_flags,
				trial_url=url,
			)
			scored.append(scored_trial)
			print(f"[Matcher] {nct_id:12} → score {result.score}")

		except Exception as e:
			print(f"[Matcher] {trial.nct_id:12} → error: {str(e)[:50]}")
			continue

	top_trials = _select_top_trials(scored, settings.min_match_score, settings.top_n_trials)
	filtered_count = len([t for t in scored if t.score >= settings.min_match_score])
	below_threshold = len(scored) - filtered_count
	if below_threshold > 0:
		print(f"[Matcher] {below_threshold} trial(s) below min_score ({settings.min_match_score})")
	print(f"[Matcher] {len(top_trials)} trials passed threshold")

	return {"scored_trials": top_trials}
