"""Procedural Clinical Trial Protocol Generator
Generates unique synthetic protocols with planted issues for RL training."""

import random
from typing import List, Dict, Any


THERAPEUTIC_AREAS = [
    {"name": "oncology", "indication": "Advanced Solid Tumors", "drug_class": "kinase inhibitor"},
    {"name": "cardiology", "indication": "Heart Failure with Reduced EF", "drug_class": "SGLT2 inhibitor"},
    {"name": "neurology", "indication": "Early Alzheimer's Disease", "drug_class": "anti-amyloid antibody"},
    {"name": "rare_disease", "indication": "Duchenne Muscular Dystrophy", "drug_class": "exon-skipping oligonucleotide"},
    {"name": "immunology", "indication": "Moderate-to-Severe Psoriasis", "drug_class": "IL-23 inhibitor"},
    {"name": "metabolic", "indication": "Type 2 Diabetes", "drug_class": "GLP-1 agonist"},
]

PHASES = ["II", "II/III", "III"]
DESIGNS = ["randomized double-blind placebo-controlled", "open-label single-arm", "randomized active-controlled"]

ISSUE_TEMPLATES = {
    "missing_section": [
        ("statistical_design", "critical", "Statistical analysis plan completely missing"),
        ("data_management", "major", "Data management procedures not specified"),
        ("ethical_considerations", "critical", "Ethics review and informed consent procedures missing"),
        ("safety_monitoring", "critical", "DSMB charter and stopping rules not defined"),
    ],
    "logical_inconsistency": [
        ("eligibility_criteria", "critical", "Age range contradiction between inclusion and exclusion criteria"),
        ("eligibility_criteria", "major", "Lab value ranges overlap between inclusion and exclusion"),
        ("study_design", "major", "Randomization ratio inconsistent across sections"),
    ],
    "statistical_error": [
        ("statistical_design", "critical", "Sample size underpowered for primary endpoint"),
        ("statistical_design", "major", "Multiplicity adjustment missing for multiple endpoints"),
        ("statistical_design", "major", "Inappropriate use of logrank test with non-proportional hazards"),
    ],
    "safety_gap": [
        ("safety_monitoring", "critical", "No interim safety analysis defined"),
        ("safety_monitoring", "major", "Adverse event reporting timeline not specified"),
        ("study_procedures", "major", "Insufficient cardiac monitoring frequency"),
    ],
    "regulatory_violation": [
        ("study_procedures", "major", "Pediatric assent procedures missing per ICH E11"),
        ("data_management", "major", "Source data verification plan absent"),
    ],
    "endpoint_issue": [
        ("endpoints", "major", "Primary endpoint not aligned with regulatory precedent"),
    ],
    "consent_issue": [
        ("ethical_considerations", "critical", "Genetic testing consent provisions missing"),
    ],
}


def generate_protocol(seed: int = None, difficulty: str = "medium") -> Dict[str, Any]:
    """Generate a unique clinical trial protocol with planted issues.
    
    Args:
        seed: Random seed for reproducibility
        difficulty: 'easy' (3-4 issues), 'medium' (5-7 issues), 'hard' (8-10 issues)
    
    Returns:
        Dict with protocol_id, text, sections_available, ground_truth_issues
    """
    if seed is None:
        seed = random.randint(1000, 9999)
    random.seed(seed)
    
    area = random.choice(THERAPEUTIC_AREAS)
    phase = random.choice(PHASES)
    design = random.choice(DESIGNS)
    
    # Determine number of issues based on difficulty
    issue_counts = {"easy": (3, 4), "medium": (5, 7), "hard": (8, 10)}
    n_issues = random.randint(*issue_counts.get(difficulty, (5, 7)))
    
    # Sample issues from templates
    all_issues = []
    for issue_type, templates in ISSUE_TEMPLATES.items():
        for tmpl in templates:
            all_issues.append({"issue_type": issue_type, "section": tmpl[0], "severity": tmpl[1], "description": tmpl[2]})
    
    sampled_issues = random.sample(all_issues, min(n_issues, len(all_issues)))
    
    # Build protocol text
    protocol_id = f"GEN-{area['name'][:3].upper()}-{seed}"
    
    sections = {
        "title": f"PROTOCOL {protocol_id}\nA {design.capitalize()} Phase {phase} Study\nto Evaluate {area['drug_class'].title()} in Patients with {area['indication']}\n\nSponsor: GenPharma International\nProtocol Version: 1.0",
        "background": f"\n\n2. BACKGROUND AND RATIONALE\nThis study evaluates a novel {area['drug_class']} for {area['indication']}. Preclinical and Phase I data support continued development.",
        "objectives": "\n\n3. STUDY OBJECTIVES\nPrimary: Evaluate efficacy of investigational product vs comparator.\nSecondary: Characterize safety, tolerability, and pharmacokinetics.",
        "study_design": f"\n\n4. STUDY DESIGN\n{design.capitalize()} multicenter Phase {phase} study. Approximately {random.choice([200, 350, 450, 600])} patients randomized {random.choice(['1:1', '2:1', '3:1'])}.",
        "eligibility_criteria": f"\n\n5. ELIGIBILITY CRITERIA\n5.1 Inclusion:\n- Age >= 18 years\n- Confirmed {area['indication']} diagnosis\n- ECOG 0-1\n- Adequate organ function\n\n5.2 Exclusion:\n- Prior treatment with similar agents\n- Significant comorbidities\n- Pregnancy",
        "study_procedures": "\n\n6. STUDY PROCEDURES\nScreening, treatment, follow-up phases as detailed in schedule of assessments.",
        "endpoints": "\n\n7. STUDY ENDPOINTS\nPrimary endpoint per disease-specific guidelines.\nSecondary endpoints include PK, safety, and quality of life.",
        "references": "\n\n10. REFERENCES\n1. Disease-specific clinical practice guidelines\n2. Regulatory guidance documents",
    }
    
    # Remove sections that have planted "missing_section" issues
    missing_sections = [iss["section"] for iss in sampled_issues if iss["issue_type"] == "missing_section"]
    available_sections = list(sections.keys())
    for sec in missing_sections:
        if sec in sections:
            del sections[sec]
            if sec in available_sections:
                available_sections.remove(sec)
    
    protocol_text = "".join(sections.values())
    
    return {
        "protocol_id": protocol_id,
        "text": protocol_text,
        "sections_available": available_sections,
        "ground_truth_issues": sampled_issues,
        "therapeutic_area": area["name"],
        "phase": phase,
        "difficulty": difficulty,
        "seed": seed,
    }


def generate_protocol_batch(n: int = 10, difficulty: str = "medium") -> List[Dict[str, Any]]:
    """Generate a batch of unique protocols for training data."""
    return [generate_protocol(seed=i, difficulty=difficulty) for i in range(1, n + 1)]


if __name__ == "__main__":
    # Test
    p = generate_protocol(seed=42, difficulty="hard")
    print(f"Generated: {p['protocol_id']}")
    print(f"Therapeutic area: {p['therapeutic_area']}")
    print(f"Issues planted: {len(p['ground_truth_issues'])}")
    print(f"\n{p['text'][:500]}...")