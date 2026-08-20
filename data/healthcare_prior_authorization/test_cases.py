from typing import List, Dict, Optional, Any
from typing_extensions import TypedDict
from generator_v5.core.system_tools_base import SystemToolsBaseClass


class AlternateCodes(TypedDict, total=False):
    # Alternate procedure codes that may be valid for the request
    alternate_codes: List[str]


class PaRequirementsResult(TypedDict):
    pa_required: bool
    notes: str
    alternate_codes: List[str]


class CriteriaDecisionTree(TypedDict, total=False):
    # Placeholder for decision tree logic; structure depends on payer
    tree: dict


class MedicalNecessityCriteria(TypedDict):
    criteria_text: str
    required_docs: List[str]
    decision_tree: Dict[str, Any]


class ClinicalDocument(TypedDict, total=False):
    # Represents a clinical document found in EHR
    doc_type: str
    doc_id: str
    summary: str
    date: str


class ClinicalDocumentationResult(TypedDict):
    docs_found: List[ClinicalDocument]
    docs_missing: List[str]
    summary: str


class ClinicalCriteriaValidationResult(TypedDict):
    criteria_met: bool
    unmet_criteria: List[str]
    notes: str


class PaForm(TypedDict, total=False):
    # Represents the completed PA form object
    patient_id: str
    payer_id: str
    cpt_code: str
    diagnosis_code: str
    clinical_summary: str


class PaSubmissionResult(TypedDict):
    pa_form: PaForm
    attachments: List[ClinicalDocument]
    ready_to_submit: bool


class SubmitPaRequestResult(TypedDict):
    submission_status: str  # submitted|failed|queued
    reference_id: str
    timestamp: str


class TrackPaStatusResult(TypedDict, total=False):
    status: str  # approved, denied, pended, expired
    auth_number: Optional[str]
    decision_notes: Optional[str]
    valid_through: Optional[str]


class AppealPaDenialResult(TypedDict):
    appeal_status: str  # submitted|failed
    new_reference_id: str
    timestamp: str


