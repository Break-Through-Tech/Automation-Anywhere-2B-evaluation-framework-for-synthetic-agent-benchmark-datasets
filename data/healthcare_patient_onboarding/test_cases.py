from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict
from system_tools_base import SystemToolsBaseClass

# --- TypedDict Definitions ---

class Demographics(TypedDict):
    """Demographic object containing: name (string), dob (ISO 8601), ssn (string, format XXX-XX-XXXX), address (string), phone (string, E.164), email (string, valid email format)"""
    name: str
    dob: str
    ssn: str
    address: str
    phone: str
    email: str

class InsuranceInfo(TypedDict):
    """Insurance object: carrier (string), policy_number (string), group_number (string), subscriber_name (string), subscriber_relationship (enum: self, parent, spouse, guardian, other)"""
    carrier: str
    policy_number: str
    group_number: str
    subscriber_name: str
    subscriber_relationship: str

class Eligibility(TypedDict, total=False):
    """Eligibility object: status (enum: active, inactive, terminated, pending), copay (number, USD), deductible (number, USD), deductible_met (number, USD), prior_auth_required (boolean), termination_date (ISO 8601, optional)"""
    status: str
    copay: Optional[float]
    deductible: Optional[float]
    deductible_met: Optional[float]
    prior_auth_required: Optional[bool]
    termination_date: Optional[str]

class Medication(TypedDict):
    """Medication object: name (string), dose (string)"""
    name: str
    dose: str

class MedicalHistory(TypedDict, total=False):
    """Medical history object: allergies (array of strings), medications (array of objects: name (string), dose (string)), conditions (array of strings), immunizations (array of strings), surgical_history (array of strings)"""
    allergies: List[str]
    medications: List[Medication]
    conditions: List[str]
    immunizations: List[str]
    surgical_history: List[str]

class PatientRecord(TypedDict):
    """Patient record object: patient_id (string), status (enum: created, updated, merged), ehr_system (string), timestamp (ISO 8601)"""
    patient_id: str
    status: str
    ehr_system: str
    timestamp: str

class Slot(TypedDict):
    """Appointment slot object: date (ISO 8601), time (HH:MM), duration (integer, minutes)"""
    date: str
    time: str
    duration: int

class AvailabilitySlot(TypedDict):
    """Availability slot for provider: date (ISO 8601), time (HH:MM), duration (integer, minutes)"""
    date: str
    time: str
    duration: int

class Availability(TypedDict):
    """Availability object: slots (array of slot objects), provider_id (string)"""
    slots: List[AvailabilitySlot]
    provider_id: str

class Appointment(TypedDict):
    """Appointment object: appointment_id (string), status (enum: scheduled, confirmed), slot (object), provider_id (string), patient_id (string)"""
    appointment_id: str
    status: str
    slot: Slot
    provider_id: str
    patient_id: str

class CommunicationStatus(TypedDict, total=False):
    """Confirmation object: message_id (string), delivery_status (enum: sent, queued, failed), timestamp (ISO 8601), estimated_delivery (ISO 8601, optional)"""
    message_id: str
    delivery_status: str
    timestamp: str
    estimated_delivery: Optional[str]

# --- Base Test Case Class ---

