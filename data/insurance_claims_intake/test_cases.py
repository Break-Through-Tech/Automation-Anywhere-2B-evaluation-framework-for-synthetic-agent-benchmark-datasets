from typing import Any, Optional, List, Dict, Union
from typing_extensions import TypedDict
from generator_v5.core.system_tools_base import SystemToolsBaseClass

# TypedDict definitions for structured parameters and return types

class ContactInfo(TypedDict, total=False):
    email: str
    phone: str

class LossDetails(TypedDict, total=False):
    date_of_loss: str
    location: str
    cause: str
    injuries: List[str]
    damages: List[str]
    policy_number: Optional[str]
    claimant_name: str
    contact_info: ContactInfo

class ClaimTypeResult(TypedDict, total=False):
    claim_type: str  # enum
    sub_type: str
    is_catastrophe: bool
    attorney_represented: bool

class CoverageLimits(TypedDict, total=False):
    # Structure not specified; placeholder for coverage limits object
    # Could contain fields like 'dwelling', 'contents', 'liability', etc.
    dwelling: Optional[float]
    contents: Optional[float]
    liability: Optional[float]

class CoverageInfo(TypedDict, total=False):
    coverage_confirmed: bool
    policy_status: str  # enum
    coverage_limits: CoverageLimits
    denial_reason: Optional[str]

class SeverityInfo(TypedDict, total=False):
    severity_level: str  # enum
    emergency_services_needed: bool
    estimated_exposure: float
    flags: List[str]

class ClaimRecordResult(TypedDict, total=False):
    claim_number: str
    claim_status: str
    flags: List[str]
    created_timestamp: str
    linked_claims: Optional[List[str]]
    adjuster_id: Optional[str]

class WorkloadInfo(TypedDict, total=False):
    # Structure not specified; placeholder for adjuster workload data
    avg_open_claims: Optional[int]
    team: Optional[str]

class RouteToAdjusterResult(TypedDict, total=False):
    assigned_team: str
    adjuster_id: str
    assignment_status: str  # enum
    assignment_timestamp: str

class EmergencyServicesResult(TypedDict, total=False):
    dispatch_status: str  # enum
    vendor_id: str
    estimated_arrival: str
    confirmation_number: str

class RecipientInfo(TypedDict, total=False):
    name: str
    email: str
    phone: str

class SendAcknowledgmentResult(TypedDict, total=False):
    message_id: str
    delivery_status: str  # enum
    timestamp: str
    estimated_delivery: str