class BaseHealthcarePriorAuthorizationAutomationAgentTestCase(SystemToolsBaseClass):
    """
    Base class containing common methods for all Healthcare Prior Authorization Automation Agent test cases.
    """

    # Agent context attributes from agent description
    role = (
        "You are a healthcare prior authorization automation agent that processes provider PA requests "
        "by checking payer requirements, gathering clinical documentation, preparing and submitting "
        "authorizations, and tracking decisions to optimize turnaround and approval rates."
    )
    goal = (
        "Your goal is to automate, accelerate, and optimize prior authorization submissions for healthcare services, "
        "ensuring all payer criteria are met, documentation is complete, and decisions are tracked and communicated, "
        "reducing administrative burden and improving patient access to care."
    )
    action_plan = {
        "assumptions": [
            "Provider requests contain accurate CPT/HCPCS codes, diagnosis codes, and clinical indication.",
            "EHR and payer portal/API integrations are available for data extraction and submission.",
        ],
        "tools_and_resources": [
            "check_pa_requirements",
            "retrieve_medical_necessity_criteria",
            "gather_clinical_documentation",
            "validate_clinical_criteria",
            "prepare_pa_submission",
            "submit_pa_request",
            "track_pa_status",
            "appeal_pa_denial",
        ],
        "guidelines": [
            "Always verify PA requirements before gathering documentation.",
            "Only submit requests when all required clinical criteria and documentation are met or missing data is explicitly addressed.",
            "Escalate cases to human review when criteria interpretation is ambiguous or urgent clinical judgment is required.",
            "Use expedited submission methods for urgent/emergency requests.",
            "Initiate appeals only when additional evidence is available or denial appears incorrect.",
        ],
        "workflow_selection": [
            "if input.service_type == \"urgent\": Route to expedited PA workflow for urgent/emergency requests.",
            "if input.appeal_requested == true: Route to denial/appeal workflow if provider requests appeal.",
            "if input.pa_status_check == true: Route to PA tracking workflow for status follow-up.",
            "if input.cpt_code in [\"72148\", \"95800\", \"E1390\", \"74177\", \"93458\", \"43644\"] and input.urgent != true: Route to standard PA submission workflow for supported CPT codes.",
            "if input.cpt_code == \"J0135\" or input.specialty_drug == true: Route to specialty drug PA workflow.",
            "if input.cpt_code == \"43644\": Route to bariatric surgery multi-step workflow.",
            "if input.additional_docs_needed == true: Route to documentation request workflow.",
            "else: Default to standard PA workflow; escalate to human if criteria ambiguous.",
        ],
        "failure_points": [
            "Missing required clinical documentation from EHR. Recovery: Request missing documentation from provider and pause submission until received.",
            "Payer portal/API unavailable or submission error. Recovery: Retry submission, switch to alternate delivery (fax/phone), or escalate to human.",
            "Criteria not met but provider insists on submission. Recovery: Submit with available documentation and flag for possible denial/appeal.",
            "Ambiguous medical necessity criteria interpretation. Recovery: Escalate to HUMAN_IN_THE_LOOP for clinical review.",
            "PA status not updated after expected SLA. Recovery: Escalate to payer contact or human follow-up.",
        ],
        "success_criteria": [
            "PA request submitted with all required documentation and clinical criteria met.",
            "PA status tracked and communicated to provider/patient within target turnaround time.",
            "Appeals initiated promptly for denials with viable clinical evidence.",
            "Urgent/emergency requests processed via expedited workflow.",
            "Provider notified of approval/denial/next steps in timely manner.",
        ],
    }

    def check_pa_requirements(
        self,
        payer_id: str,
        plan_id: str,
        cpt_code: str,
        diagnosis_code: str,
    ) -> PaRequirementsResult:
        """
        Determine if prior authorization is required for a procedure/service by payer/plan.

        Args:
            payer_id: Unique payer identifier. Format: PAYER-XXXX where X is alphanumeric.
            plan_id: Unique plan identifier. Format: PLAN-XXXX where X is alphanumeric.
            cpt_code: CPT or HCPCS procedure code. Format: NNNNN or ANNNN.
            diagnosis_code: ICD-10 diagnosis code. Format: XNN.NN

        Returns:
            PaRequirementsResult: Object with pa_required (boolean), notes (string), alternate_codes (list of strings)
        """
        print(f"--- Running check_pa_requirements ---")
        print(f"payer_id: {payer_id}, plan_id: {plan_id}, cpt_code: {cpt_code}, diagnosis_code: {diagnosis_code}")

        # Mock logic: PA required for most codes except 99213 (office visit)
        pa_required = cpt_code not in ["99213"]
        notes = "PA required for this procedure." if pa_required else "No PA required for this procedure."
        alternate_codes = ["72149"] if cpt_code == "72148" else []

        return {
            "pa_required": pa_required,
            "notes": notes,
            "alternate_codes": alternate_codes,
        }

    def retrieve_medical_necessity_criteria(
        self,
        payer_id: str,
        cpt_code: str,
        diagnosis_code: str,
    ) -> MedicalNecessityCriteria:
        """
        Retrieve payer's medical necessity criteria for the procedure/diagnosis.

        Args:
            payer_id: Unique payer identifier. Format: PAYER-XXXX.
            cpt_code: CPT/HCPCS procedure code.
            diagnosis_code: ICD-10 diagnosis code.

        Returns:
            MedicalNecessityCriteria: Criteria object containing:
                - criteria_text (string)
                - required_docs (list of strings)
                - decision_tree (object)
        """
        print(f"--- Running retrieve_medical_necessity_criteria ---")
        print(f"payer_id: {payer_id}, cpt_code: {cpt_code}, diagnosis_code: {diagnosis_code}")

        # Mock data
        criteria_text = f"Medical necessity for {cpt_code} with diagnosis {diagnosis_code} per {payer_id}."
        required_docs = ["Progress Notes", "Imaging Report"] if cpt_code == "72148" else ["Provider Notes"]
        decision_tree = {"step1": "Check diagnosis", "step2": "Check prior treatment"}

        return {
            "criteria_text": criteria_text,
            "required_docs": required_docs,
            "decision_tree": decision_tree,
        }

    def gather_clinical_documentation(
        self,
        patient_id: str,
        required_docs: List[str],
    ) -> ClinicalDocumentationResult:
        """
        Extract clinical notes, labs, imaging, and treatment history from EHR.

        Args:
            patient_id: Unique patient identifier. Format: PAT-XXXXXX.
            required_docs: List of required clinical document types (strings), min 1, max 20 items.

        Returns:
            ClinicalDocumentationResult: Object containing:
                - docs_found (list of document objects)
                - docs_missing (list of strings)
                - summary (string)
        """
        print(f"--- Running gather_clinical_documentation ---")
        print(f"patient_id: {patient_id}, required_docs: {required_docs}")

        # Mock: Assume all but one doc is found
        docs_found = []
        docs_missing = []
        for doc in required_docs:
            if doc.lower() == "imaging report":
                docs_missing.append(doc)
            else:
                docs_found.append({
                    "doc_type": doc,
                    "doc_id": f"DOC-{doc[:3].upper()}-001",
                    "summary": f"{doc} summary for {patient_id}",
                    "date": "2024-01-20",
                })

        summary = (
            f"Found {len(docs_found)} documents, missing {len(docs_missing)}."
            if docs_missing else "All required documents found."
        )
        return {
            "docs_found": docs_found,
            "docs_missing": docs_missing,
            "summary": summary,
        }

    def validate_clinical_criteria(
        self,
        criteria_object: MedicalNecessityCriteria,
        clinical_data: ClinicalDocumentationResult,
    ) -> ClinicalCriteriaValidationResult:
        """
        Check if patient clinical data meets payer's medical necessity criteria.

        Args:
            criteria_object: Criteria data structure from retrieve_medical_necessity_criteria.
            clinical_data: Clinical documentation extracted from EHR.

        Returns:
            ClinicalCriteriaValidationResult: Object with criteria_met (boolean), unmet_criteria (list of strings), notes (string)
        """
        print(f"--- Running validate_clinical_criteria ---")
        print(f"criteria_object: {criteria_object}")
        print(f"clinical_data: {clinical_data}")

        unmet_criteria = []
        criteria_met = True

        # Check for missing docs
        if clinical_data["docs_missing"]:
            criteria_met = False
            unmet_criteria.extend([f"Missing {doc}" for doc in clinical_data["docs_missing"]])

        notes = "All criteria met." if criteria_met else f"Unmet criteria: {', '.join(unmet_criteria)}"
        return {
            "criteria_met": criteria_met,
            "unmet_criteria": unmet_criteria,
            "notes": notes,
        }

    def prepare_pa_submission(
        self,
        patient_id: str,
        payer_id: str,
        cpt_code: str,
        diagnosis_code: str,
        clinical_summary: str,
        attachments: List[ClinicalDocument],
    ) -> PaSubmissionResult:
        """
        Complete PA request form and assemble clinical justification and required attachments.

        Args:
            patient_id: Unique patient identifier. Format: PAT-XXXXXX.
            payer_id: Unique payer identifier.
            cpt_code: CPT/HCPCS code.
            diagnosis_code: ICD-10 code.
            clinical_summary: Narrative summary of clinical justification. Length: 50-2000 characters.
            attachments: List of document objects to attach. Minimum 1, maximum 20.

        Returns:
            PaSubmissionResult: Submission object:
                - pa_form (object)
                - attachments (list)
                - ready_to_submit (boolean)
        """
        print(f"--- Running prepare_pa_submission ---")
        print(f"patient_id: {patient_id}, payer_id: {payer_id}, cpt_code: {cpt_code}, diagnosis_code: {diagnosis_code}")
        print(f"clinical_summary: {clinical_summary[:60]}..., attachments: {len(attachments)} files")

        ready_to_submit = len(attachments) > 0 and len(clinical_summary) >= 50
        pa_form = {
            "patient_id": patient_id,
            "payer_id": payer_id,
            "cpt_code": cpt_code,
            "diagnosis_code": diagnosis_code,
            "clinical_summary": clinical_summary,
        }

        return {
            "pa_form": pa_form,
            "attachments": attachments,
            "ready_to_submit": ready_to_submit,
        }

    def submit_pa_request(
        self,
        pa_submission: PaSubmissionResult,
        delivery_method: str,
        portal_id: Optional[str] = None,
    ) -> SubmitPaRequestResult:
        """
        Submit the PA request via payer portal, API, or EDI transaction.

        Args:
            pa_submission: PA submission object from prepare_pa_submission.
            delivery_method: Submission channel. Must be one of: portal, API, EDI_278, fax, phone.
            portal_id: Portal identifier if using portal. Format: PORTAL-XXXX.

        Returns:
            SubmitPaRequestResult: Object with submission_status (string: submitted|failed|queued), reference_id (string), timestamp (ISO 8601)
        """
        valid_methods = ["portal", "API", "EDI_278", "fax", "phone"]
        if delivery_method not in valid_methods:
            raise ValueError(f"Invalid delivery_method: {delivery_method}. Must be one of {valid_methods}")

        print(f"--- Running submit_pa_request ---")
        print(f"delivery_method: {delivery_method}, portal_id: {portal_id}")
        print(f"pa_submission: {pa_submission}")

        if not pa_submission.get("ready_to_submit", False):
            return {
                "submission_status": "failed",
                "reference_id": "",
                "timestamp": "",
            }

        reference_id = "PA-445601"
        timestamp = "2024-04-22T10:00:00Z"
        return {
            "submission_status": "submitted",
            "reference_id": reference_id,
            "timestamp": timestamp,
        }

    def track_pa_status(
        self,
        reference_id: str,
        payer_id: str,
    ) -> TrackPaStatusResult:
        """
        Monitor and update the status of submitted PA requests.

        Args:
            reference_id: Unique PA submission reference. Format: PA-XXXXXX.
            payer_id: Unique payer identifier.

        Returns:
            TrackPaStatusResult: Status object:
                - status (enum: approved, denied, pended, expired)
                - auth_number (string)
                - decision_notes (string)
                - valid_through (ISO 8601)
        """
        print(f"--- Running track_pa_status ---")
        print(f"reference_id: {reference_id}, payer_id: {payer_id}")

        # Mock logic: Approve if reference_id starts with "PA-"
        status = "approved" if reference_id.startswith("PA-") else "denied"
        auth_number = "AUTH-556677" if status == "approved" else ""
        decision_notes = "Approved for 90 days, MRI criteria met." if status == "approved" else "Denied: criteria not met."
        valid_through = "2024-09-10" if status == "approved" else ""

        return {
            "status": status,
            "auth_number": auth_number,
            "decision_notes": decision_notes,
            "valid_through": valid_through,
        }

    def appeal_pa_denial(
        self,
        reference_id: str,
        payer_id: str,
        additional_docs: List[ClinicalDocument],
        appeal_reason: str,
    ) -> AppealPaDenialResult:
        """
        Prepare and submit an appeal for denied PA requests.

        Args:
            reference_id: PA request reference identifier.
            payer_id: Payer identifier.
            additional_docs: List of additional document objects. Minimum 1, maximum 10.
            appeal_reason: Narrative reason for appeal. Length: 30-1000 characters.

        Returns:
            AppealPaDenialResult: Appeal object:
                - appeal_status (string: submitted|failed)
                - new_reference_id (string)
                - timestamp (ISO 8601)
        """
        print(f"--- Running appeal_pa_denial ---")
        print(f"reference_id: {reference_id}, payer_id: {payer_id}, additional_docs: {len(additional_docs)} files")
        print(f"appeal_reason: {appeal_reason[:60]}...")

        appeal_status = "submitted" if len(additional_docs) >= 1 and len(appeal_reason) >= 30 else "failed"
        new_reference_id = "APPEAL-223344" if appeal_status == "submitted" else ""
        timestamp = "2024-04-22T12:00:00Z" if appeal_status == "submitted" else ""

        return {
            "appeal_status": appeal_status,
            "new_reference_id": new_reference_id,
            "timestamp": timestamp,
        }

    # System tools are inherited from SystemToolsBaseClass
    # If customization is needed for SUCCESS, FAILED, CANCELLED, HUMAN_IN_THE_LOOP, override here

