# Copyright (c) 2026 Aditya Satapathy
# Clinical Trial Protocol Auditor - Protocol Data
# Synthetic clinical trial protocols with planted issues for deterministic grading

from typing import Any, Dict, List


# =============================================================================
# PROTOCOL 1: Easy Task - Section Completeness
# A Phase III oncology trial with deliberately missing/incomplete sections
# =============================================================================

PROTOCOL_1_SECTIONS = {
    "title": """PROTOCOL XR-2024-001
A Randomized, Double-Blind, Placebo-Controlled Phase III Study
to Evaluate the Efficacy and Safety of Compound XR-7721
in Patients with Advanced Non-Small Cell Lung Cancer (NSCLC)

Sponsor: PharmaCorp International
Protocol Version: 3.2
Date: January 15, 2024
IND Number: 123456""",

    "background": """2. BACKGROUND AND RATIONALE
Compound XR-7721 is a selective tyrosine kinase inhibitor targeting EGFR mutations.
Preclinical studies in xenograft models demonstrated tumor regression in 78% of subjects.
Phase I studies (XR-2021-001) established the maximum tolerated dose at 150mg BID.
Phase II studies (XR-2022-003) showed an objective response rate of 42% vs 18% for SOC.
The current study aims to confirm these findings in a larger, controlled population.""",

    "objectives": """3. STUDY OBJECTIVES
Primary Objective:
- To evaluate the overall survival (OS) benefit of XR-7721 vs placebo in advanced NSCLC patients.

Secondary Objectives:
- To assess progression-free survival (PFS)
- To evaluate objective response rate (ORR) per RECIST v1.1
- To characterize the safety and tolerability profile""",

    "study_design": """4. STUDY DESIGN
This is a randomized, double-blind, placebo-controlled, multicenter Phase III study.
Approximately 450 patients will be randomized 2:1 to XR-7721 or placebo.
Stratification factors: ECOG performance status (0 vs 1), prior lines of therapy (1 vs 2+).""",

    "eligibility_criteria": """5. ELIGIBILITY CRITERIA
5.1 Inclusion Criteria:
1. Age >= 18 years
2. Histologically confirmed NSCLC with documented EGFR mutation
3. ECOG performance status 0-1
4. At least one measurable lesion per RECIST v1.1
5. Adequate organ function as defined by protocol-specified lab values
6. Life expectancy > 12 weeks

5.2 Exclusion Criteria:
1. Prior treatment with EGFR tyrosine kinase inhibitors
2. Active brain metastases (treated and stable allowed)
3. Significant cardiovascular disease within 6 months
4. Pregnant or breastfeeding women
5. Known hypersensitivity to study drug components""",

    "study_procedures": """6. STUDY PROCEDURES
6.1 Screening (Day -28 to Day -1):
- Informed consent, medical history, physical exam
- CT scan (chest/abdomen/pelvis), brain MRI
- Laboratory assessments: CBC, CMP, coagulation panel
- ECG and echocardiogram
- Tumor biopsy for biomarker analysis

6.2 Treatment Period:
- XR-7721 150mg or matching placebo BID continuously in 28-day cycles
- Tumor assessments every 8 weeks per RECIST v1.1
- Safety labs every 2 weeks for first 3 cycles, then every 4 weeks""",

    # DELIBERATELY MISSING: statistical_design section
    # This is a planted issue for the easy task

    # DELIBERATELY INCOMPLETE: safety_monitoring section
    "safety_monitoring": """8. SAFETY MONITORING
8.1 Adverse Event Reporting:
All adverse events will be graded per CTCAE v5.0.
Serious adverse events must be reported within 24 hours.""",
    # Missing: DSMB details, stopping rules, dose modification guidelines

    "endpoints": """7. STUDY ENDPOINTS
Primary Endpoint: Overall Survival (OS)
Secondary Endpoints:
- Progression-Free Survival (PFS)
- Objective Response Rate (ORR)
- Duration of Response (DOR)
- Patient-Reported Outcomes (EORTC QLQ-C30)""",

    # DELIBERATELY MISSING: data_management section
    # DELIBERATELY MISSING: ethical_considerations section (ICH-GCP E6 requirement)

    "references": """10. REFERENCES
1. Smith et al. (2022) J Clin Oncol. Phase II results of XR-7721.
2. Jones et al. (2021) Cancer Res. Preclinical activity of XR-7721.
3. NCCN Guidelines v2.2024 - Non-Small Cell Lung Cancer.""",
}

