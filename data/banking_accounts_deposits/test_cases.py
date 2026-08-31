from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict
from system_tools_base import SystemToolsBaseClass

# --- TypedDict Definitions ---

class CustomerData(TypedDict, total=False):
    """Customer data object for identity and AML tools."""
    name: str
    dob: str  # ISO 8601
    ssn: str  # 9 digits
    address: str
    email: str
    phone: str  # E.164 format
    id_type: str  # driver's_license, passport, state_id
    id_number: str
    country_of_residence: str
    business_type: Optional[str]
    student_status: Optional[bool]
    owners: Optional[List[Dict[str, Any]]]  # List of owner objects

class Owner(TypedDict):
    """Owner object for joint or business accounts."""
    name: str
    dob: str
    ssn: str
    id_type: str
    id_number: str

class CustomerProfile(TypedDict, total=False):
    """Profile object for account tier calculation."""
    age: int
    student_status: bool
    business_type: Optional[str]
    relationship_value: Optional[float]

class SpecialConditions(TypedDict, total=False):
    """Special conditions for fee schedule configuration."""
    fee_waivers: bool
    overdraft_protection: bool
    atm_network: str  # free, paid, waived
    transaction_fee_override: Optional[float]

class FundingSource(TypedDict, total=False):
    """Funding source object for linking funding."""
    type: str  # external_bank, wire, check, cash, parent_account
    account_number: Optional[str]
    routing_number: Optional[str]
    bank_name: Optional[str]
    amount: Optional[float]

class Limits(TypedDict, total=False):
    """Limits configuration object."""
    withdrawal_limit: float
    transfer_limit: float
    transaction_limit: float
    owner_access: Dict[str, Any]

class FeeSchedule(TypedDict, total=False):
    """Fee schedule object."""
    monthly_fee: float
    atm_fee: float
    overdraft_fee: float
    transaction_fee: float
    waivers: Dict[str, Any]

class DisclosurePackage(TypedDict, total=False):
    """Disclosure package returned by generate_account_disclosures."""
    documents: List[str]
    delivery_status: str  # delivered, pending, failed
    timestamp: str

class IdentityVerificationResult(TypedDict, total=False):
    """Result of identity verification."""
    status: str  # verified, failed, pending
    match_score: float
    details: Dict[str, Any]

class AMLScreeningResult(TypedDict, total=False):
    """Result of AML screening."""
    status: str  # clear, match, high_risk, medium_risk, low_risk
    details: Dict[str, Any]

class AccountTierResult(TypedDict, total=False):
    """Result of account tier calculation."""
    tier: str  # premium, standard, student, business_basic
    eligibility: bool
    details: Dict[str, Any]

class FundingVerificationResult(TypedDict, total=False):
    """Result of funding source verification."""
    status: str  # verified, pending, failed
    details: Dict[str, Any]
    estimated_completion: str

class AccountOpeningResult(TypedDict, total=False):
    """Result of account opening."""
    account_id: str
    status: str  # opened, restricted, failed
    confirmation: Dict[str, Any]
    timestamp: str

class ErrorDetails(TypedDict, total=False):
    """Error details for failures."""
    error_code: str
    error_message: str
    remediation_steps: List[str]

class EscalationDetails(TypedDict, total=False):
    """Details of escalation to human review."""
    ai_message: str
    human_response: str
    timestamp: str

# --- Base Test Case Class ---

