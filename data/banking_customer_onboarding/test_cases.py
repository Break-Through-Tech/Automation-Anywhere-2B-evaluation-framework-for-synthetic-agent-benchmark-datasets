from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from generator_v5.core.system_tools_base import SystemToolsBaseClass

# TypedDict definitions for structured object parameters

class ExtractedData(TypedDict):
    """Structured KYC data extracted from documents."""
    name: str
    dob: str  # ISO 8601 date string
    address: str
    id_type: str
    id_number: str

class CustomerData(TypedDict, total=False):
    """Customer and related party info for sanctions screening and core banking."""
    name: str
    dob: str  # ISO 8601
    nationality: str
    business_name: Optional[str]
    owner_names: Optional[List[str]]

class ProfileData(TypedDict, total=False):
    """Profile data for AML risk scoring."""
    nationality: str
    occupation: str
    business_type: Optional[str]
    transaction_volume: float  # USD
    geography: str

class CoreBankingCustomerData(TypedDict):
    """Customer profile for core banking creation."""
    name: str
    dob: str  # ISO 8601
    address: str
    kyc_status: str
    risk_level: str
    documents: List[Any]

class RelationshipData(TypedDict, total=False):
    """Optional relationship info for CRM profile."""
    business_owners: Optional[List[str]]
    review_frequency: Optional[str]  # annual|quarterly|monthly

class CommunicationResult(TypedDict):
    """Result from sending a communication."""
    message_id: str
    delivery_status: str
    timestamp: str
    estimated_delivery: str