class TestCase1_HealthcarePriorAuthorizationAutomationAgent_W1_Standard_Prior_Authorization_Submission_easy(BaseHealthcarePriorAuthorizationAutomationAgentTestCase):
    """Standard MRI PA - All Documentation Present, Criteria Met

    Validates standard PA flow for a common imaging procedure (MRI) with all required documentation present and criteria met.
    """

    test_case_id = "HealthcarePA_W1_TC1"
    title = "Standard MRI PA - All Documentation Present, Criteria Met"
    workflow = "W1 - Standard Prior Authorization Submission"

    input_data = {
        "patient_id": "PAT-445566",
        "payer_id": "PAYER-ANTHEM",
        "plan_id": "PLAN-BCBS-01",
        "cpt_code": "72148",
        "diagnosis_code": "M54.5",
        "service_type": "standard"
    }

    expected_tool_calls = [
        # Step 1: Check if PA required
        {
            "name": "check_pa_requirements",
            "tool_inputs": {
                "payer_id": "PAYER-ANTHEM",
                "plan_id": "PLAN-BCBS-01",
                "cpt_code": "72148",
                "diagnosis_code": "M54.5"
            }
        },
        # Step 2: Retrieve medical necessity criteria
        {
            "name": "retrieve_medical_necessity_criteria",
            "tool_inputs": {
                "payer_id": "PAYER-ANTHEM",
                "cpt_code": "72148",
                "diagnosis_code": "M54.5"
            }
        },
        # Step 3: Gather clinical documentation
        {
            "name": "gather_clinical_documentation",
            "tool_inputs": {
                "patient_id": "PAT-445566",
                "required_docs": ["clinical note", "imaging report"]
            }
        },
        # Step 4: Validate clinical criteria
        {
            "name": "validate_clinical_criteria",
            "tool_inputs": {
                "criteria_object": {
                    "criteria_text": "MRI criteria",
                    "required_docs": ["clinical note", "imaging report"],
                    "decision_tree": {}
                },
                "clinical_data": {
                    "docs_found": [
                        {"type": "clinical note", "content": "Outpatient note - back pain"},
                        {"type": "imaging report", "content": "X-ray: negative, MRI requested"}
                    ],
                    "docs_missing": [],
                    "summary": "All required documentation present."
                }
            }
        },
        # Step 5: Prepare PA submission
        {
            "name": "prepare_pa_submission",
            "tool_inputs": {
                "patient_id": "PAT-445566",
                "payer_id": "PAYER-ANTHEM",
                "cpt_code": "72148",
                "diagnosis_code": "M54.5",
                "clinical_summary": "Patient meets MRI criteria for lumbar spine; all documentation attached.",
                "attachments": [
                    {"type": "clinical note", "content": "Outpatient note - back pain"},
                    {"type": "imaging report", "content": "X-ray: negative, MRI requested"}
                ]
            }
        },
        # Step 6: Submit PA request
        {
            "name": "submit_pa_request",
            "tool_inputs": {
                "pa_submission": {
                    "pa_form": {
                        "patient_id": "PAT-445566",
                        "payer_id": "PAYER-ANTHEM",
                        "cpt_code": "72148",
                        "diagnosis_code": "M54.5",
                        "clinical_summary": "Patient meets MRI criteria for lumbar spine; all documentation attached."
                    },
                    "attachments": [
                        {"type": "clinical note", "content": "Outpatient note - back pain"},
                        {"type": "imaging report", "content": "X-ray: negative, MRI requested"}
                    ],
                    "ready_to_submit": True
                },
                "delivery_method": "portal",
                "portal_id": "PORTAL-ANTHEM"
            }
        },
        # Step 7: Track PA status
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "PA-778899",
                "payer_id": "PAYER-ANTHEM"
            }
        },
        # Final: SUCCESS system tool
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "PA approved and provider notified.",
                "result_data": {
                    "pa_status": "approved",
                    "auth_number": "AUTH-556677",
                    "decision_notes": "Approved for 90 days, MRI criteria met.",
                    "reference_id": "PA-778899",
                    "valid_through": "2024-09-10"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "PA requirement checked for MRI",
            "expected_state": {
                "pa_required": True
            }
        },
        {
            "step": 2,
            "description": "Medical necessity criteria retrieved for MRI",
            "expected_state": {
                "criteria_text": "MRI criteria",
                "required_docs": [
                    "clinical note",
                    "imaging report"
                ]
            }
        },
        {
            "step": 3,
            "description": "All required clinical documentation gathered",
            "expected_state": {
                "docs_found": [
                    "clinical note",
                    "imaging report"
                ],
                "docs_missing": []
            }
        },
        {
            "step": 4,
            "description": "Clinical criteria validated",
            "expected_state": {
                "criteria_met": True
            }
        },
        {
            "step": 5,
            "description": "PA submission prepared and assembled",
            "expected_state": {
                "ready_to_submit": True
            }
        },
        {
            "step": 6,
            "description": "PA request submitted via API/portal",
            "expected_state": {
                "submission_status": "submitted"
            }
        },
        {
            "step": 7,
            "description": "PA status tracked; provider notified of approval",
            "expected_state": {
                "pa_status": "approved",
                "auth_number": "AUTH-556677"
            }
        }
    ]

    description = (
        "Validates standard PA flow for a common imaging procedure (MRI) with all required documentation present and criteria met."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This is a straightforward, happy-path scenario: all required documentation is present in the EHR, "
        "the medical necessity criteria are clearly met, and the PA is submitted and approved without any exceptions or escalations."
    )