class BaseInsuranceClaimsIntakeAndTriageAgentTestCase(SystemToolsBaseClass):
    """
    Base class containing common methods for all Insurance - Claims Processing test cases.
    """

    # Agent context attributes from agent description
    role = (
        "You are an intelligent claims intake and triage agent that automates First "
        "Notice of Loss (FNOL) processing for insurance carriers. You extract, validate, "
        "classify, and route claims received via email, web forms, or phone transcripts, "
        "ensuring accurate data capture and rapid assignment to the correct teams and vendors.\n"
    )
    goal = (
        "Your goal is to process FNOL submissions in under 5 minutes, extracting all "
        "required claim data, validating coverage, classifying claim type and severity, "
        "triggering emergency services when needed, creating claims in the core system, "
        "and ensuring timely, compliant customer acknowledgment and routing.\n"
    )
    action_plan = {
        "assumptions": [
            "All FNOL submissions contain enough information to begin extraction and triage.",
            "Policy and claims systems are available and responsive for validation and record creation."
        ],
        "tools_and_resources": [
            "extract_loss_details",
            "classify_claim_type",
            "validate_policy_coverage",
            "assess_claim_severity",
            "create_claim_record",
            "route_to_adjuster",
            "trigger_emergency_services",
            "send_claim_acknowledgment"
        ],
        "guidelines": [
            "Always validate policy coverage before claim creation or vendor dispatch.",
            "Route claims to specialized teams for catastrophe, large loss, BI, or attorney-represented scenarios.",
            "Trigger emergency services only when claim severity warrants immediate action.",
            "Escalate to human review for ambiguous, high-severity, or complex cases (e.g., litigation, fraud, coverage disputes)."
        ],
        "workflow_selection": [
            "If input.claim_type == 'property' and input.severity == 'emergency', route to storm damage emergency workflow for immediate mitigation and CAT team assignment.",
            "If input.claim_type == 'auto' and input.injury_reported == true, route to Auto Accident workflow with BI flag and injury triage.",
            "If input.catastrophe_event == true and input.batch_size > 1, route to Catastrophe Event workflow for batch intake and routing.",
            "If input.claim_type == 'workers_comp' and input.injury_reported == true, route to Workers Compensation workflow with medical management.",
            "If input.claim_type == 'liability' and input.attorney_represented == true, route to Liability workflow for attorney-represented claims and legal notification.",
            "If input.policy_status == 'lapsed' or input.coverage_confirmed == false, route to Denied Claim workflow for coverage denial and regulatory notification.",
            "If input.duplicate_claim_found == true, route to Duplicate Claim workflow for linking and acknowledgment.",
            "If input.claim_type == 'commercial_property' and input.business_interruption == true, route to Complex Commercial Claim workflow for large loss and BI handling.",
            "If input.claim_type not recognized or input.data_incomplete == true, escalate to human review for ambiguous or incomplete FNOL submissions."
        ],
        "failure_points": [
            "Policy system unavailable or unresponsive during coverage validation: Retry up to 3 times, escalate to HUMAN_IN_THE_LOOP if unresolved.",
            "Key claim data missing or ambiguous after extraction: Request clarification from customer, escalate to HUMAN_IN_THE_LOOP if not resolved.",
            "Claim creation fails due to system error: Log error, notify adjuster supervisor, escalate to HUMAN_IN_THE_LOOP.",
            "Emergency vendor dispatch fails (no availability): Escalate to HUMAN_IN_THE_LOOP for manual vendor assignment."
        ],
        "success_criteria": [
            "Claim created in core system with all required data and correct classification.",
            "Policy coverage validated and documented.",
            "Claim routed to appropriate team/adjuster within SLA (5 minutes for emergencies, 30 minutes for standard claims).",
            "Customer/claimant receives timely acknowledgment with claim number and next steps.",
            "Emergency services triggered when required.",
            "All regulatory notifications and documentation completed."
        ]
    }

    # -------------------- DOMAIN TOOLS --------------------

    def extract_loss_details(self, source_text: str) -> LossDetails:
        """
        Extract structured loss details (date, location, cause, injuries, damages) from unstructured FNOL submission.

        Args:
            source_text: Raw FNOL submission text (email, web form, transcript). 
                         Length: 50-5000 characters.

        Returns:
            LossDetails: 
                - date_of_loss (ISO 8601)
                - location (string)
                - cause (string)
                - injuries (array of strings)
                - damages (array of strings)
                - policy_number (string, optional)
                - claimant_name (string)
                - contact_info (object: email, phone)
        """
        if not isinstance(source_text, str) or not (50 <= len(source_text) <= 5000):
            raise ValueError("source_text must be a string of length 50-5000 characters.")
        print(f"--- Running extract_loss_details ---")
        print(f"source_text: {source_text[:100]}...")
        # Mock extraction
        return {
            "date_of_loss": "2025-09-12",
            "location": "123 Main St, Springfield, IL 62704",
            "cause": "wind",
            "injuries": [],
            "damages": ["roof", "interior water"],
            "policy_number": "HO-887766",
            "claimant_name": "John Doe",
            "contact_info": {"email": "john.doe@email.com", "phone": "+12175551234"}
        }

    def classify_claim_type(self, loss_details: LossDetails) -> ClaimTypeResult:
        """
        Categorize claim type based on extracted details.

        Args:
            loss_details: Extracted loss details object from extract_loss_details.

        Returns:
            ClaimTypeResult:
                - claim_type (enum: property, auto, liability, workers_comp, commercial_property, business_interruption)
                - sub_type (string)
                - is_catastrophe (boolean)
                - attorney_represented (boolean, default: False)
        """
        print(f"--- Running classify_claim_type ---")
        print(f"loss_details: {loss_details}")
        # Mock classification
        return {
            "claim_type": "property",
            "sub_type": "wind",
            "is_catastrophe": False,
            "attorney_represented": False
        }

    def validate_policy_coverage(
        self, policy_number: str, date_of_loss: str, peril: str
    ) -> CoverageInfo:
        """
        Validate if the policy is active, loss date is within coverage period, and peril is covered.

        Args:
            policy_number: Policy identifier. Format: [policy type prefix]-[6+ digits], e.g., HO-887766.
            date_of_loss: Date of loss. ISO 8601 format (YYYY-MM-DD).
            peril: Type of peril/loss (e.g., fire, wind, water, theft, liability, injury).

        Returns:
            CoverageInfo:
                - coverage_confirmed (boolean)
                - policy_status (enum: active, lapsed, cancelled, expired)
                - coverage_limits (object)
                - denial_reason (string, optional)
        """
        valid_status = ["active", "lapsed", "cancelled", "expired"]
        print(f"--- Running validate_policy_coverage ---")
        print(f"policy_number: {policy_number}, date_of_loss: {date_of_loss}, peril: {peril}")
        # Mock validation
        return {
            "coverage_confirmed": True,
            "policy_status": "active",
            "coverage_limits": {"dwelling": 250000.0, "contents": 75000.0},
            "denial_reason": None
        }

    def assess_claim_severity(
        self, loss_details: LossDetails, coverage_info: CoverageInfo
    ) -> SeverityInfo:
        """
        Assess claim urgency, emergency needs, and complexity for triage.

        Args:
            loss_details: Extracted loss details object.
            coverage_info: Policy coverage validation result.

        Returns:
            SeverityInfo:
                - severity_level (enum: standard, emergency, catastrophe, large_loss, litigation, denied)
                - emergency_services_needed (boolean)
                - estimated_exposure (number, USD, >=0, max 2 decimals)
                - flags (array: emergency, BI, litigation, duplicate, denied)
        """
        valid_severity = ["standard", "emergency", "catastrophe", "large_loss", "litigation", "denied"]
        print(f"--- Running assess_claim_severity ---")
        print(f"loss_details: {loss_details}")
        print(f"coverage_info: {coverage_info}")
        # Mock assessment
        return {
            "severity_level": "emergency",
            "emergency_services_needed": True,
            "estimated_exposure": 30000.00,
            "flags": ["emergency"]
        }

    def create_claim_record(
        self,
        loss_details: LossDetails,
        claim_type: str,
        coverage_info: CoverageInfo,
        severity_info: SeverityInfo
    ) -> ClaimRecordResult:
        """
        Create claim in core system with all available information.

        Args:
            loss_details: Extracted loss details.
            claim_type: Claim type. Must match claim_type from classify_claim_type.
                        Valid values: ['property', 'auto', 'liability', 'workers_comp', 'commercial_property', 'business_interruption']
            coverage_info: Policy coverage validation result.
            severity_info: Claim severity assessment result.

        Returns:
            ClaimRecordResult:
                - claim_number (string, Format: YYYY-XXXXXX)
                - claim_status (string)
                - flags (array)
                - created_timestamp (ISO 8601)
                - linked_claims (array of claim_numbers, optional)
                - adjuster_id (string, optional)
        """
        valid_types = [
            "property", "auto", "liability", "workers_comp", "commercial_property", "business_interruption"
        ]
        if claim_type not in valid_types:
            raise ValueError(f"Invalid claim_type: {claim_type}. Must be one of {valid_types}")
        print(f"--- Running create_claim_record ---")
        print(f"loss_details: {loss_details}")
        print(f"claim_type: {claim_type}")
        print(f"coverage_info: {coverage_info}")
        print(f"severity_info: {severity_info}")
        # Mock creation
        return {
            "claim_number": "2025-445521",
            "claim_status": "created",
            "flags": severity_info.get("flags", []),
            "created_timestamp": "2025-09-12T09:30:00Z",
            "linked_claims": [],
            "adjuster_id": None
        }

    def route_to_adjuster(
        self,
        claim_number: str,
        claim_type: str,
        severity_info: SeverityInfo,
        location: str,
        workload_info: Optional[WorkloadInfo] = None
    ) -> RouteToAdjusterResult:
        """
        Assign claim to appropriate adjuster or team based on type, severity, location, and adjuster workload.

        Args:
            claim_number: Unique claim identifier. Format: YYYY-XXXXXX.
            claim_type: Claim type. Valid values: ['property', 'auto', 'liability', 'workers_comp', 'commercial_property', 'business_interruption']
            severity_info: Claim severity assessment result.
            location: Loss location (city, state, ZIP).
            workload_info: Adjuster team workload data (optional).

        Returns:
            RouteToAdjusterResult:
                - assigned_team (string)
                - adjuster_id (string)
                - assignment_status (enum: assigned, queued, failed)
                - assignment_timestamp (ISO 8601)
        """
        valid_types = [
            "property", "auto", "liability", "workers_comp", "commercial_property", "business_interruption"
        ]
        valid_assignment_status = ["assigned", "queued", "failed"]
        if claim_type not in valid_types:
            raise ValueError(f"Invalid claim_type: {claim_type}. Must be one of {valid_types}")
        print(f"--- Running route_to_adjuster ---")
        print(f"claim_number: {claim_number}, claim_type: {claim_type}, severity_info: {severity_info}, location: {location}, workload_info: {workload_info}")
        # Mock routing
        return {
            "assigned_team": "CAT team" if severity_info.get("severity_level") == "emergency" else "Property team",
            "adjuster_id": "ADJ-1001",
            "assignment_status": "assigned",
            "assignment_timestamp": "2025-09-12T09:32:00Z"
        }

    def trigger_emergency_services(
        self,
        claim_number: str,
        emergency_type: str,
        location: str,
        vendor_network: str
    ) -> EmergencyServicesResult:
        """
        Dispatch emergency vendors for mitigation, repairs, medical, or other urgent needs.

        Args:
            claim_number: Unique claim identifier.
            emergency_type: Type of emergency service required. 
                            Valid values: ['water_mitigation', 'tarping', 'fire_boardup', 'medical', 'temporary_housing', 'towing', 'security', 'salvage']
            location: Loss location (address, city, state, ZIP).
            vendor_network: Preferred vendor network. 
                            Valid values: ['ServiceMaster', 'Paul Davis', 'Enterprise', 'LocalVendor']

        Returns:
            EmergencyServicesResult:
                - dispatch_status (enum: dispatched, queued, failed)
                - vendor_id (string)
                - estimated_arrival (ISO 8601)
                - confirmation_number (string)
        """
        valid_emergency_types = [
            "water_mitigation", "tarping", "fire_boardup", "medical", "temporary_housing", "towing", "security", "salvage"
        ]
        valid_vendor_networks = [
            "ServiceMaster", "Paul Davis", "Enterprise", "LocalVendor"
        ]
        valid_dispatch_status = ["dispatched", "queued", "failed"]
        if emergency_type not in valid_emergency_types:
            raise ValueError(f"Invalid emergency_type: {emergency_type}. Must be one of {valid_emergency_types}")
        if vendor_network not in valid_vendor_networks:
            raise ValueError(f"Invalid vendor_network: {vendor_network}. Must be one of {valid_vendor_networks}")
        print(f"--- Running trigger_emergency_services ---")
        print(f"claim_number: {claim_number}, emergency_type: {emergency_type}, location: {location}, vendor_network: {vendor_network}")
        # Mock dispatch
        return {
            "dispatch_status": "dispatched",
            "vendor_id": "VEND-2001",
            "estimated_arrival": "2025-09-12T11:00:00Z",
            "confirmation_number": "CONF-123456"
        }

    def send_claim_acknowledgment(
        self,
        claim_number: str,
        recipient_info: RecipientInfo,
        message_type: str,
        delivery_method: str,
        content: str
    ) -> SendAcknowledgmentResult:
        """
        Send claim acknowledgment or notification to customer/claimant.

        Args:
            claim_number: Unique claim identifier.
            recipient_info: Recipient contact details: name (string), email (string, valid format), phone (string, E.164 format).
            message_type: Type of communication to send.
                          Valid values: ['acknowledgment', 'denial', 'status_update', 'emergency_notification', 'attorney_notification', 'duplicate_notification']
            delivery_method: Preferred delivery channel.
                             Valid values: ['email', 'sms', 'portal', 'mail']
            content: Message content. Length: 10-2000 characters.

        Returns:
            SendAcknowledgmentResult:
                - message_id (string)
                - delivery_status (enum: sent, queued, failed)
                - timestamp (ISO 8601)
                - estimated_delivery (ISO 8601)
        """
        valid_message_types = [
            "acknowledgment", "denial", "status_update", "emergency_notification", "attorney_notification", "duplicate_notification"
        ]
        valid_delivery_methods = ["email", "sms", "portal", "mail"]
        valid_delivery_status = ["sent", "queued", "failed"]
        if message_type not in valid_message_types:
            raise ValueError(f"Invalid message_type: {message_type}. Must be one of {valid_message_types}")
        if delivery_method not in valid_delivery_methods:
            raise ValueError(f"Invalid delivery_method: {delivery_method}. Must be one of {valid_delivery_methods}")
        if not (10 <= len(content) <= 2000):
            raise ValueError("content length must be between 10 and 2000 characters.")
        print(f"--- Running send_claim_acknowledgment ---")
        print(f"claim_number: {claim_number}, recipient_info: {recipient_info}, message_type: {message_type}, delivery_method: {delivery_method}, content: {content[:50]}...")
        # Mock notification
        return {
            "message_id": "MSG-001",
            "delivery_status": "sent",
            "timestamp": "2025-09-12T09:33:00Z",
            "estimated_delivery": "2025-09-12T09:34:00Z"
        }

    # -------------------- SYSTEM TOOLS (inherited from SystemToolsBaseClass) --------------------
    # SUCCESS, FAILED, CANCELLED, HUMAN_IN_THE_LOOP are provided by SystemToolsBaseClass

