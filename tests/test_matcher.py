import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.state import ClinicalTrialState, ExtractedEntities, CandidateTrial
from agents.matcher import matcher_node

# Test with 3 real trial dicts in the candidate format from Phase 2
test_state: ClinicalTrialState = {
	"run_id": "test-003",
	"patient_profile": "",
	"extracted_entities": ExtractedEntities(
		diseases=["NSCLC", "non-small cell lung cancer"],
		medications=["osimertinib"],
		genes=["EGFR"],
		age=58,
	),
	"candidate_trials": [
		CandidateTrial(
			nct_id="NCT05382728",
			title="Phase III Study of TY-9591 in Patients With Locally Advanced or Metastatic NSCLC",
			phase=["PHASE3"],
			status="RECRUITING",
			eligibility="""Inclusion Criteria:

1. Male or female aged ≥18 years and <80 years.
2. Locally advanced or metastatic NSCLC diagnosed by histology or cytology.
3. Presence of an activating EGFR-sensitive mutations (including exon 19 deletions, L858R, the above mentioned mutations alone or co-existed with other EGFR-mutated sites).
4. No prior systemic antitumor therapy for locally advanced or metastatic NSCLC.
5. At least one measurable lesion according to RECIST v1.1.""",
			url="https://clinicaltrials.gov/study/NCT05382728",
		),
		CandidateTrial(
			nct_id="NCT06068049",
			title="OSIREAL - Osimertinib RWE on EGFRm NSCLC in Spain",
			phase=[],
			status="RECRUITING",
			eligibility="""Inclusion Criteria:

* Female or male patients, treated with osimertinib
* Age ≥ 18 years at start of osimertinib treatment.
* Patients histologically diagnosed with EGFRm NSCLC:
  - Patients with first-line treatment with EGFRm locally advanced or metastatic NSCLC.
  - Patients with stage IB-IIIA whose tumours have EGFR exon 19 deletions or exon 21 (L858R) substitution mutations.""",
			url="https://clinicaltrials.gov/study/NCT06068049",
		),
		CandidateTrial(
			nct_id="NCT05033691",
			title="A Study to Evaluate the Efficacy of Osimertinib With Early Intervention SRS Treatment",
			phase=["NA"],
			status="RECRUITING",
			eligibility="""Inclusion Criteria:

1. Newly diagnosed metastatic NSCLC, not amenable to curative surgery or curative radiotherapy.
2. Documented EGFR mutation (exon 19 del, L858R, G719X, L861G, S768I, T790M) known to be sensitive to Osimertinib.
3. MRI showing brain metastases. Number of brain lesions under 20.""",
			url="https://clinicaltrials.gov/study/NCT05033691",
		),
	],
	"scored_trials": [],
	"final_report": "",
}

result = matcher_node(test_state)
scored = result["scored_trials"]

print(f"\n── {len(scored)} trials scored and passed threshold ──")
for trial in scored:
	print(f"\n{trial.nct_id}")
	print(f"  Title: {trial.title[:70]}")
	print(f"  Score: {trial.score}")
	print(f"  Matching: {trial.matching_criteria[:2]}")
	if trial.exclusion_flags:
		print(f"  Flags: {trial.exclusion_flags[:1]}")

if len(scored) == 0:
	print("\n(No trials scored - check that GROQ_API_KEY in .env is valid)")