class TestCase2_HealthcarePriorAuthorizationAutomationAgent_W1_Standard_Prior_Authorization_Submission_easy(
    BaseHealthcarePriorAuthorizationAutomationAgentTestCase
):
    """
    Standard Sleep Study PA - Alternate Documentation Path

    Tests standard PA for a sleep study (CPT 95800), where alternate documentation (e.g., home sleep test report) is required and present.
    """

    test_case_id = "HealthcarePA_W1_TC2"
    title = "Standard Sleep Study PA - Alternate Documentation Path"
    workflow = "W1 - Standard Prior Authorization Submission"
    input_data = {
        "patient_id": "PAT-445641",
        "payer_id": "PAYER-UHC",
        "plan_id": "PLAN-MEDICARE-02",
        "cpt_code": "95800",
        "diagnosis_code": "G47.33",
        "service_type": "standard"
    }
    expected_tool_calls = [
        {
            "name": "check_pa_requirements",
            "tool_inputs": {
                "payer_id": "PAYER-UHC",
                "plan_id": "PLAN-MEDICARE-02",
                "cpt_code": "95800",
                "diagnosis_code": "G47.33"
            }
        },
        {
            "name": "retrieve_medical_necessity_criteria",
            "tool_inputs": {
                "payer_id": "PAYER-UHC",
                "cpt_code": "95800",
                "diagnosis_code": "G47.33"
            }
        },
        {
            "name": "gather_clinical_documentation",
            "tool_inputs": {
                "patient_id": "PAT-445641",
                "required_docs": [
                    "clinical note",
                    "home sleep test report"
                ]
            }
        },
        {
            "name": "validate_clinical_criteria",
            "tool_inputs": {
                "criteria_object": {
                    "criteria_text": "Sleep study criteria",
                    "required_docs": [
                        "clinical note",
                        "home sleep test report"
                    ]
                },
                "clinical_data": {
                    "docs_found": ["clinical note", "home sleep test report"],
                    "docs_missing": [],
                    "summary": "Clinical note and home sleep test report available."
                }
            }
        },
        {
            "name": "prepare_pa_submission",
            "tool_inputs": {
                "patient_id": "PAT-445641",
                "payer_id": "PAYER-UHC",
                "cpt_code": "95800",
                "diagnosis_code": "G47.33",
                "clinical_summary": "Clinical note and home sleep test report meet criteria for sleep study.",
                "attachments": [
                    {"type": "clinical note", "content": "..."}, 
                    {"type": "home sleep test report", "content": "..."}
                ]
            }
        },
        {
            "name": "submit_pa_request",
            "tool_inputs": {
                "pa_submission": {
                    "pa_form": {
                        "patient_id": "PAT-445641",
                        "payer_id": "PAYER-UHC",
                        "cpt_code": "95800",
                        "diagnosis_code": "G47.33",
                        "clinical_summary": "Clinical note and home sleep test report meet criteria for sleep study."
                    },
                    "attachments": [
                        {"type": "clinical note", "content": "..."},
                        {"type": "home sleep test report", "content": "..."}
                    ],
                    "ready_to_submit": True
                },
                "delivery_method": "portal",
                "portal_id": None
            }
        },
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "PA-445601",
                "payer_id": "PAYER-UHC"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "PA approved and provider notified.",
                "result_data": {
                    "pa_status": "approved",
                    "auth_number": "AUTH-991122",
                    "decision_notes": "Approved, home sleep study criteria met.",
                    "reference_id": "PA-445601",
                    "valid_through": "2025-01-15"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "PA requirement checked for sleep study",
            "expected_state": {
                "pa_required": True
            }
        },
        {
            "step": 2,
            "description": "Medical necessity criteria retrieved for sleep study",
            "expected_state": {
                "criteria_text": "Sleep study criteria",
                "required_docs": [
                    "clinical note",
                    "home sleep test report"
                ]
            }
        },
        {
            "step": 3,
            "description": "Alternate required documentation gathered",
            "expected_state": {
                "docs_found": [
                    "clinical note",
                    "home sleep test report"
                ],
                "docs_missing": []
            }
        },
        {
            "step": 4,
            "description": "Clinical criteria validated using alternate documentation",
            "expected_state": {
                "criteria_met": True
            }
        },
        {
            "step": 5,
            "description": "PA submission prepared",
            "expected_state": {
                "ready_to_submit": True
            }
        },
        {
            "step": 6,
            "description": "PA request submitted via portal",
            "expected_state": {
                "submission_status": "submitted"
            }
        },
        {
            "step": 7,
            "description": "PA status tracked; provider notified of approval",
            "expected_state": {
                "pa_status": "approved",
                "auth_number": "AUTH-991122"
            }
        }
    ]
    description = (
        "Tests standard PA for a sleep study (CPT 95800), where alternate documentation (e.g., home sleep test report) "
        "is required and present."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This is a straightforward standard PA case for a common procedure (sleep study) where all required and alternate "
        "documentation is available up front, and criteria are clearly met. No ambiguous or missing data, and no escalation or appeal needed."
    )

class TestCase3_HealthcarePriorAuthorizationAutomationAgent_W2_Documentation_Request_and_Completion_Workflow_medium(BaseHealthcarePriorAuthorizationAutomationAgentTestCase):
    """Documentation Completion After Initial EHR Deficiency

    Validates agent's ability to successfully complete PA after missing documents are requested and received from provider.
    """

    test_case_id = "HealthcarePA_W2_TC1"
    title = "Documentation Completion After Initial EHR Deficiency"
    workflow = "W2 - Documentation Request and Completion Workflow"

    input_data = {
        "patient_id": "PAT-445566",
        "payer_id": "PAYER-ANTHEM",
        "plan_id": "PLAN-BCBS-01",
        "cpt_code": "72148",
        "diagnosis_code": "M54.5",
        "service_type": "standard",
        "additional_docs_needed": True
    }

    expected_tool_calls = [
        # Step 1: Check PA requirements
        {
            "name": "check_pa_requirements",
            "tool_inputs": {
                "payer_id": "PAYER-ANTHEM",
                "plan_id": "PLAN-BCBS-01",
                "cpt_code": "72148",
                "diagnosis_code": "M54.5"
            }
        },
        # Step 1: Retrieve medical necessity criteria
        {
            "name": "retrieve_medical_necessity_criteria",
            "tool_inputs": {
                "payer_id": "PAYER-ANTHEM",
                "cpt_code": "72148",
                "diagnosis_code": "M54.5"
            }
        },
        # Step 2: Attempt to gather available clinical documentation (only "clinical note" found)
        {
            "name": "gather_clinical_documentation",
            "tool_inputs": {
                "patient_id": "PAT-445566",
                "required_docs": ["clinical note", "imaging report"]
            }
        },
        # Step 3: HUMAN_IN_THE_LOOP - request missing docs from provider
        {
            "name": "HUMAN_IN_THE_LOOP",
            "tool_inputs": {
                "ai_message": "Requesting missing documentation from provider: imaging report required for PA submission."
            }
        },
        # Step 3: gather_clinical_documentation again after provider sends missing doc
        {
            "name": "gather_clinical_documentation",
            "tool_inputs": {
                "patient_id": "PAT-445566",
                "required_docs": ["imaging report"]
            }
        },
        # Step 4: validate_clinical_criteria (now all docs present)
        {
            "name": "validate_clinical_criteria",
            "tool_inputs": {
                "criteria_object": {
                    "criteria_text": "MRI lumbar spine: clinical note and imaging report required.",
                    "required_docs": ["clinical note", "imaging report"],
                    "decision_tree": {}
                },
                "clinical_data": {
                    "docs_found": ["clinical note", "imaging report"],
                    "docs_missing": [],
                    "summary": "Clinical note and imaging report received."
                }
            }
        },
        # Step 5: prepare_pa_submission
        {
            "name": "prepare_pa_submission",
            "tool_inputs": {
                "patient_id": "PAT-445566",
                "payer_id": "PAYER-ANTHEM",
                "cpt_code": "72148",
                "diagnosis_code": "M54.5",
                "clinical_summary": "Clinical note and imaging report confirm MRI meets medical necessity criteria.",
                "attachments": [
                    {"type": "clinical note", "status": "attached"},
                    {"type": "imaging report", "status": "attached"}
                ]
            }
        },
        # Step 5: submit_pa_request
        {
            "name": "submit_pa_request",
            "tool_inputs": {
                "pa_submission": {
                    "pa_form": {"patient_id": "PAT-445566", "cpt_code": "72148"},
                    "attachments": [
                        {"type": "clinical note", "status": "attached"},
                        {"type": "imaging report", "status": "attached"}
                    ],
                    "ready_to_submit": True
                },
                "delivery_method": "portal",
                "portal_id": "PORTAL-ANTHEM"
            }
        },
        # Step 6: track_pa_status
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "PA-778899",
                "payer_id": "PAYER-ANTHEM"
            }
        },
        # Step 6: SUCCESS - notify provider of approval
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "PA approved and provider notified.",
                "result_data": {
                    "pa_status": "approved",
                    "auth_number": "AUTH-556677",
                    "decision_notes": "Approved for 90 days, MRI criteria met after additional documentation received.",
                    "reference_id": "PA-778899",
                    "valid_through": "2024-09-10"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "PA requirements and criteria checked",
            "expected_state": {
                "pa_required": True
            }
        },
        {
            "step": 2,
            "description": "Initial clinical documentation gathered; some documents missing",
            "expected_state": {
                "docs_found": ["clinical note"],
                "docs_missing": ["imaging report"]
            }
        },
        {
            "step": 3,
            "description": "Provider supplies missing documentation (imaging report)",
            "expected_state": {
                "docs_found": ["imaging report"],
                "docs_missing": []
            }
        },
        {
            "step": 4,
            "description": "Clinical criteria validated after all docs present",
            "expected_state": {
                "criteria_met": True
            }
        },
        {
            "step": 5,
            "description": "PA submission prepared and sent",
            "expected_state": {
                "ready_to_submit": True
            }
        },
        {
            "step": 6,
            "description": "PA status tracked; provider notified of approval",
            "expected_state": {
                "pa_status": "approved",
                "auth_number": "AUTH-556677"
            }
        }
    ]

    description = (
        "Validates agent's ability to successfully complete PA after missing documents are requested "
        "and received from provider. This test follows the workflow branch where initial EHR query is "
        "missing required documentation, the provider is prompted, and upon receipt the workflow completes successfully."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This test involves handling a missing documentation branch, requiring the agent to pause, request, and successfully "
        "integrate supplemental documents from the provider before proceeding. It tests state management and proper workflow resumption."
    )

