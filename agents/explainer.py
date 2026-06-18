from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config.config import settings
from config.state import ClinicalTrialState


_llm = ChatGroq(api_key=settings.groq_api_key, model="llama-3.3-70b-versatile")

_SYSTEM = """You are an expert oncology trial navigator. Your job is to produce a clear, concise markdown report that helps a patient and their oncologist understand which clinical trials are the best match.

Format your report as:
# Clinical Trial Match Report

## Patient Summary
(brief bullet list of key patient characteristics)

## Recommended Trials

For each trial (ranked by match score, highest first):

### [Rank]. [Trial Title]
- **Match Score**: [score]/100
- **NCT ID**: [id] | **Phase**: [phase]
- **Why this trial fits**: (2–3 sentences, plain language, no jargon)
- **Watch out for**: (1–2 eligibility flags, or "None identified")
- **Learn more**: [url]

End with a one-sentence next step recommendation.

Be direct, clinical, and useful. Write for a patient who can handle medical detail."""


def explainer_node(state: ClinicalTrialState) -> dict:
	"""
	Reads: state["scored_trials"], state["extracted_entities"]
	Writes: state["final_report"]
	Generates a human-readable markdown report from the scored trials.
	"""
	scored_trials = state.get("scored_trials", [])
	entities = state.get("extracted_entities")

	if not scored_trials:
		report = (
			"# Clinical Trial Match Report\n\n"
			"No matching clinical trials were found for this patient profile.\n\n"
			"Consider broadening the search criteria or consulting your oncologist "
			"about alternative treatment options or expanded access programs."
		)
		print("\n[Explainer] No trials to report — returning empty result message")
		return {"final_report": report}

	print(f"\n[Explainer] Generating report for {len(scored_trials)} trial(s)...")

	# Format patient summary
	if entities:
		patient_lines = [
			f"Diseases: {', '.join(entities.diseases) or 'None'}",
			f"Medications: {', '.join(entities.medications) or 'None'}",
			f"Genes: {', '.join(entities.genes) or 'None'}",
			f"Age: {entities.age or 'N/A'}",
		]
	else:
		patient_lines = ["Patient profile not available"]

	# Format trial summaries for the prompt
	trial_blocks = []
	for i, trial in enumerate(scored_trials, start=1):
		flags = "; ".join(trial.exclusion_flags) if trial.exclusion_flags else "None"
		criteria = "; ".join(trial.matching_criteria)
		block = (
			f"Trial {i}: {trial.title}\n"
			f"  NCT ID: {trial.nct_id}\n"
			f"  Phase: {trial.phase}\n"
			f"  Match Score: {trial.score}/100\n"
			f"  Matching criteria: {criteria}\n"
			f"  Exclusion flags: {flags}\n"
			f"  URL: {trial.trial_url}"
		)
		trial_blocks.append(block)

	human_content = (
		"Patient profile:\n" + "\n".join(f"  - {l}" for l in patient_lines) +
		"\n\nScored trials (already ranked by score):\n\n" +
		"\n\n".join(trial_blocks)
	)

	response = _llm.invoke([
		SystemMessage(content=_SYSTEM),
		HumanMessage(content=human_content),
	])

	report = response.content
	print(f"[Explainer] Report generated ({len(report)} chars)")

	return {"final_report": report}
