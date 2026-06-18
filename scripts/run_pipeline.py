import uuid
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from graph import graph
from config.database import RunRepository

PATIENT_PROFILE = """
58-year-old male, Stage III non-small cell lung cancer (NSCLC).
EGFR mutation positive — exon 19 deletion confirmed by liquid biopsy.
Currently receiving osimertinib 80mg daily. Non-smoker. ECOG 1.
History of hypertension, controlled with lisinopril 10mg.
"""


def run_and_save(patient_profile: str) -> dict:
    run_id = str(uuid.uuid4())
    repo = RunRepository()
    repo.create(run_id, patient_profile)

    start = time.monotonic()
    try:
        result = graph.invoke({
            "run_id": run_id,
            "patient_profile": patient_profile,
            "extracted_entities": None,
            "candidate_trials": [],
            "scored_trials": [],
            "final_report": "",
        })
        repo.complete(run_id, result, time.monotonic() - start)
        return result
    except Exception as e:
        repo.fail(run_id, str(e), time.monotonic() - start)
        raise


if __name__ == "__main__":
    result = run_and_save(PATIENT_PROFILE)
    print("\n" + "=" * 60)
    print(result["final_report"])