PROTOCOL_1_FULL_TEXT = "\n\n".join(PROTOCOL_1_SECTIONS.values())

# Ground truth issues for Protocol 1 (Easy task: section completeness)
PROTOCOL_1_ISSUES: List[Dict[str, Any]] = [
    {
        "id": "P1-001",
        "section": "statistical_design",
        "issue_type": "missing_section",
        "severity": "critical",
        "description": "Statistical Analysis Plan section is completely missing. No sample size justification, power calculation, analysis populations, or primary analysis method specified.",
        "keywords": ["statistical", "sample size", "power", "analysis plan", "missing"],
    },
    {
        "id": "P1-002",
        "section": "safety_monitoring",
        "issue_type": "missing_section",
        "severity": "critical",
        "description": "Safety monitoring section is incomplete. Missing Data Safety Monitoring Board (DSMB) charter, interim analysis plan, stopping rules for futility/efficacy, and dose modification guidelines.",
        "keywords": ["dsmb", "safety monitoring", "stopping rules", "dose modification", "incomplete", "interim"],
    },
    {
        "id": "P1-003",
        "section": "data_management",
        "issue_type": "missing_section",
        "severity": "major",
        "description": "Data Management section is entirely absent. No description of data collection methods, CRF design, database management, data quality assurance, or data lock procedures.",
        "keywords": ["data management", "crf", "database", "data collection", "missing"],
    },
    {
        "id": "P1-004",
        "section": "ethical_considerations",
        "issue_type": "missing_section",
        "severity": "critical",
        "description": "Ethical Considerations section is missing. ICH-GCP E6(R2) requires documentation of IRB/IEC approval process, informed consent procedures, subject confidentiality, and insurance/indemnity provisions.",
        "keywords": ["ethics", "irb", "iec", "informed consent", "ich-gcp", "confidentiality", "missing"],
    },
    {
        "id": "P1-005",
        "section": "safety_monitoring",
        "issue_type": "safety_gap",
        "severity": "major",
        "description": "No dose modification or dose reduction guidelines specified for managing adverse events related to study drug.",
        "keywords": ["dose modification", "dose reduction", "adverse event management"],
    },
]


# =============================================================================
# PROTOCOL 2: Medium Task - Eligibility Criteria Validation
# A cardiovascular outcomes trial with logical issues in criteria
# =============================================================================