class BaseDigitalAccountOpeningAgentTestCase(SystemToolsBaseClass):
    """
    Base class containing common methods for all Digital Account Opening Agent test cases.
    """

    # Agent context attributes
    role = (
        "You are a digital account opening agent that automates the end-to-end process "
        "of onboarding new deposit account customers. You validate customer identity, "
        "perform AML and sanctions screening, determine account tier and product configuration, "
        "generate required disclosures, verify funding sources, and open accounts in the core "
        "banking system, ensuring full regulatory compliance and operational accuracy.\n"
    )
    goal = (
        "Your goal is to process digital account applications instantly and compliantly, "
        "minimizing manual intervention, reducing onboarding time, and ensuring all regulatory, "
        "risk, and product configuration requirements are met for every new account.\n"
    )
    action_plan = {
        "assumptions": [
            "All customer-provided data is received in structured digital format.",
            "Integration with identity, AML, core banking, and funding verification systems is available and reliable."
        ],
        "tools_and_resources": [
            "validate_customer_identity",
            "perform_aml_screening",
            "calculate_account_tier",
            "configure_account_limits",
            "configure_fee_schedule",
            "generate_account_disclosures",
            "link_funding_source",
            "open_account"
        ],
        "guidelines": [
            "Always perform identity and AML screening before any account configuration or opening.",
            "Escalate high-risk or ambiguous cases to human compliance review before proceeding."
        ],
        "workflow_selection": [
            "If identity verification fails, route to identity remediation and fraud detection workflow.",
            "If AML screening returns high risk or sanctions match, escalate to enhanced due diligence and compliance review.",
            "If application type is 'business' and multiple owners provided, trigger business account workflow with multi-signer setup.",
            "If account type is 'student checking' and applicant age < 25, apply student checking workflow with special fee structure.",
            "If account type is 'joint savings' and multiple owners provided, trigger joint account workflow with survivorship rights.",
            "If funding source verification fails or is pending, hold account in restricted mode until funding is verified.",
            "If initial deposit is cash and amount >= 10000, file CTR and process same-day account opening.",
            "If deposit amount >= 5000 and applicant is individual, apply premium savings account workflow.",
            "If none of the above conditions are met, default to standard account opening workflow."
        ],
        "failure_points": [
            "Identity verification fails or documents are fraudulent: Request additional documents, escalate to fraud team, and decline application if fraud confirmed.",
            "AML screening returns sanctions or high-risk match: Escalate to compliance for enhanced due diligence and manual review.",
            "Funding source cannot be verified: Hold account in restricted mode, notify customer, and retry verification.",
            "Core banking system integration fails: Retry operation, escalate to IT support if persistent."
        ],
        "success_criteria": [
            "Account opened with all compliance checks passed and disclosures delivered.",
            "Customer receives confirmation and account details within 15 minutes of application submission."
        ]
    }

    # --- Domain Tool Methods ---

    def validate_customer_identity(
        self,
        application_id: str,
        customer_data: CustomerData
    ) -> IdentityVerificationResult:
        """
        Verify customer identity using credit bureau, government ID, and enrollment databases.

        Args:
            application_id: Unique application identifier. Format: ACC-XXXX where X is numeric.
            customer_data: Customer data object containing:
                - name (string)
                - dob (ISO 8601)
                - ssn (string, 9 digits)
                - address (string)
                - email (string, valid format)
                - phone (string, E.164 format)
                - id_type (string, enum: driver's_license, passport, state_id)
                - id_number (string)

        Returns:
            IdentityVerificationResult: 
                - status (string: verified|failed|pending)
                - match_score (number, 0-100)
                - details (object)
        """
        valid_id_types = ["driver's_license", "passport", "state_id"]
        id_type = customer_data.get("id_type", "")
        if id_type and id_type not in valid_id_types:
            raise ValueError(f"Invalid id_type: {id_type}. Must be one of {valid_id_types}")

        print(f"--- Running validate_customer_identity ---")
        print(f"application_id: {application_id}")
        print(f"customer_data: {customer_data}")

        # Mock logic: If ssn ends with '9', fail; else verified
        ssn = customer_data.get("ssn", "")
        status = "verified" if ssn and not ssn.endswith("9") else "failed"
        match_score = 95.0 if status == "verified" else 40.0
        return {
            "status": status,
            "match_score": match_score,
            "details": {"id_type": id_type, "checked": True}
        }

    def perform_aml_screening(
        self,
        application_id: str,
        customer_data: CustomerData
    ) -> AMLScreeningResult:
        """
        Screen customer against OFAC, sanctions, and PEP lists for AML compliance.

        Args:
            application_id: Unique application identifier. Format: ACC-XXXX where X is numeric.
            customer_data: Customer data object containing:
                - name (string)
                - dob (ISO 8601)
                - country_of_residence (string, ISO 3166-1 alpha-2)
                - business_type (string, optional)
                - owners (array of objects, optional)

        Returns:
            AMLScreeningResult:
                - status (string: clear|match|high_risk|medium_risk|low_risk)
                - details (object)
        """
        print(f"--- Running perform_aml_screening ---")
        print(f"application_id: {application_id}")
        print(f"customer_data: {customer_data}")

        # Mock logic: If country_of_residence is 'IR', high_risk; else clear
        country = customer_data.get("country_of_residence", "US")
        status = "high_risk" if country == "IR" else "clear"
        return {
            "status": status,
            "details": {"country": country, "screened": True}
        }

    def calculate_account_tier(
        self,
        application_id: str,
        deposit_amount: float,
        customer_profile: CustomerProfile
    ) -> AccountTierResult:
        """
        Determine account product tier based on deposit amount, age, and customer profile.

        Args:
            application_id: Unique application identifier. Format: ACC-XXXX where X is numeric.
            deposit_amount: Initial deposit amount in USD, must be >= 0, max 2 decimal places.
            customer_profile: Profile object:
                - age (integer)
                - student_status (boolean)
                - business_type (string, optional)
                - relationship_value (number, optional)

        Returns:
            AccountTierResult:
                - tier (string: premium|standard|student|business_basic)
                - eligibility (boolean)
                - details (object)
        """
        print(f"--- Running calculate_account_tier ---")
        print(f"application_id: {application_id}")
        print(f"deposit_amount: {deposit_amount}")
        print(f"customer_profile: {customer_profile}")

        age = customer_profile.get("age", 30)
        student_status = customer_profile.get("student_status", False)
        business_type = customer_profile.get("business_type", None)

        if business_type:
            tier = "business_basic"
        elif student_status or age < 25:
            tier = "student"
        elif deposit_amount >= 5000:
            tier = "premium"
        else:
            tier = "standard"

        eligibility = True
        return {
            "tier": tier,
            "eligibility": eligibility,
            "details": {"age": age, "student_status": student_status}
        }

    def configure_account_limits(
        self,
        application_id: str,
        tier: str,
        risk_level: str,
        owners: Optional[List[str]] = None
    ) -> Limits:
        """
        Set account withdrawal, transfer, and transaction limits according to tier and risk.

        Args:
            application_id: Unique application identifier. Format: ACC-XXXX where X is numeric.
            tier: Account tier. Must be one of: premium, standard, student, business_basic
            risk_level: Risk level. Must be one of: low, medium, high
            owners: List of owner IDs (strings), minimum 1, maximum 5 items (optional)

        Returns:
            Limits:
                - withdrawal_limit (number, USD)
                - transfer_limit (number, USD)
                - transaction_limit (number, USD)
                - owner_access (object)
        """
        valid_tiers = ["premium", "standard", "student", "business_basic"]
        valid_risk_levels = ["low", "medium", "high"]
        if tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {valid_tiers}")
        if risk_level not in valid_risk_levels:
            raise ValueError(f"Invalid risk_level: {risk_level}. Must be one of {valid_risk_levels}")

        print(f"--- Running configure_account_limits ---")
        print(f"application_id: {application_id}")
        print(f"tier: {tier}, risk_level: {risk_level}, owners: {owners}")

        # Mock limits based on tier and risk
        base_limit = {
            "premium": 10000,
            "standard": 5000,
            "student": 1000,
            "business_basic": 20000
        }[tier]
        risk_factor = {"low": 1.0, "medium": 0.7, "high": 0.4}[risk_level]
        withdrawal_limit = base_limit * risk_factor
        transfer_limit = withdrawal_limit * 2
        transaction_limit = withdrawal_limit / 2

        owner_access = {"owners": owners or [], "multi_sign": bool(owners and len(owners) > 1)}
        return {
            "withdrawal_limit": withdrawal_limit,
            "transfer_limit": transfer_limit,
            "transaction_limit": transaction_limit,
            "owner_access": owner_access
        }

    def configure_fee_schedule(
        self,
        application_id: str,
        tier: str,
        special_conditions: Optional[SpecialConditions] = None
    ) -> FeeSchedule:
        """
        Apply appropriate fee waivers, maintenance fees, and transaction fees based on account tier.

        Args:
            application_id: Unique application identifier. Format: ACC-XXXX where X is numeric.
            tier: Account tier. Must be one of: premium, standard, student, business_basic
            special_conditions: Special conditions object:
                - fee_waivers (boolean)
                - overdraft_protection (boolean)
                - atm_network (string, enum: free, paid, waived)
                - transaction_fee_override (number, optional)

        Returns:
            FeeSchedule:
                - monthly_fee (number, USD)
                - atm_fee (number, USD)
                - overdraft_fee (number, USD)
                - transaction_fee (number, USD)
                - waivers (object)
        """
        valid_tiers = ["premium", "standard", "student", "business_basic"]
        valid_atm_networks = ["free", "paid", "waived"]
        if tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {valid_tiers}")
        if special_conditions:
            atm_network = special_conditions.get("atm_network", "paid")
            if atm_network not in valid_atm_networks:
                raise ValueError(f"Invalid atm_network: {atm_network}. Must be one of {valid_atm_networks}")

        print(f"--- Running configure_fee_schedule ---")
        print(f"application_id: {application_id}")
        print(f"tier: {tier}, special_conditions: {special_conditions}")

        # Mock fee schedule
        fee_map = {
            "premium": {"monthly_fee": 0, "atm_fee": 0, "overdraft_fee": 10, "transaction_fee": 0},
            "standard": {"monthly_fee": 10, "atm_fee": 2, "overdraft_fee": 35, "transaction_fee": 0.5},
            "student": {"monthly_fee": 0, "atm_fee": 0, "overdraft_fee": 0, "transaction_fee": 0},
            "business_basic": {"monthly_fee": 25, "atm_fee": 3, "overdraft_fee": 40, "transaction_fee": 1}
        }
        fees = fee_map[tier]
        waivers = {
            "fee_waivers": special_conditions.get("fee_waivers", False) if special_conditions else False,
            "overdraft_protection": special_conditions.get("overdraft_protection", False) if special_conditions else False
        }
        transaction_fee = special_conditions.get("transaction_fee_override", fees["transaction_fee"]) if special_conditions and "transaction_fee_override" in special_conditions else fees["transaction_fee"]

        return {
            "monthly_fee": fees["monthly_fee"],
            "atm_fee": fees["atm_fee"],
            "overdraft_fee": fees["overdraft_fee"],
            "transaction_fee": transaction_fee,
            "waivers": waivers
        }

    def generate_account_disclosures(
        self,
        application_id: str,
        tier: str,
        fee_schedule: FeeSchedule,
        limits: Limits,
        account_type: str,
        owners: Optional[List[str]] = None
    ) -> DisclosurePackage:
        """
        Generate and deliver required regulatory disclosures and product documentation.

        Args:
            application_id: Unique application identifier. Format: ACC-XXXX where X is numeric.
            tier: Account tier. Must be one of: premium, standard, student, business_basic
            fee_schedule: Fee schedule object as returned by configure_fee_schedule
            limits: Limits object as returned by configure_account_limits
            account_type: Type of account. Must be one of: savings, checking, business_checking, joint_savings, student_checking
            owners: List of owner IDs (strings), minimum 1, maximum 5 items (optional)

        Returns:
            DisclosurePackage:
                - documents (array of strings: document IDs)
                - delivery_status (string: delivered|pending|failed)
                - timestamp (ISO 8601)
        """
        valid_tiers = ["premium", "standard", "student", "business_basic"]
        valid_account_types = ["savings", "checking", "business_checking", "joint_savings", "student_checking"]
        if tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {valid_tiers}")
        if account_type not in valid_account_types:
            raise ValueError(f"Invalid account_type: {account_type}. Must be one of {valid_account_types}")

        print(f"--- Running generate_account_disclosures ---")
        print(f"application_id: {application_id}")
        print(f"tier: {tier}, fee_schedule: {fee_schedule}, limits: {limits}, account_type: {account_type}, owners: {owners}")

        # Mock disclosure package
        docs = ["DOC-123", "DOC-456"]
        if account_type == "student_checking":
            docs.append("DOC-STUDENT")
        if account_type == "business_checking":
            docs.append("DOC-BUSINESS")
        return {
            "documents": docs,
            "delivery_status": "delivered",
            "timestamp": "2024-06-01T14:22:00Z"
        }

    def link_funding_source(
        self,
        application_id: str,
        funding_source: FundingSource,
        verification_method: str
    ) -> FundingVerificationResult:
        """
        Verify and link external funding sources for initial deposit.

        Args:
            application_id: Unique application identifier. Format: ACC-XXXX where X is numeric.
            funding_source: Funding source object:
                - type (string, enum: external_bank, wire, check, cash, parent_account)
                - account_number (string)
                - routing_number (string, optional)
                - bank_name (string, optional)
            verification_method: Method of verification. Must be one of: instant, micro_deposit, manual, in_person

        Returns:
            FundingVerificationResult:
                - status (string: verified|pending|failed)
                - details (object)
                - estimated_completion (ISO 8601)
        """
        valid_types = ["external_bank", "wire", "check", "cash", "parent_account"]
        valid_methods = ["instant", "micro_deposit", "manual", "in_person"]
        fs_type = funding_source.get("type", "")
        if fs_type not in valid_types:
            raise ValueError(f"Invalid funding_source.type: {fs_type}. Must be one of {valid_types}")
        if verification_method not in valid_methods:
            raise ValueError(f"Invalid verification_method: {verification_method}. Must be one of {valid_methods}")

        print(f"--- Running link_funding_source ---")
        print(f"application_id: {application_id}")
        print(f"funding_source: {funding_source}, verification_method: {verification_method}")

        # Mock logic: cash is always verified, micro_deposit is pending, others verified
        if fs_type == "cash":
            status = "verified"
            estimated_completion = "2024-06-01T14:30:00Z"
        elif verification_method == "micro_deposit":
            status = "pending"
            estimated_completion = "2024-06-03T10:00:00Z"
        else:
            status = "verified"
            estimated_completion = "2024-06-01T14:25:00Z"
        return {
            "status": status,
            "details": {"funding_type": fs_type, "method": verification_method},
            "estimated_completion": estimated_completion
        }

    def open_account(
        self,
        application_id: str,
        customer_data: CustomerData,
        tier: str,
        limits: Limits,
        fee_schedule: FeeSchedule,
        disclosures: DisclosurePackage,
        funding_status: str,
        owners: Optional[List[str]] = None
    ) -> AccountOpeningResult:
        """
        Create new account in core banking system with all configurations and documentation.

        Args:
            application_id: Unique application identifier. Format: ACC-XXXX where X is numeric.
            customer_data: Customer data object as used in validate_customer_identity
            tier: Account tier. Must be one of: premium, standard, student, business_basic
            limits: Limits object as returned by configure_account_limits
            fee_schedule: Fee schedule object as returned by configure_fee_schedule
            disclosures: Disclosure package as returned by generate_account_disclosures
            funding_status: Funding verification status. Must be one of: verified, pending, failed
            owners: List of owner IDs (strings), minimum 1, maximum 5 items (optional)

        Returns:
            AccountOpeningResult:
                - account_id (string, format: XXXX-XXXX-XXXX)
                - status (string: opened|restricted|failed)
                - confirmation (object)
                - timestamp (ISO 8601)
        """
        valid_tiers = ["premium", "standard", "student", "business_basic"]
        valid_funding_status = ["verified", "pending", "failed"]
        if tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {valid_tiers}")
        if funding_status not in valid_funding_status:
            raise ValueError(f"Invalid funding_status: {funding_status}. Must be one of {valid_funding_status}")

        print(f"--- Running open_account ---")
        print(f"application_id: {application_id}")
        print(f"tier: {tier}, limits: {limits}, fee_schedule: {fee_schedule}, disclosures: {disclosures}, funding_status: {funding_status}, owners: {owners}")

        # Mock logic: If funding_status is verified, opened; if pending, restricted; else failed
        if funding_status == "verified":
            status = "opened"
        elif funding_status == "pending":
            status = "restricted"
        else:
            status = "failed"
        account_id = "4455-6677-8899"
        confirmation = {
            "timestamp": "2024-06-01T14:22:00Z",
            "disclosures": disclosures.get("documents", []),
            "funding_status": funding_status,
            "fee_schedule": fee_schedule,
            "limits": limits
        }
        return {
            "account_id": account_id,
            "status": status,
            "confirmation": confirmation,
            "timestamp": "2024-06-01T14:22:00Z"
        }

    # --- System Tool Methods (inherited from SystemToolsBaseClass) ---
    # SUCCESS, FAILED, CANCELLED, HUMAN_IN_THE_LOOP are provided by SystemToolsBaseClass