class BaseHealthcarePatientOnboardingAgentTestCase(SystemToolsBaseClass):
    """
    Base class containing common methods for all Healthcare / Patient Registration test cases.
    """

    # Agent context attributes
    role = (
        "You are an automated healthcare patient onboarding agent that streamlines "
        "the registration process by extracting patient data from intake forms, verifying "
        "insurance eligibility, creating/updating EHR patient records, and scheduling initial "
        "appointments according to provider availability and patient preferences.\n"
    )
    goal = (
        "Your goal is to ensure every new patient is onboarded efficiently, with accurate "
        "demographic and insurance data, validated eligibility, and a scheduled appointment, "
        "while maintaining HIPAA compliance and minimizing manual intervention.\n"
    )
    action_plan = {
        "assumptions": [
            "All intake forms are accessible in a structured format (digital or OCR-converted).",
            "Insurance verification APIs and EHR systems are available and integrated.",
        ],
        "tools_and_resources": [
            "extract_patient_demographics",
            "extract_insurance_info",
            "verify_insurance_eligibility",
            "extract_medical_history",
            "create_ehr_patient_record",
            "check_provider_availability",
            "schedule_appointment",
            "send_patient_communication",
        ],
        "guidelines": [
            "Always validate that required demographic and insurance fields are present before proceeding.",
            "Do not create EHR records or schedule appointments until insurance eligibility is confirmed, unless patient is self-pay.",
            "Detect duplicate patient records by matching name + DOB or SSN; update/merge as needed and flag for staff review.",
            "Escalate to human-in-the-loop for insurance issues, prior authorization delays, or ambiguous duplicates.",
            "Maintain HIPAA compliance by ensuring secure data handling and access logging.",
        ],
        "workflow_selection": [
            "If all required demographics and insurance fields are present AND insurance eligibility is active",
            "If subscriber is parent/guardian AND patient age < 18",
            "If insurance eligibility check returns inactive/terminated coverage",
            "If referral for specialist AND prior authorization required",
            "If patient selects self-pay or no insurance provided",
            "If patient demographics match existing EHR record (name + DOB or SSN)",
            "If complex medical history (multiple high-risk conditions or >5 medications)",
            "If intake form is missing required fields or insurance details are illegible",
        ],
        "failure_points": [
            "Insurance eligibility API unavailable or returns error: Escalate to HUMAN_IN_THE_LOOP for manual verification or follow-up.",
            "Duplicate detection ambiguous (similar but not exact match): Escalate to HUMAN_IN_THE_LOOP for staff review and decision.",
            "Missing required demographic or insurance fields: Send request for missing data via send_patient_communication tool.",
            "Prior authorization denied or delayed beyond acceptable time: Escalate to HUMAN_IN_THE_LOOP for alternate scheduling or patient notification.",
        ],
        "success_criteria": [
            "Patient record created or updated in EHR with accurate demographics, insurance, and medical history.",
            "Insurance eligibility verified and appointment scheduled.",
            "Patient or guardian receives confirmation communication with instructions.",
            "Duplicate records merged or flagged for review; HIPAA compliance maintained.",
            "All required data fields validated and complete prior to onboarding completion.",
        ]
    }

    # --- Domain Tool Methods ---

    def extract_patient_demographics(self, form_id: str) -> Demographics:
        """
        Extracts patient name, date of birth, SSN, address, phone, and email from intake form.

        Args:
            form_id: Unique intake form identifier. Format: PAT-XXXXXX where X is alphanumeric.

        Returns:
            Demographics: Demographic object containing:
                - name (string)
                - dob (ISO 8601)
                - ssn (string, format XXX-XX-XXXX)
                - address (string)
                - phone (string, E.164)
                - email (string, valid email format)
        """
        print(f"[extract_patient_demographics] form_id={form_id}")
        # Mocked extraction for testing
        return Demographics(
            name="John Doe",
            dob="1980-01-01",
            ssn="123-45-6789",
            address="123 Main St, Springfield, IL",
            phone="+11234567890",
            email="johndoe@example.com"
        )

    def extract_insurance_info(self, form_id: str) -> InsuranceInfo:
        """
        Extracts insurance carrier, policy number, group number, subscriber name, and relationship from intake form.

        Args:
            form_id: Unique intake form identifier. Format: PAT-XXXXXX.

        Returns:
            InsuranceInfo: Insurance object:
                - carrier (string)
                - policy_number (string)
                - group_number (string)
                - subscriber_name (string)
                - subscriber_relationship (enum: self, parent, spouse, guardian, other)
        """
        print(f"[extract_insurance_info] form_id={form_id}")
        # Mocked insurance info for testing
        return InsuranceInfo(
            carrier="Blue Cross",
            policy_number="BC1234567",
            group_number="GRP890",
            subscriber_name="John Doe",
            subscriber_relationship="self"
        )

    def verify_insurance_eligibility(
        self,
        carrier: str,
        policy_number: str,
        group_number: Optional[str],
        subscriber_name: str,
        dob: str
    ) -> Eligibility:
        """
        Verifies insurance coverage status, copay, deductible, and prior authorization requirements via payer API.

        Args:
            carrier: Insurance carrier name. Must match payer system values.
            policy_number: Policy number as provided on insurance card.
            group_number: Group number as provided on insurance card. Optional for some payers.
            subscriber_name: Name of insurance subscriber (patient or guardian).
            dob: Date of birth of subscriber. ISO 8601 format (YYYY-MM-DD).

        Returns:
            Eligibility: Eligibility object:
                - status (enum: active, inactive, terminated, pending)
                - copay (number, USD)
                - deductible (number, USD)
                - deductible_met (number, USD)
                - prior_auth_required (boolean)
                - termination_date (ISO 8601, optional)
        """
        valid_status = ["active", "inactive", "terminated", "pending"]
        print(f"[verify_insurance_eligibility] carrier={carrier}, policy_number={policy_number}, group_number={group_number}, subscriber_name={subscriber_name}, dob={dob}")
        # Mocked logic
        return Eligibility(
            status="active",
            copay=30.0,
            deductible=500.0,
            deductible_met=200.0,
            prior_auth_required=False
        )

    def extract_medical_history(self, form_id: str) -> MedicalHistory:
        """
        Extracts allergies, medications, chronic conditions, immunizations, and surgical history from intake form.

        Args:
            form_id: Unique intake form identifier. Format: PAT-XXXXXX.

        Returns:
            MedicalHistory: Medical history object:
                - allergies (array of strings)
                - medications (array of objects: name (string), dose (string))
                - conditions (array of strings)
                - immunizations (array of strings)
                - surgical_history (array of strings)
        """
        print(f"[extract_medical_history] form_id={form_id}")
        # Mocked history
        return MedicalHistory(
            allergies=["Penicillin"],
            medications=[{"name": "Atorvastatin", "dose": "10mg"}],
            conditions=["Hypertension"],
            immunizations=["MMR", "Tetanus"],
            surgical_history=["Appendectomy"]
        )

    def create_ehr_patient_record(
        self,
        demographics: Demographics,
        insurance: InsuranceInfo,
        medical_history: MedicalHistory,
        existing_patient_id: Optional[str] = None
    ) -> PatientRecord:
        """
        Creates or updates patient record in EHR system with all onboarding data.

        Args:
            demographics: Patient demographic data object as returned by extract_patient_demographics.
            insurance: Insurance object as returned by extract_insurance_info and verify_insurance_eligibility.
            medical_history: Medical history object as returned by extract_medical_history.
            existing_patient_id: EHR patient ID if updating/merging record. Format: numeric or alphanumeric per EHR system. Optional.

        Returns:
            PatientRecord: Patient record object:
                - patient_id (string)
                - status (enum: created, updated, merged)
                - ehr_system (string)
                - timestamp (ISO 8601)
        """
        valid_status = ["created", "updated", "merged"]
        print(f"[create_ehr_patient_record] demographics={demographics}, insurance={insurance}, medical_history={medical_history}, existing_patient_id={existing_patient_id}")
        patient_id = existing_patient_id if existing_patient_id else "876543"
        status = "updated" if existing_patient_id else "created"
        return PatientRecord(
            patient_id=patient_id,
            status=status,
            ehr_system="Epic",
            timestamp="2024-02-10T12:00:00Z"
        )

    def check_provider_availability(
        self,
        provider_id: str,
        appointment_type: str,
        preferred_dates: Optional[List[str]] = None
    ) -> Availability:
        """
        Checks scheduling system for available appointment slots for given provider and appointment type.

        Args:
            provider_id: Unique identifier for provider. Format: PROV-XXXXXX.
            appointment_type: Type of appointment. Must be one of: annual_physical, well_child, specialty_consult, chronic_care, initial_visit, follow_up.
            preferred_dates: Preferred appointment dates. Array of ISO 8601 dates. Optional.

        Returns:
            Availability: Availability object:
                - slots (array of objects: date (ISO 8601), time (string, HH:MM), duration (integer, minutes))
                - provider_id (string)
        """
        valid_types = ["annual_physical", "well_child", "specialty_consult", "chronic_care", "initial_visit", "follow_up"]
        if appointment_type not in valid_types:
            raise ValueError(f"Invalid appointment_type: {appointment_type}. Must be one of {valid_types}")
        print(f"[check_provider_availability] provider_id={provider_id}, appointment_type={appointment_type}, preferred_dates={preferred_dates}")
        # Mocked slot selection
        slots = [AvailabilitySlot(date="2024-02-12", time="14:00", duration=30)]
        return Availability(
            slots=slots,
            provider_id=provider_id
        )

    def schedule_appointment(
        self,
        patient_id: str,
        provider_id: str,
        slot: Slot,
        appointment_type: str,
        prior_auth_number: Optional[str] = None,
        payment_type: str = "insurance"
    ) -> Appointment:
        """
        Books appointment for patient, adds to provider calendar, and triggers confirmation.

        Args:
            patient_id: Unique patient identifier. Format: numeric or alphanumeric.
            provider_id: Provider identifier. Format: PROV-XXXXXX.
            slot: Appointment slot object: date (ISO 8601), time (HH:MM), duration (integer, minutes).
            appointment_type: Type of appointment. Must match check_provider_availability. Valid values: annual_physical, well_child, specialty_consult, chronic_care, initial_visit, follow_up.
            prior_auth_number: Prior authorization number if required for appointment. Optional.
            payment_type: Payment type. Must be one of: insurance, self_pay. Default: insurance.

        Returns:
            Appointment: Appointment object:
                - appointment_id (string)
                - status (enum: scheduled, confirmed)
                - slot (object)
                - provider_id (string)
                - patient_id (string)
        """
        valid_types = ["annual_physical", "well_child", "specialty_consult", "chronic_care", "initial_visit", "follow_up"]
        valid_payments = ["insurance", "self_pay"]
        if appointment_type not in valid_types:
            raise ValueError(f"Invalid appointment_type: {appointment_type}. Must be one of {valid_types}")
        if payment_type not in valid_payments:
            raise ValueError(f"Invalid payment_type: {payment_type}. Must be one of {valid_payments}")
        print(f"[schedule_appointment] patient_id={patient_id}, provider_id={provider_id}, slot={slot}, appointment_type={appointment_type}, prior_auth_number={prior_auth_number}, payment_type={payment_type}")
        return Appointment(
            appointment_id="APPT-10001",
            status="scheduled",
            slot=slot,
            provider_id=provider_id,
            patient_id=patient_id
        )

    def send_patient_communication(
        self,
        recipient_contact: str,
        message_type: str,
        content: str,
        delivery_method: str = "email",
        attachments: Optional[List[str]] = None
    ) -> CommunicationStatus:
        """
        Sends confirmation, instructions, or requests for missing information to patient or guardian.

        Args:
            recipient_contact: Patient or guardian contact (email or phone, must be valid format).
            message_type: Type of communication to send. Valid values: confirmation, document_request, status_update, preparation_instructions, pricing_estimate, missing_information, duplicate_alert, prior_auth_notification.
            content: Message content. Length: 10-2000 characters.
            delivery_method: Preferred delivery channel. Valid values: email, sms, portal. Default: email.
            attachments: List of attachment URLs or document IDs (strings), optional.

        Returns:
            CommunicationStatus: Confirmation object:
                - message_id (string)
                - delivery_status (enum: sent, queued, failed)
                - timestamp (ISO 8601)
                - estimated_delivery (ISO 8601, optional)
        """
        valid_message_types = [
            "confirmation", "document_request", "status_update",
            "preparation_instructions", "pricing_estimate", "missing_information",
            "duplicate_alert", "prior_auth_notification"
        ]
        valid_delivery_methods = ["email", "sms", "portal"]
        if message_type not in valid_message_types:
            raise ValueError(f"Invalid message_type: {message_type}. Must be one of {valid_message_types}")
        if delivery_method not in valid_delivery_methods:
            raise ValueError(f"Invalid delivery_method: {delivery_method}. Must be one of {valid_delivery_methods}")
        if not (10 <= len(content) <= 2000):
            raise ValueError("Content length must be between 10 and 2000 characters.")
        print(f"[send_patient_communication] recipient_contact={recipient_contact}, message_type={message_type}, content_length={len(content)}, delivery_method={delivery_method}, attachments={attachments}")
        return CommunicationStatus(
            message_id="MSG-20001",
            delivery_status="sent",
            timestamp="2024-02-10T15:30:00Z",
            estimated_delivery="2024-02-10T15:35:00Z"
        )

    # --- System Tools (inherited, but included for clarity and override) ---

    # SUCCESS, FAILED, CANCELLED, HUMAN_IN_THE_LOOP are inherited from SystemToolsBaseClass

    # If needed, override system tool methods here for specialized test behavior

