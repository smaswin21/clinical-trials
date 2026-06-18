import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from graph import graph

initial_state = {
	"run_id": str(uuid.uuid4()),
	"patient_profile": """
		58-year-old male, Stage III non-small cell lung cancer (NSCLC).
		EGFR mutation positive — exon 19 deletion confirmed by liquid biopsy.
		Currently receiving osimertinib 80mg daily. Non-smoker. ECOG 1.
		History of hypertension, controlled with lisinopril 10mg.
	""",
	"extracted_entities": None,
	"candidate_trials": [],
	"scored_trials": [],
	"final_report": "",
}

result = graph.invoke(initial_state)

print("\n" + "=" * 60)
print(result["final_report"])