class TestCase4_HealthcarePriorAuthorizationAutomationAgent_W3_Specialty_Drug_Prior_Authorization_Workflow_easy(
    BaseHealthcarePriorAuthorizationAutomationAgentTestCase
):
    """
    Specialty Drug PA - High-Cost Medication, All Criteria Met

    Tests successful specialty drug PA for a high-cost medication (J0135), with all intensive documentation and review requirements met.
    """

    test_case_id = "HealthcarePA_W3_TC1"
    title = "Specialty Drug PA - High-Cost Medication, All Criteria Met"
    workflow = "W3 - Specialty Drug Prior Authorization Workflow"
    input_data = {
        "patient_id": "PAT-445641",
        "payer_id": "PAYER-UHC",
        "plan_id": "PLAN-MEDICARE-02",
        "cpt_code": "J0135",
        "diagnosis_code": "M06.9",
        "service_type": "specialty_drug",
        "specialty_drug": True,
    }
    expected_tool_calls = [
        {
            "name": "check_pa_requirements",
            "tool_inputs": {
                "payer_id": "PAYER-UHC",
                "plan_id": "PLAN-MEDICARE-02",
                "cpt_code": "J0135",
                "diagnosis_code": "M06.9",
            },
        },
        {
            "name": "retrieve_medical_necessity_criteria",
            "tool_inputs": {
                "payer_id": "PAYER-UHC",
                "cpt_code": "J0135",
                "diagnosis_code": "M06.9",
            },
        },
        {
            "name": "gather_clinical_documentation",
            "tool_inputs": {
                "patient_id": "PAT-445641",
                "required_docs": ["labs", "treatment history", "provider notes"],
            },
        },
        {
            "name": "validate_clinical_criteria",
            "tool_inputs": {
                "criteria_object": {
                    "criteria_text": "Specialty drug criteria",
                    "required_docs": ["labs", "treatment history", "provider notes"],
                    "decision_tree": {},
                },
                "clinical_data": {
                    "docs_found": ["labs", "treatment history", "provider notes"],
                    "docs_missing": [],
                    "summary": "All required specialty drug documentation present.",
                },
            },
        },
        {
            "name": "prepare_pa_submission",
            "tool_inputs": {
                "patient_id": "PAT-445641",
                "payer_id": "PAYER-UHC",
                "cpt_code": "J0135",
                "diagnosis_code": "M06.9",
                "clinical_summary": "All specialty drug criteria and documentation met for J0135.",
                "attachments": [
                    {"type": "labs", "content": "Lab results for J0135"},
                    {"type": "treatment history", "content": "Tx history for J0135"},
                    {"type": "provider notes", "content": "Provider notes for J0135"},
                ],
            },
        },
        {
            "name": "submit_pa_request",
            "tool_inputs": {
                "pa_submission": {
                    "pa_form": {
                        "patient_id": "PAT-445641",
                        "payer_id": "PAYER-UHC",
                        "cpt_code": "J0135",
                        "diagnosis_code": "M06.9",
                        "clinical_summary": "All specialty drug criteria and documentation met for J0135.",
                    },
                    "attachments": [
                        {"type": "labs", "content": "Lab results for J0135"},
                        {"type": "treatment history", "content": "Tx history for J0135"},
                        {"type": "provider notes", "content": "Provider notes for J0135"},
                    ],
                    "ready_to_submit": True,
                },
                "delivery_method": "portal",
                "portal_id": "PORTAL-UHC",
            },
        },
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "PA-445601",
                "payer_id": "PAYER-UHC",
            },
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Specialty drug PA approved after clinical review.",
                "result_data": {
                    "pa_status": "approved",
                    "auth_number": "AUTH-991122",
                    "decision_notes": "Specialty drug PA approved after clinical review.",
                    "reference_id": "PA-445601",
                    "valid_through": "2025-01-15",
                },
            },
        },
    ]
    milestones = [
        {
            "step": 1,
            "description": "PA requirement checked for specialty drug",
            "expected_state": {
                "pa_required": True,
            },
        },
        {
            "step": 2,
            "description": "Detailed medical necessity criteria retrieved",
            "expected_state": {
                "criteria_text": "Specialty drug criteria",
                "required_docs": ["labs", "treatment history", "provider notes"],
            },
        },
        {
            "step": 3,
            "description": "Extensive documentation gathered",
            "expected_state": {
                "docs_found": ["labs", "treatment history", "provider notes"],
                "docs_missing": [],
            },
        },
        {
            "step": 4,
            "description": "Clinical criteria validated",
            "expected_state": {
                "criteria_met": True,
            },
        },
        {
            "step": 5,
            "description": "Comprehensive PA submission prepared",
            "expected_state": {
                "ready_to_submit": True,
            },
        },
        {
            "step": 6,
            "description": "PA submitted via appropriate channel",
            "expected_state": {
                "submission_status": "submitted",
            },
        },
        {
            "step": 7,
            "description": "PA status tracked; provider notified of approval",
            "expected_state": {
                "pa_status": "approved",
                "auth_number": "AUTH-991122",
            },
        },
    ]
    description = (
        "Tests successful specialty drug PA for a high-cost medication (J0135), with all intensive documentation and review requirements met."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "All required documentation and criteria are present and met; the workflow follows the happy path for specialty drug PA approval with no missing data, ambiguous criteria, or escalation required."
    )