class TestCase1_HealthcarePatientOnboardingAgent_W1_Full_New_Patient_Onboarding_easy(BaseHealthcarePatientOnboardingAgentTestCase):
    """
    Adult patient with active insurance, initial visit, and preferred dates.

    Covers standard onboarding for a new adult patient with valid insurance; utilizes preferred appointment dates branch.
    """

    test_case_id = "HealthcarePatientOnboardingAgent_HealthcareOnboarding_W1_TC1"
    title = "Adult patient with active insurance, initial visit, and preferred dates"
    workflow = "W1 - Full New Patient Onboarding"

    input_data = {
        "form_id": "PAT-10001",
        "appointment_type": "initial_visit",
        "preferred_dates": [
            "2024-04-10",
            "2024-04-12"
        ],
        "provider_id": "PROV-12345",
        "self_pay": False
    }

    expected_tool_calls = [
        {
            "name": "extract_patient_demographics",
            "tool_inputs": {
                "form_id": "PAT-10001"
            }
        },
        {
            "name": "extract_insurance_info",
            "tool_inputs": {
                "form_id": "PAT-10001"
            }
        },
        {
            "name": "verify_insurance_eligibility",
            "tool_inputs": {
                "carrier": "Aetna",
                "policy_number": "POL-20001",
                "group_number": "GRP-30001",
                "subscriber_name": "John Smith",
                "dob": "1980-01-15"
            }
        },
        {
            "name": "extract_medical_history",
            "tool_inputs": {
                "form_id": "PAT-10001"
            }
        },
        {
            "name": "create_ehr_patient_record",
            "tool_inputs": {
                "demographics": {
                    "name": "John Smith",
                    "dob": "1980-01-15",
                    "ssn": "123-45-6789",
                    "address": "123 Main St, Springfield, IL",
                    "phone": "+12175551234",
                    "email": "john.smith@email.com"
                },
                "insurance": {
                    "carrier": "Aetna",
                    "policy_number": "POL-20001",
                    "group_number": "GRP-30001",
                    "subscriber_name": "John Smith",
                    "subscriber_relationship": "self",
                    "eligibility": {
                        "status": "active",
                        "copay": 25,
                        "deductible": 500,
                        "deductible_met": 150,
                        "prior_auth_required": False
                    }
                },
                "medical_history": {
                    "allergies": [],
                    "medications": [],
                    "conditions": [],
                    "immunizations": [],
                    "surgical_history": []
                }
            }
        },
        {
            "name": "check_provider_availability",
            "tool_inputs": {
                "provider_id": "PROV-12345",
                "appointment_type": "initial_visit",
                "preferred_dates": [
                    "2024-04-10",
                    "2024-04-12"
                ]
            }
        },
        {
            "name": "schedule_appointment",
            "tool_inputs": {
                "patient_id": "900001",
                "provider_id": "PROV-12345",
                "slot": {
                    "date": "2024-04-10",
                    "time": "09:00",
                    "duration": 30
                },
                "appointment_type": "initial_visit",
                "payment_type": "insurance"
            }
        },
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "john.smith@email.com",
                "message_type": "confirmation",
                "content": "Your appointment is scheduled for 2024-04-10 at 09:00 with provider PROV-12345. Please bring your insurance card and arrive 15 minutes early.",
                "delivery_method": "email"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Patient onboarding completed successfully.",
                "result_data": {
                    "patient_record": {
                        "patient_id": "900001",
                        "status": "created",
                        "ehr_system": "Epic"
                    },
                    "insurance_eligibility": {
                        "status": "active",
                        "copay": 25,
                        "deductible": 500,
                        "deductible_met": 150,
                        "prior_auth_required": False
                    },
                    "appointment": {
                        "appointment_id": "APPT-10101",
                        "provider_id": "PROV-12345",
                        "slot": {
                            "date": "2024-04-10",
                            "time": "09:00",
                            "duration": 30
                        },
                        "status": "scheduled"
                    },
                    "communication_status": {
                        "message_id": "MSG-30001",
                        "delivery_status": "sent",
                        "timestamp": "2024-03-01T10:30:00Z"
                    },
                    "escalation_flag": False
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Extract patient demographics from intake form",
            "expected_state": {
                "demographics_status": "extracted",
                "required_fields_present": True
            }
        },
        {
            "step": 2,
            "description": "Extract insurance info from intake form",
            "expected_state": {
                "insurance_fields_status": "extracted",
                "required_fields_present": True
            }
        },
        {
            "step": 3,
            "description": "Verify insurance eligibility using extracted info",
            "expected_state": {
                "insurance_eligibility_status": "active",
                "prior_auth_required": False
            }
        },
        {
            "step": 4,
            "description": "Extract medical history from intake form",
            "expected_state": {
                "medical_history_status": "extracted"
            }
        },
        {
            "step": 5,
            "description": "Create new patient record in EHR",
            "expected_state": {
                "patient_record_status": "created"
            }
        },
        {
            "step": 6,
            "description": "Check provider availability for initial appointment",
            "expected_state": {
                "available_slots_found": True
            }
        },
        {
            "step": 7,
            "description": "Schedule appointment and send confirmation",
            "expected_state": {
                "appointment_status": "scheduled",
                "confirmation_sent": True
            }
        },
        {
            "step": 8,
            "description": "Signal successful onboarding",
            "expected_state": {
                "final_status": "success"
            }
        }
    ]

    description = (
        "Covers standard onboarding for a new adult patient with valid insurance; utilizes preferred appointment dates branch."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test follows the standard onboarding process for an adult patient with no missing data, active insurance, and available provider slots matching preferred dates. "
        "No error, escalation, or special handling is required, making it a straightforward 'happy path' scenario."
    )

class TestCase2_HealthcarePatientOnboardingAgent_W1_Full_New_Patient_Onboarding_easy(BaseHealthcarePatientOnboardingAgentTestCase):
    """Adult patient with active insurance, annual physical, no preferred dates"""

    test_case_id = "HealthcareOnboarding_W1_TC2"
    title = "Adult patient with active insurance, annual physical, no preferred dates"
    workflow = "W1 - Full New Patient Onboarding"

    input_data = {
        "form_id": "PAT-10002",
        "appointment_type": "annual_physical",
        "provider_id": "PROV-67890",
        "self_pay": False
    }

    expected_tool_calls = [
        # Step 1: Extract patient demographics from intake form
        {
            "name": "extract_patient_demographics",
            "tool_inputs": {
                "form_id": "PAT-10002"
            }
        },
        # Step 2: Extract insurance info from intake form
        {
            "name": "extract_insurance_info",
            "tool_inputs": {
                "form_id": "PAT-10002"
            }
        },
        # Step 3: Verify insurance eligibility using extracted info (mocked with sample data)
        {
            "name": "verify_insurance_eligibility",
            "tool_inputs": {
                "carrier": "Blue Cross",
                "policy_number": "BC-123456789",
                "group_number": "GRP-55555",
                "subscriber_name": "John Smith",
                "dob": "1985-06-15"
            }
        },
        # Step 4: Extract medical history from intake form
        {
            "name": "extract_medical_history",
            "tool_inputs": {
                "form_id": "PAT-10002"
            }
        },
        # Step 5: Create new patient record in EHR
        {
            "name": "create_ehr_patient_record",
            "tool_inputs": {
                "demographics": {
                    "name": "John Smith",
                    "dob": "1985-06-15",
                    "ssn": "123-45-6789",
                    "address": "123 Main St, Springfield, IL",
                    "phone": "+12175551234",
                    "email": "john.smith@email.com"
                },
                "insurance": {
                    "carrier": "Blue Cross",
                    "policy_number": "BC-123456789",
                    "group_number": "GRP-55555",
                    "subscriber_name": "John Smith",
                    "subscriber_relationship": "self",
                    "eligibility": {
                        "status": "active",
                        "copay": 0,
                        "deductible": 1000,
                        "deductible_met": 500,
                        "prior_auth_required": False
                    }
                },
                "medical_history": {
                    "allergies": [],
                    "medications": [],
                    "conditions": [],
                    "immunizations": [],
                    "surgical_history": []
                }
            }
        },
        # Step 6: Check provider availability for annual physical (no preferred_dates)
        {
            "name": "check_provider_availability",
            "tool_inputs": {
                "provider_id": "PROV-67890",
                "appointment_type": "annual_physical"
                # preferred_dates omitted since none provided
            }
        },
        # Step 7: Schedule appointment and send confirmation
        {
            "name": "schedule_appointment",
            "tool_inputs": {
                "patient_id": "900002",
                "provider_id": "PROV-67890",
                "slot": {
                    "date": "2024-04-15",
                    "time": "13:00",
                    "duration": 45
                },
                "appointment_type": "annual_physical",
                "payment_type": "insurance"
            }
        },
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "+12175551234",
                "message_type": "confirmation",
                "content": "Your annual physical with Dr. Adams is scheduled for 2024-04-15 at 13:00. Please arrive 15 minutes early.",
                "delivery_method": "email"
            }
        },
        # Step 8: Signal successful onboarding
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Patient successfully onboarded, EHR record created, appointment scheduled, and confirmation sent.",
                "result_data": {
                    "patient_record": {
                        "patient_id": "900002",
                        "status": "created",
                        "ehr_system": "Epic"
                    },
                    "insurance_eligibility": {
                        "status": "active",
                        "copay": 0,
                        "deductible": 1000,
                        "deductible_met": 500,
                        "prior_auth_required": False
                    },
                    "appointment": {
                        "appointment_id": "APPT-10102",
                        "provider_id": "PROV-67890",
                        "slot": {
                            "date": "2024-04-15",
                            "time": "13:00",
                            "duration": 45
                        },
                        "status": "scheduled"
                    },
                    "communication_status": {
                        "message_id": "MSG-30002",
                        "delivery_status": "sent",
                        "timestamp": "2024-03-02T12:00:00Z"
                    },
                    "escalation_flag": False
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Extract patient demographics from intake form",
            "expected_state": {
                "demographics_status": "extracted",
                "required_fields_present": True
            }
        },
        {
            "step": 2,
            "description": "Extract insurance info from intake form",
            "expected_state": {
                "insurance_fields_status": "extracted",
                "required_fields_present": True
            }
        },
        {
            "step": 3,
            "description": "Verify insurance eligibility using extracted info",
            "expected_state": {
                "insurance_eligibility_status": "active",
                "prior_auth_required": False
            }
        },
        {
            "step": 4,
            "description": "Extract medical history from intake form",
            "expected_state": {
                "medical_history_status": "extracted"
            }
        },
        {
            "step": 5,
            "description": "Create new patient record in EHR",
            "expected_state": {
                "patient_record_status": "created"
            }
        },
        {
            "step": 6,
            "description": "Check provider availability for annual physical",
            "expected_state": {
                "available_slots_found": True
            }
        },
        {
            "step": 7,
            "description": "Schedule appointment and send confirmation",
            "expected_state": {
                "appointment_status": "scheduled",
                "confirmation_sent": True
            }
        },
        {
            "step": 8,
            "description": "Signal successful onboarding",
            "expected_state": {
                "final_status": "success"
            }
        }
    ]

    description = (
        "Tests onboarding when patient does not specify preferred dates; agent selects earliest available slot. "
        "Patient is an adult with active insurance and all required information provided. "
        "Validates the happy path for annual physical scheduling."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "All required data is present, insurance is active, no prior auth or duplicate detection needed, "
        "and the agent simply selects the earliest available slot due to no preferred dates. "
        "No recovery or escalation logic is triggered."
    )