PROTOCOL_2_SECTIONS = {
    "title": """PROTOCOL CV-2024-088
A Multicenter, Randomized, Open-Label Phase III Study to Evaluate
CardioShield (CS-4410) for Prevention of Major Adverse Cardiovascular
Events in Patients with Type 2 Diabetes and Established CVD

Sponsor: HeartGenix Therapeutics
Protocol Version: 2.1
Date: March 10, 2024""",

    "background": """2. BACKGROUND
CS-4410 is a novel PCSK9 inhibitor with dual anti-inflammatory properties.
Phase II data showed 35% LDL reduction and significant decrease in hs-CRP.
Cardiovascular outcomes trial required by FDA for approval.""",

    "objectives": """3. OBJECTIVES
Primary: Time to first occurrence of MACE (CV death, non-fatal MI, non-fatal stroke).
Secondary: All-cause mortality, hospitalization for heart failure, LDL-C change.""",

    "study_design": """4. STUDY DESIGN
Randomized 1:1 to CS-4410 200mg SC monthly + SOC vs SOC alone.
Open-label design. N=8,000. Event-driven: ~950 primary endpoint events.
Planned duration: median 3.5 years follow-up.""",

    "eligibility_criteria": """5. ELIGIBILITY CRITERIA

5.1 Inclusion Criteria:
1. Adults aged 40-85 years with Type 2 Diabetes (HbA1c 6.5-12.0%)
2. Established cardiovascular disease defined as:
   a. Prior MI (>3 months ago), OR
   b. Prior stroke (>6 months ago), OR
   c. Documented coronary artery disease (>50% stenosis), OR
   d. Peripheral arterial disease with ABI < 0.9
3. LDL-C >= 70 mg/dL despite maximally tolerated statin therapy
4. eGFR >= 30 mL/min/1.73m2
5. BMI 18.5 - 45 kg/m2
6. Age >= 18 years
7. Willing to self-administer monthly subcutaneous injections
8. Women of childbearing potential must use two forms of contraception
9. Fasting triglycerides < 200 mg/dL
10. Platelet count > 100,000/μL

5.2 Exclusion Criteria:
1. Type 1 Diabetes
2. HbA1c > 10.0%
3. Recent ACS event within 30 days
4. NYHA Class IV heart failure
5. Planned coronary revascularization
6. Severe hepatic impairment (Child-Pugh C)
7. Active malignancy (except non-melanoma skin cancer)
8. Prior treatment with any PCSK9 inhibitor within 90 days
9. eGFR < 15 mL/min/1.73m2
10. Pregnancy or lactation
11. Known allergy to CS-4410 or excipients
12. Age < 40 years
13. Systolic BP > 180 mmHg or Diastolic BP > 110 mmHg at screening
14. Life expectancy < 2 years""",

    "statistical_design": """6. STATISTICAL ANALYSIS
Primary analysis: Cox proportional hazards model stratified by region and diabetes duration.
Two-sided alpha = 0.05 with group sequential design (O'Brien-Fleming boundaries).
Two planned interim analyses at 50% and 75% information fraction.
Sample size: 8,000 patients for 90% power to detect HR=0.80.
Missing data handled by multiple imputation under MAR assumption.""",

    "safety_monitoring": """7. SAFETY
Independent DSMB with quarterly reviews. Unblinding rules per charter.
Hepatotoxicity monitoring: LFTs at baseline, 3, 6, 12 months, then annually.
Injection site reaction monitoring protocol in place.
SAE reporting within 24 hours. SUSAR reporting per local regulations.""",

    "study_procedures": """8. STUDY PROCEDURES
Screening: up to 4 weeks. Randomization via IVRS.
Visits: baseline, month 1, 3, 6, then every 6 months.
Labs: lipid panel, HbA1c, CBC, CMP, hs-CRP, LFTs at each visit.
Endpoint adjudication by blinded Clinical Events Committee.""",

    "ethical_considerations": """9. ETHICAL CONSIDERATIONS
Study conducted per ICH-GCP E6(R2) and Declaration of Helsinki.
IRB/IEC approval required before enrollment at each site.
Written informed consent obtained from all participants.
Subject data protected per HIPAA and local privacy regulations.
Insurance provisions per local regulatory requirements.""",

    "data_management": """10. DATA MANAGEMENT
Electronic data capture (EDC) system used for all data collection.
100% source data verification for primary endpoint events.
Database lock procedures with dual programming for primary analysis.""",
}

PROTOCOL_2_FULL_TEXT = "\n\n".join(PROTOCOL_2_SECTIONS.values())

