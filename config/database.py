from pymongo import MongoClient
from datetime import datetime, timezone
from config.config import settings

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongodb_uri)
    return _client


def get_db():
    return get_client()[settings.mongodb_db_name]


class RunRepository:
    def __init__(self):
        self._col = get_db()["pipeline_runs"]

    def create(self, run_id: str, patient_profile: str) -> None:
        self._col.insert_one({
            "_id": run_id,
            "patient_profile": patient_profile,
            "status": "running",
            "started_at": datetime.now(timezone.utc),
            "completed_at": None,
            "duration_seconds": None,
            "extracted_entities": None,
            "candidate_trials": [],
            "scored_trials": [],
            "final_report": None,
            "error": None,
        })

    def complete(self, run_id: str, state: dict, duration_seconds: float) -> None:
        entities = state.get("extracted_entities")
        scored = state.get("scored_trials", [])
        self._col.update_one(
            {"_id": run_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc),
                "duration_seconds": round(duration_seconds, 2),
                "extracted_entities": entities.model_dump() if entities else None,
                "candidate_trials": state.get("candidate_trials", []),
                "scored_trials": [t.model_dump() for t in scored],
                "final_report": state.get("final_report"),
            }},
        )

    def fail(self, run_id: str, error: str, duration_seconds: float) -> None:
        self._col.update_one(
            {"_id": run_id},
            {"$set": {
                "status": "failed",
                "completed_at": datetime.now(timezone.utc),
                "duration_seconds": round(duration_seconds, 2),
                "error": error,
            }},
        )