class TestCase1_InsuranceClaimsIntakeAndTriageAgent_W1_easy(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """
    Emergency Property Claim – Water Intrusion, Storm Peril, Coverage Confirmed

    Covers urgent property claim with water damage, storm peril, policy active, emergency vendor dispatch via ServiceMaster.
    """

    test_case_id = "InsuranceClaimsIntakeAndTriageAgent_W1_TC1"
    title = "Emergency Property Claim – Water Intrusion, Storm Peril, Coverage Confirmed"
    workflow = "W1"
    input_data = {
        "source_text": "Tree fell on my roof during last night's storm. Water leaking into bedroom. Need help ASAP.",
        "policy_number": "HO-887766",
        "claim_type": "property",
        "severity": "emergency",
        "injury_reported": False,
        "catastrophe_event": False,
        "batch_size": 1,
        "policy_status": "active",
        "coverage_confirmed": True,
        "business_interruption": False,
        "duplicate_claim_found": False,
        "data_incomplete": False
    }
    expected_tool_calls = [
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Tree fell on my roof during last night's storm. Water leaking into bedroom. Need help ASAP."
            }
        },
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-10-08",
                    "location": "123 Main St, Springfield, IL",
                    "cause": "storm/wind",
                    "injuries": [],
                    "damages": ["roof", "water intrusion", "bedroom"],
                    "policy_number": "HO-887766",
                    "claimant_name": "John Doe",
                    "contact_info": {
                        "email": "john.doe@email.com",
                        "phone": "+12175552345"
                    }
                }
            }
        },
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "HO-887766",
                "date_of_loss": "2026-10-08",
                "peril": "storm/wind"
            }
        },
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-10-08",
                    "location": "123 Main St, Springfield, IL",
                    "cause": "storm/wind",
                    "injuries": [],
                    "damages": ["roof", "water intrusion", "bedroom"],
                    "policy_number": "HO-887766",
                    "claimant_name": "John Doe",
                    "contact_info": {
                        "email": "john.doe@email.com",
                        "phone": "+12175552345"
                    }
                },
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {
                        "dwelling": 250000,
                        "personal_property": 100000,
                        "deductible": 1000
                    }
                }
            }
        },
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-10-08",
                    "location": "123 Main St, Springfield, IL",
                    "cause": "storm/wind",
                    "injuries": [],
                    "damages": ["roof", "water intrusion", "bedroom"],
                    "policy_number": "HO-887766",
                    "claimant_name": "John Doe",
                    "contact_info": {
                        "email": "john.doe@email.com",
                        "phone": "+12175552345"
                    }
                },
                "claim_type": "property",
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {
                        "dwelling": 250000,
                        "personal_property": 100000,
                        "deductible": 1000
                    }
                },
                "severity_info": {
                    "severity_level": "emergency",
                    "emergency_services_needed": True,
                    "estimated_exposure": 15000.00,
                    "flags": ["emergency"]
                }
            }
        },
        {
            "name": "trigger_emergency_services",
            "tool_inputs": {
                "claim_number": "2026-445521",
                "emergency_type": "water_mitigation",
                "location": "123 Main St, Springfield, IL",
                "vendor_network": "ServiceMaster"
            }
        },
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-445521",
                "claim_type": "property",
                "severity_info": {
                    "severity_level": "emergency",
                    "emergency_services_needed": True,
                    "estimated_exposure": 15000.00,
                    "flags": ["emergency"]
                },
                "location": "123 Main St, Springfield, IL",
                "workload_info": {
                    "CAT_team_capacity": "available"
                }
            }
        },
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-445521",
                "recipient_info": {
                    "name": "John Doe",
                    "email": "john.doe@email.com",
                    "phone": "+12175552345"
                },
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "Your claim (2026-445521) has been created. Emergency water mitigation has been dispatched. The CAT team will contact you shortly."
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Claim created, vendor dispatched, CAT team assigned, customer notified.",
                "result_data": {
                    "claim_number": "2026-445521",
                    "claim_status": "created",
                    "assigned_team": "CAT team",
                    "customer_acknowledgment_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Loss details extracted (storm, water intrusion)",
            "expected_state": {
                "loss_details": "complete",
                "cause": "storm/wind"
            }
        },
        {
            "step": 2,
            "description": "Claim classified as property, peril: storm/wind",
            "expected_state": {
                "claim_type": "property",
                "peril": "storm/wind"
            }
        },
        {
            "step": 3,
            "description": "Policy coverage validated (active, peril covered)",
            "expected_state": {
                "coverage_confirmed": True,
                "policy_status": "active"
            }
        },
        {
            "step": 4,
            "description": "Claim severity assessed (emergency)",
            "expected_state": {
                "severity_level": "emergency",
                "emergency_services_needed": True
            }
        },
        {
            "step": 5,
            "description": "Claim record created with emergency flag",
            "expected_state": {
                "claim_status": "created",
                "flags": [
                    "emergency"
                ]
            }
        },
        {
            "step": 6,
            "description": "Emergency water mitigation vendor dispatched",
            "expected_state": {
                "dispatch_status": "dispatched",
                "emergency_type": "water_mitigation",
                "vendor_network": "ServiceMaster"
            }
        },
        {
            "step": 7,
            "description": "Claim routed to CAT team",
            "expected_state": {
                "assigned_team": "CAT team",
                "assignment_status": "assigned"
            }
        },
        {
            "step": 8,
            "description": "Claim acknowledgment sent to customer",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "acknowledgment"
            }
        }
    ]
    description = "Covers urgent property claim with water damage, storm peril, policy active, emergency vendor dispatch via ServiceMaster."
    difficulty = "easy"
    difficulty_reasoning = (
        "All data is present, no ambiguity or escalation required. "
        "Straightforward happy path: emergency claim with clear coverage, triggers vendor dispatch and CAT team assignment."
    )

class TestCase2_InsuranceClaimsIntakeAndTriageAgent_W1_medium(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """
    Emergency Property Claim – Water Intrusion, Storm Peril, Local Vendor, Alternate Address

    Tests alternate vendor dispatch and address parsing, confirms agent supports different vendor networks and locations.
    """

    test_case_id = "InsuranceClaimsIntakeAndTriageAgent_W1_TC2"
    title = "Emergency Property Claim – Water Intrusion, Storm Peril, Local Vendor, Alternate Address"
    workflow = "W1"

    input_data = {
        "source_text": "Heavy rain caused basement flooding at 88 Oak St, Springfield, IL. Water rising quickly.",
        "policy_number": "HO-998877",
        "claim_type": "property",
        "severity": "emergency",
        "injury_reported": False,
        "catastrophe_event": False,
        "batch_size": 1,
        "policy_status": "active",
        "coverage_confirmed": True,
        "business_interruption": False,
        "duplicate_claim_found": False,
        "data_incomplete": False
    }

    expected_tool_calls = [
        # 1. Extract loss details from FNOL submission
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": input_data["source_text"]
            }
        },
        # 2. Classify claim type as property damage, storm/wind peril
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-16",
                    "location": "88 Oak St, Springfield, IL",
                    "cause": "water/storm",
                    "injuries": [],
                    "damages": ["basement flooding", "water intrusion"],
                    "policy_number": input_data["policy_number"],
                    "claimant_name": "Unknown",
                    "contact_info": {
                        "email": "unknown@example.com",
                        "phone": "+11234567890"
                    }
                }
            }
        },
        # 3. Validate policy coverage for storm peril
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": input_data["policy_number"],
                "date_of_loss": "2026-04-16",
                "peril": "water"
            }
        },
        # 4. Assess claim severity and flag as emergency
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-16",
                    "location": "88 Oak St, Springfield, IL",
                    "cause": "water/storm",
                    "injuries": [],
                    "damages": ["basement flooding", "water intrusion"],
                    "policy_number": input_data["policy_number"],
                    "claimant_name": "Unknown",
                    "contact_info": {
                        "email": "unknown@example.com",
                        "phone": "+11234567890"
                    }
                },
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {
                        "dwelling": 250000,
                        "personal_property": 100000,
                        "water_backup": 15000
                    }
                }
            }
        },
        # 5. Create claim record with emergency flag
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-16",
                    "location": "88 Oak St, Springfield, IL",
                    "cause": "water/storm",
                    "injuries": [],
                    "damages": ["basement flooding", "water intrusion"],
                    "policy_number": input_data["policy_number"],
                    "claimant_name": "Unknown",
                    "contact_info": {
                        "email": "unknown@example.com",
                        "phone": "+11234567890"
                    }
                },
                "claim_type": "property",
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {
                        "dwelling": 250000,
                        "personal_property": 100000,
                        "water_backup": 15000
                    }
                },
                "severity_info": {
                    "severity_level": "emergency",
                    "emergency_services_needed": True,
                    "estimated_exposure": 20000.00,
                    "flags": ["emergency"]
                }
            }
        },
        # 6. Trigger emergency water mitigation vendor dispatch (LocalVendor, alternate address)
        {
            "name": "trigger_emergency_services",
            "tool_inputs": {
                "claim_number": "2026-445522",
                "emergency_type": "water_mitigation",
                "location": "88 Oak St, Springfield, IL",
                "vendor_network": "LocalVendor"
            }
        },
        # 7. Route claim to CAT team
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-445522",
                "claim_type": "property",
                "severity_info": {
                    "severity_level": "emergency",
                    "emergency_services_needed": True,
                    "estimated_exposure": 20000.00,
                    "flags": ["emergency"]
                },
                "location": "Springfield, IL"
            }
        },
        # 8. Send claim acknowledgment to customer
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-445522",
                "recipient_info": {
                    "name": "Unknown",
                    "email": "unknown@example.com",
                    "phone": "+11234567890"
                },
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "Your property claim has been created and assigned to our CAT team. Emergency vendor has been dispatched to 88 Oak St, Springfield, IL. Claim #: 2026-445522."
            }
        },
        # 9. SUCCESS
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Claim intake, triage, emergency mitigation, and acknowledgment complete.",
                "result_data": {
                    "claim_number": "2026-445522",
                    "claim_status": "created",
                    "assigned_team": "CAT team",
                    "customer_acknowledgment_status": "sent"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Loss details extracted (flood, alternate address)",
            "expected_state": {
                "loss_details": "complete",
                "location": "88 Oak St, Springfield, IL"
            }
        },
        {
            "step": 2,
            "description": "Claim classified as property, peril: water/storm",
            "expected_state": {
                "claim_type": "property",
                "peril": "water"
            }
        },
        {
            "step": 3,
            "description": "Policy coverage validated (active, peril covered)",
            "expected_state": {
                "coverage_confirmed": True,
                "policy_status": "active"
            }
        },
        {
            "step": 4,
            "description": "Claim severity assessed (emergency)",
            "expected_state": {
                "severity_level": "emergency",
                "emergency_services_needed": True
            }
        },
        {
            "step": 5,
            "description": "Claim record created with emergency flag",
            "expected_state": {
                "claim_status": "created",
                "flags": [
                    "emergency"
                ]
            }
        },
        {
            "step": 6,
            "description": "Emergency water mitigation vendor dispatched (LocalVendor)",
            "expected_state": {
                "dispatch_status": "dispatched",
                "emergency_type": "water_mitigation",
                "vendor_network": "LocalVendor"
            }
        },
        {
            "step": 7,
            "description": "Claim routed to CAT team",
            "expected_state": {
                "assigned_team": "CAT team",
                "assignment_status": "assigned"
            }
        },
        {
            "step": 8,
            "description": "Claim acknowledgment sent to customer",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "acknowledgment"
            }
        }
    ]

    description = (
        "Tests alternate vendor dispatch and address parsing, confirms agent supports different vendor networks and locations."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This test involves standard emergency property claim intake but adds complexity by requiring correct parsing of an alternate address, "
        "selecting a non-default vendor network ('LocalVendor'), and ensuring all steps (extraction, classification, coverage, severity, creation, "
        "dispatch, routing, acknowledgment) are executed in sequence. It tests flexible vendor selection and address handling, both of which are "
        "critical for robust FNOL automation."
    )