# Ground truth issues for Protocol 2 (Medium task: eligibility validation)
PROTOCOL_2_ISSUES: List[Dict[str, Any]] = [
    {
        "id": "P2-001",
        "section": "eligibility_criteria",
        "issue_type": "logical_inconsistency",
        "severity": "critical",
        "description": "Contradictory age criteria: Inclusion criterion 1 states 'aged 40-85 years' but Inclusion criterion 6 states 'Age >= 18 years'. These are inconsistent - criterion 6 is redundant and confusing given the more restrictive criterion 1. Additionally, Exclusion criterion 12 states 'Age < 40 years' which partially overlaps with Inclusion criterion 1.",
        "keywords": ["age", "contradiction", "inconsistent", "40", "18", "redundant"],
    },
    {
        "id": "P2-002",
        "section": "eligibility_criteria",
        "issue_type": "logical_inconsistency",
        "severity": "critical",
        "description": "Contradictory HbA1c criteria: Inclusion criterion 1 allows HbA1c up to 12.0%, but Exclusion criterion 2 excludes patients with HbA1c > 10.0%. The effective range is 6.5-10.0%, making the upper inclusion bound of 12.0% misleading and the criteria internally inconsistent.",
        "keywords": ["hba1c", "contradiction", "inconsistent", "12", "10", "diabetes"],
    },
    {
        "id": "P2-003",
        "section": "eligibility_criteria",
        "issue_type": "safety_gap",
        "severity": "major",
        "description": "Inadequate washout for prior PCSK9 inhibitor use: Exclusion criterion 8 only excludes PCSK9 inhibitor use within 90 days. Given the long half-life of monoclonal antibody PCSK9 inhibitors (evolocumab ~11-17 days, alirocumab ~12-20 days), 90 days may be sufficient pharmacologically, but no baseline PCSK9 level or LDL verification after washout is required to confirm drug clearance.",
        "keywords": ["pcsk9", "washout", "90 days", "half-life", "clearance"],
    },
    {
        "id": "P2-004",
        "section": "eligibility_criteria",
        "issue_type": "logical_inconsistency",
        "severity": "major",
        "description": "Inconsistent renal function thresholds: Inclusion criterion 4 requires eGFR >= 30, but Exclusion criterion 9 only excludes eGFR < 15. Patients with eGFR 15-29 are excluded by inclusion but not by exclusion criteria, creating ambiguity. The criteria should align: either the inclusion threshold should be >= 15 or the exclusion should be < 30.",
        "keywords": ["egfr", "renal", "kidney", "inconsistent", "30", "15", "threshold"],
    },
    {
        "id": "P2-005",
        "section": "eligibility_criteria",
        "issue_type": "safety_gap",
        "severity": "major",
        "description": "No exclusion for patients on anticoagulant therapy despite subcutaneous injection route. Monthly SC injections in anticoagulated patients pose bleeding/hematoma risk. Should include guidance or exclusion for patients on therapeutic anticoagulation.",
        "keywords": ["anticoagulant", "bleeding", "subcutaneous", "injection", "hematoma"],
    },
    {
        "id": "P2-006",
        "section": "eligibility_criteria",
        "issue_type": "safety_gap",
        "severity": "critical",
        "description": "Recent ACS exclusion window of only 30 days is too short. Most cardiovascular outcome trials require 60-90 days post-ACS stabilization. Including patients 30 days post-ACS introduces confounding from acute event recovery and elevated risk of recurrent events unrelated to study drug.",
        "keywords": ["acs", "acute coronary", "30 days", "too short", "stabilization", "window"],
    },
    {
        "id": "P2-007",
        "section": "eligibility_criteria",
        "issue_type": "regulatory_violation",
        "severity": "major",
        "description": "Open-label design with subjective endpoints: The study is open-label but includes endpoints (hospitalization for heart failure) that can be influenced by knowledge of treatment assignment. This introduces bias. Either the study should be blinded or these endpoints should be adjudicated by a blinded committee (noted in procedures but not cross-referenced in design rationale).",
        "keywords": ["open-label", "bias", "blinding", "subjective", "heart failure"],
    },
]


# =============================================================================
# PROTOCOL 3: Hard Task - Full Protocol Audit
# A pediatric rare disease trial with multiple types of issues
# =============================================================================

