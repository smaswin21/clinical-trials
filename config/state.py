# src/trial_matcher/state.py
from typing import TypedDict, Optional
from pydantic import BaseModel, Field

class ExtractedEntities(BaseModel):
    """Output of the Extractor agent."""
    diseases:    list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    genes:       list[str] = Field(default_factory=list)
    age:         Optional[int] = None


class CandidateTrial(BaseModel):
    """A trial fetched from ClinicalTrials.gov before scoring."""
    nct_id:      str
    title:       str
    phase:       list[str] = Field(default_factory=list)
    status:      str = ""
    eligibility: str = ""
    url:         str = ""


class ScoredTrial(BaseModel):
    """Output of the Matcher agent — one trial with a match score."""
    nct_id:            str
    title:             str
    phase:             str
    score:             int
    matching_criteria: list[str]
    exclusion_flags:   list[str]
    trial_url:         str


class ClinicalTrialState(TypedDict):
    """The object that flows through the LangGraph pipeline."""
    run_id:             str
    patient_profile:    str
    extracted_entities: Optional[ExtractedEntities]
    candidate_trials:   list[CandidateTrial]
    scored_trials:      list[ScoredTrial]
    final_report:       str