class TestCase5_HealthcarePriorAuthorizationAutomationAgent_W4_Denial_and_Appeal_Workflow_easy(BaseHealthcarePriorAuthorizationAutomationAgentTestCase):
    """
    Appeal After Initial PA Denial - Additional Evidence Provided

    Validates successful appeal process when new documentation is available and appeal is approved.
    """

    test_case_id = "HealthcarePA_W4_TC1"
    title = "Appeal After Initial PA Denial - Additional Evidence Provided"
    workflow = "W4 - Denial and Appeal Workflow"
    input_data = {
        "patient_id": "PAT-445641",
        "payer_id": "PAYER-UHC",
        "plan_id": "PLAN-MEDICARE-02",
        "cpt_code": "J0135",
        "diagnosis_code": "M06.9",
        "service_type": "specialty_drug",
        "appeal_requested": True
    }
    expected_tool_calls = [
        # Step 1: Track PA status and retrieve denial reason
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "PA-445641-J0135",  # Assuming a reference_id convention; in real world, this would be available from previous PA submission
                "payer_id": "PAYER-UHC"
            },
            "mock_response": {
                "status": "denied",
                "auth_number": None,
                "decision_notes": "Initial criteria not met",
                "valid_through": None
            }
        },
        # Step 2: Gather supplemental documentation or evidence for appeal
        {
            "name": "gather_clinical_documentation",
            "tool_inputs": {
                "patient_id": "PAT-445641",
                "required_docs": ["additional labs", "specialist note"]
            },
            "mock_response": {
                "docs_found": ["additional labs", "specialist note"],
                "docs_missing": [],
                "summary": "Supplemental documentation for appeal gathered: additional labs, specialist note."
            }
        },
        # Step 3: Prepare appeal submission with additional evidence and justification
        {
            "name": "appeal_pa_denial",
            "tool_inputs": {
                "reference_id": "PA-445641-J0135",
                "payer_id": "PAYER-UHC",
                "additional_docs": ["additional labs", "specialist note"],
                "appeal_reason": "Additional evidence provided - clinical necessity supported by new documentation."
            },
            "mock_response": {
                "appeal_status": "submitted",
                "new_reference_id": "APPEAL-223344",
                "timestamp": "2024-12-01T10:00:00Z"
            }
        },
        # Step 4: Submit appeal and monitor status
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "APPEAL-223344",
                "payer_id": "PAYER-UHC"
            },
            "mock_response": {
                "status": "approved",
                "auth_number": "AUTH-991122",
                "decision_notes": "Appeal approved after review of supplemental documentation.",
                "valid_through": "2025-01-15"
            }
        },
        # Step 5: Notify provider of outcome
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Appeal approved after review of supplemental documentation.",
                "result_data": {
                    "final_status": "approved",
                    "pa_status": "approved",
                    "auth_number": "AUTH-991122",
                    "decision_notes": "Appeal approved after review of supplemental documentation.",
                    "reference_id": "APPEAL-223344",
                    "valid_through": "2025-01-15"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "PA status tracked; denial reason obtained",
            "expected_state": {
                "pa_status": "denied",
                "decision_notes": "Initial criteria not met"
            }
        },
        {
            "step": 2,
            "description": "Supplemental documentation gathered for appeal",
            "expected_state": {
                "docs_found": [
                    "additional labs",
                    "specialist note"
                ],
                "docs_missing": []
            }
        },
        {
            "step": 3,
            "description": "Appeal submission prepared",
            "expected_state": {
                "appeal_status": "submitted",
                "new_reference_id": "APPEAL-223344"
            }
        },
        {
            "step": 4,
            "description": "Appeal status tracked; appeal approved",
            "expected_state": {
                "pa_status": "approved",
                "auth_number": "AUTH-991122"
            }
        },
        {
            "step": 5,
            "description": "Provider notified of appeal approval",
            "expected_state": {
                "final_status": "approved"
            }
        }
    ]
    description = "Validates successful appeal process when new documentation is available and appeal is approved."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the straightforward appeal path: initial denial is confirmed, "
        "all required supplemental documentation is available, the appeal is submitted with a valid reason, "
        "and approval is granted without escalation or missing data. No error handling or ambiguous cases."
    )

    # Optionally, override tool methods if specific behavior is needed for this test case
    # For this test, base class methods are sufficient as the path is standard and successful

class TestCase6_HealthcarePriorAuthorizationAutomationAgent_W5_Durable_Medical_Equipment_PA_Workflow_easy(BaseHealthcarePriorAuthorizationAutomationAgentTestCase):
    """
    DME PA - Home Oxygen, All Clinical Criteria Met

    Validates successful DME PA for home oxygen (E1390) with all required documentation (pulse ox, ABG, diagnosis) present.
    """

    test_case_id = "HealthcarePA_W5_TC1"
    title = "DME PA - Home Oxygen, All Clinical Criteria Met"
    workflow = "W5 - Durable Medical Equipment PA Workflow"

    input_data = {
        "patient_id": "PAT-445566",
        "payer_id": "PAYER-ANTHEM",
        "plan_id": "PLAN-BCBS-01",
        "cpt_code": "E1390",
        "diagnosis_code": "J44.9",
        "service_type": "dme"
    }

    expected_tool_calls = [
        {
            "name": "check_pa_requirements",
            "tool_inputs": {
                "payer_id": "PAYER-ANTHEM",
                "plan_id": "PLAN-BCBS-01",
                "cpt_code": "E1390",
                "diagnosis_code": "J44.9"
            }
        },
        {
            "name": "retrieve_medical_necessity_criteria",
            "tool_inputs": {
                "payer_id": "PAYER-ANTHEM",
                "cpt_code": "E1390",
                "diagnosis_code": "J44.9"
            }
        },
        {
            "name": "gather_clinical_documentation",
            "tool_inputs": {
                "patient_id": "PAT-445566",
                "required_docs": ["diagnosis", "pulse ox", "ABG"]
            }
        },
        {
            "name": "validate_clinical_criteria",
            "tool_inputs": {
                "criteria_object": {
                    "criteria_text": "DME criteria",
                    "required_docs": ["diagnosis", "pulse ox", "ABG"]
                },
                "clinical_data": {
                    "docs_found": ["diagnosis", "pulse ox", "ABG"],
                    "docs_missing": [],
                    "summary": "All required DME documentation present."
                }
            }
        },
        {
            "name": "prepare_pa_submission",
            "tool_inputs": {
                "patient_id": "PAT-445566",
                "payer_id": "PAYER-ANTHEM",
                "cpt_code": "E1390",
                "diagnosis_code": "J44.9",
                "clinical_summary": "All required DME documentation present. Criteria met for home oxygen.",
                "attachments": ["diagnosis", "pulse ox", "ABG"]
            }
        },
        {
            "name": "submit_pa_request",
            "tool_inputs": {
                "pa_submission": {
                    "pa_form": {
                        "patient_id": "PAT-445566",
                        "payer_id": "PAYER-ANTHEM",
                        "cpt_code": "E1390",
                        "diagnosis_code": "J44.9",
                        "clinical_summary": "All required DME documentation present. Criteria met for home oxygen."
                    },
                    "attachments": ["diagnosis", "pulse ox", "ABG"],
                    "ready_to_submit": True
                },
                "delivery_method": "portal",
                "portal_id": "PORTAL-ANTHEM"
            }
        },
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "PA-778899",
                "payer_id": "PAYER-ANTHEM"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "DME PA approved; home oxygen delivery authorized.",
                "result_data": {
                    "pa_status": "approved",
                    "auth_number": "AUTH-556677",
                    "decision_notes": "DME PA approved; home oxygen delivery authorized.",
                    "reference_id": "PA-778899",
                    "valid_through": "2024-09-10"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "PA requirement checked for DME",
            "expected_state": {
                "pa_required": True
            }
        },
        {
            "step": 2,
            "description": "Medical necessity criteria for DME retrieved",
            "expected_state": {
                "criteria_text": "DME criteria",
                "required_docs": [
                    "diagnosis",
                    "pulse ox",
                    "ABG"
                ]
            }
        },
        {
            "step": 3,
            "description": "Required DME documentation gathered",
            "expected_state": {
                "docs_found": [
                    "diagnosis",
                    "pulse ox",
                    "ABG"
                ],
                "docs_missing": []
            }
        },
        {
            "step": 4,
            "description": "Clinical criteria validated",
            "expected_state": {
                "criteria_met": True
            }
        },
        {
            "step": 5,
            "description": "PA submission prepared and sent",
            "expected_state": {
                "ready_to_submit": True
            }
        },
        {
            "step": 6,
            "description": "PA status tracked; supplier notified",
            "expected_state": {
                "pa_status": "approved",
                "auth_number": "AUTH-556677"
            }
        }
    ]

    description = (
        "Validates successful DME PA for home oxygen (E1390) with all required documentation (pulse ox, ABG, diagnosis) present."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "All clinical criteria and documentation are present and valid for DME PA. "
        "This is a straightforward approval scenario with no missing data, ambiguous criteria, or system errors."
    )

