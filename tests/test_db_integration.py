import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_pipeline import run_and_save, PATIENT_PROFILE
from config.database import get_db


def test_pipeline_saves_to_mongodb():
    result = run_and_save(PATIENT_PROFILE)
    run_id = result["run_id"]

    doc = get_db()["pipeline_runs"].find_one({"_id": run_id})
    assert doc is not None
    assert doc["status"] == "completed"
    assert doc["final_report"] is not None and len(doc["final_report"]) > 0
    assert doc["extracted_entities"] is not None
    assert doc["duration_seconds"] is not None and doc["duration_seconds"] > 0
    assert doc["error"] is None