class TestCase3_InsuranceClaimsIntakeAndTriageAgent_W2_easy(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """
    Test Case 3: Auto Accident with Bodily Injury – Standard BI, Coverage Confirmed

    Covers auto accident with a single injury, liability coverage confirmed, BI adjuster assignment.
    """

    test_case_id = "InsuranceClaimsIntakeAndTriageAgent_W2_TC1"
    title = "Auto Accident with Bodily Injury – Standard BI, Coverage Confirmed"
    workflow = "W2"
    input_data = {
        "source_text": "I was rear-ended on I-95. Neck pain, went to hospital.",
        "policy_number": "AUTO-123456",
        "claim_type": "auto",
        "severity": "standard",
        "injury_reported": True,
        "catastrophe_event": False,
        "batch_size": 1,
        "policy_status": "active",
        "coverage_confirmed": True,
        "duplicate_claim_found": False,
        "business_interruption": False,
        "data_incomplete": False
    }
    expected_tool_calls = [
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "I was rear-ended on I-95. Neck pain, went to hospital."
            }
        },
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-15",
                    "location": "I-95",
                    "cause": "rear-end collision",
                    "injuries": ["neck pain"],
                    "damages": [],
                    "policy_number": "AUTO-123456",
                    "claimant_name": "Unknown",
                    "contact_info": {
                        "email": "",
                        "phone": ""
                    }
                }
            }
        },
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "AUTO-123456",
                "date_of_loss": "2026-04-15",
                "peril": "injury"
            }
        },
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-15",
                    "location": "I-95",
                    "cause": "rear-end collision",
                    "injuries": ["neck pain"],
                    "damages": [],
                    "policy_number": "AUTO-123456",
                    "claimant_name": "Unknown",
                    "contact_info": {
                        "email": "",
                        "phone": ""
                    }
                },
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {},
                }
            }
        },
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-15",
                    "location": "I-95",
                    "cause": "rear-end collision",
                    "injuries": ["neck pain"],
                    "damages": [],
                    "policy_number": "AUTO-123456",
                    "claimant_name": "Unknown",
                    "contact_info": {
                        "email": "",
                        "phone": ""
                    }
                },
                "claim_type": "auto",
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {},
                },
                "severity_info": {
                    "severity_level": "standard",
                    "emergency_services_needed": False,
                    "estimated_exposure": 2500.00,
                    "flags": ["BI"]
                }
            }
        },
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-445523",
                "claim_type": "auto",
                "severity_info": {
                    "severity_level": "standard",
                    "emergency_services_needed": False,
                    "estimated_exposure": 2500.00,
                    "flags": ["BI"]
                },
                "location": "I-95"
            }
        },
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-445523",
                "recipient_info": {
                    "name": "Unknown",
                    "email": "",
                    "phone": ""
                },
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "Your auto claim has been created and assigned to a BI adjuster. Claim #: 2026-445523."
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Claim created, BI adjuster assigned, acknowledgment sent.",
                "result_data": {
                    "claim_number": "2026-445523",
                    "claim_status": "created",
                    "assigned_team": "BI adjuster",
                    "customer_acknowledgment_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Loss details extracted (auto, injury)",
            "expected_state": {
                "loss_details": "complete",
                "injuries": [
                    "neck pain"
                ]
            }
        },
        {
            "step": 2,
            "description": "Claim classified as auto liability",
            "expected_state": {
                "claim_type": "auto",
                "sub_type": "liability"
            }
        },
        {
            "step": 3,
            "description": "Policy coverage validated (active, liability covered)",
            "expected_state": {
                "coverage_confirmed": True,
                "policy_status": "active"
            }
        },
        {
            "step": 4,
            "description": "Claim severity assessed (BI flag)",
            "expected_state": {
                "severity_level": "standard",
                "flags": [
                    "BI"
                ]
            }
        },
        {
            "step": 5,
            "description": "Claim record created with injury flag",
            "expected_state": {
                "claim_status": "created",
                "flags": [
                    "BI"
                ]
            }
        },
        {
            "step": 6,
            "description": "Claim routed to BI adjuster",
            "expected_state": {
                "assigned_team": "BI adjuster",
                "assignment_status": "assigned"
            }
        },
        {
            "step": 7,
            "description": "Claim acknowledgment sent to claimant",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "acknowledgment"
            }
        }
    ]
    description = "Covers auto accident with a single injury, liability coverage confirmed, BI adjuster assignment."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case represents a standard, well-documented auto liability claim with bodily injury. "
        "All required information is present, coverage is confirmed, and no escalation or exception handling is needed. "
        "The workflow follows the straightforward BI path with no ambiguous or complex elements."
    )

