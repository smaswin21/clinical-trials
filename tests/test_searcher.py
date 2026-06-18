import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.state import ClinicalTrialState, ExtractedEntities
from agents.searcher import searcher_node

test_state = {
	"run_id": "test-002",
	"patient_profile": "",
	"extracted_entities": ExtractedEntities(
		diseases=["NSCLC", "non-small cell lung cancer"],
		medications=["osimertinib"],
		genes=["EGFR"],
		age=58,
	),
	"candidate_trials": [],
	"scored_trials": [],
	"final_report": "",
}

result = searcher_node(test_state)
trials = result["candidate_trials"]

print(f"\n── {len(trials)} trials found ──")
for t in trials[:3]:
	print(f"  {t.nct_id:12} {t.title[:70]}")