class TestCase3_HealthcarePatientOnboardingAgent_W2_PediatricPatientOnboarding_easy(BaseHealthcarePatientOnboardingAgentTestCase):
    """
    Pediatric patient (<18) with parent as subscriber, well-child visit

    Ensures pediatric onboarding with parent/guardian as insurance subscriber and well-child appointment.
    """

    test_case_id = "HealthcareOnboarding_W2_TC1"
    title = "Pediatric patient (<18) with parent as subscriber, well-child visit"
    workflow = "W2 - Pediatric Patient Onboarding"

    input_data = {
        "form_id": "PAT-20001",
        "appointment_type": "well_child",
        "provider_id": "PROV-54321",
        "self_pay": False
    }

    expected_tool_calls = [
        # Step 1: Extract patient and parent/guardian demographics
        {
            "name": "extract_patient_demographics",
            "tool_inputs": {
                "form_id": "PAT-20001"
            }
        },
        # Step 2: Extract insurance info, verify parent/guardian as subscriber
        {
            "name": "extract_insurance_info",
            "tool_inputs": {
                "form_id": "PAT-20001"
            }
        },
        # Step 3: Verify insurance eligibility for dependent
        {
            "name": "verify_insurance_eligibility",
            "tool_inputs": {
                "carrier": "BlueCross",
                "policy_number": "PC-1234567",
                "group_number": "GRP-54321",
                "subscriber_name": "Jane Doe (parent)",
                "dob": "1980-05-10"
            }
        },
        # Step 4: Extract medical history and immunization status
        {
            "name": "extract_medical_history",
            "tool_inputs": {
                "form_id": "PAT-20001"
            }
        },
        # Step 5: Create pediatric patient record in EHR, link to parent
        {
            "name": "create_ehr_patient_record",
            "tool_inputs": {
                "demographics": {
                    "name": "John Doe",
                    "dob": "2015-07-04",
                    "ssn": "123-45-6789",
                    "address": "123 Main St, Springfield",
                    "phone": "+15555550123",
                    "email": "parent@example.com"
                },
                "insurance": {
                    "carrier": "BlueCross",
                    "policy_number": "PC-1234567",
                    "group_number": "GRP-54321",
                    "subscriber_name": "Jane Doe",
                    "subscriber_relationship": "parent",
                    "status": "active",
                    "copay": 10,
                    "deductible": 250,
                    "deductible_met": 50,
                    "prior_auth_required": False
                },
                "medical_history": {
                    "allergies": [],
                    "medications": [],
                    "conditions": [],
                    "immunizations": ["MMR", "DTaP", "Polio"],
                    "surgical_history": []
                },
                "existing_patient_id": None
            }
        },
        # Step 6: Schedule well-child appointment
        {
            "name": "schedule_appointment",
            "tool_inputs": {
                "patient_id": "910001",
                "provider_id": "PROV-54321",
                "slot": {
                    "date": "2024-05-10",
                    "time": "10:00",
                    "duration": 30
                },
                "appointment_type": "well_child",
                "payment_type": "insurance"
            }
        },
        # Step 7: Send confirmation and vaccine requirements to parent
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "parent@example.com",
                "message_type": "confirmation",
                "content": "Your child John Doe is scheduled for a well-child visit on 2024-05-10 at 10:00. Please bring immunization records and insurance card. Vaccines required: MMR, DTaP, Polio.",
                "delivery_method": "email"
            }
        },
        # Step 8: Signal successful onboarding
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Pediatric patient onboarding completed successfully.",
                "result_data": {
                    "patient_record": {
                        "patient_id": "910001",
                        "status": "created",
                        "ehr_system": "Epic"
                    },
                    "insurance_eligibility": {
                        "status": "active",
                        "copay": 10,
                        "deductible": 250,
                        "deductible_met": 50,
                        "prior_auth_required": False
                    },
                    "appointment": {
                        "appointment_id": "APPT-20101",
                        "provider_id": "PROV-54321",
                        "slot": {
                            "date": "2024-05-10",
                            "time": "10:00",
                            "duration": 30
                        },
                        "status": "scheduled"
                    },
                    "communication_status": {
                        "message_id": "MSG-40001",
                        "delivery_status": "sent",
                        "timestamp": "2024-04-01T14:00:00Z"
                    },
                    "escalation_flag": False
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Extract patient and parent/guardian demographics",
            "expected_state": {
                "demographics_status": "extracted",
                "subscriber_relationship": "parent"
            }
        },
        {
            "step": 2,
            "description": "Extract insurance info, verify parent/guardian as subscriber",
            "expected_state": {
                "insurance_fields_status": "extracted",
                "subscriber_relationship": "parent"
            }
        },
        {
            "step": 3,
            "description": "Verify insurance eligibility for dependent",
            "expected_state": {
                "insurance_eligibility_status": "active",
                "prior_auth_required": False
            }
        },
        {
            "step": 4,
            "description": "Extract medical history and immunization status",
            "expected_state": {
                "medical_history_status": "extracted"
            }
        },
        {
            "step": 5,
            "description": "Create pediatric patient record in EHR, link to parent",
            "expected_state": {
                "patient_record_status": "created"
            }
        },
        {
            "step": 6,
            "description": "Schedule well-child appointment",
            "expected_state": {
                "appointment_status": "scheduled"
            }
        },
        {
            "step": 7,
            "description": "Send confirmation and vaccine requirements to parent",
            "expected_state": {
                "confirmation_sent": True
            }
        },
        {
            "step": 8,
            "description": "Signal successful onboarding",
            "expected_state": {
                "final_status": "success"
            }
        }
    ]

    description = (
        "Ensures pediatric onboarding with parent/guardian as insurance subscriber and well-child appointment. "
        "Tests the agent's ability to extract and process parent-subscriber information, verify eligibility, "
        "create a linked EHR record, schedule an age-appropriate appointment, and send confirmation to the parent."
    )

    difficulty = "easy"
    difficulty_reasoning = (
        "This scenario is straightforward: all required data is present, insurance is active, and there are no failures or escalations. "
        "The only complexity is the use of a parent as the subscriber for a pediatric patient, which is a standard but essential workflow branch."
    )