PROTOCOL_3_SECTIONS = {
    "title": """PROTOCOL RD-2024-155
A Phase II/III Adaptive, Randomized, Double-Blind Study to Evaluate
GeneRx-550 Gene Therapy for Treatment of Severe Combined
Immunodeficiency Due to Adenosine Deaminase Deficiency (ADA-SCID)
in Pediatric Patients

Sponsor: GenomicCure Biotherapeutics
Protocol Version: 1.0
Date: June 5, 2024
IND Number: 789012""",

    "background": """2. BACKGROUND AND RATIONALE
ADA-SCID is an ultra-rare autosomal recessive disorder affecting approximately
1 in 200,000-1,000,000 live births. Current treatment options include enzyme
replacement therapy (ERT) with PEG-ADA, hematopoietic stem cell transplant
(HSCT) from matched donors, and gene therapy.

GeneRx-550 uses a lentiviral vector to deliver functional ADA gene to autologous
CD34+ cells. Preclinical studies in ADA-knockout mice showed immune reconstitution
in 85% of treated animals. A Phase I study (RD-2021-010, N=6) demonstrated
engraftment and ADA expression in 5/6 patients with no vector-related SAEs.

This Phase II/III adaptive design aims to confirm efficacy and support
regulatory filing for approval.""",

    "objectives": """3. STUDY OBJECTIVES
Primary Objective:
- To evaluate the efficacy of GeneRx-550 as measured by overall survival
  at 24 months post-treatment.

Secondary Objectives:
- Immune reconstitution as measured by T-cell counts at 6, 12, and 24 months
- Freedom from ERT at 12 months post-treatment
- Reduction in infection frequency compared to pre-treatment baseline
- Engraftment and ADA enzyme activity levels in peripheral blood

Exploratory Objectives:
- Quality of life assessment using PedsQL
- Long-term vector integration site analysis
- Healthcare resource utilization""",

    "study_design": """4. STUDY DESIGN
4.1 Overview:
Phase II/III adaptive design with initial Phase II cohort (N=12) for dose
confirmation, followed by Phase III expansion (total N=40). Randomized 3:1
to GeneRx-550 vs. continued ERT (control).

4.2 Adaptive Elements:
- Interim analysis after Phase II cohort for dose selection (high vs low cell dose)
- Sample size re-estimation at 60% enrollment based on conditional power
- Futility stopping if conditional power < 20%

4.3 Blinding:
Double-blind design. Unblinding permitted for medical emergencies only.

4.4 Control Arm:
Patients randomized to control will receive continued standard ERT.
Crossover to GeneRx-550 permitted after 24-month primary endpoint assessment.""",

    "eligibility_criteria": """5. ELIGIBILITY CRITERIA
5.1 Inclusion Criteria:
1. Age 3 months to 5 years at time of screening
2. Confirmed ADA-SCID diagnosis by genetic testing AND biochemical assay
3. Currently receiving ERT with PEG-ADA
4. Weight >= 5 kg at screening
5. Adequate organ function:
   a. ALT/AST < 5x ULN
   b. Total bilirubin < 3x ULN
   c. Creatinine < 2x ULN for age
6. Parent/guardian able to provide informed consent
7. Available for 24-month follow-up

5.2 Exclusion Criteria:
1. Available HLA-matched sibling donor for HSCT
2. Prior gene therapy
3. Active, uncontrolled infection at time of conditioning
4. HIV positivity
5. Known hypersensitivity to conditioning agents (busulfan)
6. Hepatic cirrhosis or fibrosis
7. Significant cardiac dysfunction (SF < 25% by echo)""",

    "study_procedures": """6. STUDY PROCEDURES
6.1 Screening (Day -60 to Day -14):
- Informed consent/assent, complete medical history
- HLA typing, genetic confirmation of ADA deficiency
- Baseline immune function panel (T, B, NK cells)
- Baseline ADA enzyme activity
- Infectious disease screening (HIV, HBV, HCV, CMV, EBV)
- Organ function assessments

6.2 Cell Collection (Day -10 to Day -7):
- Bone marrow harvest or mobilized peripheral blood apheresis
- CD34+ cell selection and quality assessment
- Backup cryopreserved cells stored

6.3 Conditioning (Day -4 to Day -2):
- Reduced-intensity conditioning with busulfan (target AUC 60-70 mg*h/L)
- Pharmacokinetic monitoring and dose adjustment
- Supportive care per institutional guidelines

6.4 Gene Therapy Administration (Day 0):
- IV infusion of GeneRx-550 transduced CD34+ cells
- Minimum dose: 2x10^6 CD34+ cells/kg
- Monitoring for infusion reactions

6.5 Follow-up:
- Weekly visits for first 3 months, monthly until 12 months, then quarterly
- Immune function monitoring at each visit
- ADA enzyme activity measurement
- Vector copy number (VCN) analysis quarterly
- Integration site analysis at 6, 12, 24 months
- Replication-competent lentivirus (RCL) testing quarterly""",

    "statistical_design": """7. STATISTICAL ANALYSIS
7.1 Sample Size:
Total N=40 (30 GeneRx-550, 10 ERT control) with 3:1 randomization.
Based on historical ERT data (75% OS at 24 months), 80% power to detect
improvement to 95% OS at 24 months using Fisher exact test, one-sided
alpha = 0.025.

7.2 Primary Analysis:
Kaplan-Meier survival curves with log-rank test comparison.
Point estimate and 95% CI for OS difference at 24 months.

7.3 Interim Analyses:
Phase II interim after 12 patients treated: Bayesian predictive probability
for dose selection. Phase III interim at 60% enrollment: conditional power
for sample size re-estimation.

7.4 Multiplicity:
Hochberg step-up procedure for secondary endpoints. Exploratory endpoints
not adjusted for multiplicity.

7.5 Analysis Populations:
- ITT: All randomized patients
- mITT: All patients who received study treatment
- Safety: All patients who received conditioning
- Per-Protocol: mITT excluding major protocol violations""",

    "safety_monitoring": """8. SAFETY MONITORING
8.1 Data Safety Monitoring Board (DSMB):
Independent DSMB with expertise in gene therapy, pediatric immunology,
and biostatistics. DSMB will review safety data quarterly and after each
cohort of 6 patients in Phase II.

8.2 Risk Management:
- Insertional mutagenesis monitoring via integration site analysis
- RCL testing per FDA guidance
- Long-term follow-up study (15 years) per FDA requirement for gene therapy

8.3 Dose Modification:
Not applicable for gene therapy (single administration).
Busulfan dose adjusted based on PK monitoring.

8.4 Stopping Rules:
- >= 2 treatment-related deaths: mandatory DSMB review and potential hold
- Any case of vector-related malignancy: immediate study halt
- Conditional power < 20% at interim: consider futility stopping""",

    "ethical_considerations": """9. ETHICAL CONSIDERATIONS
9.1 Regulatory:
Study conducted per ICH-GCP E6(R2), 21 CFR Parts 11/50/56/312.
FDA IND and local IRB/IEC approval required.

9.2 Informed Consent:
Written informed consent from parent/legal guardian.
Age-appropriate assent from children >= 7 years where applicable.

9.3 Pediatric Considerations:
- Parental consent with ongoing assessment of child's developing autonomy
- Pediatric dosing justification based on weight and body surface area
- Child-friendly study materials and procedures where feasible
- Independent pediatric ethics review

9.4 Long-term Monitoring:
Participants enrolled in 15-year long-term follow-up study per FDA
gene therapy guidance.""",

    "data_management": """10. DATA MANAGEMENT
Electronic Data Capture using validated EDC system.
Source data verification for 100% of primary and key secondary endpoints.
Centralized monitoring supplemented by on-site visits.
Independent data review before database lock.""",

    "references": """11. REFERENCES
1. Kohn DB et al. (2021) N Engl J Med. Gene therapy for ADA-SCID.
2. Cicalese MP et al. (2020) Blood. Long-term outcomes of gene therapy.
3. FDA Guidance: Long Term Follow-Up After Gene Therapy, 2020.
4. European Medicines Agency: Guideline on gene therapy products, 2018.""",
}