class TestCase1_DigitalAccountOpeningAgent_W1_easy(BaseDigitalAccountOpeningAgentTestCase):
    """
    Premium Savings Account - Individual, Large Deposit, Instant Funding

    Covers premium tier path for individual with deposit >= $5000 and instant funding verification.
    """

    test_case_id = "DigitalAccountOpening_DigitalAccountOpening_W1_TC1"
    title = "Premium Savings Account - Individual, Large Deposit, Instant Funding"
    workflow = "W1"

    input_data = {
        "application_id": "ACC-1001",
        "customer_data": {
            "name": "Alice Johnson",
            "dob": "1980-05-15",
            "ssn": "123456789",
            "address": "456 Elm St, Springfield, IL",
            "email": "alice.johnson@email.com",
            "phone": "+15551234567",
            "id_type": "driver's_license",
            "id_number": "D9876543",
            "country_of_residence": "US"
        },
        "account_type": "savings",
        "deposit_amount": 10000,
        "funding_source": {
            "type": "external_bank",
            "account_number": "987654321",
            "routing_number": "021000021",
            "bank_name": "Wells Fargo"
        }
    }

    expected_tool_calls = [
        {
            "name": "validate_customer_identity",
            "tool_inputs": {
                "application_id": "ACC-1001",
                "customer_data": {
                    "name": "Alice Johnson",
                    "dob": "1980-05-15",
                    "ssn": "123456789",
                    "address": "456 Elm St, Springfield, IL",
                    "email": "alice.johnson@email.com",
                    "phone": "+15551234567",
                    "id_type": "driver's_license",
                    "id_number": "D9876543",
                    "country_of_residence": "US"
                }
            }
        },
        {
            "name": "perform_aml_screening",
            "tool_inputs": {
                "application_id": "ACC-1001",
                "customer_data": {
                    "name": "Alice Johnson",
                    "dob": "1980-05-15",
                    "ssn": "123456789",
                    "address": "456 Elm St, Springfield, IL",
                    "email": "alice.johnson@email.com",
                    "phone": "+15551234567",
                    "id_type": "driver's_license",
                    "id_number": "D9876543",
                    "country_of_residence": "US"
                }
            }
        },
        {
            "name": "calculate_account_tier",
            "tool_inputs": {
                "application_id": "ACC-1001",
                "deposit_amount": 10000,
                "customer_profile": {
                    "age": 44,
                    "student_status": False
                }
            }
        },
        {
            "name": "configure_account_limits",
            "tool_inputs": {
                "application_id": "ACC-1001",
                "tier": "premium",
                "risk_level": "low"
            }
        },
        {
            "name": "configure_fee_schedule",
            "tool_inputs": {
                "application_id": "ACC-1001",
                "tier": "premium",
                "special_conditions": {
                    "fee_waivers": True,
                    "overdraft_protection": True,
                    "atm_network": "free"
                }
            }
        },
        {
            "name": "generate_account_disclosures",
            "tool_inputs": {
                "application_id": "ACC-1001",
                "tier": "premium",
                "fee_schedule": {
                    "monthly_fee": 0,
                    "atm_fee": 0,
                    "overdraft_fee": 0,
                    "transaction_fee": 0,
                    "waivers": {
                        "premium": True
                    }
                },
                "limits": {
                    "withdrawal_limit": 25000,
                    "transfer_limit": 50000,
                    "transaction_limit": 10000
                },
                "account_type": "savings"
            }
        },
        {
            "name": "link_funding_source",
            "tool_inputs": {
                "application_id": "ACC-1001",
                "funding_source": {
                    "type": "external_bank",
                    "account_number": "987654321",
                    "routing_number": "021000021",
                    "bank_name": "Wells Fargo"
                },
                "verification_method": "instant"
            }
        },
        {
            "name": "open_account",
            "tool_inputs": {
                "application_id": "ACC-1001",
                "customer_data": {
                    "name": "Alice Johnson",
                    "dob": "1980-05-15",
                    "ssn": "123456789",
                    "address": "456 Elm St, Springfield, IL",
                    "email": "alice.johnson@email.com",
                    "phone": "+15551234567",
                    "id_type": "driver's_license",
                    "id_number": "D9876543",
                    "country_of_residence": "US"
                },
                "tier": "premium",
                "limits": {
                    "withdrawal_limit": 25000,
                    "transfer_limit": 50000,
                    "transaction_limit": 10000
                },
                "fee_schedule": {
                    "monthly_fee": 0,
                    "atm_fee": 0,
                    "overdraft_fee": 0,
                    "transaction_fee": 0,
                    "waivers": {
                        "premium": True
                    }
                },
                "disclosures": {
                    "documents": ["DOC-123", "DOC-456"],
                    "delivery_status": "delivered",
                    "timestamp": "2024-06-01T14:22:00Z"
                },
                "funding_status": "verified"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Account opened successfully. Confirmation sent to customer.",
                "result_data": {
                    "account_id": "4455-6677-8899",
                    "status": "opened",
                    "confirmation": {
                        "timestamp": "2024-06-01T14:22:00Z",
                        "disclosures": [
                            "DOC-123",
                            "DOC-456"
                        ],
                        "funding_status": "verified",
                        "fee_schedule": {
                            "monthly_fee": 0,
                            "atm_fee": 0,
                            "overdraft_fee": 0,
                            "transaction_fee": 0,
                            "waivers": {
                                "premium": True
                            }
                        },
                        "limits": {
                            "withdrawal_limit": 25000,
                            "transfer_limit": 50000,
                            "transaction_limit": 10000
                        }
                    }
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Customer identity validated",
            "expected_state": {
                "identity_status": "verified",
                "match_score": 95
            }
        },
        {
            "step": 2,
            "description": "AML screening clear",
            "expected_state": {
                "aml_status": "clear"
            }
        },
        {
            "step": 3,
            "description": "Account tier calculated as premium",
            "expected_state": {
                "tier": "premium",
                "eligibility": True
            }
        },
        {
            "step": 4,
            "description": "Premium account limits configured",
            "expected_state": {
                "limits": {
                    "withdrawal_limit": 25000,
                    "transfer_limit": 50000,
                    "transaction_limit": 10000
                }
            }
        },
        {
            "step": 5,
            "description": "Fee schedule with premium waivers applied",
            "expected_state": {
                "fee_schedule": {
                    "monthly_fee": 0,
                    "waivers": {
                        "premium": True
                    }
                }
            }
        },
        {
            "step": 6,
            "description": "Disclosures generated and delivered",
            "expected_state": {
                "disclosures_status": "delivered"
            }
        },
        {
            "step": 7,
            "description": "Funding source linked and verified instantly",
            "expected_state": {
                "funding_status": "verified"
            }
        },
        {
            "step": 8,
            "description": "Account opened and confirmation sent",
            "expected_state": {
                "status": "opened",
                "confirmation_sent": True
            }
        }
    ]

    description = (
        "Covers premium tier path for individual with deposit >= $5000 and instant funding verification. "
        "Premium tier triggers higher limits and fee waivers; instant funding verification allows immediate account opening."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This is a straightforward, happy-path scenario for an individual applicant with a large deposit and instant funding verification. "
        "No escalations, failures, or special handling are required."
    )

class TestCase2_DigitalAccountOpeningAgent_W1_easy(BaseDigitalAccountOpeningAgentTestCase):
    """Standard Checking Account - Individual, Small Deposit, Micro-Deposit Funding

    Covers standard tier path for individual with deposit < $5000 and micro-deposit funding verification.
    """

    test_case_id = "DigitalAccountOpeningAgent_W1_TC2"
    title = "Standard Checking Account - Individual, Small Deposit, Micro-Deposit Funding"
    workflow = "W1"

    input_data = {
        "application_id": "ACC-1002",
        "customer_data": {
            "name": "Brian Lee",
            "dob": "1992-11-30",
            "ssn": "987654321",
            "address": "789 Oak Ave, Dallas, TX",
            "email": "brian.lee@email.com",
            "phone": "+15559876543",
            "id_type": "state_id",
            "id_number": "TX1234567",
            "country_of_residence": "US"
        },
        "account_type": "checking",
        "deposit_amount": 1500,
        "funding_source": {
            "type": "external_bank",
            "account_number": "123456789",
            "routing_number": "111000025",
            "bank_name": "Chase"
        }
    }

    expected_tool_calls = [
        # Step 1: Customer identity validated
        {
            "name": "validate_customer_identity",
            "tool_inputs": {
                "application_id": "ACC-1002",
                "customer_data": {
                    "name": "Brian Lee",
                    "dob": "1992-11-30",
                    "ssn": "987654321",
                    "address": "789 Oak Ave, Dallas, TX",
                    "email": "brian.lee@email.com",
                    "phone": "+15559876543",
                    "id_type": "state_id",
                    "id_number": "TX1234567",
                    "country_of_residence": "US"
                }
            }
        },
        # Step 2: AML screening clear
        {
            "name": "perform_aml_screening",
            "tool_inputs": {
                "application_id": "ACC-1002",
                "customer_data": {
                    "name": "Brian Lee",
                    "dob": "1992-11-30",
                    "ssn": "987654321",
                    "address": "789 Oak Ave, Dallas, TX",
                    "email": "brian.lee@email.com",
                    "phone": "+15559876543",
                    "id_type": "state_id",
                    "id_number": "TX1234567",
                    "country_of_residence": "US"
                }
            }
        },
        # Step 3: Account tier calculated as standard
        {
            "name": "calculate_account_tier",
            "tool_inputs": {
                "application_id": "ACC-1002",
                "deposit_amount": 1500,
                "customer_profile": {
                    "age": 31,  # 2024 - 1992
                    "student_status": False
                }
            }
        },
        # Step 4: Standard account limits configured
        {
            "name": "configure_account_limits",
            "tool_inputs": {
                "application_id": "ACC-1002",
                "tier": "standard",
                "risk_level": "low"
            }
        },
        # Step 5: Fee schedule with standard fees applied
        {
            "name": "configure_fee_schedule",
            "tool_inputs": {
                "application_id": "ACC-1002",
                "tier": "standard"
            }
        },
        # Step 6: Disclosures generated and delivered
        {
            "name": "generate_account_disclosures",
            "tool_inputs": {
                "application_id": "ACC-1002",
                "tier": "standard",
                "fee_schedule": {
                    "monthly_fee": 5,
                    "atm_fee": 2,
                    "overdraft_fee": 35,
                    "transaction_fee": 0.5,
                    "waivers": {
                        "standard": False
                    }
                },
                "limits": {
                    "withdrawal_limit": 5000,
                    "transfer_limit": 10000,
                    "transaction_limit": 2000
                },
                "account_type": "checking"
            }
        },
        # Step 7: Funding source linked and verified via micro-deposit
        {
            "name": "link_funding_source",
            "tool_inputs": {
                "application_id": "ACC-1002",
                "funding_source": {
                    "type": "external_bank",
                    "account_number": "123456789",
                    "routing_number": "111000025",
                    "bank_name": "Chase"
                },
                "verification_method": "micro_deposit"
            }
        },
        # Step 8: Account opened and confirmation sent
        {
            "name": "open_account",
            "tool_inputs": {
                "application_id": "ACC-1002",
                "customer_data": {
                    "name": "Brian Lee",
                    "dob": "1992-11-30",
                    "ssn": "987654321",
                    "address": "789 Oak Ave, Dallas, TX",
                    "email": "brian.lee@email.com",
                    "phone": "+15559876543",
                    "id_type": "state_id",
                    "id_number": "TX1234567",
                    "country_of_residence": "US"
                },
                "tier": "standard",
                "limits": {
                    "withdrawal_limit": 5000,
                    "transfer_limit": 10000,
                    "transaction_limit": 2000
                },
                "fee_schedule": {
                    "monthly_fee": 5,
                    "atm_fee": 2,
                    "overdraft_fee": 35,
                    "transaction_fee": 0.5,
                    "waivers": {
                        "standard": False
                    }
                },
                "disclosures": {
                    "documents": ["DOC-789", "DOC-101"],
                    "delivery_status": "delivered",
                    "timestamp": "2024-06-01T15:00:00Z"
                },
                "funding_status": "verified"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Account opened successfully. Confirmation sent to customer.",
                "result_data": {
                    "account_id": "1122-3344-5566",
                    "status": "opened",
                    "confirmation": {
                        "timestamp": "2024-06-01T15:00:00Z",
                        "disclosures": [
                            "DOC-789",
                            "DOC-101"
                        ],
                        "funding_status": "verified",
                        "fee_schedule": {
                            "monthly_fee": 5,
                            "atm_fee": 2,
                            "overdraft_fee": 35,
                            "transaction_fee": 0.5,
                            "waivers": {
                                "standard": False
                            }
                        },
                        "limits": {
                            "withdrawal_limit": 5000,
                            "transfer_limit": 10000,
                            "transaction_limit": 2000
                        }
                    }
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Customer identity validated",
            "expected_state": {
                "identity_status": "verified",
                "match_score": 90
            }
        },
        {
            "step": 2,
            "description": "AML screening clear",
            "expected_state": {
                "aml_status": "clear"
            }
        },
        {
            "step": 3,
            "description": "Account tier calculated as standard",
            "expected_state": {
                "tier": "standard",
                "eligibility": True
            }
        },
        {
            "step": 4,
            "description": "Standard account limits configured",
            "expected_state": {
                "limits": {
                    "withdrawal_limit": 5000,
                    "transfer_limit": 10000,
                    "transaction_limit": 2000
                }
            }
        },
        {
            "step": 5,
            "description": "Fee schedule with standard fees applied",
            "expected_state": {
                "fee_schedule": {
                    "monthly_fee": 5,
                    "waivers": {
                        "standard": False
                    }
                }
            }
        },
        {
            "step": 6,
            "description": "Disclosures generated and delivered",
            "expected_state": {
                "disclosures_status": "delivered"
            }
        },
        {
            "step": 7,
            "description": "Funding source linked and verified via micro-deposit",
            "expected_state": {
                "funding_status": "verified"
            }
        },
        {
            "step": 8,
            "description": "Account opened and confirmation sent",
            "expected_state": {
                "status": "opened",
                "confirmation_sent": True
            }
        }
    ]

    description = (
        "Covers standard tier path for individual with deposit < $5000 and micro-deposit funding verification. "
        "Standard tier triggers lower limits and standard fees; micro-deposit funding requires verification but is completed successfully."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the standard, low-risk path for an individual applicant with a small deposit and successful micro-deposit funding verification. "
        "No escalations, failures, or special conditions are present."
    )

class TestCase3_DigitalAccountOpeningAgent_W2_easy(BaseDigitalAccountOpeningAgentTestCase):
    """Student Checking - Verified Student, Parent Account Funding

    Covers student checking workflow for applicant <25, verified student status, parent account funding.
    """

    test_case_id = "DigitalAccountOpeningAgent_W2_TC1"
    title = "Student Checking - Verified Student, Parent Account Funding"
    workflow = "W2"
    input_data = {
        "application_id": "ACC-2001",
        "customer_data": {
            "name": "Jane Smith",
            "dob": "2003-09-22",
            "ssn": "234567890",
            "address": "321 College Rd, Boston, MA",
            "email": "jane.smith@university.edu",
            "phone": "+15552345678",
            "id_type": "passport",
            "id_number": "P1234567",
            "country_of_residence": "US",
            "student_status": True
        },
        "account_type": "student_checking",
        "deposit_amount": 500,
        "funding_source": {
            "type": "parent_account",
            "account_number": "555555555",
            "bank_name": "Bank of America"
        }
    }
    expected_tool_calls = [
        # Step 1: Validate customer identity and student status
        {
            "name": "validate_customer_identity",
            "tool_inputs": {
                "application_id": "ACC-2001",
                "customer_data": {
                    "name": "Jane Smith",
                    "dob": "2003-09-22",
                    "ssn": "234567890",
                    "address": "321 College Rd, Boston, MA",
                    "email": "jane.smith@university.edu",
                    "phone": "+15552345678",
                    "id_type": "passport",
                    "id_number": "P1234567",
                    "country_of_residence": "US",
                    "student_status": True
                }
            }
        },
        # Step 2: Perform AML screening
        {
            "name": "perform_aml_screening",
            "tool_inputs": {
                "application_id": "ACC-2001",
                "customer_data": {
                    "name": "Jane Smith",
                    "dob": "2003-09-22",
                    "ssn": "234567890",
                    "address": "321 College Rd, Boston, MA",
                    "email": "jane.smith@university.edu",
                    "phone": "+15552345678",
                    "id_type": "passport",
                    "id_number": "P1234567",
                    "country_of_residence": "US",
                    "student_status": True
                }
            }
        },
        # Step 3: Calculate account tier as student
        {
            "name": "calculate_account_tier",
            "tool_inputs": {
                "application_id": "ACC-2001",
                "deposit_amount": 500,
                "customer_profile": {
                    "age": 20,
                    "student_status": True
                }
            }
        },
        # Step 4: Configure account limits for student tier
        {
            "name": "configure_account_limits",
            "tool_inputs": {
                "application_id": "ACC-2001",
                "tier": "student",
                "risk_level": "low"
            }
        },
        # Step 5: Configure fee schedule with student waivers
        {
            "name": "configure_fee_schedule",
            "tool_inputs": {
                "application_id": "ACC-2001",
                "tier": "student",
                "special_conditions": {
                    "fee_waivers": True
                }
            }
        },
        # Step 6: Generate student checking disclosures
        {
            "name": "generate_account_disclosures",
            "tool_inputs": {
                "application_id": "ACC-2001",
                "tier": "student",
                "fee_schedule": {
                    "monthly_fee": 0,
                    "atm_fee": 0,
                    "overdraft_fee": 0,
                    "transaction_fee": 0,
                    "waivers": {
                        "student": True
                    }
                },
                "limits": {
                    "withdrawal_limit": 1000,
                    "transfer_limit": 2000,
                    "transaction_limit": 500
                },
                "account_type": "student_checking"
            }
        },
        # Step 7: Link funding source (parent account)
        {
            "name": "link_funding_source",
            "tool_inputs": {
                "application_id": "ACC-2001",
                "funding_source": {
                    "type": "parent_account",
                    "account_number": "555555555",
                    "bank_name": "Bank of America"
                },
                "verification_method": "instant"
            }
        },
        # Step 8: Open account and send confirmation
        {
            "name": "open_account",
            "tool_inputs": {
                "application_id": "ACC-2001",
                "customer_data": {
                    "name": "Jane Smith",
                    "dob": "2003-09-22",
                    "ssn": "234567890",
                    "address": "321 College Rd, Boston, MA",
                    "email": "jane.smith@university.edu",
                    "phone": "+15552345678",
                    "id_type": "passport",
                    "id_number": "P1234567",
                    "country_of_residence": "US",
                    "student_status": True
                },
                "tier": "student",
                "limits": {
                    "withdrawal_limit": 1000,
                    "transfer_limit": 2000,
                    "transaction_limit": 500
                },
                "fee_schedule": {
                    "monthly_fee": 0,
                    "atm_fee": 0,
                    "overdraft_fee": 0,
                    "transaction_fee": 0,
                    "waivers": {
                        "student": True
                    }
                },
                "disclosures": {
                    "documents": ["DOC-201", "DOC-202"],
                    "delivery_status": "delivered",
                    "timestamp": "2024-06-01T16:00:00Z"
                },
                "funding_status": "verified"
            }
        },
        # Final system tool: SUCCESS
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Account opened successfully with student tier, disclosures delivered, and funding verified.",
                "result_data": {
                    "account_id": "2233-4455-6677",
                    "status": "opened",
                    "confirmation": {
                        "timestamp": "2024-06-01T16:00:00Z",
                        "disclosures": ["DOC-201", "DOC-202"],
                        "funding_status": "verified",
                        "fee_schedule": {
                            "monthly_fee": 0,
                            "atm_fee": 0,
                            "overdraft_fee": 0,
                            "transaction_fee": 0,
                            "waivers": {
                                "student": True
                            }
                        },
                        "limits": {
                            "withdrawal_limit": 1000,
                            "transfer_limit": 2000,
                            "transaction_limit": 500
                        }
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Customer identity and student status validated",
            "expected_state": {
                "identity_status": "verified",
                "student_status": True
            }
        },
        {
            "step": 2,
            "description": "AML screening clear",
            "expected_state": {
                "aml_status": "clear"
            }
        },
        {
            "step": 3,
            "description": "Account tier calculated as student",
            "expected_state": {
                "tier": "student",
                "eligibility": True
            }
        },
        {
            "step": 4,
            "description": "Student account limits configured",
            "expected_state": {
                "limits": {
                    "withdrawal_limit": 1000,
                    "transfer_limit": 2000,
                    "transaction_limit": 500
                }
            }
        },
        {
            "step": 5,
            "description": "Fee schedule with student waivers applied",
            "expected_state": {
                "fee_schedule": {
                    "monthly_fee": 0,
                    "waivers": {
                        "student": True
                    }
                }
            }
        },
        {
            "step": 6,
            "description": "Student disclosures generated and delivered",
            "expected_state": {
                "disclosures_status": "delivered"
            }
        },
        {
            "step": 7,
            "description": "Funding source linked and verified",
            "expected_state": {
                "funding_status": "verified"
            }
        },
        {
            "step": 8,
            "description": "Account opened and confirmation sent",
            "expected_state": {
                "status": "opened",
                "confirmation_sent": True
            }
        }
    ]
    description = "Covers student checking workflow for applicant <25, verified student status, parent account funding."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the standard student checking workflow with all conditions met: "
        "applicant is under 25, student status is verified, and parent account funding is instantly verified. "
        "No escalations, failures, or edge cases are present, making it a straightforward success path."
    )

class TestCase4_DigitalAccountOpeningAgent_W2_easy(BaseDigitalAccountOpeningAgentTestCase):
    """Student Checking - Verified Student, External Bank Funding

    Covers student checking workflow for applicant <25, verified student status, external bank funding.
    """

    test_case_id = "DigitalAccountOpeningAgent_W2_TC2"
    title = "Student Checking - Verified Student, External Bank Funding"
    workflow = "W2"

    input_data = {
        "application_id": "ACC-2002",
        "customer_data": {
            "name": "Tom Nguyen",
            "dob": "2002-03-10",
            "ssn": "345678901",
            "address": "789 Dorm St, Ann Arbor, MI",
            "email": "tom.nguyen@university.edu",
            "phone": "+15553456789",
            "id_type": "state_id",
            "id_number": "MI7654321",
            "country_of_residence": "US",
            "student_status": True
        },
        "account_type": "student_checking",
        "deposit_amount": 300,
        "funding_source": {
            "type": "external_bank",
            "account_number": "222333444",
            "routing_number": "072000326",
            "bank_name": "Chase"
        }
    }

    expected_tool_calls = [
        # Step 1: Validate customer identity and student status
        {
            "name": "validate_customer_identity",
            "tool_inputs": {
                "application_id": "ACC-2002",
                "customer_data": {
                    "name": "Tom Nguyen",
                    "dob": "2002-03-10",
                    "ssn": "345678901",
                    "address": "789 Dorm St, Ann Arbor, MI",
                    "email": "tom.nguyen@university.edu",
                    "phone": "+15553456789",
                    "id_type": "state_id",
                    "id_number": "MI7654321",
                    "country_of_residence": "US",
                    "student_status": True
                }
            }
        },
        # Step 2: Perform AML screening
        {
            "name": "perform_aml_screening",
            "tool_inputs": {
                "application_id": "ACC-2002",
                "customer_data": {
                    "name": "Tom Nguyen",
                    "dob": "2002-03-10",
                    "ssn": "345678901",
                    "address": "789 Dorm St, Ann Arbor, MI",
                    "email": "tom.nguyen@university.edu",
                    "phone": "+15553456789",
                    "id_type": "state_id",
                    "id_number": "MI7654321",
                    "country_of_residence": "US",
                    "student_status": True
                }
            }
        },
        # Step 3: Calculate account tier as student
        {
            "name": "calculate_account_tier",
            "tool_inputs": {
                "application_id": "ACC-2002",
                "deposit_amount": 300,
                "customer_profile": {
                    "age": 22,  # 2024 - 2002
                    "student_status": True
                }
            }
        },
        # Step 4: Configure account limits for student tier
        {
            "name": "configure_account_limits",
            "tool_inputs": {
                "application_id": "ACC-2002",
                "tier": "student",
                "risk_level": "low",
                # No owners for individual student account
            }
        },
        # Step 5: Configure fee schedule with student waivers
        {
            "name": "configure_fee_schedule",
            "tool_inputs": {
                "application_id": "ACC-2002",
                "tier": "student",
                "special_conditions": {
                    "fee_waivers": True
                }
            }
        },
        # Step 6: Generate student checking disclosures
        {
            "name": "generate_account_disclosures",
            "tool_inputs": {
                "application_id": "ACC-2002",
                "tier": "student",
                "fee_schedule": {
                    "monthly_fee": 0,
                    "atm_fee": 0,
                    "overdraft_fee": 0,
                    "transaction_fee": 0,
                    "waivers": {
                        "student": True
                    }
                },
                "limits": {
                    "withdrawal_limit": 1000,
                    "transfer_limit": 2000,
                    "transaction_limit": 500
                },
                "account_type": "student_checking"
            }
        },
        # Step 7: Link funding source (external bank)
        {
            "name": "link_funding_source",
            "tool_inputs": {
                "application_id": "ACC-2002",
                "funding_source": {
                    "type": "external_bank",
                    "account_number": "222333444",
                    "routing_number": "072000326",
                    "bank_name": "Chase"
                },
                "verification_method": "instant"
            }
        },
        # Step 8: Open account and send confirmation
        {
            "name": "open_account",
            "tool_inputs": {
                "application_id": "ACC-2002",
                "customer_data": {
                    "name": "Tom Nguyen",
                    "dob": "2002-03-10",
                    "ssn": "345678901",
                    "address": "789 Dorm St, Ann Arbor, MI",
                    "email": "tom.nguyen@university.edu",
                    "phone": "+15553456789",
                    "id_type": "state_id",
                    "id_number": "MI7654321",
                    "country_of_residence": "US",
                    "student_status": True
                },
                "tier": "student",
                "limits": {
                    "withdrawal_limit": 1000,
                    "transfer_limit": 2000,
                    "transaction_limit": 500
                },
                "fee_schedule": {
                    "monthly_fee": 0,
                    "atm_fee": 0,
                    "overdraft_fee": 0,
                    "transaction_fee": 0,
                    "waivers": {
                        "student": True
                    }
                },
                "disclosures": {
                    "documents": ["DOC-203", "DOC-204"],
                    "delivery_status": "delivered",
                    "timestamp": "2024-06-01T16:30:00Z"
                },
                "funding_status": "verified"
            }
        },
        # Final: SUCCESS system tool
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Account opened successfully. Confirmation sent to customer.",
                "result_data": {
                    "account_id": "3344-5566-7788",
                    "status": "opened",
                    "confirmation": {
                        "timestamp": "2024-06-01T16:30:00Z",
                        "disclosures": [
                            "DOC-203",
                            "DOC-204"
                        ],
                        "funding_status": "verified",
                        "fee_schedule": {
                            "monthly_fee": 0,
                            "atm_fee": 0,
                            "overdraft_fee": 0,
                            "transaction_fee": 0,
                            "waivers": {
                                "student": True
                            }
                        },
                        "limits": {
                            "withdrawal_limit": 1000,
                            "transfer_limit": 2000,
                            "transaction_limit": 500
                        }
                    }
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Customer identity and student status validated",
            "expected_state": {
                "identity_status": "verified",
                "student_status": True
            }
        },
        {
            "step": 2,
            "description": "AML screening clear",
            "expected_state": {
                "aml_status": "clear"
            }
        },
        {
            "step": 3,
            "description": "Account tier calculated as student",
            "expected_state": {
                "tier": "student",
                "eligibility": True
            }
        },
        {
            "step": 4,
            "description": "Student account limits configured",
            "expected_state": {
                "limits": {
                    "withdrawal_limit": 1000,
                    "transfer_limit": 2000,
                    "transaction_limit": 500
                }
            }
        },
        {
            "step": 5,
            "description": "Fee schedule with student waivers applied",
            "expected_state": {
                "fee_schedule": {
                    "monthly_fee": 0,
                    "waivers": {
                        "student": True
                    }
                }
            }
        },
        {
            "step": 6,
            "description": "Student disclosures generated and delivered",
            "expected_state": {
                "disclosures_status": "delivered"
            }
        },
        {
            "step": 7,
            "description": "Funding source linked and verified",
            "expected_state": {
                "funding_status": "verified"
            }
        },
        {
            "step": 8,
            "description": "Account opened and confirmation sent",
            "expected_state": {
                "status": "opened",
                "confirmation_sent": True
            }
        }
    ]

    description = (
        "Covers student checking workflow for applicant <25, verified student status, external bank funding. "
        "Student tier triggers special fee waivers and lower limits; external bank funding verified via instant or micro-deposit."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This is a straightforward happy path for a student checking account: "
        "applicant is under 25, student status is verified, and funding is from an external bank with instant verification. "
        "No escalations, failures, or complex owner structures."
    )

class TestCase5_DigitalAccountOpeningAgent_W3_medium(BaseDigitalAccountOpeningAgentTestCase):
    """
    Business Checking - Multi-Owner, Wire Funding

    Covers business account opening for multiple owners with wire transfer funding.
    """

    test_case_id = "DigitalAccountOpeningAgent_W3_TC1"
    title = "Business Checking - Multi-Owner, Wire Funding"
    workflow = "W3"
    input_data = {
        "application_id": "ACC-3001",
        "customer_data": {
            "name": "Acme LLC",
            "dob": "2000-01-01",
            "ssn": "12-3456789",
            "address": "100 Business Park, Houston, TX",
            "email": "contact@acmellc.com",
            "phone": "+15551230000",
            "id_type": "business_license",
            "id_number": "TX-BIZ-12345",
            "country_of_residence": "US",
            "business_type": "LLC",
            "owners": [
                {
                    "name": "John Smith",
                    "dob": "1975-02-20",
                    "ssn": "111223333",
                    "id_type": "driver's_license",
                    "id_number": "D1112222"
                },
                {
                    "name": "Mary Jones",
                    "dob": "1980-07-15",
                    "ssn": "222334444",
                    "id_type": "passport",
                    "id_number": "P2223333"
                }
            ]
        },
        "account_type": "business_checking",
        "deposit_amount": 20000,
        "funding_source": {
            "type": "wire",
            "account_number": "888999000",
            "bank_name": "Wells Fargo"
        },
        "owners": [
            {
                "name": "John Smith",
                "dob": "1975-02-20",
                "ssn": "111223333",
                "id_type": "driver's_license",
                "id_number": "D1112222"
            },
            {
                "name": "Mary Jones",
                "dob": "1980-07-15",
                "ssn": "222334444",
                "id_type": "passport",
                "id_number": "P2223333"
            }
        ]
    }
    expected_tool_calls = [
        # Step 1: Validate identity for all business owners
        {
            "name": "validate_customer_identity",
            "tool_inputs": {
                "application_id": "ACC-3001",
                "customer_data": {
                    "name": "Acme LLC",
                    "dob": "2000-01-01",
                    "ssn": "12-3456789",
                    "address": "100 Business Park, Houston, TX",
                    "email": "contact@acmellc.com",
                    "phone": "+15551230000",
                    "id_type": "business_license",
                    "id_number": "TX-BIZ-12345",
                    "country_of_residence": "US",
                    "business_type": "LLC",
                    "owners": [
                        {
                            "name": "John Smith",
                            "dob": "1975-02-20",
                            "ssn": "111223333",
                            "id_type": "driver's_license",
                            "id_number": "D1112222"
                        },
                        {
                            "name": "Mary Jones",
                            "dob": "1980-07-15",
                            "ssn": "222334444",
                            "id_type": "passport",
                            "id_number": "P2223333"
                        }
                    ]
                }
            }
        },
        # Step 2: Perform AML screening for business and all owners
        {
            "name": "perform_aml_screening",
            "tool_inputs": {
                "application_id": "ACC-3001",
                "customer_data": {
                    "name": "Acme LLC",
                    "dob": "2000-01-01",
                    "ssn": "12-3456789",
                    "address": "100 Business Park, Houston, TX",
                    "email": "contact@acmellc.com",
                    "phone": "+15551230000",
                    "id_type": "business_license",
                    "id_number": "TX-BIZ-12345",
                    "country_of_residence": "US",
                    "business_type": "LLC",
                    "owners": [
                        {
                            "name": "John Smith",
                            "dob": "1975-02-20",
                            "ssn": "111223333",
                            "id_type": "driver's_license",
                            "id_number": "D1112222"
                        },
                        {
                            "name": "Mary Jones",
                            "dob": "1980-07-15",
                            "ssn": "222334444",
                            "id_type": "passport",
                            "id_number": "P2223333"
                        }
                    ]
                }
            }
        },
        # Step 3: Calculate account tier as business_basic
        {
            "name": "calculate_account_tier",
            "tool_inputs": {
                "application_id": "ACC-3001",
                "deposit_amount": 20000,
                "customer_profile": {
                    "age": 24,  # Derived from dob 2000-01-01 (assuming test year 2024)
                    "business_type": "LLC"
                }
            }
        },
        # Step 4: Configure account limits for business tier and multi-signers
        {
            "name": "configure_account_limits",
            "tool_inputs": {
                "application_id": "ACC-3001",
                "tier": "business_basic",
                "risk_level": "low",
                "owners": ["John Smith", "Mary Jones"]
            }
        },
        # Step 5: Configure fee schedule for business account
        {
            "name": "configure_fee_schedule",
            "tool_inputs": {
                "application_id": "ACC-3001",
                "tier": "business_basic",
                "special_conditions": {
                    "fee_waivers": False,
                    "overdraft_protection": False,
                    "atm_network": "paid"
                }
            }
        },
        # Step 6: Generate business account disclosures
        {
            "name": "generate_account_disclosures",
            "tool_inputs": {
                "application_id": "ACC-3001",
                "tier": "business_basic",
                "fee_schedule": {
                    "monthly_fee": 15,
                    "atm_fee": 3,
                    "overdraft_fee": 40,
                    "transaction_fee": 1,
                    "waivers": {
                        "business": False
                    }
                },
                "limits": {
                    "withdrawal_limit": 50000,
                    "transfer_limit": 100000,
                    "transaction_limit": 20000,
                    "owner_access": {
                        "John Smith": "full",
                        "Mary Jones": "full"
                    }
                },
                "account_type": "business_checking",
                "owners": ["John Smith", "Mary Jones"]
            }
        },
        # Step 7: Link funding source (wire transfer)
        {
            "name": "link_funding_source",
            "tool_inputs": {
                "application_id": "ACC-3001",
                "funding_source": {
                    "type": "wire",
                    "account_number": "888999000",
                    "bank_name": "Wells Fargo"
                },
                "verification_method": "manual"
            }
        },
        # Step 8: Open account with all authorized signers
        {
            "name": "open_account",
            "tool_inputs": {
                "application_id": "ACC-3001",
                "customer_data": {
                    "name": "Acme LLC",
                    "dob": "2000-01-01",
                    "ssn": "12-3456789",
                    "address": "100 Business Park, Houston, TX",
                    "email": "contact@acmellc.com",
                    "phone": "+15551230000",
                    "id_type": "business_license",
                    "id_number": "TX-BIZ-12345",
                    "country_of_residence": "US",
                    "business_type": "LLC",
                    "owners": [
                        {
                            "name": "John Smith",
                            "dob": "1975-02-20",
                            "ssn": "111223333",
                            "id_type": "driver's_license",
                            "id_number": "D1112222"
                        },
                        {
                            "name": "Mary Jones",
                            "dob": "1980-07-15",
                            "ssn": "222334444",
                            "id_type": "passport",
                            "id_number": "P2223333"
                        }
                    ]
                },
                "tier": "business_basic",
                "limits": {
                    "withdrawal_limit": 50000,
                    "transfer_limit": 100000,
                    "transaction_limit": 20000,
                    "owner_access": {
                        "John Smith": "full",
                        "Mary Jones": "full"
                    }
                },
                "fee_schedule": {
                    "monthly_fee": 15,
                    "atm_fee": 3,
                    "overdraft_fee": 40,
                    "transaction_fee": 1,
                    "waivers": {
                        "business": False
                    }
                },
                "disclosures": {
                    "documents": ["DOC-301", "DOC-302"],
                    "delivery_status": "delivered",
                    "timestamp": "2024-06-01T17:00:00Z"
                },
                "funding_status": "verified",
                "owners": ["John Smith", "Mary Jones"]
            }
        },
        # Final: SUCCESS system tool
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Business account opened with all signers and disclosures delivered.",
                "result_data": {
                    "account_id": "5566-7788-9900",
                    "status": "opened",
                    "confirmation": {
                        "timestamp": "2024-06-01T17:00:00Z",
                        "disclosures": ["DOC-301", "DOC-302"],
                        "funding_status": "verified",
                        "fee_schedule": {
                            "monthly_fee": 15,
                            "atm_fee": 3,
                            "overdraft_fee": 40,
                            "transaction_fee": 1,
                            "waivers": {
                                "business": False
                            }
                        },
                        "limits": {
                            "withdrawal_limit": 50000,
                            "transfer_limit": 100000,
                            "transaction_limit": 20000,
                            "owner_access": {
                                "John Smith": "full",
                                "Mary Jones": "full"
                            }
                        }
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "All business owners' identities validated",
            "expected_state": {
                "identity_status": "verified",
                "owners_verified": True
            }
        },
        {
            "step": 2,
            "description": "AML screening clear for business and owners",
            "expected_state": {
                "aml_status": "clear"
            }
        },
        {
            "step": 3,
            "description": "Account tier calculated as business_basic",
            "expected_state": {
                "tier": "business_basic",
                "eligibility": True
            }
        },
        {
            "step": 4,
            "description": "Business account limits configured for multi-signers",
            "expected_state": {
                "limits": {
                    "withdrawal_limit": 50000,
                    "owner_access": {
                        "John Smith": "full",
                        "Mary Jones": "full"
                    }
                }
            }
        },
        {
            "step": 5,
            "description": "Fee schedule for business applied",
            "expected_state": {
                "fee_schedule": {
                    "monthly_fee": 15,
                    "waivers": {
                        "business": False
                    }
                }
            }
        },
        {
            "step": 6,
            "description": "Business disclosures generated and delivered",
            "expected_state": {
                "disclosures_status": "delivered"
            }
        },
        {
            "step": 7,
            "description": "Wire funding source linked and verified",
            "expected_state": {
                "funding_status": "verified"
            }
        },
        {
            "step": 8,
            "description": "Account opened with all authorized signers",
            "expected_state": {
                "status": "opened",
                "confirmation_sent": True
            }
        }
    ]
    description = "Covers business account opening for multiple owners with wire transfer funding."
    difficulty = "medium"
    difficulty_reasoning = (
        "This test case involves handling a business account with multiple owners, "
        "requiring identity and AML checks for all, configuration of business tier, "
        "multi-signer limits, business fee schedule, wire funding verification, and "
        "proper disclosure delivery. The multi-entity and multi-step nature adds moderate complexity."
    )

class TestCase6_DigitalAccountOpeningAgent_W6_easy(BaseDigitalAccountOpeningAgentTestCase):
    """Joint Savings Account - Two Owners, Transfer Funding

    Covers joint account opening for two owners with transfer from existing account.
    """

    test_case_id = "DigitalAccountOpeningAgent_W6_TC1"
    title = "Joint Savings Account - Two Owners, Transfer Funding"
    workflow = "W6"
    input_data = {
        "application_id": "ACC-6001",
        "customer_data": {
            "name": "Joint Account",
            "dob": "1990-01-01",
            "ssn": "000000000",
            "address": "200 Family St, Seattle, WA",
            "email": "joint.account@email.com",
            "phone": "+15552000000",
            "id_type": "joint",
            "id_number": "JA-12345",
            "country_of_residence": "US",
            "owners": [
                {
                    "name": "Emily Clark",
                    "dob": "1985-06-10",
                    "ssn": "333445555",
                    "id_type": "driver's_license",
                    "id_number": "D3334444"
                },
                {
                    "name": "Michael Clark",
                    "dob": "1983-08-22",
                    "ssn": "444556666",
                    "id_type": "passport",
                    "id_number": "P4445555"
                }
            ]
        },
        "account_type": "joint_savings",
        "deposit_amount": 8000,
        "funding_source": {
            "type": "external_bank",
            "account_number": "777888999",
            "routing_number": "125000024",
            "bank_name": "US Bank"
        },
        "owners": [
            {
                "name": "Emily Clark",
                "dob": "1985-06-10",
                "ssn": "333445555",
                "id_type": "driver's_license",
                "id_number": "D3334444"
            },
            {
                "name": "Michael Clark",
                "dob": "1983-08-22",
                "ssn": "444556666",
                "id_type": "passport",
                "id_number": "P4445555"
            }
        ]
    }
    expected_tool_calls = [
        # Step 1: Validate identity for all owners
        {
            "name": "validate_customer_identity",
            "tool_inputs": {
                "application_id": "ACC-6001",
                "customer_data": {
                    "name": "Joint Account",
                    "dob": "1990-01-01",
                    "ssn": "000000000",
                    "address": "200 Family St, Seattle, WA",
                    "email": "joint.account@email.com",
                    "phone": "+15552000000",
                    "id_type": "joint",
                    "id_number": "JA-12345",
                    "country_of_residence": "US",
                    "owners": [
                        {
                            "name": "Emily Clark",
                            "dob": "1985-06-10",
                            "ssn": "333445555",
                            "id_type": "driver's_license",
                            "id_number": "D3334444"
                        },
                        {
                            "name": "Michael Clark",
                            "dob": "1983-08-22",
                            "ssn": "444556666",
                            "id_type": "passport",
                            "id_number": "P4445555"
                        }
                    ]
                }
            }
        },
        # Step 2: Perform AML screening for all owners
        {
            "name": "perform_aml_screening",
            "tool_inputs": {
                "application_id": "ACC-6001",
                "customer_data": {
                    "name": "Joint Account",
                    "dob": "1990-01-01",
                    "ssn": "000000000",
                    "address": "200 Family St, Seattle, WA",
                    "email": "joint.account@email.com",
                    "phone": "+15552000000",
                    "id_type": "joint",
                    "id_number": "JA-12345",
                    "country_of_residence": "US",
                    "owners": [
                        {
                            "name": "Emily Clark",
                            "dob": "1985-06-10",
                            "ssn": "333445555",
                            "id_type": "driver's_license",
                            "id_number": "D3334444"
                        },
                        {
                            "name": "Michael Clark",
                            "dob": "1983-08-22",
                            "ssn": "444556666",
                            "id_type": "passport",
                            "id_number": "P4445555"
                        }
                    ]
                }
            }
        },
        # Step 3: Calculate account tier based on deposit and profile
        {
            "name": "calculate_account_tier",
            "tool_inputs": {
                "application_id": "ACC-6001",
                "deposit_amount": 8000,
                "customer_profile": {
                    "age": 34,  # Approximate from dob 1990-01-01
                    "student_status": False
                }
            }
        },
        # Step 4: Configure account limits for joint ownership
        {
            "name": "configure_account_limits",
            "tool_inputs": {
                "application_id": "ACC-6001",
                "tier": "standard",
                "risk_level": "low",
                "owners": [
                    "D3334444",  # Emily Clark's id_number
                    "P4445555"   # Michael Clark's id_number
                ]
            }
        },
        # Step 5: Configure fee schedule for joint account
        {
            "name": "configure_fee_schedule",
            "tool_inputs": {
                "application_id": "ACC-6001",
                "tier": "standard",
                "special_conditions": {
                    "fee_waivers": True,
                    "overdraft_protection": False,
                    "atm_network": "waived"
                }
            }
        },
        # Step 6: Generate joint account disclosures
        {
            "name": "generate_account_disclosures",
            "tool_inputs": {
                "application_id": "ACC-6001",
                "tier": "standard",
                "fee_schedule": {
                    "monthly_fee": 3,
                    "atm_fee": 1,
                    "overdraft_fee": 30,
                    "transaction_fee": 0.25,
                    "waivers": {
                        "joint": True
                    }
                },
                "limits": {
                    "withdrawal_limit": 15000,
                    "transfer_limit": 30000,
                    "transaction_limit": 5000,
                    "owner_access": {
                        "Emily Clark": "full",
                        "Michael Clark": "full"
                    }
                },
                "account_type": "joint_savings",
                "owners": [
                    "D3334444",
                    "P4445555"
                ]
            }
        },
        # Step 7: Link funding source (transfer from existing account)
        {
            "name": "link_funding_source",
            "tool_inputs": {
                "application_id": "ACC-6001",
                "funding_source": {
                    "type": "external_bank",
                    "account_number": "777888999",
                    "routing_number": "125000024",
                    "bank_name": "US Bank"
                },
                "verification_method": "instant"
            }
        },
        # Step 8: Open joint account with survivorship rights
        {
            "name": "open_account",
            "tool_inputs": {
                "application_id": "ACC-6001",
                "customer_data": {
                    "name": "Joint Account",
                    "dob": "1990-01-01",
                    "ssn": "000000000",
                    "address": "200 Family St, Seattle, WA",
                    "email": "joint.account@email.com",
                    "phone": "+15552000000",
                    "id_type": "joint",
                    "id_number": "JA-12345",
                    "country_of_residence": "US",
                    "owners": [
                        {
                            "name": "Emily Clark",
                            "dob": "1985-06-10",
                            "ssn": "333445555",
                            "id_type": "driver's_license",
                            "id_number": "D3334444"
                        },
                        {
                            "name": "Michael Clark",
                            "dob": "1983-08-22",
                            "ssn": "444556666",
                            "id_type": "passport",
                            "id_number": "P4445555"
                        }
                    ]
                },
                "tier": "standard",
                "limits": {
                    "withdrawal_limit": 15000,
                    "transfer_limit": 30000,
                    "transaction_limit": 5000,
                    "owner_access": {
                        "Emily Clark": "full",
                        "Michael Clark": "full"
                    }
                },
                "fee_schedule": {
                    "monthly_fee": 3,
                    "atm_fee": 1,
                    "overdraft_fee": 30,
                    "transaction_fee": 0.25,
                    "waivers": {
                        "joint": True
                    }
                },
                "disclosures": {
                    "documents": ["DOC-601", "DOC-602"],
                    "delivery_status": "delivered",
                    "timestamp": "2024-06-01T18:00:00Z"
                },
                "funding_status": "verified",
                "owners": [
                    "D3334444",
                    "P4445555"
                ]
            }
        },
        # Final: SUCCESS system tool
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Joint account opened successfully with all owners, disclosures delivered, and funding verified.",
                "result_data": {
                    "account_id": "6677-8899-0011",
                    "status": "opened",
                    "confirmation": {
                        "timestamp": "2024-06-01T18:00:00Z",
                        "disclosures": [
                            "DOC-601",
                            "DOC-602"
                        ],
                        "funding_status": "verified",
                        "fee_schedule": {
                            "monthly_fee": 3,
                            "atm_fee": 1,
                            "overdraft_fee": 30,
                            "transaction_fee": 0.25,
                            "waivers": {
                                "joint": True
                            }
                        },
                        "limits": {
                            "withdrawal_limit": 15000,
                            "transfer_limit": 30000,
                            "transaction_limit": 5000,
                            "owner_access": {
                                "Emily Clark": "full",
                                "Michael Clark": "full"
                            }
                        }
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "All owners' identities validated",
            "expected_state": {
                "identity_status": "verified",
                "owners_verified": True
            }
        },
        {
            "step": 2,
            "description": "AML screening clear for all owners",
            "expected_state": {
                "aml_status": "clear"
            }
        },
        {
            "step": 3,
            "description": "Account tier calculated based on deposit and profile",
            "expected_state": {
                "tier": "standard",
                "eligibility": True
            }
        },
        {
            "step": 4,
            "description": "Joint account limits configured",
            "expected_state": {
                "limits": {
                    "withdrawal_limit": 15000,
                    "owner_access": {
                        "Emily Clark": "full",
                        "Michael Clark": "full"
                    }
                }
            }
        },
        {
            "step": 5,
            "description": "Fee schedule for joint account applied",
            "expected_state": {
                "fee_schedule": {
                    "monthly_fee": 3,
                    "waivers": {
                        "joint": True
                    }
                }
            }
        },
        {
            "step": 6,
            "description": "Joint account disclosures generated and delivered",
            "expected_state": {
                "disclosures_status": "delivered"
            }
        },
        {
            "step": 7,
            "description": "Funding source linked and verified",
            "expected_state": {
                "funding_status": "verified"
            }
        },
        {
            "step": 8,
            "description": "Joint account opened with survivorship rights",
            "expected_state": {
                "status": "opened",
                "confirmation_sent": True
            }
        }
    ]
    description = "Covers joint account opening for two owners with transfer from existing account."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the standard joint account opening workflow (W6) with two owners, "
        "all data provided, and no exceptional or failure conditions. All compliance and funding "
        "checks pass, and the process is linear with no escalations or manual interventions required."
    )

class TestCase7_DigitalAccountOpeningAgent_W7_easy(BaseDigitalAccountOpeningAgentTestCase):
    """Restricted Account - Pending Micro-Deposit Funding Verification

    Covers restricted account opening when funding source verification is pending via micro-deposit.
    """

    test_case_id = "DigitalAccountOpeningAgent_W7_TC1"
    title = "Restricted Account - Pending Micro-Deposit Funding Verification"
    workflow = "W7"
    input_data = {
        "application_id": "ACC-7001",
        "customer_data": {
            "name": "Samuel Green",
            "dob": "1995-12-05",
            "ssn": "555667777",
            "address": "400 Maple St, Denver, CO",
            "email": "samuel.green@email.com",
            "phone": "+15554000000",
            "id_type": "driver's_license",
            "id_number": "D5556666",
            "country_of_residence": "US"
        },
        "account_type": "savings",
        "deposit_amount": 2500,
        "funding_source": {
            "type": "external_bank",
            "account_number": "333444555",
            "routing_number": "102000021",
            "bank_name": "PNC"
        }
    }
    expected_tool_calls = [
        {
            "name": "validate_customer_identity",
            "tool_inputs": {
                "application_id": "ACC-7001",
                "customer_data": {
                    "name": "Samuel Green",
                    "dob": "1995-12-05",
                    "ssn": "555667777",
                    "address": "400 Maple St, Denver, CO",
                    "email": "samuel.green@email.com",
                    "phone": "+15554000000",
                    "id_type": "driver's_license",
                    "id_number": "D5556666",
                    "country_of_residence": "US"
                }
            }
        },
        {
            "name": "perform_aml_screening",
            "tool_inputs": {
                "application_id": "ACC-7001",
                "customer_data": {
                    "name": "Samuel Green",
                    "dob": "1995-12-05",
                    "ssn": "555667777",
                    "address": "400 Maple St, Denver, CO",
                    "email": "samuel.green@email.com",
                    "phone": "+15554000000",
                    "id_type": "driver's_license",
                    "id_number": "D5556666",
                    "country_of_residence": "US"
                }
            }
        },
        {
            "name": "calculate_account_tier",
            "tool_inputs": {
                "application_id": "ACC-7001",
                "deposit_amount": 2500,
                "customer_profile": {
                    "age": 28,
                    "student_status": None,
                    "business_type": None,
                    "relationship_value": None
                }
            }
        },
        {
            "name": "link_funding_source",
            "tool_inputs": {
                "application_id": "ACC-7001",
                "funding_source": {
                    "type": "external_bank",
                    "account_number": "333444555",
                    "routing_number": "102000021",
                    "bank_name": "PNC"
                },
                "verification_method": "micro_deposit"
            }
        },
        {
            "name": "configure_account_limits",
            "tool_inputs": {
                "application_id": "ACC-7001",
                "tier": "standard",
                "risk_level": "low"
            }
        },
        {
            "name": "open_account",
            "tool_inputs": {
                "application_id": "ACC-7001",
                "customer_data": {
                    "name": "Samuel Green",
                    "dob": "1995-12-05",
                    "ssn": "555667777",
                    "address": "400 Maple St, Denver, CO",
                    "email": "samuel.green@email.com",
                    "phone": "+15554000000",
                    "id_type": "driver's_license",
                    "id_number": "D5556666",
                    "country_of_residence": "US"
                },
                "tier": "standard",
                "limits": {
                    "withdrawal_limit": 0,
                    "transfer_limit": 0,
                    "transaction_limit": 0
                },
                "fee_schedule": {
                    "monthly_fee": 5,
                    "atm_fee": 2,
                    "overdraft_fee": 35,
                    "transaction_fee": 0.5,
                    "waivers": {
                        "standard": False
                    }
                },
                "disclosures": {
                    "documents": ["DOC-701", "DOC-702"],
                    "delivery_status": "delivered",
                    "timestamp": "2024-06-01T19:00:00Z"
                },
                "funding_status": "pending"
            }
        },
        {
            "name": "generate_account_disclosures",
            "tool_inputs": {
                "application_id": "ACC-7001",
                "tier": "standard",
                "fee_schedule": {
                    "monthly_fee": 5,
                    "atm_fee": 2,
                    "overdraft_fee": 35,
                    "transaction_fee": 0.5,
                    "waivers": {
                        "standard": False
                    }
                },
                "limits": {
                    "withdrawal_limit": 0,
                    "transfer_limit": 0,
                    "transaction_limit": 0
                },
                "account_type": "savings"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Account opened in restricted mode, disclosures delivered, funding verification pending.",
                "result_data": {
                    "account_id": "7788-9900-1122",
                    "status": "restricted",
                    "confirmation": {
                        "timestamp": "2024-06-01T19:00:00Z",
                        "disclosures": [
                            "DOC-701",
                            "DOC-702"
                        ],
                        "funding_status": "pending",
                        "fee_schedule": {
                            "monthly_fee": 5,
                            "atm_fee": 2,
                            "overdraft_fee": 35,
                            "transaction_fee": 0.5,
                            "waivers": {
                                "standard": False
                            }
                        },
                        "limits": {
                            "withdrawal_limit": 0,
                            "transfer_limit": 0,
                            "transaction_limit": 0
                        }
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Customer identity validated",
            "expected_state": {
                "identity_status": "verified",
                "match_score": 92
            }
        },
        {
            "step": 2,
            "description": "AML screening clear",
            "expected_state": {
                "aml_status": "clear"
            }
        },
        {
            "step": 3,
            "description": "Account tier calculated as standard",
            "expected_state": {
                "tier": "standard",
                "eligibility": True
            }
        },
        {
            "step": 4,
            "description": "Funding source linked, micro-deposit verification initiated",
            "expected_state": {
                "funding_status": "pending"
            }
        },
        {
            "step": 5,
            "description": "Restricted account limits configured",
            "expected_state": {
                "limits": {
                    "withdrawal_limit": 0,
                    "transfer_limit": 0,
                    "transaction_limit": 0
                }
            }
        },
        {
            "step": 6,
            "description": "Account opened in restricted mode",
            "expected_state": {
                "status": "restricted"
            }
        },
        {
            "step": 7,
            "description": "Disclosures including funding verification requirements delivered",
            "expected_state": {
                "disclosures_status": "delivered"
            }
        }
    ]
    description = "Covers restricted account opening when funding source verification is pending via micro-deposit."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows a straightforward restricted account opening path where all compliance checks pass, "
        "but funding source verification is pending. No escalations or failures occur, and all tool calls are standard."
    )

class TestCase8_DigitalAccountOpeningAgent_W8_easy(BaseDigitalAccountOpeningAgentTestCase):
    """Same-Day Account Opening - Cash Deposit >= $10,000

    Covers same-day account opening with large cash deposit and CTR filing.
    """

    test_case_id = "DigitalAccountOpeningAgent_W8_TC1"
    title = "Same-Day Account Opening - Cash Deposit >= $10,000"
    workflow = "W8"
    input_data = {
        "application_id": "ACC-8001",
        "customer_data": {
            "name": "Linda Perez",
            "dob": "1970-03-25",
            "ssn": "666778888",
            "address": "500 Market St, San Francisco, CA",
            "email": "linda.perez@email.com",
            "phone": "+15555000000",
            "id_type": "driver's_license",
            "id_number": "D6667777",
            "country_of_residence": "US"
        },
        "account_type": "checking",
        "deposit_amount": 15000,
        "funding_source": {
            "type": "cash",
            "account_number": "N/A",
            "amount": 15000
        }
    }
    expected_tool_calls = [
        {
            "name": "validate_customer_identity",
            "tool_inputs": {
                "application_id": "ACC-8001",
                "customer_data": {
                    "name": "Linda Perez",
                    "dob": "1970-03-25",
                    "ssn": "666778888",
                    "address": "500 Market St, San Francisco, CA",
                    "email": "linda.perez@email.com",
                    "phone": "+15555000000",
                    "id_type": "driver's_license",
                    "id_number": "D6667777",
                    "country_of_residence": "US"
                }
            }
        },
        {
            "name": "perform_aml_screening",
            "tool_inputs": {
                "application_id": "ACC-8001",
                "customer_data": {
                    "name": "Linda Perez",
                    "dob": "1970-03-25",
                    "ssn": "666778888",
                    "address": "500 Market St, San Francisco, CA",
                    "email": "linda.perez@email.com",
                    "phone": "+15555000000",
                    "id_type": "driver's_license",
                    "id_number": "D6667777",
                    "country_of_residence": "US"
                }
            }
        },
        {
            # Step 3: File CTR for cash deposit >= $10,000 (simulated as HUMAN_IN_THE_LOOP for compliance filing)
            "name": "HUMAN_IN_THE_LOOP",
            "tool_inputs": {
                "ai_message": "File Currency Transaction Report (CTR) for cash deposit of $15,000."
            }
        },
        {
            "name": "calculate_account_tier",
            "tool_inputs": {
                "application_id": "ACC-8001",
                "deposit_amount": 15000,
                "customer_profile": {
                    "age": 54,  # 2024 - 1970
                    "student_status": False
                }
            }
        },
        {
            "name": "configure_account_limits",
            "tool_inputs": {
                "application_id": "ACC-8001",
                "tier": "premium",
                "risk_level": "low"
            }
        },
        {
            "name": "configure_fee_schedule",
            "tool_inputs": {
                "application_id": "ACC-8001",
                "tier": "premium",
                "special_conditions": {
                    "fee_waivers": True,
                    "overdraft_protection": True,
                    "atm_network": "free"
                }
            }
        },
        {
            "name": "generate_account_disclosures",
            "tool_inputs": {
                "application_id": "ACC-8001",
                "tier": "premium",
                "fee_schedule": {
                    "monthly_fee": 0,
                    "atm_fee": 0,
                    "overdraft_fee": 0,
                    "transaction_fee": 0,
                    "waivers": {
                        "premium": True
                    }
                },
                "limits": {
                    "withdrawal_limit": 25000,
                    "transfer_limit": 50000,
                    "transaction_limit": 10000
                },
                "account_type": "checking"
            }
        },
        {
            "name": "open_account",
            "tool_inputs": {
                "application_id": "ACC-8001",
                "customer_data": {
                    "name": "Linda Perez",
                    "dob": "1970-03-25",
                    "ssn": "666778888",
                    "address": "500 Market St, San Francisco, CA",
                    "email": "linda.perez@email.com",
                    "phone": "+15555000000",
                    "id_type": "driver's_license",
                    "id_number": "D6667777",
                    "country_of_residence": "US"
                },
                "tier": "premium",
                "limits": {
                    "withdrawal_limit": 25000,
                    "transfer_limit": 50000,
                    "transaction_limit": 10000
                },
                "fee_schedule": {
                    "monthly_fee": 0,
                    "atm_fee": 0,
                    "overdraft_fee": 0,
                    "transaction_fee": 0,
                    "waivers": {
                        "premium": True
                    }
                },
                "disclosures": {
                    "documents": ["DOC-801", "DOC-802"],
                    "delivery_status": "delivered",
                    "timestamp": "2024-06-01T20:00:00Z"
                },
                "funding_status": "verified"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Account opened and cash deposit processed successfully.",
                "result_data": {
                    "account_id": "8899-0011-2233",
                    "status": "opened",
                    "confirmation": {
                        "timestamp": "2024-06-01T20:00:00Z",
                        "disclosures": [
                            "DOC-801",
                            "DOC-802"
                        ],
                        "funding_status": "verified",
                        "fee_schedule": {
                            "monthly_fee": 0,
                            "atm_fee": 0,
                            "overdraft_fee": 0,
                            "transaction_fee": 0,
                            "waivers": {
                                "premium": True
                            }
                        },
                        "limits": {
                            "withdrawal_limit": 25000,
                            "transfer_limit": 50000,
                            "transaction_limit": 10000
                        }
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Customer identity validated (in-person or digital)",
            "expected_state": {
                "identity_status": "verified",
                "match_score": 97
            }
        },
        {
            "step": 2,
            "description": "AML screening clear",
            "expected_state": {
                "aml_status": "clear"
            }
        },
        {
            "step": 3,
            "description": "CTR filed for cash deposit",
            "expected_state": {
                "ctr_status": "filed"
            }
        },
        {
            "step": 4,
            "description": "Account tier calculated as premium",
            "expected_state": {
                "tier": "premium",
                "eligibility": True
            }
        },
        {
            "step": 5,
            "description": "Premium account limits configured",
            "expected_state": {
                "limits": {
                    "withdrawal_limit": 25000,
                    "transfer_limit": 50000,
                    "transaction_limit": 10000
                }
            }
        },
        {
            "step": 6,
            "description": "Fee schedule with premium waivers applied",
            "expected_state": {
                "fee_schedule": {
                    "monthly_fee": 0,
                    "waivers": {
                        "premium": True
                    }
                }
            }
        },
        {
            "step": 7,
            "description": "Disclosures generated and delivered",
            "expected_state": {
                "disclosures_status": "delivered"
            }
        },
        {
            "step": 8,
            "description": "Account opened and cash deposit processed",
            "expected_state": {
                "status": "opened",
                "confirmation_sent": True
            }
        }
    ]
    description = "Covers same-day account opening with large cash deposit and CTR filing."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the standard W8 workflow for cash deposits >= $10,000. "
        "All steps are successful, no escalations or failures, and the scenario is a straightforward premium-tier account opening with compliance filing."
    )

    # No tool overrides are required for this test case; all tool behaviors are standard and successful.