class TestCase4_HealthcarePatientOnboardingAgent_W3_Insurance_Eligibility_Failure_Request_Update_medium(BaseHealthcarePatientOnboardingAgentTestCase):
    """
    Patient provides updated insurance after initial inactive coverage

    Tests successful resolution after patient supplies new insurance following a coverage failure.
    """

    test_case_id = "HealthcarePatientOnboardingAgent_HealthcareOnboarding_W3_TC1"
    title = "Patient provides updated insurance after initial inactive coverage"
    workflow = "W3 - Insurance Eligibility Failure - Request Update"

    input_data = {
        "form_id": "PAT-30001",
        "appointment_type": "initial_visit",
        "provider_id": "PROV-13579",
        "self_pay": False,
        "insurance_update": {
            "carrier": "NewHealth",
            "policy_number": "NH-55555",
            "group_number": "NHG-8888",
            "subscriber_name": "John Doe",
            "dob": "1990-06-15"
        }
    }

    expected_tool_calls = [
        # Step 1: Extract patient demographics and insurance info
        {"name": "extract_patient_demographics", "tool_inputs": {"form_id": "PAT-30001"}},
        {"name": "extract_insurance_info", "tool_inputs": {"form_id": "PAT-30001"}},
        # Step 2: Attempt insurance eligibility verification (simulate inactive status)
        {
            "name": "verify_insurance_eligibility",
            "tool_inputs": {
                "carrier": "NewHealth",  # Assume initial carrier is inactive; using updated for simplicity
                "policy_number": "NH-55555",
                "group_number": "NHG-8888",
                "subscriber_name": "John Doe",
                "dob": "1990-06-15"
            },
            "mock_response": {
                "status": "inactive"
            }
        },
        # Step 3: Send request for updated insurance or self-pay
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "john.doe@email.com",  # Assumed from demographics
                "message_type": "document_request",
                "content": "Your insurance coverage appears inactive. Please provide updated insurance details or confirm self-pay arrangement.",
                "delivery_method": "email"
            }
        },
        # Step 4: Patient responds with updated insurance (simulated by input_data['insurance_update'])
        # Step 5: Re-attempt insurance verification (now returns active)
        {
            "name": "verify_insurance_eligibility",
            "tool_inputs": {
                "carrier": "NewHealth",
                "policy_number": "NH-55555",
                "group_number": "NHG-8888",
                "subscriber_name": "John Doe",
                "dob": "1990-06-15"
            },
            "mock_response": {
                "status": "active",
                "copay": 20,
                "deductible": 400,
                "deductible_met": 100,
                "prior_auth_required": False
            }
        },
        # Step 6: Create EHR record, schedule appointment, send confirmation
        {
            "name": "create_ehr_patient_record",
            "tool_inputs": {
                "demographics": {
                    "name": "John Doe",
                    "dob": "1990-06-15",
                    "ssn": "123-45-6789",
                    "address": "123 Main St",
                    "phone": "+15555550123",
                    "email": "john.doe@email.com"
                },
                "insurance": {
                    "carrier": "NewHealth",
                    "policy_number": "NH-55555",
                    "group_number": "NHG-8888",
                    "subscriber_name": "John Doe",
                    "subscriber_relationship": "self",
                    "status": "active",
                    "copay": 20,
                    "deductible": 400,
                    "deductible_met": 100,
                    "prior_auth_required": False
                },
                "medical_history": {
                    "allergies": [],
                    "medications": [],
                    "conditions": [],
                    "immunizations": [],
                    "surgical_history": []
                }
            },
            "mock_response": {
                "patient_id": "920001",
                "status": "created",
                "ehr_system": "Epic"
            }
        },
        {
            "name": "schedule_appointment",
            "tool_inputs": {
                "patient_id": "920001",
                "provider_id": "PROV-13579",
                "slot": {
                    "date": "2024-06-05",
                    "time": "11:00",
                    "duration": 30
                },
                "appointment_type": "initial_visit",
                "payment_type": "insurance"
            },
            "mock_response": {
                "appointment_id": "APPT-30101",
                "status": "scheduled",
                "slot": {
                    "date": "2024-06-05",
                    "time": "11:00",
                    "duration": 30
                },
                "provider_id": "PROV-13579",
                "patient_id": "920001"
            }
        },
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "john.doe@email.com",
                "message_type": "confirmation",
                "content": "Your appointment is scheduled for 2024-06-05 at 11:00 with provider PROV-13579. Please bring your updated insurance card.",
                "delivery_method": "email"
            },
            "mock_response": {
                "message_id": "MSG-50001",
                "delivery_status": "sent",
                "timestamp": "2024-05-01T09:00:00Z"
            }
        },
        # Step 7: Signal success
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Patient onboarding completed with updated insurance and appointment scheduled.",
                "result_data": {
                    "patient_record": {
                        "patient_id": "920001",
                        "status": "created",
                        "ehr_system": "Epic"
                    },
                    "insurance_eligibility": {
                        "status": "active",
                        "copay": 20,
                        "deductible": 400,
                        "deductible_met": 100,
                        "prior_auth_required": False
                    },
                    "appointment": {
                        "appointment_id": "APPT-30101",
                        "provider_id": "PROV-13579",
                        "slot": {
                            "date": "2024-06-05",
                            "time": "11:00",
                            "duration": 30
                        },
                        "status": "scheduled"
                    },
                    "communication_status": {
                        "message_id": "MSG-50001",
                        "delivery_status": "sent",
                        "timestamp": "2024-05-01T09:00:00Z"
                    },
                    "escalation_flag": False
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Extract patient demographics and insurance info",
            "expected_state": {
                "demographics_status": "extracted",
                "insurance_fields_status": "extracted"
            }
        },
        {
            "step": 2,
            "description": "Attempt insurance eligibility verification (inactive)",
            "expected_state": {
                "insurance_eligibility_status": "inactive"
            }
        },
        {
            "step": 3,
            "description": "Send request for updated insurance or self-pay",
            "expected_state": {
                "request_sent": True
            }
        },
        {
            "step": 4,
            "description": "Patient responds with updated insurance",
            "expected_state": {
                "insurance_update_received": True
            }
        },
        {
            "step": 5,
            "description": "Re-attempt insurance verification (active)",
            "expected_state": {
                "insurance_eligibility_status": "active"
            }
        },
        {
            "step": 6,
            "description": "Create EHR record, schedule appointment, send confirmation",
            "expected_state": {
                "patient_record_status": "created",
                "appointment_status": "scheduled",
                "confirmation_sent": True
            }
        },
        {
            "step": 7,
            "description": "Signal success",
            "expected_state": {
                "final_status": "success"
            }
        }
    ]

    description = (
        "Tests successful resolution after patient supplies new insurance following a coverage failure. "
        "Agent requests updated insurance after initial failure; patient responds, agent re-verifies and proceeds with onboarding."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This test involves handling an insurance eligibility failure, requesting updated information, "
        "processing a patient response, and reattempting verification before proceeding. "
        "It requires correct branching, state management, and the ability to recover from initial failure."
    )

    # Override tool methods to simulate insurance eligibility status transitions
    def verify_insurance_eligibility(self, carrier: str, policy_number: str, group_number: str = None, subscriber_name: str = "", dob: str = "") -> dict:
        """
        Override to simulate insurance eligibility: first call returns inactive, second returns active.
        """
        # Track call count using an instance attribute
        if not hasattr(self, "_eligibility_attempt"):
            self._eligibility_attempt = 1
        else:
            self._eligibility_attempt += 1

        print(f"[DEBUG] verify_insurance_eligibility call #{self._eligibility_attempt} for carrier={carrier}")

        if self._eligibility_attempt == 1:
            return {"status": "inactive"}
        else:
            return {
                "status": "active",
                "copay": 20,
                "deductible": 400,
                "deductible_met": 100,
                "prior_auth_required": False
            }

