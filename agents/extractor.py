

import re
from openmed import analyze_text
from config.state import ClinicalTrialState, ExtractedEntities

def extractor_node(state: ClinicalTrialState) -> dict:
    """
    Reads: state["patient_profile"]
    Writes: state["extracted_entities"]
    """
    profile = state["patient_profile"]

    # Run three OpenMed models sequentially — each specialised for one entity type
    disease_result  = analyze_text(
        profile, model="OpenMed/OpenMed-NER-DiseaseDetect-BioMed-335M"
    )
    chemical_result = analyze_text(
        profile, model="OpenMed/OpenMed-NER-ChemicalDetect-ElectraMed-33M"
    )
    gene_result     = analyze_text(
        profile, model="OpenMed/OpenMed-NER-GenomicDetect-PubMed-109M"
    )

    # Only keep high-confidence detections (confidence > 0.85)
    # Use sets to deduplicate (same entity detected twice at different spans)
    diseases    = list({e.text for e in disease_result.entities  if e.confidence > 0.85})
    medications = list({e.text for e in chemical_result.entities if e.confidence > 0.85})
    genes       = list({e.text for e in gene_result.entities     if e.confidence > 0.85})

    # Age isn't an entity type in NER — use a simple regex as fallback
    age_match = re.search(r"(\d{2})[- ]?year[- ]?old", profile, re.IGNORECASE)
    age = int(age_match.group(1)) if age_match else None

    entities = ExtractedEntities(
        diseases=diseases,
        medications=medications,
        genes=genes,
        age=age,
    )

    # Print for visibility during development
    print(f"\n[Extractor] Diseases:    {entities.diseases}")
    print(f"[Extractor] Medications: {entities.medications}")
    print(f"[Extractor] Genes:       {entities.genes}")
    print(f"[Extractor] Age:         {entities.age}")

    # Return ONLY the keys this node modifies — LangGraph merges this into the full state
    return {"extracted_entities": entities}