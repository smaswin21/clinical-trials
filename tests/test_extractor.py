# tests/test_extractor.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.extractor import extractor_node

# Simulate what the state object looks like when it reaches the extractor
test_state = {
    "run_id":             "test-001",
    "patient_profile":    """
        58-year-old male, Stage III non-small cell lung cancer (NSCLC).
        EGFR mutation positive — exon 19 deletion confirmed by liquid biopsy.
        Currently receiving osimertinib 80mg daily. Non-smoker. ECOG 1.
        History of hypertension, controlled with lisinopril 10mg.
    """,
    "extracted_entities": None,
    "candidate_trials":   [],
    "scored_trials":      [],
    "final_report":       "",
}

result = extractor_node(test_state)
entities = result["extracted_entities"]

print("\n── Extraction complete ──")
print(f"Diseases:    {entities.diseases}")
print(f"Medications: {entities.medications}")
print(f"Genes:       {entities.genes}")
print(f"Age:         {entities.age}")