class TestCase5_HealthcarePatientOnboardingAgent_W4_SpecialtyReferralwithPriorAuthorization_medium(BaseHealthcarePatientOnboardingAgentTestCase):
    """
    Validates successful specialty onboarding when prior authorization is required and approved.
    """

    test_case_id = "HealthcareOnboarding_W4_TC1"
    title = "Specialty referral with prior auth approved"
    workflow = "W4 - Specialty Referral with Prior Authorization"

    input_data = {
        "form_id": "PAT-40001",
        "appointment_type": "specialty_consult",
        "provider_id": "PROV-24680",
        "referral_id": "REF-10001",
        "self_pay": False,
        "prior_auth_number": "AUTH-12345"
    }

    expected_tool_calls = [
        {
            "name": "extract_patient_demographics",
            "tool_inputs": {
                "form_id": "PAT-40001"
            }
        },
        {
            "name": "verify_insurance_eligibility",
            "tool_inputs": {
                # These would be extracted from insurance info, but for test purposes, mock values:
                "carrier": "HealthPlus",
                "policy_number": "POL-80001",
                "group_number": "GRP-20001",
                "subscriber_name": "Jane Smith",
                "dob": "1987-03-22"
            }
        },
        # Step 3: Initiate prior auth request (handled as milestone, not a tool call)
        # Step 4: Hold scheduling until prior auth approved (handled as milestone, not a tool call)
        {
            "name": "schedule_appointment",
            "tool_inputs": {
                "patient_id": "PAT-40001",  # Simulate patient_id = form_id for test
                "provider_id": "PROV-24680",
                "slot": {
                    "date": "2024-07-10",
                    "time": "15:00",
                    "duration": 60
                },
                "appointment_type": "specialty_consult",
                "prior_auth_number": "AUTH-12345",
                "payment_type": "insurance"
            }
        },
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "jane.smith@email.com",
                "message_type": "confirmation",
                "content": (
                    "Your specialty appointment is scheduled for 2024-07-10 at 15:00 with provider PROV-24680. "
                    "Your prior authorization number is AUTH-12345."
                ),
                "delivery_method": "email"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Specialty referral onboarding completed successfully.",
                "result_data": {
                    "appointment": {
                        "appointment_id": "APPT-40101",
                        "provider_id": "PROV-24680",
                        "slot": {
                            "date": "2024-07-10",
                            "time": "15:00",
                            "duration": 60
                        },
                        "status": "scheduled"
                    },
                    "communication_status": {
                        "message_id": "MSG-60001",
                        "delivery_status": "sent",
                        "timestamp": "2024-06-15T16:00:00Z"
                    },
                    "escalation_flag": False
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Extract patient demographics and referral details",
            "expected_state": {
                "demographics_status": "extracted",
                "referral_status": "valid"
            }
        },
        {
            "step": 2,
            "description": "Verify insurance eligibility, check prior auth requirement",
            "expected_state": {
                "insurance_eligibility_status": "active",
                "prior_auth_required": True
            }
        },
        {
            "step": 3,
            "description": "Initiate prior authorization request",
            "expected_state": {
                "prior_auth_status": "approved"
            }
        },
        {
            "step": 4,
            "description": "Hold scheduling until prior auth approved",
            "expected_state": {
                "scheduling_status": "pending"
            }
        },
        {
            "step": 5,
            "description": "Schedule specialist appointment",
            "expected_state": {
                "appointment_status": "scheduled"
            }
        },
        {
            "step": 6,
            "description": "Send communication with auth number and appointment details",
            "expected_state": {
                "confirmation_sent": True
            }
        },
        {
            "step": 7,
            "description": "Signal success",
            "expected_state": {
                "final_status": "success"
            }
        }
    ]

    description = (
        "Validates successful specialty onboarding when prior authorization is required and approved. "
        "This test ensures the agent follows the prior auth flow, holds scheduling until approval, "
        "and includes auth number in patient communication."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This scenario requires handling a multi-step workflow with conditional logic: "
        "the agent must detect that prior auth is required, wait for approval, and only then proceed to scheduling. "
        "It also validates communication content and correct integration of the prior auth number."
    )

    # Optionally, override tool methods to return the expected mock data for this test case.
    def extract_patient_demographics(self, form_id: str) -> dict:
        """
        Override to return mock demographics for this test case.
        """
        print(f"--- Running extract_patient_demographics (override) ---")
        print(f"form_id: {form_id}")
        return {
            "name": "Jane Smith",
            "dob": "1987-03-22",
            "ssn": "111-22-3333",
            "address": "789 Willow St, Springfield, IL",
            "phone": "+15556667777",
            "email": "jane.smith@email.com"
        }

    def verify_insurance_eligibility(
        self,
        carrier: str,
        policy_number: str,
        group_number: str,
        subscriber_name: str,
        dob: str
    ) -> dict:
        """
        Override to return active eligibility with prior auth required and approved.
        """
        print(f"--- Running verify_insurance_eligibility (override) ---")
        print(f"carrier: {carrier}, policy_number: {policy_number}, group_number: {group_number}, subscriber_name: {subscriber_name}, dob: {dob}")
        return {
            "status": "active",
            "copay": 40,
            "deductible": 500,
            "deductible_met": 250,
            "prior_auth_required": True
        }

    def schedule_appointment(
        self,
        patient_id: str,
        provider_id: str,
        slot: dict,
        appointment_type: str,
        prior_auth_number: str = None,
        payment_type: str = "insurance"
    ) -> dict:
        """
        Override to return the expected appointment details for this test.
        """
        print(f"--- Running schedule_appointment (override) ---")
        print(f"patient_id: {patient_id}, provider_id: {provider_id}, slot: {slot}, appointment_type: {appointment_type}, prior_auth_number: {prior_auth_number}, payment_type: {payment_type}")
        return {
            "appointment_id": "APPT-40101",
            "provider_id": provider_id,
            "slot": slot,
            "status": "scheduled",
            "patient_id": patient_id
        }

    def send_patient_communication(
        self,
        recipient_contact: str,
        message_type: str,
        content: str,
        delivery_method: str = "email",
        attachments: list = None
    ) -> dict:
        """
        Override to return the expected communication status for this test.
        """
        print(f"--- Running send_patient_communication (override) ---")
        print(f"recipient_contact: {recipient_contact}, message_type: {message_type}, content: {content[:50]}..., delivery_method: {delivery_method}")
        return {
            "message_id": "MSG-60001",
            "delivery_status": "sent",
            "timestamp": "2024-06-15T16:00:00Z",
            "estimated_delivery": "2024-06-15T16:00:05Z"
        }

class TestCase6_HealthcarePatientOnboardingAgent_W5_SelfPayPatientOnboarding_easy(BaseHealthcarePatientOnboardingAgentTestCase):
    """Self-pay patient onboarding with initial visit
    Covers onboarding for patient who selects self-pay; skips insurance, provides pricing estimate."""

    test_case_id = "HealthcareOnboarding_W5_TC1"
    title = "Self-pay patient onboarding with initial visit"
    workflow = "W5"
    input_data = {
        "form_id": "PAT-50001",
        "appointment_type": "initial_visit",
        "provider_id": "PROV-11223",
        "self_pay": True
    }
    expected_tool_calls = [
        {
            "name": "extract_patient_demographics",
            "tool_inputs": {
                "form_id": "PAT-50001"
            }
        },
        {
            "name": "extract_medical_history",
            "tool_inputs": {
                "form_id": "PAT-50001"
            }
        },
        {
            "name": "create_ehr_patient_record",
            "tool_inputs": {
                "demographics": {
                    "name": "Jane Smith",
                    "dob": "1985-05-14",
                    "ssn": "123-45-6789",
                    "address": "123 Main St, Springfield, IL",
                    "phone": "+12175551234",
                    "email": "jane.smith@email.com"
                },
                "insurance": None,
                "medical_history": {
                    "allergies": [],
                    "medications": [],
                    "conditions": [],
                    "immunizations": [],
                    "surgical_history": []
                },
                "existing_patient_id": None
            }
        },
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "jane.smith@email.com",
                "message_type": "pricing_estimate",
                "content": "Dear Jane Smith, as a self-pay patient, your estimated cost for the initial visit is $150. Payment is required at time of service.",
                "delivery_method": "email"
            }
        },
        {
            "name": "schedule_appointment",
            "tool_inputs": {
                "patient_id": "930001",
                "provider_id": "PROV-11223",
                "slot": {
                    "date": "2024-08-01",
                    "time": "09:30",
                    "duration": 30
                },
                "appointment_type": "initial_visit",
                "payment_type": "self_pay"
            }
        },
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "jane.smith@email.com",
                "message_type": "confirmation",
                "content": "Your appointment is confirmed for 2024-08-01 at 09:30 with Dr. Provider. Please arrive 15 minutes early and be prepared to pay at check-in.",
                "delivery_method": "email"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Self-pay onboarding completed: EHR record created, appointment scheduled, patient notified.",
                "result_data": {
                    "patient_record": {
                        "patient_id": "930001",
                        "status": "created",
                        "ehr_system": "Epic"
                    },
                    "appointment": {
                        "appointment_id": "APPT-50101",
                        "provider_id": "PROV-11223",
                        "slot": {
                            "date": "2024-08-01",
                            "time": "09:30",
                            "duration": 30
                        },
                        "status": "scheduled"
                    },
                    "communication_status": {
                        "message_id": "MSG-70001",
                        "delivery_status": "sent",
                        "timestamp": "2024-07-01T09:00:00Z"
                    },
                    "escalation_flag": False
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Extract patient demographics",
            "expected_state": {
                "demographics_status": "extracted"
            }
        },
        {
            "step": 2,
            "description": "Extract medical history",
            "expected_state": {
                "medical_history_status": "extracted"
            }
        },
        {
            "step": 3,
            "description": "Create self-pay patient record in EHR",
            "expected_state": {
                "patient_record_status": "created"
            }
        },
        {
            "step": 4,
            "description": "Provide pricing estimate via communication",
            "expected_state": {
                "pricing_sent": True
            }
        },
        {
            "step": 5,
            "description": "Schedule appointment with payment required at visit",
            "expected_state": {
                "appointment_status": "scheduled"
            }
        },
        {
            "step": 6,
            "description": "Send appointment confirmation with payment instructions",
            "expected_state": {
                "confirmation_sent": True
            }
        },
        {
            "step": 7,
            "description": "Signal successful onboarding",
            "expected_state": {
                "final_status": "success"
            }
        }
    ]
    description = (
        "Covers onboarding for patient who selects self-pay; skips insurance, provides pricing estimate."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This flow is straightforward because it skips insurance extraction and eligibility verification. "
        "All required demographics are present, and no error or escalation paths are triggered."
    )

    # No tool method overrides required for this test case (all behavior is standard for self-pay onboarding)