PROTOCOL_3_FULL_TEXT = "\n\n".join(PROTOCOL_3_SECTIONS.values())

# Ground truth issues for Protocol 3 (Hard task: full protocol audit)
PROTOCOL_3_ISSUES: List[Dict[str, Any]] = [
    {
        "id": "P3-001",
        "section": "study_design",
        "issue_type": "logical_inconsistency",
        "severity": "critical",
        "description": "Double-blind design is claimed but impossible to implement. Gene therapy arm requires bone marrow harvest, conditioning chemotherapy, and IV cell infusion - procedures the control arm (continued ERT) would not undergo. Patients and clinicians would inevitably know their assignment. The protocol should describe this as open-label with blinded endpoint adjudication.",
        "keywords": ["double-blind", "blinding", "impossible", "gene therapy", "open-label", "conditioning"],
    },
    {
        "id": "P3-002",
        "section": "statistical_design",
        "issue_type": "statistical_error",
        "severity": "critical",
        "description": "Sample size of N=40 with 3:1 randomization (30 treatment, 10 control) is grossly underpowered. With historical ERT OS of 75% and target of 95%, Fisher exact test with N=30 vs N=10 provides approximately 45-55% power, not the claimed 80%. The small control arm (N=10) severely limits statistical power for survival comparison.",
        "keywords": ["sample size", "underpowered", "power", "40", "fisher", "control arm"],
    },
    {
        "id": "P3-003",
        "section": "statistical_design",
        "issue_type": "statistical_error",
        "severity": "major",
        "description": "Using one-sided alpha = 0.025 for a primary endpoint analysis of a gene therapy with significant risks (conditioning chemotherapy, insertional mutagenesis) is inappropriate. Two-sided testing should be used to also detect potential harm. One-sided testing assumes the treatment cannot be worse, which is not justified for a novel gene therapy.",
        "keywords": ["one-sided", "alpha", "two-sided", "harm", "inappropriate"],
    },
    {
        "id": "P3-004",
        "section": "eligibility_criteria",
        "issue_type": "safety_gap",
        "severity": "major",
        "description": "No minimum immune function criteria for enrollment despite conditioning with busulfan. Patients with severely compromised immunity undergoing myeloablative conditioning are at extreme infection risk. Baseline immune function thresholds should be specified.",
        "keywords": ["immune function", "baseline", "busulfan", "conditioning", "infection risk"],
    },
    {
        "id": "P3-005",
        "section": "study_design",
        "issue_type": "endpoint_issue",
        "severity": "critical",
        "description": "Primary endpoint of overall survival at 24 months is inappropriate for a rare disease with N=40. With expected 75-95% survival rates, the study would need many more patients or longer follow-up to detect survival differences. Immune reconstitution endpoints (T-cell counts, freedom from ERT) would be more sensitive and clinically appropriate primary endpoints for this sample size.",
        "keywords": ["primary endpoint", "overall survival", "inappropriate", "rare disease", "immune reconstitution", "sensitive"],
    },
    {
        "id": "P3-006",
        "section": "eligibility_criteria",
        "issue_type": "consent_issue",
        "severity": "major",
        "description": "Assent requirement for children >= 7 years is specified, but the inclusion criteria limit enrollment to children 3 months to 5 years. No patient in the eligible age range would qualify for assent under this criterion, making it irrelevant and suggesting the protocol was not carefully tailored to the actual study population.",
        "keywords": ["assent", "age", "7 years", "5 years", "consent", "inconsistent", "pediatric"],
    },
    {
        "id": "P3-007",
        "section": "study_design",
        "issue_type": "regulatory_violation",
        "severity": "major",
        "description": "Control arm receives continued ERT (standard of care) but crossover is only permitted after 24 months. For a life-threatening pediatric condition where gene therapy has shown promising results, delaying crossover for 2 years raises ethical concerns. A pre-specified crossover trigger based on clinical deterioration should be included.",
        "keywords": ["crossover", "delay", "24 months", "ethical", "control arm", "pediatric"],
    },
    {
        "id": "P3-008",
        "section": "safety_monitoring",
        "issue_type": "safety_gap",
        "severity": "major",
        "description": "Stopping rule of >= 2 treatment-related deaths is vague. With only 30 treated patients, 2 deaths represents 6.7% mortality directly attributed to treatment. For a pediatric gene therapy trial, a single treatment-related death should trigger immediate DSMB review. The threshold should be more conservative.",
        "keywords": ["stopping rule", "deaths", "conservative", "pediatric", "threshold", "dsmb"],
    },
    {
        "id": "P3-009",
        "section": "statistical_design",
        "issue_type": "statistical_error",
        "severity": "major",
        "description": "Multiple testing correction using Hochberg step-up procedure is specified for secondary endpoints, but the adaptive design elements (dose selection, sample size re-estimation) require alpha spending function adjustment for the primary endpoint that is not fully specified. The Type I error control across interim and final analyses is unclear.",
        "keywords": ["multiplicity", "alpha spending", "adaptive", "type i error", "interim"],
    },
    {
        "id": "P3-010",
        "section": "study_procedures",
        "issue_type": "safety_gap",
        "severity": "critical",
        "description": "No detailed rescue therapy plan specified if gene therapy fails (graft failure, poor engraftment). The backup cryopreserved cells are mentioned for collection but no protocol for their use is defined. For pediatric patients undergoing conditioning, a clear rescue protocol is essential.",
        "keywords": ["rescue", "graft failure", "engraftment", "backup", "cryopreserved", "contingency"],
    },
]