class TestCase7_HealthcarePriorAuthorizationAutomationAgent_W6_Urgent_Expedited_Prior_Authorization_Workflow_easy(
    BaseHealthcarePriorAuthorizationAutomationAgentTestCase
):
    """
    Urgent Cardiac Cath PA - Expedited Approval

    Validates agent's ability to process urgent PA requests for cardiac catheterization (CPT 93458), ensuring expedited workflow and approval.
    """

    test_case_id = "HealthcarePA_W6_TC1"
    title = "Urgent Cardiac Cath PA - Expedited Approval"
    workflow = "W6 - Urgent/Expedited Prior Authorization Workflow"

    input_data = {
        "patient_id": "PAT-445566",
        "payer_id": "PAYER-ANTHEM",
        "plan_id": "PLAN-BCBS-01",
        "cpt_code": "93458",
        "diagnosis_code": "I25.10",
        "service_type": "urgent",
        "urgent": True
    }

    expected_tool_calls = [
        {
            "name": "check_pa_requirements",
            "tool_inputs": {
                "payer_id": "PAYER-ANTHEM",
                "plan_id": "PLAN-BCBS-01",
                "cpt_code": "93458",
                "diagnosis_code": "I25.10"
            }
        },
        {
            "name": "gather_clinical_documentation",
            "tool_inputs": {
                "patient_id": "PAT-445566",
                "required_docs": ["ER note", "labs"]
            }
        },
        {
            "name": "prepare_pa_submission",
            "tool_inputs": {
                "patient_id": "PAT-445566",
                "payer_id": "PAYER-ANTHEM",
                "cpt_code": "93458",
                "diagnosis_code": "I25.10",
                "clinical_summary": "Urgent cardiac cath requested. Clinical criteria met per ER notes and labs.",
                "attachments": [
                    {"doc_type": "ER note", "content": "ER visit note for chest pain on 2024-08-31"},
                    {"doc_type": "labs", "content": "Troponin elevated, EKG abnormal"}
                ]
            }
        },
        {
            "name": "submit_pa_request",
            "tool_inputs": {
                "pa_submission": {
                    "pa_form": {
                        "patient_id": "PAT-445566",
                        "payer_id": "PAYER-ANTHEM",
                        "cpt_code": "93458",
                        "diagnosis_code": "I25.10",
                        "clinical_summary": "Urgent cardiac cath requested. Clinical criteria met per ER notes and labs."
                    },
                    "attachments": [
                        {"doc_type": "ER note", "content": "ER visit note for chest pain on 2024-08-31"},
                        {"doc_type": "labs", "content": "Troponin elevated, EKG abnormal"}
                    ],
                    "ready_to_submit": True
                },
                "delivery_method": "phone"
            }
        },
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "PA-778899",
                "payer_id": "PAYER-ANTHEM"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Urgent PA approved for cardiac cath; expedited review.",
                "result_data": {
                    "pa_status": "approved",
                    "auth_number": "AUTH-556677",
                    "decision_notes": "Urgent PA approved for cardiac cath; expedited review.",
                    "reference_id": "PA-778899",
                    "valid_through": "2024-09-10"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "PA requirement checked for urgent procedure",
            "expected_state": {
                "pa_required": True
            }
        },
        {
            "step": 2,
            "description": "Urgent clinical documentation (ER notes, labs) gathered",
            "expected_state": {
                "docs_found": [
                    "ER note",
                    "labs"
                ],
                "docs_missing": []
            }
        },
        {
            "step": 3,
            "description": "Expedited PA submission prepared",
            "expected_state": {
                "ready_to_submit": True
            }
        },
        {
            "step": 4,
            "description": "PA submitted via fastest method",
            "expected_state": {
                "submission_status": "submitted"
            }
        },
        {
            "step": 5,
            "description": "Expedited PA status tracked",
            "expected_state": {
                "pa_status": "approved",
                "auth_number": "AUTH-556677"
            }
        },
        {
            "step": 6,
            "description": "Provider notified of urgent approval",
            "expected_state": {
                "final_status": "approved"
            }
        }
    ]

    description = (
        "Validates agent's ability to process urgent PA requests for cardiac catheterization (CPT 93458), "
        "ensuring expedited workflow and approval."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case covers a straightforward urgent PA approval scenario: all clinical criteria and documents are available, "
        "and the agent must follow the expedited workflow without obstacles or exceptions."
    )