class TestCase4_InsuranceClaimsIntakeAndTriageAgent_W2_easy(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """Auto Accident with Bodily Injury – Multiple Injuries, Coverage Confirmed

    Tests agent's ability to process multiple injury details and route accordingly.
    """

    test_case_id = "InsuranceClaimsIntakeAndTriageAgent_W2_TC2"
    title = "Auto Accident with Bodily Injury – Multiple Injuries, Coverage Confirmed"
    workflow = "W2"
    input_data = {
        "source_text": "Our car was hit from the side at Main & 5th. My wife and I both have back and shoulder pain.",
        "policy_number": "AUTO-654321",
        "claim_type": "auto",
        "severity": "standard",
        "injury_reported": True,
        "catastrophe_event": False,
        "batch_size": 1,
        "policy_status": "active",
        "coverage_confirmed": True,
        "duplicate_claim_found": False,
        "business_interruption": False,
        "data_incomplete": False
    }

    expected_tool_calls = [
        # Step 1: Extract loss details from FNOL submission
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Our car was hit from the side at Main & 5th. My wife and I both have back and shoulder pain."
            }
        },
        # Step 2: Classify claim type as auto liability
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-05-01",
                    "location": "Main & 5th",
                    "cause": "side-impact collision",
                    "injuries": ["back pain", "shoulder pain"],
                    "damages": [],
                    "policy_number": "AUTO-654321",
                    "claimant_name": "Unknown",
                    "contact_info": {"email": None, "phone": None}
                }
            }
        },
        # Step 3: Validate policy coverage
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "AUTO-654321",
                "date_of_loss": "2026-05-01",
                "peril": "injury"
            }
        },
        # Step 4: Assess claim severity, BI flag
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-05-01",
                    "location": "Main & 5th",
                    "cause": "side-impact collision",
                    "injuries": ["back pain", "shoulder pain"],
                    "damages": [],
                    "policy_number": "AUTO-654321",
                    "claimant_name": "Unknown",
                    "contact_info": {"email": None, "phone": None}
                },
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {"bodily_injury": 100000, "property_damage": 50000}
                }
            }
        },
        # Step 5: Create claim record with injury flag
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-05-01",
                    "location": "Main & 5th",
                    "cause": "side-impact collision",
                    "injuries": ["back pain", "shoulder pain"],
                    "damages": [],
                    "policy_number": "AUTO-654321",
                    "claimant_name": "Unknown",
                    "contact_info": {"email": None, "phone": None}
                },
                "claim_type": "auto",
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {"bodily_injury": 100000, "property_damage": 50000}
                },
                "severity_info": {
                    "severity_level": "standard",
                    "emergency_services_needed": False,
                    "estimated_exposure": 10000.00,
                    "flags": ["BI"]
                }
            }
        },
        # Step 6: Route claim to BI adjuster
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-445524",
                "claim_type": "auto",
                "severity_info": {
                    "severity_level": "standard",
                    "emergency_services_needed": False,
                    "estimated_exposure": 10000.00,
                    "flags": ["BI"]
                },
                "location": "Main & 5th",
                "workload_info": None
            }
        },
        # Step 7: Send claim acknowledgment to claimant
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-445524",
                "recipient_info": {
                    "name": "Unknown",
                    "email": None,
                    "phone": None
                },
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "Your auto claim (2026-445524) has been created and assigned to a BI adjuster. We will contact you soon with next steps."
            }
        },
        # Step 8: Signal successful claim intake
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Claim created, BI adjuster assigned, acknowledgment sent.",
                "result_data": {
                    "claim_number": "2026-445524",
                    "claim_status": "created",
                    "assigned_team": "BI adjuster",
                    "customer_acknowledgment_status": "sent"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Loss details extracted (auto, multiple injuries)",
            "expected_state": {
                "loss_details": "complete",
                "injuries": [
                    "back pain",
                    "shoulder pain"
                ]
            }
        },
        {
            "step": 2,
            "description": "Claim classified as auto liability",
            "expected_state": {
                "claim_type": "auto",
                "sub_type": "liability"
            }
        },
        {
            "step": 3,
            "description": "Policy coverage validated (active, liability covered)",
            "expected_state": {
                "coverage_confirmed": True,
                "policy_status": "active"
            }
        },
        {
            "step": 4,
            "description": "Claim severity assessed (BI flag)",
            "expected_state": {
                "severity_level": "standard",
                "flags": [
                    "BI"
                ]
            }
        },
        {
            "step": 5,
            "description": "Claim record created with injury flag",
            "expected_state": {
                "claim_status": "created",
                "flags": [
                    "BI"
                ]
            }
        },
        {
            "step": 6,
            "description": "Claim routed to BI adjuster",
            "expected_state": {
                "assigned_team": "BI adjuster",
                "assignment_status": "assigned"
            }
        },
        {
            "step": 7,
            "description": "Claim acknowledgment sent to claimant",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "acknowledgment"
            }
        }
    ]

    description = "Tests agent's ability to process multiple injury details and route accordingly."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the standard auto accident with bodily injury workflow. "
        "Although there are multiple injuries, the workflow remains straightforward with clear coverage, "
        "no ambiguity, and no escalation or error handling required. All systems are available and inputs are complete."
    )

class TestCase5_InsuranceClaimsIntakeAndTriageAgent_W3_medium(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """Catastrophe Event – Batch Processing, Emergencies Flagged
    
    Covers batch intake for hurricane event, mixture of emergencies and standard claims, all coverage confirmed.
    """

    test_case_id = "InsuranceClaimsIntakeAndTriageAgent_W3_TC1"
    title = "Catastrophe Event – Batch Processing, Emergencies Flagged"
    workflow = "W3"
    input_data = {
        "catastrophe_event": True,
        "batch_size": 3,
        "source_text": [
            "Hurricane wind blew off roof, major water damage at 22 Bay Rd, Miami, FL.",
            "Fence destroyed by fallen tree, minor damage at 11 Pine St, Miami, FL.",
            "Basement flooding, urgent help needed at 99 Ocean Blvd, Miami, FL."
        ],
        "policy_number": [
            "HO-111111",
            "HO-222222",
            "HO-333333"
        ],
        "claim_type": [
            "property",
            "property",
            "property"
        ],
        "severity": [
            "emergency",
            "standard",
            "emergency"
        ],
        "injury_reported": [
            False,
            False,
            False
        ],
        "policy_status": [
            "active",
            "active",
            "active"
        ],
        "coverage_confirmed": [
            True,
            True,
            True
        ],
        "business_interruption": [
            False,
            False,
            False
        ],
        "duplicate_claim_found": [
            False,
            False,
            False
        ],
        "data_incomplete": [
            False,
            False,
            False
        ]
    }
    expected_tool_calls = [
        # Step 1: Batch loss details extracted for all claims
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Hurricane wind blew off roof, major water damage at 22 Bay Rd, Miami, FL."
            }
        },
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Fence destroyed by fallen tree, minor damage at 11 Pine St, Miami, FL."
            }
        },
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Basement flooding, urgent help needed at 99 Ocean Blvd, Miami, FL."
            }
        },
        # Step 2: Each claim classified by type
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": "<extracted_loss_details_1>"
            }
        },
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": "<extracted_loss_details_2>"
            }
        },
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": "<extracted_loss_details_3>"
            }
        },
        # Step 3: Batch policy coverage validated
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "HO-111111",
                "date_of_loss": "<date_of_loss_1>",
                "peril": "<peril_1>"
            }
        },
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "HO-222222",
                "date_of_loss": "<date_of_loss_2>",
                "peril": "<peril_2>"
            }
        },
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "HO-333333",
                "date_of_loss": "<date_of_loss_3>",
                "peril": "<peril_3>"
            }
        },
        # Step 4: Severity assessed; emergencies flagged
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": "<extracted_loss_details_1>",
                "coverage_info": "<coverage_info_1>"
            }
        },
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": "<extracted_loss_details_2>",
                "coverage_info": "<coverage_info_2>"
            }
        },
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": "<extracted_loss_details_3>",
                "coverage_info": "<coverage_info_3>"
            }
        },
        # Step 5: Bulk claim records created, CAT event tagged
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": "<extracted_loss_details_1>",
                "claim_type": "property",
                "coverage_info": "<coverage_info_1>",
                "severity_info": "<severity_info_1>"
            }
        },
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": "<extracted_loss_details_2>",
                "claim_type": "property",
                "coverage_info": "<coverage_info_2>",
                "severity_info": "<severity_info_2>"
            }
        },
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": "<extracted_loss_details_3>",
                "claim_type": "property",
                "coverage_info": "<coverage_info_3>",
                "severity_info": "<severity_info_3>"
            }
        },
        # Step 6: All claims routed to CAT team, emergencies prioritized
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-445525",
                "claim_type": "property",
                "severity_info": "<severity_info_1>",
                "location": "<location_1>"
            }
        },
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-445526",
                "claim_type": "property",
                "severity_info": "<severity_info_2>",
                "location": "<location_2>"
            }
        },
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-445527",
                "claim_type": "property",
                "severity_info": "<severity_info_3>",
                "location": "<location_3>"
            }
        },
        # Step 7: Emergency vendors dispatched for flagged claims (emergencies only)
        {
            "name": "trigger_emergency_services",
            "tool_inputs": {
                "claim_number": "2026-445525",
                "emergency_type": "water_mitigation",
                "location": "<location_1>",
                "vendor_network": "ServiceMaster"
            }
        },
        {
            "name": "trigger_emergency_services",
            "tool_inputs": {
                "claim_number": "2026-445527",
                "emergency_type": "water_mitigation",
                "location": "<location_3>",
                "vendor_network": "ServiceMaster"
            }
        },
        # Step 8: Batch claim acknowledgment sent to claimants
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-445525",
                "recipient_info": "<recipient_info_1>",
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "Your claim 2026-445525 has been created and routed to the CAT team."
            }
        },
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-445526",
                "recipient_info": "<recipient_info_2>",
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "Your claim 2026-445526 has been created and routed to the CAT team."
            }
        },
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-445527",
                "recipient_info": "<recipient_info_3>",
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "Your claim 2026-445527 has been created and routed to the CAT team."
            }
        },
        # Step 9: Signal successful batch processing
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "All claims processed successfully. Emergencies prioritized, CAT team assigned, notifications sent.",
                "result_data": {
                    "claim_number": [
                        "2026-445525",
                        "2026-445526",
                        "2026-445527"
                    ],
                    "claim_status": [
                        "created",
                        "created",
                        "created"
                    ],
                    "assigned_team": [
                        "CAT team",
                        "CAT team",
                        "CAT team"
                    ],
                    "customer_acknowledgment_status": [
                        "sent",
                        "sent",
                        "sent"
                    ]
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Batch loss details extracted for all claims",
            "expected_state": {
                "loss_details": "complete",
                "batch_size": 3
            }
        },
        {
            "step": 2,
            "description": "Each claim classified by type",
            "expected_state": {
                "claim_type": [
                    "property",
                    "property",
                    "property"
                ]
            }
        },
        {
            "step": 3,
            "description": "Batch policy coverage validated",
            "expected_state": {
                "coverage_confirmed": [
                    True,
                    True,
                    True
                ]
            }
        },
        {
            "step": 4,
            "description": "Severity assessed; emergencies flagged",
            "expected_state": {
                "severity_level": [
                    "emergency",
                    "standard",
                    "emergency"
                ]
            }
        },
        {
            "step": 5,
            "description": "Bulk claim records created, CAT event tagged",
            "expected_state": {
                "claim_status": [
                    "created",
                    "created",
                    "created"
                ],
                "flags": [
                    "catastrophe"
                ]
            }
        },
        {
            "step": 6,
            "description": "All claims routed to CAT team, emergencies prioritized",
            "expected_state": {
                "assigned_team": [
                    "CAT team",
                    "CAT team",
                    "CAT team"
                ]
            }
        },
        {
            "step": 7,
            "description": "Emergency vendors dispatched for flagged claims",
            "expected_state": {
                "dispatch_status": [
                    "dispatched",
                    None,
                    "dispatched"
                ]
            }
        },
        {
            "step": 8,
            "description": "Batch claim acknowledgment sent to claimants",
            "expected_state": {
                "delivery_status": [
                    "sent",
                    "sent",
                    "sent"
                ]
            }
        }
    ]
    description = (
        "Covers batch intake for hurricane event, mixture of emergencies and standard claims, "
        "all coverage confirmed. Emergency claims trigger vendor dispatch; standard claims routed "
        "without emergency vendor. All routed to CAT team."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This scenario involves batch processing, conditional emergency prioritization, and parallel claim flows. "
        "It requires handling multiple claims with different severities in a single event, ensuring correct routing, "
        "vendor dispatch for emergencies, and bulk acknowledgment—all while maintaining atomicity and correct mapping "
        "of outputs. The logic is more complex than single-claim workflows but does not involve intricate failure handling."
    )