class TestCase7_HealthcarePatientOnboardingAgent_W6_Duplicate_Patient_Detection_and_Merge_easy(BaseHealthcarePatientOnboardingAgentTestCase):
    """Duplicate patient detected by SSN and DOB, records merged"""

    test_case_id = "HealthcareOnboarding_W6_TC1"
    title = "Duplicate patient detected by SSN and DOB, records merged"
    workflow = "W6 - Duplicate Patient Detection and Merge"

    input_data = {
        "form_id": "PAT-60001",
        "appointment_type": "follow_up",
        "provider_id": "PROV-33445",
        "existing_patient_id": "876543",
        "self_pay": False
    }

    expected_tool_calls = [
        # Step 1: Extract patient demographics
        {
            "name": "extract_patient_demographics",
            "tool_inputs": {
                "form_id": "PAT-60001"
            }
        },
        # Step 3: Merge/update existing record with new info (demographics, insurance, medical_history)
        {
            "name": "create_ehr_patient_record",
            "tool_inputs": {
                "demographics": {
                    "name": "Jane Smith",
                    "dob": "1980-05-10",
                    "ssn": "123-45-6789",
                    "address": "100 Main St, Springfield, IL",
                    "phone": "+12175551234",
                    "email": "jane.smith@email.com"
                },
                "insurance": {
                    "carrier": "Blue Cross IL",
                    "policy_number": "BCIL-998877",
                    "group_number": "GRP-2002",
                    "subscriber_name": "Jane Smith",
                    "subscriber_relationship": "self"
                },
                "medical_history": {
                    "allergies": ["penicillin"],
                    "medications": [
                        {"name": "lisinopril", "dose": "10mg"},
                        {"name": "atorvastatin", "dose": "20mg"}
                    ],
                    "conditions": ["hypertension"],
                    "immunizations": ["influenza", "tdap"],
                    "surgical_history": []
                },
                "existing_patient_id": "876543"
            }
        },
        # Step 4: (Insurance info is merged in the previous call, so no separate call)
        # Step 5: Schedule appointment under existing patient ID
        {
            "name": "schedule_appointment",
            "tool_inputs": {
                "patient_id": "876543",
                "provider_id": "PROV-33445",
                "slot": {
                    "date": "2024-09-12",
                    "time": "11:30",
                    "duration": 30
                },
                "appointment_type": "follow_up",
                "payment_type": "insurance"
            }
        },
        # Step 6: Send duplicate alert to staff for review
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "staff@clinic.org",
                "message_type": "duplicate_alert",
                "content": "Duplicate patient detected by SSN and DOB. Records for Jane Smith (ID: 876543) were merged. Please review changes.",
                "delivery_method": "email"
            }
        },
        # Step 7: Signal success
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Duplicate patient record merged, appointment scheduled, staff notified.",
                "result_data": {
                    "patient_record": {
                        "patient_id": "876543",
                        "status": "merged",
                        "ehr_system": "Epic"
                    },
                    "appointment": {
                        "appointment_id": "APPT-60101",
                        "provider_id": "PROV-33445",
                        "slot": {
                            "date": "2024-09-12",
                            "time": "11:30",
                            "duration": 30
                        },
                        "status": "scheduled"
                    },
                    "communication_status": {
                        "message_id": "MSG-80001",
                        "delivery_status": "sent",
                        "timestamp": "2024-08-12T08:00:00Z"
                    },
                    "escalation_flag": False
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Extract patient demographics",
            "expected_state": {
                "demographics_status": "extracted"
            }
        },
        {
            "step": 2,
            "description": "Search EHR for matching records",
            "expected_state": {
                "duplicate_found": True,
                "match_type": "exact"
            }
        },
        {
            "step": 3,
            "description": "Update/merge existing record with new info",
            "expected_state": {
                "patient_record_status": "merged"
            }
        },
        {
            "step": 4,
            "description": "Merge insurance info if new/updated",
            "expected_state": {
                "insurance_merged": True
            }
        },
        {
            "step": 5,
            "description": "Schedule appointment under existing patient ID",
            "expected_state": {
                "appointment_status": "scheduled"
            }
        },
        {
            "step": 6,
            "description": "Send duplicate alert to staff for review",
            "expected_state": {
                "alert_sent": True
            }
        },
        {
            "step": 7,
            "description": "Signal success",
            "expected_state": {
                "final_status": "success"
            }
        }
    ]

    description = "Ensures agent can detect exact duplicate, merge records, and proceed without escalation."
    difficulty = "easy"
    difficulty_reasoning = (
        "This is an 'easy' test case because the duplicate patient match is exact (by SSN and DOB), "
        "no ambiguity exists, and all required data is present. The workflow is linear with no error recovery, "
        "escalation, or missing data handling required. All system integrations succeed as expected."
    )

    # No tool method overrides are required for this test case.

class TestCase8_HealthcarePatientOnboardingAgent_W7_HighRiskComplexMedicalHistoryOnboarding_easy(BaseHealthcarePatientOnboardingAgentTestCase):
    """
    Validates onboarding path for patients with complex medical history triggering care coordinator assignment.
    """

    test_case_id = "HealthcareOnboarding_W7_TC1"
    title = "High-risk patient with >2 chronic conditions and >5 medications"
    workflow = "W7 - High-Risk/Complex Medical History Onboarding"

    input_data = {
        "form_id": "PAT-70001",
        "appointment_type": "chronic_care",
        "provider_id": "PROV-55667",
        "self_pay": False
    }

    expected_tool_calls = [
        {
            "name": "extract_patient_demographics",
            "tool_inputs": {
                "form_id": "PAT-70001"
            }
        },
        {
            "name": "extract_medical_history",
            "tool_inputs": {
                "form_id": "PAT-70001"
            }
        },
        {
            "name": "extract_insurance_info",
            "tool_inputs": {
                "form_id": "PAT-70001"
            }
        },
        {
            "name": "verify_insurance_eligibility",
            "tool_inputs": {
                "carrier": "Blue Cross",
                "policy_number": "BC123456789",
                "group_number": "GRP-8001",
                "subscriber_name": "Jane Smith",
                "dob": "1970-05-14"
            }
        },
        {
            "name": "create_ehr_patient_record",
            "tool_inputs": {
                "demographics": {
                    "name": "Jane Smith",
                    "dob": "1970-05-14",
                    "ssn": "123-45-6789",
                    "address": "123 Main St, Springfield, IL",
                    "phone": "+12175551234",
                    "email": "jane.smith@example.com"
                },
                "insurance": {
                    "carrier": "Blue Cross",
                    "policy_number": "BC123456789",
                    "group_number": "GRP-8001",
                    "subscriber_name": "Jane Smith",
                    "subscriber_relationship": "self",
                    "status": "active",
                    "copay": 15,
                    "deductible": 600,
                    "deductible_met": 400,
                    "prior_auth_required": False
                },
                "medical_history": {
                    "allergies": ["Penicillin"],
                    "medications": [
                        {"name": "Metformin", "dose": "500mg"},
                        {"name": "Lisinopril", "dose": "10mg"},
                        {"name": "Atorvastatin", "dose": "20mg"},
                        {"name": "Amlodipine", "dose": "5mg"},
                        {"name": "Levothyroxine", "dose": "75mcg"},
                        {"name": "Omeprazole", "dose": "20mg"}
                    ],
                    "conditions": ["Diabetes", "Hypertension", "Hyperlipidemia"],
                    "immunizations": ["Influenza", "COVID-19"],
                    "surgical_history": ["Appendectomy"]
                },
                "existing_patient_id": None
            }
        },
        # Step 5: Assign care coordinator (manual or system) - no tool call, internal state change.
        {
            "name": "check_provider_availability",
            "tool_inputs": {
                "provider_id": "PROV-55667",
                "appointment_type": "chronic_care",
                "preferred_dates": None
            }
        },
        {
            "name": "schedule_appointment",
            "tool_inputs": {
                "patient_id": "940001",
                "provider_id": "PROV-55667",
                "slot": {
                    "date": "2024-10-05",
                    "time": "10:30",
                    "duration": 60
                },
                "appointment_type": "chronic_care",
                "payment_type": "insurance"
            }
        },
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "jane.smith@example.com",
                "message_type": "confirmation",
                "content": "Welcome to our chronic care program. Your appointment is scheduled for 2024-10-05 at 10:30. Please review the attached disease management resources.",
                "delivery_method": "email",
                "attachments": ["WELCOME-PACKET-001", "DM-RESOURCES-2024"]
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "High-risk patient onboarded, care coordinator assigned, and extended visit scheduled.",
                "result_data": {
                    "patient_record": {
                        "patient_id": "940001",
                        "status": "created",
                        "ehr_system": "Epic"
                    },
                    "insurance_eligibility": {
                        "status": "active",
                        "copay": 15,
                        "deductible": 600,
                        "deductible_met": 400,
                        "prior_auth_required": False
                    },
                    "appointment": {
                        "appointment_id": "APPT-70101",
                        "provider_id": "PROV-55667",
                        "slot": {
                            "date": "2024-10-05",
                            "time": "10:30",
                            "duration": 60
                        },
                        "status": "scheduled"
                    },
                    "communication_status": {
                        "message_id": "MSG-90001",
                        "delivery_status": "sent",
                        "timestamp": "2024-09-01T10:00:00Z"
                    },
                    "escalation_flag": False
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Extract patient demographics",
            "expected_state": {
                "demographics_status": "extracted"
            }
        },
        {
            "step": 2,
            "description": "Extract detailed medical history",
            "expected_state": {
                "medical_history_status": "extracted",
                "chronic_conditions_count": 3,
                "medications_count": 6
            }
        },
        {
            "step": 3,
            "description": "Verify insurance eligibility",
            "expected_state": {
                "insurance_eligibility_status": "active"
            }
        },
        {
            "step": 4,
            "description": "Create EHR record with high-risk flag",
            "expected_state": {
                "patient_record_status": "created",
                "high_risk_flag": True
            }
        },
        {
            "step": 5,
            "description": "Assign care coordinator (manual or system)",
            "expected_state": {
                "care_coordinator_assigned": True
            }
        },
        {
            "step": 6,
            "description": "Check provider availability for extended visit",
            "expected_state": {
                "available_slots_found": True
            }
        },
        {
            "step": 7,
            "description": "Schedule extended appointment",
            "expected_state": {
                "appointment_status": "scheduled"
            }
        },
        {
            "step": 8,
            "description": "Send welcome packet and disease management resources",
            "expected_state": {
                "welcome_sent": True
            }
        },
        {
            "step": 9,
            "description": "Signal successful onboarding",
            "expected_state": {
                "final_status": "success"
            }
        }
    ]

    description = "Validates onboarding path for patients with complex medical history triggering care coordinator assignment."
    difficulty = "easy"
    difficulty_reasoning = (
        "The scenario follows a standard high-risk onboarding workflow with no failures or escalations. "
        "All data is present and valid, and the patient is eligible with known chronic conditions and medications. "
        "No overrides or error handling are required."
    )