class TestCase8_HealthcarePriorAuthorizationAutomationAgent_W7_MultiStepBariatricSurgeryPAWorkflow_easy(BaseHealthcarePriorAuthorizationAutomationAgentTestCase):
    """Bariatric Surgery PA - All Multi-Step Criteria Met

    Validates multi-step bariatric surgery PA for CPT 43644, with all documentation (nutrition, psych eval, cardiac clearance) present and criteria met.
    """

    test_case_id = "HealthcarePA_W7_TC1"
    title = "Bariatric Surgery PA - All Multi-Step Criteria Met"
    workflow = "W7 - Multi-Step Bariatric Surgery PA Workflow"
    input_data = {
        "patient_id": "PAT-445641",
        "payer_id": "PAYER-UHC",
        "plan_id": "PLAN-MEDICARE-02",
        "cpt_code": "43644",
        "diagnosis_code": "E66.01",
        "service_type": "surgery"
    }
    expected_tool_calls = [
        {
            "name": "check_pa_requirements",
            "tool_inputs": {
                "payer_id": "PAYER-UHC",
                "plan_id": "PLAN-MEDICARE-02",
                "cpt_code": "43644",
                "diagnosis_code": "E66.01"
            }
        },
        {
            "name": "retrieve_medical_necessity_criteria",
            "tool_inputs": {
                "payer_id": "PAYER-UHC",
                "cpt_code": "43644",
                "diagnosis_code": "E66.01"
            }
        },
        {
            "name": "gather_clinical_documentation",
            "tool_inputs": {
                "patient_id": "PAT-445641",
                "required_docs": [
                    "nutrition eval",
                    "psych eval",
                    "cardiac clearance"
                ]
            }
        },
        {
            "name": "validate_clinical_criteria",
            "tool_inputs": {
                "criteria_object": {
                    "criteria_text": "Bariatric criteria",
                    "required_docs": [
                        "nutrition eval",
                        "psych eval",
                        "cardiac clearance"
                    ]
                },
                "clinical_data": {
                    "docs_found": [
                        "nutrition eval",
                        "psych eval",
                        "cardiac clearance"
                    ],
                    "docs_missing": [],
                    "summary": "All required documentation present for bariatric surgery PA."
                }
            }
        },
        {
            "name": "prepare_pa_submission",
            "tool_inputs": {
                "patient_id": "PAT-445641",
                "payer_id": "PAYER-UHC",
                "cpt_code": "43644",
                "diagnosis_code": "E66.01",
                "clinical_summary": "Patient meets all payer criteria for bariatric surgery. Nutrition, psych, and cardiac documentation complete.",
                "attachments": [
                    "nutrition eval",
                    "psych eval",
                    "cardiac clearance"
                ]
            }
        },
        {
            "name": "submit_pa_request",
            "tool_inputs": {
                "pa_submission": {
                    "pa_form": {
                        "patient_id": "PAT-445641",
                        "payer_id": "PAYER-UHC",
                        "cpt_code": "43644",
                        "diagnosis_code": "E66.01",
                        "clinical_summary": "Patient meets all payer criteria for bariatric surgery. Nutrition, psych, and cardiac documentation complete."
                    },
                    "attachments": [
                        "nutrition eval",
                        "psych eval",
                        "cardiac clearance"
                    ],
                    "ready_to_submit": True
                },
                "delivery_method": "portal",
                "portal_id": "PORTAL-UHC"
            }
        },
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "PA-445601",
                "payer_id": "PAYER-UHC"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Bariatric surgery PA approved; all criteria met.",
                "result_data": {
                    "pa_status": "approved",
                    "auth_number": "AUTH-991122",
                    "decision_notes": "Bariatric surgery PA approved; all criteria met.",
                    "reference_id": "PA-445601",
                    "valid_through": "2025-01-15"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "PA requirement checked for bariatric surgery",
            "expected_state": {
                "pa_required": True
            }
        },
        {
            "step": 2,
            "description": "Medical necessity criteria retrieved (BMI, comorbidities, program)",
            "expected_state": {
                "criteria_text": "Bariatric criteria",
                "required_docs": [
                    "nutrition eval",
                    "psych eval",
                    "cardiac clearance"
                ]
            }
        },
        {
            "step": 3,
            "description": "Comprehensive documentation gathered",
            "expected_state": {
                "docs_found": [
                    "nutrition eval",
                    "psych eval",
                    "cardiac clearance"
                ],
                "docs_missing": []
            }
        },
        {
            "step": 4,
            "description": "All clinical criteria validated",
            "expected_state": {
                "criteria_met": True
            }
        },
        {
            "step": 5,
            "description": "Large PA packet prepared for committee",
            "expected_state": {
                "ready_to_submit": True
            }
        },
        {
            "step": 6,
            "description": "PA submitted for committee review",
            "expected_state": {
                "submission_status": "submitted"
            }
        },
        {
            "step": 7,
            "description": "PA status tracked; provider notified",
            "expected_state": {
                "pa_status": "approved",
                "auth_number": "AUTH-991122"
            }
        }
    ]
    description = "Validates multi-step bariatric surgery PA for CPT 43644, with all documentation (nutrition, psych eval, cardiac clearance) present and criteria met."
    difficulty = "easy"
    difficulty_reasoning = (
        "All documentation is present and all clinical criteria are met. No missing data, "
        "ambiguous criteria, or escalation is required. This is the 'happy path' for the multi-step workflow."
    )

class TestCase9_HealthcarePriorAuthorizationAutomationAgent_W8_PA_Status_Tracking_and_Follow_Up_Workflow_easy(BaseHealthcarePriorAuthorizationAutomationAgentTestCase):
    """
    Test Case 9: Status Check for Approved PA

    Validates agent's ability to track and report approved PA status upon provider request.
    """

    test_case_id = "HealthcarePA_W8_TC1"
    title = "Status Check for Approved PA"
    workflow = "W8 - PA Status Tracking and Follow-Up Workflow"

    input_data = {
        "patient_id": "PAT-445566",
        "payer_id": "PAYER-ANTHEM",
        "plan_id": "PLAN-BCBS-01",
        "cpt_code": "72148",
        "diagnosis_code": "M54.5",
        "service_type": "standard",
        "pa_status_check": True
    }

    expected_tool_calls = [
        {
            "name": "track_pa_status",
            "tool_inputs": {
                "reference_id": "PA-778899",
                "payer_id": "PAYER-ANTHEM"
            },
            "mock_response": {
                "status": "approved",
                "auth_number": "AUTH-556677",
                "decision_notes": "Approved for 90 days, MRI criteria met.",
                "valid_through": "2024-09-10"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "PA approved. Authorization number: AUTH-556677. Valid through 2024-09-10. Notes: Approved for 90 days, MRI criteria met.",
                "result_data": {
                    "pa_status": "approved",
                    "auth_number": "AUTH-556677",
                    "decision_notes": "Approved for 90 days, MRI criteria met.",
                    "reference_id": "PA-778899",
                    "valid_through": "2024-09-10"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "PA status tracked for reference ID",
            "expected_state": {
                "pa_status": "approved",
                "auth_number": "AUTH-556677"
            }
        },
        {
            "step": 2,
            "description": "Results categorized as approved",
            "expected_state": {
                "final_status": "approved"
            }
        },
        {
            "step": 3,
            "description": "Provider notified of approval",
            "expected_state": {
                "final_status": "approved"
            }
        }
    ]

    description = "Validates agent's ability to track and report approved PA status upon provider request."
    difficulty = "easy"
    difficulty_reasoning = (
        "This is a straightforward status check for an already approved prior authorization. "
        "The agent only needs to perform a status lookup and communicate the result; no complex branching or error handling is required."
    )

    def track_pa_status(self, reference_id: str, payer_id: str) -> dict:
        """
        Monitor and update the status of submitted PA requests.

        Args:
            reference_id: Unique PA submission reference. Format: PA-XXXXXX.
            payer_id: Unique payer identifier.

        Returns:
            dict: Status object with status (enum: approved, denied, pended, expired),
                  auth_number (string), decision_notes (string), valid_through (ISO 8601)
        """
        print(f"--- Running track_pa_status ---")
        print(f"reference_id: {reference_id}, payer_id: {payer_id}")
        # Simulate approved PA status as per test case
        if reference_id == "PA-778899" and payer_id == "PAYER-ANTHEM":
            return {
                "status": "approved",
                "auth_number": "AUTH-556677",
                "decision_notes": "Approved for 90 days, MRI criteria met.",
                "valid_through": "2024-09-10"
            }
        # Default mock for other cases
        return {
            "status": "pended",
            "auth_number": None,
            "decision_notes": "Pending review.",
            "valid_through": None
        }