class TestCase6_InsuranceClaimsIntakeAndTriageAgent_W4_easy(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """Workers Comp Claim – Lost Time Injury, Medical Dispatch"""

    test_case_id = "InsuranceClaimsIntakeAndTriageAgent_W4_TC1"
    title = "Workers Comp Claim – Lost Time Injury, Medical Dispatch"
    workflow = "W4"

    input_data = {
        "source_text": "Employee slipped on wet floor, sprained ankle, unable to work.",
        "policy_number": "WC-777888",
        "claim_type": "workers_comp",
        "severity": "standard",
        "injury_reported": True,
        "policy_status": "active",
        "coverage_confirmed": True,
        "business_interruption": False,
        "duplicate_claim_found": False,
        "data_incomplete": False
    }

    expected_tool_calls = [
        # Step 1: Extract loss details from FNOL submission
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Employee slipped on wet floor, sprained ankle, unable to work."
            }
        },
        # Step 2: Classify claim as workers comp
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-01",
                    "location": "Workplace",
                    "cause": "slip/fall at work",
                    "injuries": ["sprained ankle"],
                    "damages": [],
                    "policy_number": "WC-777888",
                    "claimant_name": "Employee",
                    "contact_info": {
                        "email": "employee@example.com",
                        "phone": "+15551234567"
                    }
                }
            }
        },
        # Step 3: Validate WC policy and class code
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "WC-777888",
                "date_of_loss": "2026-04-01",
                "peril": "injury"
            }
        },
        # Step 4: Assess severity (lost time, medical needs)
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-01",
                    "location": "Workplace",
                    "cause": "slip/fall at work",
                    "injuries": ["sprained ankle"],
                    "damages": [],
                    "policy_number": "WC-777888",
                    "claimant_name": "Employee",
                    "contact_info": {
                        "email": "employee@example.com",
                        "phone": "+15551234567"
                    }
                },
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {
                        "medical": 100000,
                        "indemnity": 50000
                    }
                }
            }
        },
        # Step 5: Create WC claim record
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-01",
                    "location": "Workplace",
                    "cause": "slip/fall at work",
                    "injuries": ["sprained ankle"],
                    "damages": [],
                    "policy_number": "WC-777888",
                    "claimant_name": "Employee",
                    "contact_info": {
                        "email": "employee@example.com",
                        "phone": "+15551234567"
                    }
                },
                "claim_type": "workers_comp",
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {
                        "medical": 100000,
                        "indemnity": 50000
                    }
                },
                "severity_info": {
                    "severity_level": "standard",
                    "emergency_services_needed": True,
                    "estimated_exposure": 3500.00,
                    "flags": []
                }
            }
        },
        # Step 6: Route to WC adjuster and indemnity specialist
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-WC-1123",
                "claim_type": "workers_comp",
                "severity_info": {
                    "severity_level": "standard",
                    "emergency_services_needed": True,
                    "estimated_exposure": 3500.00,
                    "flags": []
                },
                "location": "Workplace"
            }
        },
        # Step 7: Trigger medical provider dispatch (nurse case manager)
        {
            "name": "trigger_emergency_services",
            "tool_inputs": {
                "claim_number": "2026-WC-1123",
                "emergency_type": "medical",
                "location": "Workplace",
                "vendor_network": "LocalVendor"
            }
        },
        # Step 8: Send claim acknowledgment to employee
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-WC-1123",
                "recipient_info": {
                    "name": "Employee",
                    "email": "employee@example.com",
                    "phone": "+15551234567"
                },
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "Your workers comp claim has been created. Claim #: 2026-WC-1123. Medical provider dispatch initiated. Your assigned adjuster will contact you soon."
            }
        },
        # Step 9: Signal successful intake
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Workers comp claim created, medical management initiated, adjuster assigned, employee notified.",
                "result_data": {
                    "claim_number": "2026-WC-1123",
                    "claim_status": "created",
                    "assigned_team": "WC adjuster",
                    "customer_acknowledgment_status": "sent"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Loss details extracted (occupational injury)",
            "expected_state": {
                "loss_details": "complete",
                "injuries": [
                    "sprained ankle"
                ]
            }
        },
        {
            "step": 2,
            "description": "Claim classified as workers comp",
            "expected_state": {
                "claim_type": "workers_comp"
            }
        },
        {
            "step": 3,
            "description": "WC policy validated",
            "expected_state": {
                "coverage_confirmed": True,
                "policy_status": "active"
            }
        },
        {
            "step": 4,
            "description": "Severity assessed (medical management needed)",
            "expected_state": {
                "severity_level": "standard",
                "emergency_services_needed": True
            }
        },
        {
            "step": 5,
            "description": "Claim record created",
            "expected_state": {
                "claim_status": "created"
            }
        },
        {
            "step": 6,
            "description": "Claim routed to WC adjuster",
            "expected_state": {
                "assigned_team": "WC adjuster",
                "assignment_status": "assigned"
            }
        },
        {
            "step": 7,
            "description": "Medical provider dispatched (nurse case manager)",
            "expected_state": {
                "dispatch_status": "dispatched",
                "emergency_type": "medical"
            }
        },
        {
            "step": 8,
            "description": "Claim acknowledgment sent to employee",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "acknowledgment"
            }
        }
    ]

    description = "Covers workers comp claim with occupational injury, lost time, medical management initiation."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the standard workers compensation lost time injury workflow with all required data present, "
        "no ambiguous or missing information, and no system or coverage failures. No escalation or error handling is needed. "
        "Medical management and WC adjuster routing are triggered as expected."
    )