# =============================================================================
# Task Definitions
# =============================================================================

TASKS = {
    "section_completeness": {
        "id": "section_completeness",
        "name": "Section Completeness Check",
        "difficulty": "easy",
        "description": (
            "Audit the clinical trial protocol for missing or incomplete required sections. "
            "According to ICH-GCP E6(R2) and standard protocol templates, a complete protocol "
            "must include: title page, background, objectives, study design, eligibility criteria, "
            "study procedures, statistical analysis plan, safety monitoring (with DSMB details and "
            "stopping rules), endpoints, data management, ethical considerations, and references. "
            "Identify any sections that are missing entirely or critically incomplete."
        ),
        "protocol_id": "XR-2024-001",
        "protocol_text": PROTOCOL_1_FULL_TEXT,
        "protocol_sections": PROTOCOL_1_SECTIONS,
        "ground_truth_issues": PROTOCOL_1_ISSUES,
        "max_steps": 10,
        "expected_score_range": "0.6-1.0 for competent agents",
    },
    "eligibility_validation": {
        "id": "eligibility_validation",
        "name": "Eligibility Criteria Validation",
        "difficulty": "medium",
        "description": (
            "Analyze the clinical trial protocol's eligibility criteria (inclusion and exclusion) "
            "for logical inconsistencies, contradictions, safety gaps, and regulatory concerns. "
            "Look for: conflicting criteria that create impossible or ambiguous patient populations, "
            "missing safety exclusions for known drug-related risks, criteria that are overly "
            "restrictive or overly permissive, and design elements that could introduce bias. "
            "Also evaluate whether criteria align with the study objectives and endpoints."
        ),
        "protocol_id": "CV-2024-088",
        "protocol_text": PROTOCOL_2_FULL_TEXT,
        "protocol_sections": PROTOCOL_2_SECTIONS,
        "ground_truth_issues": PROTOCOL_2_ISSUES,
        "max_steps": 12,
        "expected_score_range": "0.3-0.8 for competent agents",
    },
    "full_protocol_audit": {
        "id": "full_protocol_audit",
        "name": "Full Protocol Audit",
        "difficulty": "hard",
        "description": (
            "Perform a comprehensive audit of the entire clinical trial protocol. Evaluate "
            "ALL aspects: study design feasibility, statistical methodology, eligibility criteria "
            "logic, safety monitoring adequacy, endpoint appropriateness, regulatory compliance "
            "(ICH-GCP, FDA/EMA guidelines), ethical considerations, and cross-section consistency. "
            "This is a pediatric gene therapy trial with complex adaptive design elements. "
            "Identify critical flaws that could jeopardize patient safety, compromise data "
            "integrity, or prevent regulatory approval."
        ),
        "protocol_id": "RD-2024-155",
        "protocol_text": PROTOCOL_3_FULL_TEXT,
        "protocol_sections": PROTOCOL_3_SECTIONS,
        "ground_truth_issues": PROTOCOL_3_ISSUES,
        "max_steps": 15,
        "expected_score_range": "0.15-0.65 for competent agents",
    },
}


def get_task(task_id: str) -> Dict[str, Any]:
    """Get task configuration by ID."""
    if task_id not in TASKS:
        raise ValueError(f"Unknown task: {task_id}. Available: {list(TASKS.keys())}")
    return TASKS[task_id]


def list_tasks() -> List[Dict[str, str]]:
    """List all available tasks with metadata."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "difficulty": t["difficulty"],
            "description": t["description"][:200] + "...",
        }
        for t in TASKS.values()
    ]