class BaseBankingCustomerOnboardingAgentTestCase(SystemToolsBaseClass):
    """
    Base class containing common methods for all Banking Customer Onboarding test cases.
    """

    # Agent context attributes from agent description
    role = (
        "You are an automated banking customer onboarding agent that orchestrates "
        "document extraction, identity verification, sanctions screening, AML risk assessment, "
        "profile creation in core banking and CRM systems, and customer communications "
        "to ensure rapid, compliant onboarding."
    )
    goal = (
        "Your goal is to onboard new banking customers in under 30 minutes by automating "
        "KYC document processing, compliance checks, account creation, and welcome communications, "
        "while strictly adhering to regulatory requirements and minimizing manual intervention."
    )
    action_plan = {
        "assumptions": [
            "All required KYC documents are provided in standard formats (PDF, image).",
            "Integration endpoints for identity, sanctions, core banking, CRM, and communication systems are available and reliable.",
        ],
        "tools_and_resources": [
            "extract_kyc_documents",
            "validate_identity",
            "screen_sanctions_lists",
            "calculate_aml_risk_score",
            "create_core_banking_customer",
            "create_crm_profile",
            "send_welcome_communication",
            "SUCCESS/FAILED/CANCELLED/HUMAN_IN_THE_LOOP",
        ],
        "guidelines": [
            "Always verify identity and screen for sanctions before creating any account.",
            "Escalate high-risk, fraud, or sanctions-match cases to human compliance officers.",
            "Request additional documentation if required fields are missing or illegible.",
            "All workflows must end with a system tool signaling outcome.",
        ],
        "workflow_selection": [
            "Route to standard onboarding workflow for automated approval and account creation if all required KYC documents are present AND identity verification passes AND sanctions screening is clear AND AML risk is low or medium.",
            "Escalate for enhanced due diligence and human compliance review if AML risk score is high OR sanctions screening returns a partial match OR customer is from high-risk jurisdiction.",
            "Reject application and send fraud alert communication if identity verification fails OR document authenticity is questionable.",
            "Run business onboarding workflow with multi-party screening and account setup if application is for a business account with multiple beneficial owners.",
            "Immediately escalate, freeze application, and file SAR if sanctions screening returns an exact match.",
            "Request additional documentation and pause onboarding until received if any required document is missing or illegible.",
            "Request explanation, reconcile data, and proceed if resolved if address data from documents is inconsistent.",
            "Resume onboarding workflow after document receipt and validation if customer uploads additional documents after initial request.",
            "Cancel process and notify customer if any step encounters an unrecoverable system error.",
        ],
        "failure_points": [
            "Document extraction fails due to poor image quality or unsupported format. Recovery: Request document resubmission or alternative format from customer.",
            "Identity verification fails or returns ambiguous results. Recovery: Escalate to human compliance officer for manual review.",
            "Sanctions screening returns a match or possible match. Recovery: Escalate, freeze onboarding, and initiate regulatory filing if needed.",
            "Core banking or CRM system integration fails. Recovery: Retry integration, log error, and escalate if unresolved.",
            "Customer does not provide requested additional documentation. Recovery: Send reminder communication and cancel application if unresolved after 7 days.",
        ],
        "success_criteria": [
            "Customer account created in core banking and CRM systems with verified KYC and compliance checks.",
            "Welcome communication sent to customer within 30 minutes of application submission.",
            "All regulatory compliance steps (AML, sanctions, identity) completed and documented.",
            "High-risk, fraud, or sanctions cases escalated appropriately and not onboarded automatically.",
        ],
    }

    # --- Domain Tool Methods ---

    def extract_kyc_documents(self, document_files: List[str]) -> Dict[str, Any]:
        """
        Extract structured KYC data from uploaded documents using OCR and document AI.

        Args:
            document_files: List of uploaded document files (PDF, JPG, PNG). 
                Minimum 1, maximum 10. Example: ["driver_license.pdf", "utility_bill.jpg"]

        Returns:
            dict: Extracted fields as object per file, including:
                - name: str
                - dob: str (ISO 8601)
                - address: str
                - ID numbers: str
                - document_type: str
                - document_status: str
        """
        if not isinstance(document_files, list) or len(document_files) < 1 or len(document_files) > 10:
            raise ValueError("document_files must be a list with 1 to 10 filenames (PDF, JPG, PNG).")
        print(f"--- Running extract_kyc_documents ---")
        print(f"document_files: {document_files}")
        # Mock extraction: one entry per file
        extracted = []
        for fname in document_files:
            extracted.append({
                "name": "Sarah Chen",
                "dob": "1990-04-11",
                "address": "123 Main St, Boston, MA",
                "id_type": "driver_license" if "license" in fname else "passport",
                "id_number": "D12345678" if "license" in fname else "P99887766",
                "document_type": "driver_license" if "license" in fname else "passport",
                "document_status": "valid",
                "file": fname,
            })
        return {"documents": extracted}

    def validate_identity(
        self,
        extracted_data: ExtractedData,
        id_type: str,
        id_number: str
    ) -> Dict[str, Any]:
        """
        Verify customer identity using government databases and fraud detection.

        Args:
            extracted_data: Structured data from KYC extraction:
                - name: str
                - dob: str (ISO 8601)
                - address: str
                - id_type: str
                - id_number: str
            id_type: Type of identification document. Valid values:
                ['driver_license', 'passport', 'national_id', 'business_license', 'ein_letter']
            id_number: Identification number. Format depends on id_type.

        Returns:
            dict: Identity verification result:
                - status: 'verified' | 'failed' | 'pending'
                - details: str
                - fraud_flag: bool
        """
        valid_id_types = [
            "driver_license", "passport", "national_id", "business_license", "ein_letter"
        ]
        if id_type not in valid_id_types:
            raise ValueError(f"id_type must be one of {valid_id_types}, got {id_type}")
        print(f"--- Running validate_identity ---")
        print(f"extracted_data: {extracted_data}, id_type: {id_type}, id_number: {id_number}")
        # Simple mock logic: always verified unless id_number contains "X"
        if "X" in id_number:
            return {"status": "failed", "details": "ID number invalid", "fraud_flag": True}
        return {"status": "verified", "details": "ID verified", "fraud_flag": False}

    def screen_sanctions_lists(
        self,
        customer_data: CustomerData
    ) -> Dict[str, Any]:
        """
        Screen customer and related parties against OFAC, UN, EU, and PEP sanctions lists.

        Args:
            customer_data: Customer and related party info:
                - name: str
                - dob: str (ISO 8601)
                - nationality: str
                - business_name: Optional[str]
                - owner_names: Optional[List[str]]

        Returns:
            dict: Screening result:
                - match_status: 'none' | 'partial' | 'exact'
                - matched_list: List[str]
                - details: str
        """
        print(f"--- Running screen_sanctions_lists ---")
        print(f"customer_data: {customer_data}")
        # Mock: always 'none' unless customer name is "John Sanction"
        if customer_data.get("name", "") == "John Sanction":
            return {
                "match_status": "exact",
                "matched_list": ["OFAC"],
                "details": "Exact match found on OFAC list"
            }
        return {
            "match_status": "none",
            "matched_list": [],
            "details": "No matches found"
        }

    def calculate_aml_risk_score(
        self,
        profile_data: ProfileData
    ) -> Dict[str, Any]:
        """
        Calculate AML risk score based on customer profile, geography, occupation, and transaction intent.

        Args:
            profile_data: Profile data:
                - nationality: str
                - occupation: str
                - business_type: Optional[str]
                - transaction_volume: float (USD)
                - geography: str

        Returns:
            dict: Risk score object:
                - score: int (0-100)
                - risk_level: 'low' | 'medium' | 'high'
                - rationale: str
        """
        print(f"--- Running calculate_aml_risk_score ---")
        print(f"profile_data: {profile_data}")
        # Mock: high risk if geography = 'North Korea' or transaction_volume > 100000
        score = 30
        risk_level = "low"
        rationale = "Standard profile."
        if profile_data.get("geography", "").lower() == "north korea":
            score = 95
            risk_level = "high"
            rationale = "High-risk jurisdiction."
        elif profile_data.get("transaction_volume", 0) > 100000:
            score = 80
            risk_level = "high"
            rationale = "High transaction volume."
        elif profile_data.get("occupation", "").lower() == "politician":
            score = 70
            risk_level = "medium"
            rationale = "Politically exposed person."
        return {"score": score, "risk_level": risk_level, "rationale": rationale}

    def create_core_banking_customer(
        self,
        customer_data: CoreBankingCustomerData,
        account_type: str,
        authorized_signers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create new customer record and account in core banking system.

        Args:
            customer_data: Customer profile:
                - name: str
                - dob: str (ISO 8601)
                - address: str
                - kyc_status: str
                - risk_level: str
                - documents: List[Any]
            account_type: Type of account to open. Valid values:
                ['personal_checking', 'personal_savings', 'business_checking', 'business_savings']
            authorized_signers: List of authorized signer names for business accounts. 
                Minimum 0, maximum 10. Optional.

        Returns:
            dict: Banking creation result:
                - customer_id: str (CUST-XXXXXX)
                - account_id: str (ACC-XXXXXX)
                - status: 'created' | 'failed'
                - created_at: str (ISO 8601)
        """
        valid_account_types = [
            "personal_checking", "personal_savings", "business_checking", "business_savings"
        ]
        if account_type not in valid_account_types:
            raise ValueError(f"account_type must be one of {valid_account_types}, got {account_type}")
        if authorized_signers is not None and (not isinstance(authorized_signers, list) or len(authorized_signers) > 10):
            raise ValueError("authorized_signers must be a list with up to 10 names.")
        print(f"--- Running create_core_banking_customer ---")
        print(f"customer_data: {customer_data}")
        print(f"account_type: {account_type}")
        print(f"authorized_signers: {authorized_signers}")
        return {
            "customer_id": "CUST-887234",
            "account_id": "ACC-112345",
            "status": "created",
            "created_at": "2025-10-09T10:00:00Z"
        }

    def create_crm_profile(
        self,
        customer_id: str,
        risk_level: str,
        kyc_documents: List[Dict[str, Any]],
        relationship_data: Optional[RelationshipData] = None
    ) -> Dict[str, Any]:
        """
        Create or update customer profile in CRM with KYC documents and risk tier.

        Args:
            customer_id: Unique customer identifier. Format: CUST-XXXXXX.
            risk_level: Customer risk tier. Valid values: ['low', 'medium', 'high']
            kyc_documents: List of KYC document metadata (type, status, file_id). Minimum 1, maximum 10.
            relationship_data: Optional relationship info:
                - business_owners: Optional[List[str]]
                - review_frequency: Optional[str] (enum: annual|quarterly|monthly)

        Returns:
            dict: CRM profile creation result:
                - crm_id: str
                - status: 'created' | 'updated' | 'failed'
                - review_frequency: str
        """
        valid_risk_levels = ["low", "medium", "high"]
        if risk_level not in valid_risk_levels:
            raise ValueError(f"risk_level must be one of {valid_risk_levels}, got {risk_level}")
        if not isinstance(kyc_documents, list) or len(kyc_documents) < 1 or len(kyc_documents) > 10:
            raise ValueError("kyc_documents must be a list with 1 to 10 items.")
        if relationship_data is not None:
            if "review_frequency" in relationship_data:
                valid_review_frequencies = ["annual", "quarterly", "monthly"]
                if relationship_data["review_frequency"] not in valid_review_frequencies:
                    raise ValueError(
                        f"review_frequency must be one of {valid_review_frequencies}, got {relationship_data['review_frequency']}"
                    )
        print(f"--- Running create_crm_profile ---")
        print(f"customer_id: {customer_id}")
        print(f"risk_level: {risk_level}")
        print(f"kyc_documents: {kyc_documents}")
        print(f"relationship_data: {relationship_data}")
        return {
            "crm_id": "CRM-3321",
            "status": "created",
            "review_frequency": relationship_data.get("review_frequency", "annual") if relationship_data else "annual"
        }

    def send_welcome_communication(
        self,
        customer_id: str,
        communication_type: str,
        content: str,
        delivery_method: str = "email"
    ) -> CommunicationResult:
        """
        Send onboarding communication (welcome, rejection, document request) via email/SMS.

        Args:
            customer_id: Unique customer identifier. Format: CUST-XXXXXX.
            communication_type: Type of communication. Valid values:
                ['welcome', 'document_request', 'rejection', 'in_person_request', 'reminder']
            content: Message content. Length: 10-2000 characters.
            delivery_method: Preferred delivery channel. Valid values: ['email', 'sms', 'portal']
                Default: 'email'

        Returns:
            dict: Communication result:
                - message_id: str
                - delivery_status: 'sent' | 'queued' | 'failed'
                - timestamp: str (ISO 8601)
                - estimated_delivery: str (ISO 8601)
        """
        valid_comm_types = [
            "welcome", "document_request", "rejection", "in_person_request", "reminder"
        ]
        valid_delivery_methods = ["email", "sms", "portal"]
        if communication_type not in valid_comm_types:
            raise ValueError(f"communication_type must be one of {valid_comm_types}, got {communication_type}")
        if delivery_method not in valid_delivery_methods:
            raise ValueError(f"delivery_method must be one of {valid_delivery_methods}, got {delivery_method}")
        if not (10 <= len(content) <= 2000):
            raise ValueError("content length must be between 10 and 2000 characters.")
        print(f"--- Running send_welcome_communication ---")
        print(f"customer_id: {customer_id}")
        print(f"communication_type: {communication_type}")
        print(f"content: {content[:60]}...")
        print(f"delivery_method: {delivery_method}")
        return {
            "message_id": "MSG-001",
            "delivery_status": "sent",
            "timestamp": "2025-10-09T10:30:00Z",
            "estimated_delivery": "2025-10-09T10:35:00Z"
        }

    # --- System Tool Methods (inherited from SystemToolsBaseClass) ---
    # SUCCESS, FAILED, CANCELLED, HUMAN_IN_THE_LOOP are provided by SystemToolsBaseClass


class TestCase1_BankingCustomerOnboardingAgent_W1_StandardPersonalAccountOnboarding_easy(BaseBankingCustomerOnboardingAgentTestCase):
    """Low-Risk Personal Account: Standard KYC, Driver License

    Covers the most common onboarding for a personal customer with low AML risk, US nationality, and standard KYC documents.
    """

    test_case_id = "BankingCustomerOnboardingAgent_BankOnboard_W1_TC1"
    title = "Low-Risk Personal Account: Standard KYC, Driver License"
    workflow = "W1 - Standard Personal Account Onboarding"

    input_data = {
        "application_id": "APP-10001",
        "customer_type": "personal",
        "document_files": [
            "driver_license.pdf",
            "utility_bill.jpg"
        ],
        "account_type": "personal_checking",
        "contact_email": "alice.smith@email.com",
        "contact_phone": "+12025550123"
    }

    expected_tool_calls = [
        {
            "name": "extract_kyc_documents",
            "tool_inputs": {
                "document_files": [
                    "driver_license.pdf",
                    "utility_bill.jpg"
                ]
            }
        },
        {
            "name": "validate_identity",
            "tool_inputs": {
                "extracted_data": {
                    "name": "Alice Smith",
                    "dob": "1990-04-15",
                    "address": "123 Main St, Springfield, USA",
                    "id_type": "driver_license",
                    "id_number": "D12345678"
                },
                "id_type": "driver_license",
                "id_number": "D12345678"
            }
        },
        {
            "name": "screen_sanctions_lists",
            "tool_inputs": {
                "customer_data": {
                    "name": "Alice Smith",
                    "dob": "1990-04-15",
                    "nationality": "US"
                }
            }
        },
        {
            "name": "calculate_aml_risk_score",
            "tool_inputs": {
                "profile_data": {
                    "nationality": "US",
                    "occupation": "engineer",
                    "transaction_volume": 5000,
                    "geography": "US"
                }
            }
        },
        {
            "name": "create_core_banking_customer",
            "tool_inputs": {
                "customer_data": {
                    "name": "Alice Smith",
                    "dob": "1990-04-15",
                    "address": "123 Main St, Springfield, USA",
                    "kyc_status": "verified",
                    "risk_level": "low",
                    "documents": [
                        {
                            "document_type": "driver_license",
                            "document_status": "valid",
                            "file_id": "driver_license.pdf"
                        },
                        {
                            "document_type": "utility_bill",
                            "document_status": "valid",
                            "file_id": "utility_bill.jpg"
                        }
                    ]
                },
                "account_type": "personal_checking"
            }
        },
        {
            "name": "create_crm_profile",
            "tool_inputs": {
                "customer_id": "CUST-887234",
                "risk_level": "low",
                "kyc_documents": [
                    {
                        "document_type": "driver_license",
                        "document_status": "valid",
                        "file_id": "driver_license.pdf"
                    },
                    {
                        "document_type": "utility_bill",
                        "document_status": "valid",
                        "file_id": "utility_bill.jpg"
                    }
                ]
            }
        },
        {
            "name": "send_welcome_communication",
            "tool_inputs": {
                "customer_id": "CUST-887234",
                "communication_type": "welcome",
                "content": "Welcome Alice Smith! Your personal checking account (ACC-112345) is now active.",
                "delivery_method": "email"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Onboarding completed successfully.",
                "result_data": {
                    "onboarding_status": "success",
                    "customer_id": "CUST-887234",
                    "account_id": "ACC-112345",
                    "crm_id": "CRM-3321",
                    "communication_status": "sent"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Documents extracted",
            "expected_state": {
                "documents_status": "valid",
                "required_docs_present": True
            }
        },
        {
            "step": 2,
            "description": "Identity verified",
            "expected_state": {
                "identity_status": "verified",
                "fraud_flag": False
            }
        },
        {
            "step": 3,
            "description": "Sanctions screening clear",
            "expected_state": {
                "match_status": "none"
            }
        },
        {
            "step": 4,
            "description": "AML risk score calculated",
            "expected_state": {
                "risk_level": "low",
                "score": 25
            }
        },
        {
            "step": 5,
            "description": "Core banking customer created",
            "expected_state": {
                "status": "created",
                "customer_id": "CUST-887234"
            }
        },
        {
            "step": 6,
            "description": "CRM profile created",
            "expected_state": {
                "crm_id": "CRM-3321",
                "status": "created"
            }
        },
        {
            "step": 7,
            "description": "Welcome communication sent",
            "expected_state": {
                "communication_status": "sent"
            }
        }
    ]

    description = "Covers the most common onboarding for a personal customer with low AML risk, US nationality, and standard KYC documents."
    difficulty = "easy"
    difficulty_reasoning = (
        "All required documents are present and legible, customer is low risk, "
        "all compliance checks pass, and there are no branches in the workflow requiring "
        "escalation, manual review, or additional documentation. This represents the straight-through processing path."
    )

class TestCase2_BankingCustomerOnboardingAgent_W1_Standard_Personal_Account_Onboarding_medium(BaseBankingCustomerOnboardingAgentTestCase):
    """
    Medium-Risk Personal Account: Passport KYC, Foreign National, Higher Volume

    Validates onboarding for a personal customer with medium AML risk, foreign nationality, and different KYC document types.
    """

    test_case_id = "BankingCustomerOnboardingAgent_BankOnboard_W1_TC2"
    title = "Medium-Risk Personal Account: Passport KYC, Foreign National, Higher Volume"
    workflow = "W1 - Standard Personal Account Onboarding"

    input_data = {
        "application_id": "APP-10002",
        "customer_type": "personal",
        "document_files": [
            "passport.png",
            "proof_of_address.pdf"
        ],
        "account_type": "personal_savings",
        "contact_email": "oliver.jones@email.com",
        "contact_phone": "+447700900123"
    }

    expected_tool_calls = [
        {
            "name": "extract_kyc_documents",
            "tool_inputs": {
                "document_files": [
                    "passport.png",
                    "proof_of_address.pdf"
                ]
            }
        },
        {
            "name": "validate_identity",
            "tool_inputs": {
                "extracted_data": {
                    "name": "Oliver Jones",
                    "dob": "1984-07-23",
                    "address": "22 Regent Street, London, UK",
                    "id_type": "passport",
                    "id_number": "UK1234567"
                },
                "id_type": "passport",
                "id_number": "UK1234567"
            }
        },
        {
            "name": "screen_sanctions_lists",
            "tool_inputs": {
                "customer_data": {
                    "name": "Oliver Jones",
                    "dob": "1984-07-23",
                    "nationality": "UK"
                }
            }
        },
        {
            "name": "calculate_aml_risk_score",
            "tool_inputs": {
                "profile_data": {
                    "nationality": "UK",
                    "occupation": "consultant",
                    "transaction_volume": 30000,
                    "geography": "UK"
                }
            }
        },
        {
            "name": "create_core_banking_customer",
            "tool_inputs": {
                "customer_data": {
                    "name": "Oliver Jones",
                    "dob": "1984-07-23",
                    "address": "22 Regent Street, London, UK",
                    "kyc_status": "verified",
                    "risk_level": "medium",
                    "documents": [
                        {
                            "document_type": "passport",
                            "document_status": "valid",
                            "file_id": "passport.png"
                        },
                        {
                            "document_type": "proof_of_address",
                            "document_status": "valid",
                            "file_id": "proof_of_address.pdf"
                        }
                    ]
                },
                "account_type": "personal_savings"
            }
        },
        {
            "name": "create_crm_profile",
            "tool_inputs": {
                "customer_id": "CUST-992301",
                "risk_level": "medium",
                "kyc_documents": [
                    {
                        "document_type": "passport",
                        "document_status": "valid",
                        "file_id": "passport.png"
                    },
                    {
                        "document_type": "proof_of_address",
                        "document_status": "valid",
                        "file_id": "proof_of_address.pdf"
                    }
                ]
            }
        },
        {
            "name": "send_welcome_communication",
            "tool_inputs": {
                "customer_id": "CUST-992301",
                "communication_type": "welcome",
                "content": "Dear Oliver Jones, your personal savings account has been successfully opened. Welcome to our bank!",
                "delivery_method": "email"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Onboarding completed successfully for application APP-10002.",
                "result_data": {
                    "onboarding_status": "success",
                    "customer_id": "CUST-992301",
                    "account_id": "ACC-998877",
                    "crm_id": "CRM-9912",
                    "communication_status": "sent"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Documents extracted",
            "expected_state": {
                "documents_status": "valid",
                "required_docs_present": True
            }
        },
        {
            "step": 2,
            "description": "Identity verified",
            "expected_state": {
                "identity_status": "verified",
                "fraud_flag": False
            }
        },
        {
            "step": 3,
            "description": "Sanctions screening clear",
            "expected_state": {
                "match_status": "none"
            }
        },
        {
            "step": 4,
            "description": "AML risk score calculated",
            "expected_state": {
                "risk_level": "medium",
                "score": 55
            }
        },
        {
            "step": 5,
            "description": "Core banking customer created",
            "expected_state": {
                "status": "created",
                "customer_id": "CUST-992301"
            }
        },
        {
            "step": 6,
            "description": "CRM profile created",
            "expected_state": {
                "crm_id": "CRM-9912",
                "status": "created"
            }
        },
        {
            "step": 7,
            "description": "Welcome communication sent",
            "expected_state": {
                "communication_status": "sent"
            }
        }
    ]

    description = (
        "Validates onboarding for a personal customer with medium AML risk, foreign nationality, "
        "and different KYC document types. Success path differs due to medium risk score (from higher "
        "transaction volume and foreign nationality) but remains eligible for automated onboarding."
    )

    difficulty = "medium"
    difficulty_reasoning = (
        "The test case involves a non-trivial, medium AML risk scenario due to higher transaction volume "
        "and a foreign national, requiring correct risk calculation and workflow pathing. "
        "It also validates the agent's ability to process different KYC document types (passport, proof of address) "
        "and ensure all compliance and onboarding steps are completed automatically without escalation."
    )

class TestCase3_BankingCustomerOnboardingAgent_W4_Business_Account_Onboarding_Multiple_Documents_easy(BaseBankingCustomerOnboardingAgentTestCase):
    """Business Account: Multiple Owners, All Pass Screening

    Tests business onboarding with multiple beneficial owners, all with valid documents, low AML risk, and no sanctions matches.
    """

    test_case_id = "BankingCustomerOnboardingAgent_BankOnboard_W4_TC1"
    title = "Business Account: Multiple Owners, All Pass Screening"
    workflow = "W4"
    input_data = {
        "application_id": "APP-20001",
        "customer_type": "business",
        "document_files": [
            "business_license.pdf",
            "ein_letter.pdf",
            "proof_of_address.pdf",
            "john_smith_passport.jpg",
            "sarah_lee_passport.jpg"
        ],
        "account_type": "business_checking",
        "contact_email": "info@acmebiz.com",
        "contact_phone": "+16175551234",
        "beneficial_owners": [
            "John Smith",
            "Sarah Lee"
        ]
    }
    expected_tool_calls = [
        # Step 1: Extract KYC data from business and owner documents
        {
            "name": "extract_kyc_documents",
            "tool_inputs": {
                "document_files": [
                    "business_license.pdf",
                    "ein_letter.pdf",
                    "proof_of_address.pdf",
                    "john_smith_passport.jpg",
                    "sarah_lee_passport.jpg"
                ]
            }
        },
        # Step 2: Validate identity for each beneficial owner
        {
            "name": "validate_identity",
            "tool_inputs": {
                "extracted_data": {
                    "name": "John Smith",
                    "dob": "1980-04-15",
                    "address": "123 Main St, Springfield, USA",
                    "id_type": "passport",
                    "id_number": "P12345678"
                },
                "id_type": "passport",
                "id_number": "P12345678"
            }
        },
        {
            "name": "validate_identity",
            "tool_inputs": {
                "extracted_data": {
                    "name": "Sarah Lee",
                    "dob": "1985-09-21",
                    "address": "456 Oak Ave, Springfield, USA",
                    "id_type": "passport",
                    "id_number": "P87654321"
                },
                "id_type": "passport",
                "id_number": "P87654321"
            }
        },
        # Step 3: Screen business and owners for sanctions
        {
            "name": "screen_sanctions_lists",
            "tool_inputs": {
                "customer_data": {
                    "business_name": "Acme Biz LLC",
                    "owner_names": [
                        "John Smith",
                        "Sarah Lee"
                    ],
                    "name": "Acme Biz LLC"
                }
            }
        },
        # Step 4: Calculate AML risk score for business
        {
            "name": "calculate_aml_risk_score",
            "tool_inputs": {
                "profile_data": {
                    "nationality": "US",
                    "occupation": "consulting",
                    "business_type": "consulting",
                    "transaction_volume": 50000,
                    "geography": "US"
                }
            }
        },
        # Step 5: Create business account in core banking
        {
            "name": "create_core_banking_customer",
            "tool_inputs": {
                "customer_data": {
                    "name": "Acme Biz LLC",
                    "dob": "2005-01-01",
                    "address": "789 Corporate Blvd, Springfield, USA",
                    "kyc_status": "verified",
                    "risk_level": "low",
                    "documents": [
                        "business_license.pdf",
                        "ein_letter.pdf",
                        "proof_of_address.pdf",
                        "john_smith_passport.jpg",
                        "sarah_lee_passport.jpg"
                    ]
                },
                "account_type": "business_checking",
                "authorized_signers": [
                    "John Smith",
                    "Sarah Lee"
                ]
            }
        },
        # Step 6: Create CRM business profile
        {
            "name": "create_crm_profile",
            "tool_inputs": {
                "customer_id": "CUST-30001",
                "risk_level": "low",
                "kyc_documents": [
                    {
                        "type": "business_license",
                        "status": "valid",
                        "file_id": "business_license.pdf"
                    },
                    {
                        "type": "ein_letter",
                        "status": "valid",
                        "file_id": "ein_letter.pdf"
                    },
                    {
                        "type": "proof_of_address",
                        "status": "valid",
                        "file_id": "proof_of_address.pdf"
                    },
                    {
                        "type": "passport",
                        "status": "valid",
                        "file_id": "john_smith_passport.jpg"
                    },
                    {
                        "type": "passport",
                        "status": "valid",
                        "file_id": "sarah_lee_passport.jpg"
                    }
                ],
                "relationship_data": {
                    "business_owners": [
                        "John Smith",
                        "Sarah Lee"
                    ],
                    "review_frequency": "annual"
                }
            }
        },
        # Step 7: Send welcome communication to business and owners
        {
            "name": "send_welcome_communication",
            "tool_inputs": {
                "customer_id": "CUST-30001",
                "communication_type": "welcome",
                "content": "Welcome to Acme Biz LLC! Your business checking account ACC-30001 is now active.",
                "delivery_method": "email"
            }
        },
        # Step 8: Signal successful onboarding
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Business onboarding completed successfully.",
                "result_data": {
                    "onboarding_status": "success",
                    "customer_id": "CUST-30001",
                    "account_id": "ACC-30001",
                    "crm_id": "CRM-30001",
                    "communication_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Business and owner documents extracted",
            "expected_state": {
                "documents_status": "valid",
                "required_docs_present": True
            }
        },
        {
            "step": 2,
            "description": "Identities of all owners verified",
            "expected_state": {
                "identity_status": "verified",
                "fraud_flag": False
            }
        },
        {
            "step": 3,
            "description": "Business and owners screened for sanctions",
            "expected_state": {
                "match_status": "none"
            }
        },
        {
            "step": 4,
            "description": "AML risk score calculated for business",
            "expected_state": {
                "risk_level": "low",
                "score": 20
            }
        },
        {
            "step": 5,
            "description": "Business account created in core banking",
            "expected_state": {
                "status": "created",
                "customer_id": "CUST-30001",
                "account_id": "ACC-30001"
            }
        },
        {
            "step": 6,
            "description": "CRM business profile created",
            "expected_state": {
                "crm_id": "CRM-30001",
                "status": "created"
            }
        },
        {
            "step": 7,
            "description": "Welcome communication sent to business and owners",
            "expected_state": {
                "communication_status": "sent"
            }
        }
    ]
    description = (
        "Tests business onboarding with multiple beneficial owners, all with valid documents, low AML risk, "
        "and no sanctions matches. This case covers multi-owner KYC extraction, identity verification, "
        "sanctions screening, AML risk scoring, account creation, CRM update, and communication."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "All owners and documents are valid, no edge cases, no escalations, no failures. "
        "Straightforward execution of the W4 workflow for a low-risk business account."
    )

class TestCase4_BankingCustomerOnboardingAgent_W4_Business_Account_Onboarding_Multiple_Documents_medium(BaseBankingCustomerOnboardingAgentTestCase):
    """Business Account: Single Owner, Medium AML Risk

    Validates business onboarding with only one beneficial owner, medium AML risk due to higher transaction volume.
    """

    test_case_id = "BankingCustomerOnboardingAgent_BankOnboard_W4_TC2"
    title = "Business Account: Single Owner, Medium AML Risk"
    workflow = "W4"
    input_data = {
        "application_id": "APP-20002",
        "customer_type": "business",
        "document_files": [
            "business_license.pdf",
            "ein_letter.pdf",
            "maria_gomez_national_id.jpg"
        ],
        "account_type": "business_savings",
        "contact_email": "contact@importmex.com",
        "contact_phone": "+525512345678",
        "beneficial_owners": [
            "Maria Gomez"
        ]
    }
    expected_tool_calls = [
        # Step 1: Extract KYC data from business documents and owner IDs
        {
            "name": "extract_kyc_documents",
            "tool_inputs": {
                "document_files": [
                    "business_license.pdf",
                    "ein_letter.pdf",
                    "maria_gomez_national_id.jpg"
                ]
            }
        },
        # Step 2: Validate identity for all beneficial owners (here, only one)
        {
            "name": "validate_identity",
            "tool_inputs": {
                "extracted_data": {
                    "name": "Maria Gomez",
                    "dob": "1982-03-14",
                    "address": "Av. Insurgentes 123, Mexico City, Mexico",
                    "id_type": "national_id",
                    "id_number": "MXNID-12345678"
                },
                "id_type": "national_id",
                "id_number": "MXNID-12345678"
            }
        },
        # Step 3: Screen business and owners against sanctions lists
        {
            "name": "screen_sanctions_lists",
            "tool_inputs": {
                "customer_data": {
                    "name": "ImportMex S.A.",
                    "business_name": "ImportMex S.A.",
                    "owner_names": ["Maria Gomez"],
                    "dob": None,
                    "nationality": "Mexico"
                }
            }
        },
        # Step 4: Calculate AML risk score based on business type, geography, and volume
        {
            "name": "calculate_aml_risk_score",
            "tool_inputs": {
                "profile_data": {
                    "nationality": "Mexico",
                    "occupation": "import/export",
                    "business_type": "import/export",
                    "transaction_volume": 75000,
                    "geography": "Mexico"
                }
            }
        },
        # Step 5: Create business account in core banking with authorized signers
        {
            "name": "create_core_banking_customer",
            "tool_inputs": {
                "customer_data": {
                    "name": "ImportMex S.A.",
                    "dob": None,
                    "address": "Av. Insurgentes 123, Mexico City, Mexico",
                    "kyc_status": "verified",
                    "risk_level": "medium",
                    "documents": [
                        "business_license.pdf",
                        "ein_letter.pdf",
                        "maria_gomez_national_id.jpg"
                    ]
                },
                "account_type": "business_savings",
                "authorized_signers": ["Maria Gomez"]
            }
        },
        # Step 6: Create CRM business profile with ownership structure
        {
            "name": "create_crm_profile",
            "tool_inputs": {
                "customer_id": "CUST-30002",
                "risk_level": "medium",
                "kyc_documents": [
                    {"type": "business_license", "status": "valid", "file_id": "business_license.pdf"},
                    {"type": "ein_letter", "status": "valid", "file_id": "ein_letter.pdf"},
                    {"type": "national_id", "status": "valid", "file_id": "maria_gomez_national_id.jpg"}
                ],
                "relationship_data": {
                    "business_owners": ["Maria Gomez"],
                    "review_frequency": "annual"
                }
            }
        },
        # Step 7: Send welcome packet to business and owners
        {
            "name": "send_welcome_communication",
            "tool_inputs": {
                "customer_id": "CUST-30002",
                "communication_type": "welcome",
                "content": "Welcome to ImportMex S.A.! Your business savings account is now active.",
                "delivery_method": "email"
            }
        },
        # Step 8: Signal successful onboarding
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Business onboarding completed successfully.",
                "result_data": {
                    "onboarding_status": "success",
                    "customer_id": "CUST-30002",
                    "account_id": "ACC-30002",
                    "crm_id": "CRM-30002",
                    "communication_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Business and owner documents extracted",
            "expected_state": {
                "documents_status": "valid",
                "required_docs_present": True
            }
        },
        {
            "step": 2,
            "description": "Owner identity verified",
            "expected_state": {
                "identity_status": "verified",
                "fraud_flag": False
            }
        },
        {
            "step": 3,
            "description": "Business and owner screened for sanctions",
            "expected_state": {
                "match_status": "none"
            }
        },
        {
            "step": 4,
            "description": "AML risk score calculated for business",
            "expected_state": {
                "risk_level": "medium",
                "score": 60
            }
        },
        {
            "step": 5,
            "description": "Business account created in core banking",
            "expected_state": {
                "status": "created",
                "customer_id": "CUST-30002",
                "account_id": "ACC-30002"
            }
        },
        {
            "step": 6,
            "description": "CRM business profile created",
            "expected_state": {
                "crm_id": "CRM-30002",
                "status": "created"
            }
        },
        {
            "step": 7,
            "description": "Welcome communication sent to business and owner",
            "expected_state": {
                "communication_status": "sent"
            }
        }
    ]
    description = "Validates business onboarding with only one beneficial owner, medium AML risk due to higher transaction volume."
    difficulty = "medium"
    difficulty_reasoning = (
        "Medium: The scenario involves a business account with only one beneficial owner, "
        "requiring multi-document extraction, identity and sanctions screening, and an AML risk score reflecting "
        "medium risk due to geography (Mexico) and transaction volume. The flow is more complex than personal onboarding, "
        "but simpler than multi-owner or high-risk cases."
    )

class TestCase5_BankingCustomerOnboardingAgent_W6_Incomplete_Documentation_Customer_Follow_up_easy(BaseBankingCustomerOnboardingAgentTestCase):
    """
    Personal Account: Missing Proof of Address, Provided After Request

    Tests process where customer initially omits proof of address, receives document request, and provides valid document for successful onboarding.
    """

    test_case_id = "BankingCustomerOnboardingAgent_BankOnboard_W6_TC1"
    title = "Personal Account: Missing Proof of Address, Provided After Request"
    workflow = "W6 - Incomplete Documentation - Customer Follow-up"

    input_data = {
        "application_id": "APP-30001",
        "customer_type": "personal",
        "document_files": [
            "driver_license.pdf"
        ],
        "account_type": "personal_checking",
        "contact_email": "jane.doe@email.com",
        "contact_phone": "+12025550123",
        "additional_documents": [
            "proof_of_address.pdf"
        ]
    }

    expected_tool_calls = [
        # Step 1: Initial extraction (driver_license.pdf)
        {
            "name": "extract_kyc_documents",
            "tool_inputs": {
                "document_files": ["driver_license.pdf"]
            }
        },
        # Step 2: Detect missing required field (address), send document request
        {
            "name": "send_welcome_communication",
            "tool_inputs": {
                "customer_id": None,  # Customer ID not available yet
                "communication_type": "document_request",
                "content": "Dear customer, please provide a valid proof of address to complete your onboarding.",
                "delivery_method": "email"
            }
        },
        # Step 3: Extract newly submitted document (proof_of_address.pdf)
        {
            "name": "extract_kyc_documents",
            "tool_inputs": {
                "document_files": ["proof_of_address.pdf"]
            }
        },
        # Step 4: Validate identity (assume both docs now available)
        {
            "name": "validate_identity",
            "tool_inputs": {
                "extracted_data": {
                    "name": "Jane Doe",
                    "dob": "1990-01-15",
                    "address": "123 Main St, Springfield, USA",
                    "id_type": "driver_license",
                    "id_number": "D1234567"
                },
                "id_type": "driver_license",
                "id_number": "D1234567"
            }
        },
        # Step 5: Screen sanctions lists
        {
            "name": "screen_sanctions_lists",
            "tool_inputs": {
                "customer_data": {
                    "name": "Jane Doe",
                    "dob": "1990-01-15",
                    "nationality": "USA"
                }
            }
        },
        # Step 6: Calculate AML risk score
        {
            "name": "calculate_aml_risk_score",
            "tool_inputs": {
                "profile_data": {
                    "nationality": "USA",
                    "occupation": "Engineer",
                    "transaction_volume": 10000,
                    "geography": "USA"
                }
            }
        },
        # Step 7: Create core banking customer
        {
            "name": "create_core_banking_customer",
            "tool_inputs": {
                "customer_data": {
                    "name": "Jane Doe",
                    "dob": "1990-01-15",
                    "address": "123 Main St, Springfield, USA",
                    "kyc_status": "verified",
                    "risk_level": "low",
                    "documents": ["driver_license.pdf", "proof_of_address.pdf"]
                },
                "account_type": "personal_checking",
                "authorized_signers": []
            }
        },
        # Step 8: Create CRM profile
        {
            "name": "create_crm_profile",
            "tool_inputs": {
                "customer_id": "CUST-40001",
                "risk_level": "low",
                "kyc_documents": [
                    {"type": "driver_license", "status": "valid", "file_id": "driver_license.pdf"},
                    {"type": "proof_of_address", "status": "valid", "file_id": "proof_of_address.pdf"}
                ],
                "relationship_data": {}
            }
        },
        # Step 9: Send welcome communication
        {
            "name": "send_welcome_communication",
            "tool_inputs": {
                "customer_id": "CUST-40001",
                "communication_type": "welcome",
                "content": "Welcome Jane Doe! Your account ACC-40001 has been created.",
                "delivery_method": "email"
            }
        },
        # Step 10: Signal success
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Onboarding completed successfully.",
                "result_data": {
                    "onboarding_status": "success",
                    "customer_id": "CUST-40001",
                    "account_id": "ACC-40001",
                    "crm_id": "CRM-40001",
                    "communication_status": "sent"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Initial document extracted",
            "expected_state": {
                "documents_status": "valid",
                "missing_fields": [
                    "address"
                ]
            }
        },
        {
            "step": 2,
            "description": "Document request sent",
            "expected_state": {
                "communication_status": "sent",
                "communication_type": "document_request"
            }
        },
        {
            "step": 3,
            "description": "Additional document received and extracted",
            "expected_state": {
                "documents_status": "valid",
                "required_docs_present": True
            }
        },
        {
            "step": 4,
            "description": "Identity verified",
            "expected_state": {
                "identity_status": "verified",
                "fraud_flag": False
            }
        },
        {
            "step": 5,
            "description": "Sanctions screening clear",
            "expected_state": {
                "match_status": "none"
            }
        },
        {
            "step": 6,
            "description": "AML risk score calculated",
            "expected_state": {
                "risk_level": "low",
                "score": 30
            }
        },
        {
            "step": 7,
            "description": "Core banking customer created",
            "expected_state": {
                "status": "created",
                "customer_id": "CUST-40001"
            }
        },
        {
            "step": 8,
            "description": "CRM profile created",
            "expected_state": {
                "crm_id": "CRM-40001",
                "status": "created"
            }
        },
        {
            "step": 9,
            "description": "Welcome communication sent",
            "expected_state": {
                "communication_status": "sent"
            }
        }
    ]

    description = (
        "Tests process where customer initially omits proof of address, receives document request, "
        "and provides valid document for successful onboarding."
    )

    difficulty = "easy"
    difficulty_reasoning = (
        "The scenario follows a standard missing-document recovery flow for a personal account. "
        "No fraud, sanctions, or high-risk flags are present. The only deviation from the happy path "
        "is a single missing document that is promptly provided after a request, so the complexity is low."
    )

class TestCase6_BankingCustomerOnboardingAgent_W7_AddressMismatchDataReconciliation_easy(BaseBankingCustomerOnboardingAgentTestCase):
    """
    Address Mismatch: Customer Provides Explanation and Valid New Document

    Covers scenario where address mismatch is detected, customer provides explanation and new document, and onboarding proceeds successfully.
    """

    test_case_id = "BankingCustomerOnboardingAgent_BankOnboard_W7_TC1"
    title = "Address Mismatch: Customer Provides Explanation and Valid New Document"
    workflow = "W7 - Address Mismatch - Data Reconciliation"
    input_data = {
        "application_id": "APP-40001",
        "customer_type": "personal",
        "document_files": [
            "driver_license.pdf",
            "utility_bill.jpg"
        ],
        "account_type": "personal_checking",
        "contact_email": "tom.baker@email.com",
        "contact_phone": "+12025550123",
        "address_explanation": "Moved recently, utility bill and rental agreement reflect new address.",
        "additional_documents": [
            "rental_agreement.pdf"
        ]
    }

    expected_tool_calls = [
        # Step 1: Initial extraction of KYC documents
        {
            "name": "extract_kyc_documents",
            "tool_inputs": {
                "document_files": ["driver_license.pdf", "utility_bill.jpg"]
            }
        },
        # Step 2: Address mismatch detected (handled in agent logic, no tool call)
        # Step 3: Request explanation and additional address evidence
        {
            "name": "send_welcome_communication",
            "tool_inputs": {
                "customer_id": None,  # Not yet assigned, so None or placeholder
                "communication_type": "document_request",
                "content": "We detected an address mismatch in your documents. Please provide an explanation and a supporting document (e.g., rental agreement) reflecting your current address.",
                "delivery_method": "email"
            }
        },
        # Step 4: Extract KYC data from new supporting document
        {
            "name": "extract_kyc_documents",
            "tool_inputs": {
                "document_files": ["rental_agreement.pdf"]
            }
        },
        # Step 5: Validate identity and address
        {
            "name": "validate_identity",
            "tool_inputs": {
                "extracted_data": {
                    "name": "Tom Baker",
                    "dob": "1987-05-12",
                    "address": "123 Main St, Newtown, CA",
                    "id_type": "driver_license",
                    "id_number": "DL-9876543"
                },
                "id_type": "driver_license",
                "id_number": "DL-9876543"
            }
        },
        # Step 6: Screen sanctions lists
        {
            "name": "screen_sanctions_lists",
            "tool_inputs": {
                "customer_data": {
                    "name": "Tom Baker",
                    "dob": "1987-05-12",
                    "nationality": "US"
                }
            }
        },
        # Step 6: Calculate AML risk
        {
            "name": "calculate_aml_risk_score",
            "tool_inputs": {
                "profile_data": {
                    "nationality": "US",
                    "occupation": "Software Engineer",
                    "transaction_volume": 15000,
                    "geography": "US"
                }
            }
        },
        # Step 7: Create customer in core banking
        {
            "name": "create_core_banking_customer",
            "tool_inputs": {
                "customer_data": {
                    "name": "Tom Baker",
                    "dob": "1987-05-12",
                    "address": "123 Main St, Newtown, CA",
                    "kyc_status": "verified",
                    "risk_level": "low",
                    "documents": [
                        "driver_license.pdf",
                        "utility_bill.jpg",
                        "rental_agreement.pdf"
                    ]
                },
                "account_type": "personal_checking"
            }
        },
        # Step 7: Create CRM profile
        {
            "name": "create_crm_profile",
            "tool_inputs": {
                "customer_id": "CUST-50001",
                "risk_level": "low",
                "kyc_documents": [
                    {"type": "driver_license", "status": "valid", "file_id": "driver_license.pdf"},
                    {"type": "utility_bill", "status": "valid", "file_id": "utility_bill.jpg"},
                    {"type": "rental_agreement", "status": "valid", "file_id": "rental_agreement.pdf"}
                ]
            }
        },
        # Step 8: Send welcome communication
        {
            "name": "send_welcome_communication",
            "tool_inputs": {
                "customer_id": "CUST-50001",
                "communication_type": "welcome",
                "content": "Welcome Tom Baker! Your account ACC-50001 has been opened.",
                "delivery_method": "email"
            }
        },
        # Step 9: Signal success
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Onboarding completed successfully.",
                "result_data": {
                    "onboarding_status": "success",
                    "customer_id": "CUST-50001",
                    "account_id": "ACC-50001",
                    "crm_id": "CRM-50001",
                    "communication_status": "sent"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Initial documents extracted, address mismatch detected",
            "expected_state": {
                "documents_status": "valid",
                "address_mismatch": True
            }
        },
        {
            "step": 2,
            "description": "Explanation and supporting document requested",
            "expected_state": {
                "communication_status": "sent",
                "communication_type": "document_request"
            }
        },
        {
            "step": 3,
            "description": "Supporting document extracted and address reconciled",
            "expected_state": {
                "documents_status": "valid",
                "address_reconciled": True
            }
        },
        {
            "step": 4,
            "description": "Identity and address verified",
            "expected_state": {
                "identity_status": "verified",
                "fraud_flag": False
            }
        },
        {
            "step": 5,
            "description": "Sanctions screening clear, AML risk calculated",
            "expected_state": {
                "match_status": "none",
                "risk_level": "low",
                "score": 35
            }
        },
        {
            "step": 6,
            "description": "Core banking customer created",
            "expected_state": {
                "status": "created",
                "customer_id": "CUST-50001"
            }
        },
        {
            "step": 7,
            "description": "CRM profile created with reconciled address",
            "expected_state": {
                "crm_id": "CRM-50001",
                "status": "created"
            }
        },
        {
            "step": 8,
            "description": "Welcome communication sent",
            "expected_state": {
                "communication_status": "sent"
            }
        }
    ]

    description = (
        "Covers scenario where address mismatch is detected, customer provides explanation and new document, "
        "and onboarding proceeds successfully."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "The workflow follows the standard address reconciliation path with a cooperative customer providing a valid supporting document. "
        "No system, fraud, or compliance complications arise, making this a straightforward, low-risk onboarding scenario."
    )