class TestCase7_InsuranceClaimsIntakeAndTriageAgent_W5_medium(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """Attorney-Represented Slip & Fall – Liability, Legal Notification

    Covers attorney-represented liability claim, triggers legal notification and document preservation.
    """

    test_case_id = "InsuranceClaimsIntakeAndTriageAgent_W5_TC1"
    title = "Attorney-Represented Slip & Fall – Liability, Legal Notification"
    workflow = "W5"
    input_data = {
        "source_text": "Our client, Jane Doe, slipped on wet floor at your store on 5/12/2026 and sustained injuries. We represent her.",
        "policy_number": "GL-334455",
        "claim_type": "liability",
        "severity": "litigation",
        "attorney_represented": True,
        "policy_status": "active",
        "coverage_confirmed": True,
        "business_interruption": False,
        "duplicate_claim_found": False,
        "data_incomplete": False
    }
    expected_tool_calls = [
        # Step 1: Extract loss details from attorney letter
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Our client, Jane Doe, slipped on wet floor at your store on 5/12/2026 and sustained injuries. We represent her."
            }
        },
        # Step 2: Classify claim as general liability
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-05-12",
                    "location": "Insured Store",
                    "cause": "slip and fall",
                    "injuries": ["injury (details unknown)"],
                    "damages": [],
                    "policy_number": "GL-334455",
                    "claimant_name": "Jane Doe",
                    "contact_info": {
                        "email": "jane.doe@example.com",
                        "phone": "+15551234567"
                    }
                }
            }
        },
        # Step 3: Validate commercial GL policy and premises coverage
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "GL-334455",
                "date_of_loss": "2026-05-12",
                "peril": "liability"
            }
        },
        # Step 4: Assess claim severity (attorney, litigation risk)
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-05-12",
                    "location": "Insured Store",
                    "cause": "slip and fall",
                    "injuries": ["injury (details unknown)"],
                    "damages": [],
                    "policy_number": "GL-334455",
                    "claimant_name": "Jane Doe",
                    "contact_info": {
                        "email": "jane.doe@example.com",
                        "phone": "+15551234567"
                    }
                },
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {"GL": 1000000}
                }
            }
        },
        # Step 5: Create GL claim record with litigation flag
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-05-12",
                    "location": "Insured Store",
                    "cause": "slip and fall",
                    "injuries": ["injury (details unknown)"],
                    "damages": [],
                    "policy_number": "GL-334455",
                    "claimant_name": "Jane Doe",
                    "contact_info": {
                        "email": "jane.doe@example.com",
                        "phone": "+15551234567"
                    }
                },
                "claim_type": "liability",
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {"GL": 1000000}
                },
                "severity_info": {
                    "severity_level": "litigation",
                    "emergency_services_needed": False,
                    "estimated_exposure": 50000,
                    "flags": ["attorney", "litigation"]
                }
            }
        },
        # Step 6: Route to senior liability adjuster, notify legal team
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-GL-9988",
                "claim_type": "liability",
                "severity_info": {
                    "severity_level": "litigation",
                    "emergency_services_needed": False,
                    "estimated_exposure": 50000,
                    "flags": ["attorney", "litigation"]
                },
                "location": "Insured Store"
            }
        },
        # Step 7: Send document preservation request to insured
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-GL-9988",
                "recipient_info": {
                    "name": "Insured Representative",
                    "email": "insured@example.com",
                    "phone": "+15557654321"
                },
                "message_type": "attorney_notification",
                "delivery_method": "email",
                "content": "Legal hold: Please preserve all surveillance, incident reports, and communications related to the slip and fall incident on 5/12/2026."
            }
        },
        # Step 8: Send claim acknowledgment to attorney
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-GL-9988",
                "recipient_info": {
                    "name": "Jane Doe's Attorney",
                    "email": "attorney@example.com",
                    "phone": "+15559887766"
                },
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "We acknowledge receipt of your client's claim regarding the slip and fall incident on 5/12/2026. Claim number: 2026-GL-9988. A senior liability adjuster will contact you."
            }
        },
        # Step 9: Signal successful intake
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "GL claim created, legal notified, document preservation sent, attorney acknowledged.",
                "result_data": {
                    "claim_number": "2026-GL-9988",
                    "claim_status": "created",
                    "assigned_team": "Senior liability adjuster",
                    "customer_acknowledgment_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Loss details extracted (attorney letter, injury details)",
            "expected_state": {
                "loss_details": "complete",
                "attorney_represented": True
            }
        },
        {
            "step": 2,
            "description": "Claim classified as liability",
            "expected_state": {
                "claim_type": "liability",
                "sub_type": "slip and fall"
            }
        },
        {
            "step": 3,
            "description": "GL policy and premises coverage validated",
            "expected_state": {
                "coverage_confirmed": True,
                "policy_status": "active"
            }
        },
        {
            "step": 4,
            "description": "Severity assessed (litigation risk flagged)",
            "expected_state": {
                "severity_level": "litigation",
                "flags": [
                    "attorney",
                    "litigation"
                ]
            }
        },
        {
            "step": 5,
            "description": "GL claim record created with litigation flag",
            "expected_state": {
                "claim_status": "created",
                "flags": [
                    "litigation"
                ]
            }
        },
        {
            "step": 6,
            "description": "Claim routed to senior liability adjuster, legal team notified",
            "expected_state": {
                "assigned_team": "Senior liability adjuster",
                "assignment_status": "assigned"
            }
        },
        {
            "step": 7,
            "description": "Document preservation request sent to insured",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "attorney_notification"
            }
        },
        {
            "step": 8,
            "description": "Claim acknowledgment sent to attorney",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "acknowledgment"
            }
        }
    ]
    description = (
        "Covers attorney-represented liability claim, triggers legal notification and document preservation."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "Involves attorney representation, litigation risk, legal team notification, and multiple specialized notifications. "
        "Requires strict workflow adherence and correct routing/flagging for legal/regulatory compliance."
    )

class TestCase8_InsuranceClaimsIntakeAndTriageAgent_W6_easy(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """Denied Claim – Policy Lapsed, Coverage Not Confirmed"""

    test_case_id = "ClaimsAgent_W6_TC1"
    title = "Denied Claim – Policy Lapsed, Coverage Not Confirmed"
    workflow = "W6"
    input_data = {
        "source_text": "Tree branch broke window during windstorm. Need to file claim.",
        "policy_number": "HO-555666",
        "claim_type": "property",
        "severity": "denied",
        "policy_status": "lapsed",
        "coverage_confirmed": False,
        "business_interruption": False,
        "duplicate_claim_found": False,
        "data_incomplete": False
    }
    expected_tool_calls = [
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Tree branch broke window during windstorm. Need to file claim."
            }
        },
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-18",
                    "location": "123 Main St, Springfield, IL",
                    "cause": "windstorm",
                    "injuries": [],
                    "damages": ["window"],
                    "policy_number": "HO-555666",
                    "claimant_name": "John Doe",
                    "contact_info": {
                        "email": "john.doe@email.com",
                        "phone": "+12175551234"
                    }
                }
            }
        },
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "HO-555666",
                "date_of_loss": "2026-04-18",
                "peril": "windstorm"
            }
        },
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-18",
                    "location": "123 Main St, Springfield, IL",
                    "cause": "windstorm",
                    "injuries": [],
                    "damages": ["window"],
                    "policy_number": "HO-555666",
                    "claimant_name": "John Doe",
                    "contact_info": {
                        "email": "john.doe@email.com",
                        "phone": "+12175551234"
                    }
                },
                "coverage_info": {
                    "coverage_confirmed": False,
                    "policy_status": "lapsed",
                    "coverage_limits": {},
                    "denial_reason": "Policy is lapsed as of date of loss"
                }
            }
        },
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-18",
                    "location": "123 Main St, Springfield, IL",
                    "cause": "windstorm",
                    "injuries": [],
                    "damages": ["window"],
                    "policy_number": "HO-555666",
                    "claimant_name": "John Doe",
                    "contact_info": {
                        "email": "john.doe@email.com",
                        "phone": "+12175551234"
                    }
                },
                "claim_type": "property",
                "coverage_info": {
                    "coverage_confirmed": False,
                    "policy_status": "lapsed",
                    "coverage_limits": {},
                    "denial_reason": "Policy is lapsed as of date of loss"
                },
                "severity_info": {
                    "severity_level": "denied",
                    "emergency_services_needed": False,
                    "estimated_exposure": 0.0,
                    "flags": ["denied"]
                }
            }
        },
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-445528",
                "recipient_info": {
                    "name": "John Doe",
                    "email": "john.doe@email.com",
                    "phone": "+12175551234"
                },
                "message_type": "denial",
                "delivery_method": "email",
                "content": (
                    "Dear John Doe, your claim for policy HO-555666 has been denied due to lapsed policy status as of 2026-04-18. "
                    "If you have questions regarding this decision, please contact our support team."
                )
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Claim intake completed: denied due to lapsed policy, customer notified.",
                "result_data": {
                    "claim_number": "2026-445528",
                    "claim_status": "denied",
                    "customer_acknowledgment_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Loss details extracted (property, windstorm)",
            "expected_state": {
                "loss_details": "complete",
                "cause": "windstorm"
            }
        },
        {
            "step": 2,
            "description": "Claim classified as property",
            "expected_state": {
                "claim_type": "property"
            }
        },
        {
            "step": 3,
            "description": "Policy status and coverage validated (lapsed, not covered)",
            "expected_state": {
                "coverage_confirmed": False,
                "policy_status": "lapsed"
            }
        },
        {
            "step": 4,
            "description": "Severity assessed (denied flag)",
            "expected_state": {
                "severity_level": "denied",
                "flags": [
                    "denied"
                ]
            }
        },
        {
            "step": 5,
            "description": "Claim record created as denied",
            "expected_state": {
                "claim_status": "denied"
            }
        },
        {
            "step": 6,
            "description": "Coverage denial letter sent to customer",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "denial"
            }
        }
    ]
    description = "Covers claim for lapsed policy, triggers denial letter and regulatory documentation."
    difficulty = "easy"
    difficulty_reasoning = (
        "The workflow is straightforward: policy is lapsed and coverage not confirmed, "
        "so the claim is processed as denied without branching, escalation, or emergency handling. "
        "All tool invocations follow the standard denied-claim path."
    )