class TestCase9_HealthcarePatientOnboardingAgent_W8_IncompleteIntakeFormRequestInformation_easy(BaseHealthcarePatientOnboardingAgentTestCase):
    """Test: Missing insurance fields, patient supplies info on request

    Covers path where required insurance info is missing, agent requests and receives update, then completes onboarding.
    """

    test_case_id = "HealthcareOnboarding_W8_TC1"
    title = "Missing insurance fields, patient supplies info on request"
    workflow = "W8 - Incomplete Intake Form - Request Information"

    input_data = {
        "form_id": "PAT-80001",
        "appointment_type": "initial_visit",
        "provider_id": "PROV-77889",
        "missing_fields": [
            "policy_number",
            "group_number"
        ],
        "insurance_update": {
            "carrier": "HealthPlus",
            "policy_number": "HP-22222",
            "group_number": "HPG-3333",
            "subscriber_name": "Jane Smith",
            "dob": "1985-03-22"
        }
    }

    expected_tool_calls = [
        # Step 1: Extract available demographics and insurance info (insurance info will be incomplete)
        {
            "name": "extract_patient_demographics",
            "tool_inputs": {
                "form_id": "PAT-80001"
            }
        },
        {
            "name": "extract_insurance_info",
            "tool_inputs": {
                "form_id": "PAT-80001"
            }
        },
        # Step 2: Identify missing required fields (handled internally, no tool call)
        # Step 3: Send request for missing information to patient/guardian
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "auto-detected-from-demographics",  # In a real test, would use extracted email/phone
                "message_type": "missing_information",
                "content": "Your intake form is missing required insurance fields: policy_number, group_number. Please provide the missing information to proceed with onboarding.",
                "delivery_method": "email"
            }
        },
        # Step 4: Patient supplies missing info (simulated by insurance_update in input_data)
        # Step 5: Extract updated data and re-verify insurance
        {
            "name": "extract_patient_demographics",
            "tool_inputs": {
                "form_id": "PAT-80001"
            }
        },
        {
            "name": "extract_insurance_info",
            "tool_inputs": {
                "form_id": "PAT-80001"
            }
        },
        {
            "name": "verify_insurance_eligibility",
            "tool_inputs": {
                "carrier": "HealthPlus",
                "policy_number": "HP-22222",
                "group_number": "HPG-3333",
                "subscriber_name": "Jane Smith",
                "dob": "1985-03-22"
            }
        },
        # Step 6: Create EHR patient record and schedule appointment
        {
            "name": "create_ehr_patient_record",
            "tool_inputs": {
                "demographics": "extracted-demographics",  # In a real test, would use actual extracted object
                "insurance": {
                    "carrier": "HealthPlus",
                    "policy_number": "HP-22222",
                    "group_number": "HPG-3333",
                    "subscriber_name": "Jane Smith",
                    "subscriber_relationship": "self"  # default assumption
                },
                "medical_history": "extracted-medical-history",
                "existing_patient_id": None
            }
        },
        {
            "name": "schedule_appointment",
            "tool_inputs": {
                "patient_id": "950001",
                "provider_id": "PROV-77889",
                "slot": {
                    "date": "2024-11-20",
                    "time": "14:30",
                    "duration": 30
                },
                "appointment_type": "initial_visit",
                "payment_type": "insurance"
            }
        },
        # Step 7: Send confirmation communication
        {
            "name": "send_patient_communication",
            "tool_inputs": {
                "recipient_contact": "auto-detected-from-demographics",
                "message_type": "confirmation",
                "content": "Your appointment is scheduled for 2024-11-20 at 14:30 with provider PROV-77889. Please bring your insurance card and ID.",
                "delivery_method": "email"
            }
        },
        # Step 8: Signal success
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Patient onboarding completed successfully.",
                "result_data": {
                    "patient_record": {
                        "patient_id": "950001",
                        "status": "created",
                        "ehr_system": "Epic"
                    },
                    "insurance_eligibility": {
                        "status": "active",
                        "copay": 30,
                        "deductible": 700,
                        "deductible_met": 200,
                        "prior_auth_required": False
                    },
                    "appointment": {
                        "appointment_id": "APPT-80101",
                        "provider_id": "PROV-77889",
                        "slot": {
                            "date": "2024-11-20",
                            "time": "14:30",
                            "duration": 30
                        },
                        "status": "scheduled"
                    },
                    "communication_status": {
                        "message_id": "MSG-100001",
                        "delivery_status": "sent",
                        "timestamp": "2024-10-20T13:00:00Z"
                    },
                    "escalation_flag": False
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Extract available demographics and insurance info",
            "expected_state": {
                "demographics_status": "extracted",
                "insurance_fields_status": "incomplete"
            }
        },
        {
            "step": 2,
            "description": "Identify missing required fields",
            "expected_state": {
                "missing_fields_detected": True
            }
        },
        {
            "step": 3,
            "description": "Send request for missing information to patient/guardian",
            "expected_state": {
                "request_sent": True
            }
        },
        {
            "step": 4,
            "description": "Patient supplies missing info",
            "expected_state": {
                "missing_info_received": True
            }
        },
        {
            "step": 5,
            "description": "Extract updated data and re-verify insurance",
            "expected_state": {
                "insurance_eligibility_status": "active"
            }
        },
        {
            "step": 6,
            "description": "Create EHR patient record and schedule appointment",
            "expected_state": {
                "patient_record_status": "created",
                "appointment_status": "scheduled"
            }
        },
        {
            "step": 7,
            "description": "Send confirmation communication",
            "expected_state": {
                "confirmation_sent": True
            }
        },
        {
            "step": 8,
            "description": "Signal success",
            "expected_state": {
                "final_status": "success"
            }
        }
    ]

    description = (
        "Covers path where required insurance info is missing, agent requests and receives update, "
        "then completes onboarding."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows a linear, expected recovery path: missing required insurance fields are detected, "
        "the agent requests the info, the patient responds promptly, and onboarding proceeds without any ambiguous or "
        "escalated scenarios. All systems are available and the insurance eligibility is active, making this a straightforward case."
    )