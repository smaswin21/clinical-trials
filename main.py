import uuid
from graph import graph


PATIENT_PROFILE = """
58-year-old male, Stage III non-small cell lung cancer (NSCLC).
EGFR mutation positive — exon 19 deletion confirmed by liquid biopsy.
Currently receiving osimertinib 80mg daily. Non-smoker. ECOG 1.
History of hypertension, controlled with lisinopril 10mg.
"""


def main():
	result = graph.invoke({
		"run_id": str(uuid.uuid4()),
		"patient_profile": PATIENT_PROFILE,
		"extracted_entities": None,
		"candidate_trials": [],
		"scored_trials": [],
		"final_report": "",
	})

	print("\n" + "=" * 60)
	print(result["final_report"])


if __name__ == "__main__":
	main()