class TestCase9_InsuranceClaimsIntakeAndTriageAgent_W7_easy(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """
    Duplicate Claim – FNOL Already Reported, Link and Notify

    Covers scenario where FNOL matches existing claim, links communication and notifies customer.
    """

    test_case_id = "InsuranceClaimsIntakeAndTriageAgent_W7_TC1"
    title = "Duplicate Claim – FNOL Already Reported, Link and Notify"
    workflow = "W7"
    input_data = {
        "source_text": "Following up on my previous claim for roof damage after last week's storm.",
        "policy_number": "HO-112233",
        "claim_type": "property",
        "severity": "standard",
        "duplicate_claim_found": True,
        "policy_status": "active",
        "coverage_confirmed": True,
        "business_interruption": False,
        "data_incomplete": False
    }
    expected_tool_calls = [
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Following up on my previous claim for roof damage after last week's storm."
            }
        },
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-10",
                    "location": "123 Main St, Springfield, IL",
                    "cause": "storm",
                    "injuries": [],
                    "damages": ["roof damage"],
                    "policy_number": "HO-112233",
                    "claimant_name": "John Doe",
                    "contact_info": {
                        "email": "johndoe@email.com",
                        "phone": "+12175551234"
                    }
                }
            }
        },
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-04-10",
                    "location": "123 Main St, Springfield, IL",
                    "cause": "storm",
                    "injuries": [],
                    "damages": ["roof damage"],
                    "policy_number": "HO-112233",
                    "claimant_name": "John Doe",
                    "contact_info": {
                        "email": "johndoe@email.com",
                        "phone": "+12175551234"
                    }
                },
                "claim_type": "property",
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {
                        "dwelling": 250000,
                        "personal_property": 100000
                    }
                },
                "severity_info": {
                    "severity_level": "standard",
                    "emergency_services_needed": False,
                    "estimated_exposure": 8000.00,
                    "flags": ["duplicate"]
                }
            }
        },
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-445521",
                "recipient_info": {
                    "name": "John Doe",
                    "email": "johndoe@email.com",
                    "phone": "+12175551234"
                },
                "message_type": "duplicate_notification",
                "delivery_method": "email",
                "content": "We have received your follow-up regarding your previous claim for roof damage. This submission has been linked to your existing claim #2026-445521. No additional action is required at this time. If you have new information, please reply to this email or call your adjuster."
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Duplicate FNOL linked to original claim and customer notified.",
                "result_data": {
                    "claim_number": "2026-445521",
                    "claim_status": "duplicate",
                    "customer_acknowledgment_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Loss details extracted (property, roof damage)",
            "expected_state": {
                "loss_details": "complete"
            }
        },
        {
            "step": 2,
            "description": "Claim type checked for duplication",
            "expected_state": {
                "duplicate_claim_found": True
            }
        },
        {
            "step": 3,
            "description": "Communication linked to existing claim",
            "expected_state": {
                "claim_status": "duplicate",
                "linked_claims": [
                    "2026-445521"
                ]
            }
        },
        {
            "step": 4,
            "description": "Duplicate notification sent to customer",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "duplicate_notification"
            }
        }
    ]
    description = "Covers scenario where FNOL matches existing claim, links communication and notifies customer."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows a straightforward duplicate claim workflow: extraction, classification, linking, and notification. "
        "No ambiguous data, escalation, or error handling is required. The path is direct because the duplicate is detected and all data is complete."
    )

class TestCase10_InsuranceClaimsIntakeAndTriageAgent_W8_hard(BaseInsuranceClaimsIntakeAndTriageAgentTestCase):
    """
    Complex Commercial Property Claim – Business Interruption, Large Loss
    """

    test_case_id = "InsuranceClaimsIntakeAndTriageAgent_W8_TC1"
    title = "Complex Commercial Property Claim – Business Interruption, Large Loss"
    workflow = "W8"
    input_data = {
        "source_text": "Fire in warehouse disrupted operations, lost inventory and halted business.",
        "policy_number": "CP-445566",
        "claim_type": "commercial_property",
        "severity": "large_loss",
        "business_interruption": True,
        "policy_status": "active",
        "coverage_confirmed": True,
        "duplicate_claim_found": False,
        "data_incomplete": False
    }
    expected_tool_calls = [
        {
            "name": "extract_loss_details",
            "tool_inputs": {
                "source_text": "Fire in warehouse disrupted operations, lost inventory and halted business."
            }
        },
        {
            "name": "classify_claim_type",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-03-15",
                    "location": "Warehouse, Chicago, IL",
                    "cause": "fire",
                    "injuries": [],
                    "damages": ["inventory loss", "business interruption"],
                    "policy_number": "CP-445566",
                    "claimant_name": "Acme Corp",
                    "contact_info": {
                        "email": "claims@acmecorp.com",
                        "phone": "+13125551234"
                    }
                }
            }
        },
        {
            "name": "validate_policy_coverage",
            "tool_inputs": {
                "policy_number": "CP-445566",
                "date_of_loss": "2026-03-15",
                "peril": "fire"
            }
        },
        {
            "name": "assess_claim_severity",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-03-15",
                    "location": "Warehouse, Chicago, IL",
                    "cause": "fire",
                    "injuries": [],
                    "damages": ["inventory loss", "business interruption"],
                    "policy_number": "CP-445566",
                    "claimant_name": "Acme Corp",
                    "contact_info": {
                        "email": "claims@acmecorp.com",
                        "phone": "+13125551234"
                    }
                },
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {
                        "property_limit": 1000000.0,
                        "bi_limit": 500000.0
                    }
                }
            }
        },
        {
            "name": "create_claim_record",
            "tool_inputs": {
                "loss_details": {
                    "date_of_loss": "2026-03-15",
                    "location": "Warehouse, Chicago, IL",
                    "cause": "fire",
                    "injuries": [],
                    "damages": ["inventory loss", "business interruption"],
                    "policy_number": "CP-445566",
                    "claimant_name": "Acme Corp",
                    "contact_info": {
                        "email": "claims@acmecorp.com",
                        "phone": "+13125551234"
                    }
                },
                "claim_type": "commercial_property",
                "coverage_info": {
                    "coverage_confirmed": True,
                    "policy_status": "active",
                    "coverage_limits": {
                        "property_limit": 1000000.0,
                        "bi_limit": 500000.0
                    }
                },
                "severity_info": {
                    "severity_level": "large_loss",
                    "emergency_services_needed": True,
                    "estimated_exposure": 700000.0,
                    "flags": ["BI"]
                }
            }
        },
        {
            "name": "route_to_adjuster",
            "tool_inputs": {
                "claim_number": "2026-CP-7788",
                "claim_type": "commercial_property",
                "severity_info": {
                    "severity_level": "large_loss",
                    "emergency_services_needed": True,
                    "estimated_exposure": 700000.0,
                    "flags": ["BI"]
                },
                "location": "Warehouse, Chicago, IL"
            }
        },
        {
            "name": "trigger_emergency_services",
            "tool_inputs": {
                "claim_number": "2026-CP-7788",
                "emergency_type": "salvage",
                "location": "Warehouse, Chicago, IL",
                "vendor_network": "ServiceMaster"
            }
        },
        {
            "name": "send_claim_acknowledgment",
            "tool_inputs": {
                "claim_number": "2026-CP-7788",
                "recipient_info": {
                    "name": "Acme Corp",
                    "email": "claims@acmecorp.com",
                    "phone": "+13125551234"
                },
                "message_type": "acknowledgment",
                "delivery_method": "email",
                "content": "Your claim 2026-CP-7788 has been created and assigned to the Large loss unit. Forensic accountant and engineer have been dispatched. Business Interruption claim 2026-BI-7788 is linked."
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Complex commercial property and BI claims created, routed, and acknowledged.",
                "result_data": {
                    "claim_number": "2026-CP-7788",
                    "claim_status": "created",
                    "assigned_team": "Large loss unit",
                    "customer_acknowledgment_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Loss details extracted (fire, business interruption)",
            "expected_state": {
                "loss_details": "complete",
                "cause": "fire"
            }
        },
        {
            "step": 2,
            "description": "Claim classified as commercial property + BI",
            "expected_state": {
                "claim_type": "commercial_property",
                "sub_type": "business_interruption"
            }
        },
        {
            "step": 3,
            "description": "Property and BI coverage validated",
            "expected_state": {
                "coverage_confirmed": True,
                "policy_status": "active"
            }
        },
        {
            "step": 4,
            "description": "Severity assessed (large loss, BI exposure)",
            "expected_state": {
                "severity_level": "large_loss",
                "flags": [
                    "BI"
                ]
            }
        },
        {
            "step": 5,
            "description": "Linked claims created for property and BI",
            "expected_state": {
                "claim_status": "created",
                "linked_claims": [
                    "2026-CP-7788",
                    "2026-BI-7788"
                ]
            }
        },
        {
            "step": 6,
            "description": "Claim routed to large loss unit and BI specialist",
            "expected_state": {
                "assigned_team": "Large loss unit",
                "assignment_status": "assigned"
            }
        },
        {
            "step": 7,
            "description": "Forensic accountant and engineer dispatched",
            "expected_state": {
                "dispatch_status": "dispatched",
                "emergency_type": "salvage"
            }
        },
        {
            "step": 8,
            "description": "Claim acknowledgment sent to insured",
            "expected_state": {
                "delivery_status": "sent",
                "message_type": "acknowledgment"
            }
        }
    ]
    description = (
        "Covers large commercial property claim with business interruption, "
        "triggers specialists and linked claims. Linked claims are created for "
        "property and BI; forensic accountant and engineer are dispatched. "
        "Claim is routed to large loss unit and acknowledgment sent to insured."
    )
    difficulty = "hard"
    difficulty_reasoning = (
        "This scenario involves multi-claim linkage (property + business interruption), "
        "specialist engagement (forensic accountant, engineer), complex routing to a large loss team, "
        "and requires coordination of multiple outputs and notifications. It tests the agent's ability "
        "to handle high-severity, multi-faceted commercial claims with BI exposure and specialist dispatch."
    )