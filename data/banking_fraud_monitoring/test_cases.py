from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict
from system_tools_base import SystemToolsBaseClass

# ------------------- TypedDict Definitions -------------------

class TransactionDetails(TypedDict):
    """Details of a transaction for a fraud alert."""
    transaction_id: str
    amount: float
    merchant_name: str
    merchant_mcc: str
    location: str
    device_id: str
    transaction_type: str  # enum: card_present, card_not_present, wire, online, atm
    timestamp: str
    ip_address: str

class TypicalSpendingRange(TypedDict):
    """Typical customer spending range."""
    min_amount: float
    max_amount: float
    currency: str

class CustomerProfile(TypedDict):
    """Profile of a customer for fraud analysis."""
    name: str
    age: int
    address: str
    home_state: str
    account_tenure_years: float
    account_status: str  # enum: good_standing, restricted, closed
    contact_email: str
    contact_phone: str
    typical_spending_range: TypicalSpendingRange
    recent_travel: List[str]

class VelocityMetrics(TypedDict):
    """Velocity metrics for transaction history."""
    max_per_hour: int
    max_per_day: int

class Anomaly(TypedDict):
    """Anomaly detected in transaction history."""
    type: str
    description: str
    timestamp: str

class TransactionHistory(TypedDict):
    """Historical transaction analysis for a customer."""
    total_transactions: int
    avg_amount: float
    states_visited: List[str]
    merchant_categories: List[str]
    velocity_metrics: VelocityMetrics
    anomalies: List[Anomaly]

class DeviceIntelligence(TypedDict):
    """Device intelligence signals for fraud."""
    device_type: str  # enum: mobile, desktop, tablet, unknown
    os: str
    browser_fingerprint: str
    vpn_detected: bool
    tor_detected: bool
    ip_address: str
    location: str
    device_risk_score: int
    device_history: List[str]

class FraudDatabaseHits(TypedDict, total=False):
    """Fraud database cross-reference results."""
    merchant_blacklist_hit: bool
    card_bin_attack: bool
    phone_fraud_list: bool
    fraud_database_notes: List[str]

class RiskFactor(TypedDict):
    type: str
    description: str

class FraudRiskScoreResult(TypedDict):
    fraud_risk_score: int
    risk_factors: List[RiskFactor]
    recommended_action: str  # enum: approve, decline, escalate, verify_customer
    rationale: str

class RouteToAnalystResult(TypedDict):
    case_id: str
    analyst_queue: str
    escalation_level: str  # enum: normal, urgent
    timestamp: str
    summary: str

class AutoDeclineTransactionResult(TypedDict):
    transaction_id: str
    block_status: str  # enum: blocked, failed
    timestamp: str
    notification_sent: bool

class RequestCustomerVerificationResult(TypedDict):
    verification_id: str
    delivery_status: str  # enum: sent, queued, failed
    customer_response: str  # enum: verified, denied, no_response
    timestamp: str

class InvestigationPackage(TypedDict, total=False):
    transaction_id: str
    risk_factors: List[str]
    summary: str

# ------------------- Base Test Case Class -------------------

class BaseBankingFraudMonitoringSupportAgentTestCase(SystemToolsBaseClass):
    """
    Base class containing common methods for all Banking Fraud Monitoring Support Agent test cases.
    """

    # Agent context attributes
    role: str = (
        "You are a banking fraud monitoring support agent that automates the triage and enrichment of fraud alerts. "
        "You gather contextual data from multiple systems, calculate fraud risk scores, and route suspicious cases to "
        "fraud analysts with comprehensive summaries, enabling rapid, accurate fraud detection and escalation.\n"
    )
    goal: str = (
        "Your goal is to reduce manual fraud alert triage time by automating data enrichment, risk scoring, and case "
        "routing. Success is measured by rapid, accurate identification and escalation of true fraud cases, minimizing "
        "false positives, timely customer notification, and compliance with banking regulations.\n"
    )
    action_plan: dict = {
        "assumptions": [
            "All fraud alerts received are valid and require initial triage.",
            "Systems for transaction, device, customer, and fraud database access are available and reliable.",
        ],
        "tools_and_resources": [
            "retrieve_transaction_details",
            "get_customer_profile",
            "analyze_transaction_history",
            "check_device_intelligence",
            "calculate_fraud_risk_score",
            "cross_reference_fraud_databases",
            "route_to_analyst",
            "auto_decline_transaction",
            "request_customer_verification",
        ],
        "guidelines": [
            "Always enrich alerts with data from all relevant systems before scoring.",
            "Use risk score thresholds to determine routing: <30 auto-approve, >95 auto-decline, 30-95 escalate or verify.",
        ],
        "workflow_selection": [
            "if fraud_risk_score < 30: Auto-approve transaction as legitimate; no escalation or customer contact required.",
            "if fraud_risk_score > 95: Auto-decline transaction; block account or card immediately and notify customer.",
            "if 70 < fraud_risk_score <= 95: Escalate to analyst with full investigation package and recommended actions.",
            "if 50 <= fraud_risk_score <= 70: Request customer verification via SMS/email before escalating.",
            "if alert_type == 'account_takeover': Immediately block account access and escalate to analyst for urgent review.",
            "if alert_type == 'velocity_fraud': Escalate to analyst with velocity and merchant risk context.",
            "if alert_type == 'synthetic_identity': Escalate new account alerts with synthetic identity signals for analyst review.",
            "if alert_type == 'friendly_fraud': Provide evidence summary for analyst to review chargeback dispute.",
            "if alert_type == 'authorized_push_payment': Hold wire transfer and escalate for possible elder or scam fraud.",
        ],
        "failure_points": [
            {
                "scenario": "Unable to retrieve data from a required system (e.g., transaction history, device intelligence).",
                "recovery": "Escalate to HUMAN_IN_THE_LOOP with details of missing data and request manual review.",
            },
            {
                "scenario": "Conflicting signals or ambiguous risk score (e.g., borderline score with inconsistent device data).",
                "recovery": "Escalate to HUMAN_IN_THE_LOOP for human judgment and further investigation.",
            },
            {
                "scenario": "Customer verification fails or is not completed within required timeframe.",
                "recovery": "Auto-decline transaction and notify analyst for manual follow-up.",
            },
        ],
        "success_criteria": [
            "Fraud alerts are triaged and routed within 2 minutes of receipt.",
            "All escalated cases include complete investigation packages and recommended actions.",
            "False positives are minimized, and legitimate customer activity is not disrupted.",
            "All regulatory and notification requirements are met for true fraud cases.",
        ],
    }

    # ------------------- Domain Tool Methods -------------------

    def retrieve_transaction_details(self, alert_id: str) -> TransactionDetails:
        """
        Fetch transaction details, including amount, merchant, MCC, location, device data for a specific fraud alert.

        Args:
            alert_id: Unique fraud alert identifier. Format: FA-XXXXXX where X is numeric.

        Returns:
            TransactionDetails: {
                transaction_id: str,
                amount: float (USD, 2 decimal places),
                merchant_name: str,
                merchant_mcc: str (4 digits),
                location: str (city/state/country),
                device_id: str,
                transaction_type: str (enum: card_present, card_not_present, wire, online, atm),
                timestamp: str (ISO 8601),
                ip_address: str (IPv4/IPv6)
            }
        """
        print(f"[DEBUG] retrieve_transaction_details called with alert_id: {alert_id}")
        # Return mock data
        return {
            "transaction_id": "TX-998877",
            "amount": 199.99,
            "merchant_name": "Best Electronics",
            "merchant_mcc": "5732",
            "location": "Miami, FL, USA",
            "device_id": "DEV-998877",
            "transaction_type": "online",
            "timestamp": "2024-07-01T10:30:00Z",
            "ip_address": "185.23.44.12"
        }

    def get_customer_profile(self, customer_id: str) -> CustomerProfile:
        """
        Retrieve customer information including demographics, account tenure, typical spending patterns.

        Args:
            customer_id: Unique customer identifier. Format: CUST-XXXXXX where X is alphanumeric.

        Returns:
            CustomerProfile: {
                name: str,
                age: int (18-100),
                address: str,
                home_state: str (2-letter),
                account_tenure_years: float,
                account_status: str (enum: good_standing, restricted, closed),
                contact_email: str (valid email),
                contact_phone: str (E.164 format),
                typical_spending_range: TypicalSpendingRange,
                recent_travel: List[str] (max 5)
            }
        """
        print(f"[DEBUG] get_customer_profile called with customer_id: {customer_id}")
        return {
            "name": "Jane Doe",
            "age": 34,
            "address": "123 Main St, Miami, FL",
            "home_state": "FL",
            "account_tenure_years": 5.2,
            "account_status": "good_standing",
            "contact_email": "jane.doe@email.com",
            "contact_phone": "+13055551234",
            "typical_spending_range": {
                "min_amount": 30.0,
                "max_amount": 500.0,
                "currency": "USD"
            },
            "recent_travel": ["New York", "Chicago"]
        }

    def analyze_transaction_history(self, customer_id: str, lookback_days: int) -> TransactionHistory:
        """
        Analyze customer’s historical transaction patterns, velocity, and geographic usage.

        Args:
            customer_id: Unique customer identifier. Format: CUST-XXXXXX.
            lookback_days: Number of days to look back for transaction analysis. Range: 1-365.

        Returns:
            TransactionHistory: {
                total_transactions: int,
                avg_amount: float (USD, 2 decimals),
                states_visited: List[str] (max 10),
                merchant_categories: List[str] (MCC codes, max 10),
                velocity_metrics: VelocityMetrics,
                anomalies: List[Anomaly]
            }
        """
        if not (1 <= lookback_days <= 365):
            raise ValueError(f"lookback_days must be between 1 and 365, got {lookback_days}")
        print(f"[DEBUG] analyze_transaction_history called with customer_id: {customer_id}, lookback_days: {lookback_days}")
        return {
            "total_transactions": 87,
            "avg_amount": 120.50,
            "states_visited": ["FL", "NY"],
            "merchant_categories": ["5732", "5812"],
            "velocity_metrics": {
                "max_per_hour": 2,
                "max_per_day": 5
            },
            "anomalies": [
                {
                    "type": "location_anomaly",
                    "description": "Transaction from new country",
                    "timestamp": "2024-06-20T14:00:00Z"
                }
            ]
        }

    def check_device_intelligence(self, device_id: str) -> DeviceIntelligence:
        """
        Assess device signals for fraud, including device ID, IP, browser fingerprint, VPN/TOR usage.

        Args:
            device_id: Unique device identifier as provided in transaction details.

        Returns:
            DeviceIntelligence: {
                device_type: str (enum: mobile, desktop, tablet, unknown),
                os: str,
                browser_fingerprint: str,
                vpn_detected: bool,
                tor_detected: bool,
                ip_address: str,
                location: str,
                device_risk_score: int (0-100),
                device_history: List[str] (previous_customer_ids, max 5)
            }
        """
        print(f"[DEBUG] check_device_intelligence called with device_id: {device_id}")
        return {
            "device_type": "mobile",
            "os": "iOS 16.3",
            "browser_fingerprint": "bfprnt-123456789",
            "vpn_detected": False,
            "tor_detected": False,
            "ip_address": "185.23.44.12",
            "location": "Miami, FL, USA",
            "device_risk_score": 10,
            "device_history": ["CUST-334899"]
        }

    def calculate_fraud_risk_score(
        self,
        transaction_details: TransactionDetails,
        customer_profile: CustomerProfile,
        transaction_history: TransactionHistory,
        device_intelligence: DeviceIntelligence,
        fraud_database_hits: Optional[FraudDatabaseHits] = None
    ) -> FraudRiskScoreResult:
        """
        Calculate fraud risk score (0-100) using all available signals.

        Args:
            transaction_details: Transaction details object as returned by retrieve_transaction_details.
            customer_profile: Customer profile object as returned by get_customer_profile.
            transaction_history: Transaction history object as returned by analyze_transaction_history.
            device_intelligence: Device intelligence object as returned by check_device_intelligence.
            fraud_database_hits: Fraud database hit object as returned by cross_reference_fraud_databases (optional).

        Returns:
            FraudRiskScoreResult: {
                fraud_risk_score: int (0-100),
                risk_factors: List[RiskFactor],
                recommended_action: str (enum: approve, decline, escalate, verify_customer),
                rationale: str
            }
        """
        print(f"[DEBUG] calculate_fraud_risk_score called")
        print(f"  transaction_details: {transaction_details}")
        print(f"  customer_profile: {customer_profile}")
        print(f"  transaction_history: {transaction_history}")
        print(f"  device_intelligence: {device_intelligence}")
        print(f"  fraud_database_hits: {fraud_database_hits}")
        # Mock scoring logic
        risk_score = 15
        recommended_action = "approve"
        rationale = "Low risk detected: device and location consistent, no blacklist hits."
        risk_factors = [{"type": "none", "description": "No risk factors found"}]
        return {
            "fraud_risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommended_action": recommended_action,
            "rationale": rationale
        }

    def cross_reference_fraud_databases(
        self,
        transaction_details: TransactionDetails,
        customer_profile: Optional[CustomerProfile] = None
    ) -> FraudDatabaseHits:
        """
        Check transaction, merchant, and card against fraud blacklists and attack lists.

        Args:
            transaction_details: Transaction details object.
            customer_profile: Customer profile object (optional).

        Returns:
            FraudDatabaseHits: {
                merchant_blacklist_hit: bool,
                card_bin_attack: bool,
                phone_fraud_list: bool,
                fraud_database_notes: List[str] (max 5)
            }
        """
        print(f"[DEBUG] cross_reference_fraud_databases called")
        print(f"  transaction_details: {transaction_details}")
        print(f"  customer_profile: {customer_profile}")
        return {
            "merchant_blacklist_hit": False,
            "card_bin_attack": False,
            "phone_fraud_list": False,
            "fraud_database_notes": ["No matches found"]
        }

    def route_to_analyst(
        self,
        alert_id: str,
        investigation_package: InvestigationPackage,
        recommended_action: str
    ) -> RouteToAnalystResult:
        """
        Escalate high-risk cases to fraud analysts with full context and recommendations.

        Args:
            alert_id: Fraud alert ID. Format: FA-XXXXXX.
            investigation_package: Compiled data package including transaction, customer, device, history, risk score, and notes.
            recommended_action: Recommended action for analyst. Must be one of: block_card, contact_customer, deny_chargeback, close_account, hold_transfer, escalate_sar

        Returns:
            RouteToAnalystResult: {
                case_id: str,
                analyst_queue: str,
                escalation_level: str (enum: normal, urgent),
                timestamp: str (ISO 8601),
                summary: str
            }
        """
        valid_actions = [
            "block_card",
            "contact_customer",
            "deny_chargeback",
            "close_account",
            "hold_transfer",
            "escalate_sar"
        ]
        if recommended_action not in valid_actions:
            raise ValueError(f"Invalid recommended_action: {recommended_action}. Must be one of {valid_actions}")
        print(f"[DEBUG] route_to_analyst called with alert_id: {alert_id}, recommended_action: {recommended_action}")
        print(f"  investigation_package: {investigation_package}")
        return {
            "case_id": "CASE-1001",
            "analyst_queue": "fraud_high_risk",
            "escalation_level": "normal",
            "timestamp": "2024-07-01T10:45:00Z",
            "summary": "Escalated for analyst review"
        }

    def auto_decline_transaction(self, transaction_id: str, reason: str) -> AutoDeclineTransactionResult:
        """
        Block transactions identified as obvious fraud and prevent further loss.

        Args:
            transaction_id: Transaction ID as returned by retrieve_transaction_details.
            reason: Reason for auto-decline. Must be one of: stolen_card, bad_merchant, confirmed_account_takeover, device_fraud, synthetic_identity

        Returns:
            AutoDeclineTransactionResult: {
                transaction_id: str,
                block_status: str (enum: blocked, failed),
                timestamp: str (ISO 8601),
                notification_sent: bool
            }
        """
        valid_reasons = [
            "stolen_card",
            "bad_merchant",
            "confirmed_account_takeover",
            "device_fraud",
            "synthetic_identity"
        ]
        if reason not in valid_reasons:
            raise ValueError(f"Invalid reason: {reason}. Must be one of {valid_reasons}")
        print(f"[DEBUG] auto_decline_transaction called with transaction_id: {transaction_id}, reason: {reason}")
        return {
            "transaction_id": transaction_id,
            "block_status": "blocked",
            "timestamp": "2024-07-01T10:40:00Z",
            "notification_sent": True
        }

    def request_customer_verification(
        self,
        customer_id: str,
        method: str,
        alert_id: str,
        message_content: str
    ) -> RequestCustomerVerificationResult:
        """
        Initiate customer verification via SMS, email, or app for suspicious cases.

        Args:
            customer_id: Unique customer identifier.
            method: Verification method. Must be one of: sms, email, app_push
            alert_id: Fraud alert ID.
            message_content: Message to send to customer. Length: 10-500 characters.

        Returns:
            RequestCustomerVerificationResult: {
                verification_id: str,
                delivery_status: str (enum: sent, queued, failed),
                customer_response: str (enum: verified, denied, no_response),
                timestamp: str (ISO 8601)
            }
        """
        valid_methods = ["sms", "email", "app_push"]
        if method not in valid_methods:
            raise ValueError(f"Invalid method: {method}. Must be one of {valid_methods}")
        if not (10 <= len(message_content) <= 500):
            raise ValueError(f"message_content must be 10-500 characters, got {len(message_content)}")
        print(f"[DEBUG] request_customer_verification called with customer_id: {customer_id}, method: {method}, alert_id: {alert_id}")
        print(f"  message_content: {message_content[:50]}{'...' if len(message_content) > 50 else ''}")
        return {
            "verification_id": "VER-001",
            "delivery_status": "sent",
            "customer_response": "verified",
            "timestamp": "2024-07-01T10:50:00Z"
        }

    # ------------------- System Tool Methods (provided by SystemToolsBaseClass) -------------------
    # SUCCESS, FAILED, CANCELLED, HUMAN_IN_THE_LOOP are inherited and available for use.

class TestCase1_BankingFraudMonitoringSupportAgent_W1_easy(BaseBankingFraudMonitoringSupportAgentTestCase):
    """
    Low-Risk Card Present Transaction with Typical Device

    Covers the success path for a legitimate transaction with no anomalies, typical behavior, and a fraud risk score well below threshold.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_BankingFraud_W1_TC1"
    title = "Low-Risk Card Present Transaction with Typical Device"
    workflow = "W1"
    input_data = {
        "alert_id": "FA-883421",
        "customer_id": "CUST-102345",
        "alert_type": "card_present",
        "transaction_type": "card_present",
        "lookback_days": 90,
        "additional_context": {
            "device_id": "DEV-100001",
            "location": "San Francisco, CA",
            "ip_address": "192.168.1.100"
        }
    }
    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883421"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-102345"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-102345",
                "lookback_days": 90
            }
        },
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-100001"
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-10001",
                    "amount": 120.5,
                    "merchant_name": "ABC Electronics",
                    "merchant_mcc": "5732",
                    "location": "San Francisco, CA",
                    "device_id": "DEV-100001",
                    "transaction_type": "card_present",
                    "timestamp": "2024-06-10T13:45:00Z",
                    "ip_address": "192.168.1.100"
                },
                "customer_profile": {
                    "name": "Jane Doe",
                    "age": 36,
                    "address": "123 Market St, San Francisco, CA",
                    "home_state": "CA",
                    "account_tenure_years": 7.2,
                    "account_status": "good_standing",
                    "contact_email": "jane.doe@email.com",
                    "contact_phone": "+14155550123",
                    "typical_spending_range": {
                        "min_amount": 20.0,
                        "max_amount": 500.0,
                        "currency": "USD"
                    },
                    "recent_travel": ["Los Angeles, CA", "Seattle, WA"]
                },
                "transaction_history": {
                    "total_transactions": 120,
                    "avg_amount": 110.0,
                    "states_visited": ["CA", "WA"],
                    "merchant_categories": ["5732", "5411"],
                    "velocity_metrics": {
                        "max_per_hour": 2,
                        "max_per_day": 5
                    },
                    "anomalies": []
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "iOS",
                    "browser_fingerprint": "bf-99887766",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "192.168.1.100",
                    "location": "San Francisco, CA",
                    "device_risk_score": 10,
                    "device_history": ["CUST-102345"]
                },
                "fraud_database_hits": {
                    "merchant_blacklist_hit": False,
                    "card_bin_attack": False,
                    "phone_fraud_list": False,
                    "fraud_database_notes": []
                }
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Transaction auto-approved. Low risk score and no anomalies detected.",
                "result_data": {
                    "fraud_risk_score": 15,
                    "case_status": "auto_approved",
                    "recommended_action": "approve",
                    "customer_notification_status": "not_required"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Transaction details retrieved",
            "expected_state": {
                "transaction_id": "TX-10001",
                "amount": 120.5
            }
        },
        {
            "step": 2,
            "description": "Customer profile and transaction history analyzed",
            "expected_state": {
                "account_status": "good_standing",
                "velocity_metrics": {
                    "max_per_day": 5
                }
            }
        },
        {
            "step": 3,
            "description": "Device intelligence checked",
            "expected_state": {
                "device_risk_score": 10,
                "vpn_detected": False,
                "tor_detected": False
            }
        },
        {
            "step": 4,
            "description": "Fraud risk score calculated",
            "expected_state": {
                "fraud_risk_score": 15,
                "risk_factors": []
            }
        }
    ]
    description = (
        "Covers the success path for a legitimate transaction with no anomalies, typical behavior, "
        "and a fraud risk score well below threshold."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This is a straightforward, low-risk scenario following the happy path: all data is available, "
        "no anomalies or blacklist hits, and the risk score is well below the auto-approve threshold. "
        "No error handling, escalation, or complex logic is required."
    )

class TestCase2_BankingFraudMonitoringSupportAgent_W1_easy(BaseBankingFraudMonitoringSupportAgentTestCase):
    """
    Low-Risk Card Not Present Transaction with Recent Customer Travel

    Validates success path for a low-risk online transaction with recent travel context, but all signals are consistent and below risk threshold.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_BankingFraud_W1_TC2"
    title = "Low-Risk Card Not Present Transaction with Recent Customer Travel"
    workflow = "W1"
    input_data = {
        "alert_id": "FA-883422",
        "customer_id": "CUST-334899",
        "alert_type": "card_not_present",
        "transaction_type": "online",
        "lookback_days": 90,
        "additional_context": {
            "device_id": "DEV-200002",
            "location": "Miami, FL",
            "ip_address": "185.23.44.12",
            "recent_travel": [
                "Miami, FL"
            ]
        }
    }
    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883422"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-334899"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-334899",
                "lookback_days": 90
            }
        },
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-200002"
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-20002",
                    "amount": 220.0,
                    "merchant_name": "Online Retailer",
                    "merchant_mcc": "5732",
                    "location": "Miami, FL",
                    "device_id": "DEV-200002",
                    "transaction_type": "online",
                    "timestamp": "2024-07-02T14:22:00Z",
                    "ip_address": "185.23.44.12"
                },
                "customer_profile": {
                    "name": "Jane Smith",
                    "age": 32,
                    "address": "123 Main St, Miami, FL",
                    "home_state": "FL",
                    "account_tenure_years": 5.4,
                    "account_status": "good_standing",
                    "contact_email": "jane.smith@email.com",
                    "contact_phone": "+13055551234",
                    "typical_spending_range": {
                        "min_amount": 50.0,
                        "max_amount": 500.0,
                        "currency": "USD"
                    },
                    "recent_travel": [
                        "Miami, FL"
                    ]
                },
                "transaction_history": {
                    "total_transactions": 120,
                    "avg_amount": 210.0,
                    "states_visited": ["FL", "GA"],
                    "merchant_categories": ["5732", "5812"],
                    "velocity_metrics": {"max_per_hour": 1, "max_per_day": 3},
                    "anomalies": []
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "iOS 16.5",
                    "browser_fingerprint": "fp-9988776655",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "185.23.44.12",
                    "location": "Miami, FL",
                    "device_risk_score": 15,
                    "device_history": ["CUST-334899"]
                }
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Low fraud risk score (25). Transaction auto-approved, alert closed. No customer notification required.",
                "result_data": {
                    "fraud_risk_score": 25,
                    "case_status": "auto_approved",
                    "recommended_action": "approve",
                    "customer_notification_status": "not_required"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Transaction details retrieved",
            "expected_state": {
                "transaction_id": "TX-20002",
                "amount": 220.0
            }
        },
        {
            "step": 2,
            "description": "Customer profile and transaction history analyzed",
            "expected_state": {
                "recent_travel": [
                    "Miami, FL"
                ],
                "velocity_metrics": {
                    "max_per_day": 3
                }
            }
        },
        {
            "step": 3,
            "description": "Device intelligence checked",
            "expected_state": {
                "device_risk_score": 15,
                "vpn_detected": False,
                "tor_detected": False
            }
        },
        {
            "step": 4,
            "description": "Fraud risk score calculated",
            "expected_state": {
                "fraud_risk_score": 25,
                "risk_factors": []
            }
        }
    ]
    description = (
        "Validates success path for a low-risk online transaction with recent travel context. "
        "All signals are consistent and below the risk threshold for escalation or customer contact. "
        "Ensures that location anomaly is not flagged due to matching recent travel and that the case is auto-approved."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the simple, straight-through auto-approval path: "
        "all signals are low risk, recent travel matches, and the fraud risk score is well below the threshold. "
        "No escalation, customer verification, or error handling is required."
    )

class TestCase3_BankingFraudMonitoringSupportAgent_W2_easy(BaseBankingFraudMonitoringSupportAgentTestCase):
    """
    Obvious Fraud - Blacklisted Merchant, Card Not Present

    Tests success path for auto-decline when transaction is flagged by blacklist and high risk score.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_BankingFraud_W2_TC1"
    title = "Obvious Fraud - Blacklisted Merchant, Card Not Present"
    workflow = "W2"
    input_data = {
        "alert_id": "FA-883423",
        "customer_id": "CUST-334899",
        "alert_type": "card_not_present",
        "transaction_type": "online",
        "lookback_days": 90,
        "additional_context": {
            "device_id": "DEV-300003",
            "location": "New York, NY",
            "ip_address": "203.0.113.5"
        }
    }
    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883423"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-334899"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-334899",
                "lookback_days": 90
            }
        },
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-300003"
            }
        },
        {
            "name": "cross_reference_fraud_databases",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-30003",
                    "amount": 250.00,
                    "merchant_name": "BLACKLISTED MERCHANT",
                    "merchant_mcc": "5999",
                    "location": "New York, NY",
                    "device_id": "DEV-300003",
                    "transaction_type": "online",
                    "timestamp": "2024-07-01T10:00:00Z",
                    "ip_address": "203.0.113.5"
                },
                "customer_profile": {
                    "name": "John Doe",
                    "age": 42,
                    "address": "123 Main St, New York, NY",
                    "home_state": "NY",
                    "account_tenure_years": 6.5,
                    "account_status": "good_standing",
                    "contact_email": "john.doe@email.com",
                    "contact_phone": "+15551234567",
                    "typical_spending_range": {"min_amount": 20, "max_amount": 500, "currency": "USD"},
                    "recent_travel": ["California", "Texas"]
                }
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-30003",
                    "amount": 250.00,
                    "merchant_name": "BLACKLISTED MERCHANT",
                    "merchant_mcc": "5999",
                    "location": "New York, NY",
                    "device_id": "DEV-300003",
                    "transaction_type": "online",
                    "timestamp": "2024-07-01T10:00:00Z",
                    "ip_address": "203.0.113.5"
                },
                "customer_profile": {
                    "name": "John Doe",
                    "age": 42,
                    "address": "123 Main St, New York, NY",
                    "home_state": "NY",
                    "account_tenure_years": 6.5,
                    "account_status": "good_standing",
                    "contact_email": "john.doe@email.com",
                    "contact_phone": "+15551234567",
                    "typical_spending_range": {"min_amount": 20, "max_amount": 500, "currency": "USD"},
                    "recent_travel": ["California", "Texas"]
                },
                "transaction_history": {
                    "total_transactions": 120,
                    "avg_amount": 80.50,
                    "states_visited": ["NY", "CA", "TX"],
                    "merchant_categories": ["5999", "5411"],
                    "velocity_metrics": {"max_per_hour": 2, "max_per_day": 5},
                    "anomalies": [
                        {"type": "device", "description": "New device not seen before", "timestamp": "2024-07-01T10:00:00Z"}
                    ]
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "iOS",
                    "browser_fingerprint": "abc123",
                    "vpn_detected": True,
                    "tor_detected": False,
                    "ip_address": "203.0.113.5",
                    "location": "New York, NY",
                    "device_risk_score": 95,
                    "device_history": ["CUST-334899"]
                },
                "fraud_database_hits": {
                    "merchant_blacklist_hit": True,
                    "card_bin_attack": False,
                    "phone_fraud_list": False,
                    "fraud_database_notes": ["Merchant in global blacklist"]
                }
            }
        },
        {
            "name": "auto_decline_transaction",
            "tool_inputs": {
                "transaction_id": "TX-30003",
                "reason": "bad_merchant"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Transaction auto-declined due to blacklist and high risk score. Customer notified.",
                "result_data": {
                    "fraud_risk_score": 99,
                    "case_status": "auto_declined",
                    "recommended_action": "decline",
                    "customer_notification_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Transaction details and customer profile retrieved",
            "expected_state": {
                "transaction_id": "TX-30003",
                "merchant_blacklist_hit": True
            }
        },
        {
            "step": 2,
            "description": "Transaction history and device intelligence analyzed",
            "expected_state": {
                "device_risk_score": 95
            }
        },
        {
            "step": 3,
            "description": "Fraud risk score calculated and blacklist confirmed",
            "expected_state": {
                "fraud_risk_score": 99,
                "risk_factors": [
                    "blacklist_hit",
                    "device_fraud"
                ]
            }
        },
        {
            "step": 4,
            "description": "Auto-decline transaction and block card/account",
            "expected_state": {
                "block_status": "blocked",
                "notification_sent": True
            }
        }
    ]
    description = (
        "Tests success path for auto-decline when transaction is flagged by blacklist and high risk score. "
        "Auto-decline is triggered by a merchant blacklist hit and device fraud signals; "
        "the transaction is blocked and the customer is notified."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the straightforward auto-decline path (fraud_risk_score > 95) with clear fraud signals "
        "(blacklist hit and device risk). No ambiguous or conflicting data or escalation is required."
    )

class TestCase4_BankingFraudMonitoringSupportAgent_W2_easy(BaseBankingFraudMonitoringSupportAgentTestCase):
    """
    Obvious Fraud - Account Takeover Detected on ATM Transaction

    Validates success path for auto-decline when account takeover is confirmed and risk score is above threshold.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_W2_TC2"
    title = "Obvious Fraud - Account Takeover Detected on ATM Transaction"
    workflow = "W2"
    input_data = {
        "alert_id": "FA-883424",
        "customer_id": "CUST-102345",
        "alert_type": "account_takeover",
        "transaction_type": "atm",
        "lookback_days": 90,
        "additional_context": {
            "device_id": "DEV-400004",
            "location": "Chicago, IL",
            "ip_address": "198.51.100.10"
        }
    }
    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883424"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-102345"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-102345",
                "lookback_days": 90
            }
        },
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-400004"
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-40004",
                    "amount": 500.00,
                    "merchant_name": "ATM Network",
                    "merchant_mcc": "6011",
                    "location": "Chicago, IL",
                    "device_id": "DEV-400004",
                    "transaction_type": "atm",
                    "timestamp": "2024-06-27T12:00:00Z",
                    "ip_address": "198.51.100.10"
                },
                "customer_profile": {
                    "name": "John Doe",
                    "age": 37,
                    "address": "123 Main St, Chicago, IL",
                    "home_state": "IL",
                    "account_tenure_years": 7.2,
                    "account_status": "good_standing",
                    "contact_email": "john.doe@email.com",
                    "contact_phone": "+13125550000",
                    "typical_spending_range": {
                        "min_amount": 25.00,
                        "max_amount": 400.00,
                        "currency": "USD"
                    },
                    "recent_travel": []
                },
                "transaction_history": {
                    "total_transactions": 120,
                    "avg_amount": 110.00,
                    "states_visited": ["IL", "WI"],
                    "merchant_categories": ["6011", "5411"],
                    "velocity_metrics": {
                        "max_per_hour": 2,
                        "max_per_day": 4
                    },
                    "anomalies": []
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "Android",
                    "browser_fingerprint": "bf-998877",
                    "vpn_detected": False,
                    "tor_detected": True,
                    "ip_address": "198.51.100.10",
                    "location": "Chicago, IL",
                    "device_risk_score": 97,
                    "device_history": ["CUST-102345"]
                },
                "fraud_database_hits": {
                    "merchant_blacklist_hit": False,
                    "card_bin_attack": False,
                    "phone_fraud_list": False,
                    "fraud_database_notes": []
                }
            }
        },
        {
            "name": "cross_reference_fraud_databases",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-40004",
                    "amount": 500.00,
                    "merchant_name": "ATM Network",
                    "merchant_mcc": "6011",
                    "location": "Chicago, IL",
                    "device_id": "DEV-400004",
                    "transaction_type": "atm",
                    "timestamp": "2024-06-27T12:00:00Z",
                    "ip_address": "198.51.100.10"
                },
                "customer_profile": {
                    "name": "John Doe",
                    "age": 37,
                    "address": "123 Main St, Chicago, IL",
                    "home_state": "IL",
                    "account_tenure_years": 7.2,
                    "account_status": "good_standing",
                    "contact_email": "john.doe@email.com",
                    "contact_phone": "+13125550000",
                    "typical_spending_range": {
                        "min_amount": 25.00,
                        "max_amount": 400.00,
                        "currency": "USD"
                    },
                    "recent_travel": []
                }
            }
        },
        {
            "name": "auto_decline_transaction",
            "tool_inputs": {
                "transaction_id": "TX-40004",
                "reason": "confirmed_account_takeover"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Transaction auto-declined due to confirmed account takeover and high risk score. Customer notified.",
                "result_data": {
                    "fraud_risk_score": 98,
                    "case_status": "auto_declined",
                    "recommended_action": "decline",
                    "customer_notification_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Transaction details and customer profile retrieved",
            "expected_state": {
                "transaction_id": "TX-40004",
                "account_status": "good_standing"
            }
        },
        {
            "step": 2,
            "description": "Transaction history and device intelligence analyzed",
            "expected_state": {
                "device_risk_score": 97,
                "tor_detected": True
            }
        },
        {
            "step": 3,
            "description": "Fraud risk score calculated and takeover confirmed",
            "expected_state": {
                "fraud_risk_score": 98,
                "risk_factors": [
                    "account_takeover",
                    "device_fraud"
                ]
            }
        },
        {
            "step": 4,
            "description": "Auto-decline transaction and block account",
            "expected_state": {
                "block_status": "blocked",
                "notification_sent": True
            }
        }
    ]
    description = (
        "Validates success path for auto-decline when account takeover is confirmed and risk score is above threshold. "
        "Auto-decline based on account takeover signals and high risk score; transaction blocked and notifications sent."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This is an easy case as all fraud signals are clear, the risk score is well above the auto-decline threshold, "
        "and there is no ambiguity or need for escalation or human review. The workflow follows the straightforward W2 path."
    )

class TestCase5_BankingFraudMonitoringSupportAgent_W3_hard(BaseBankingFraudMonitoringSupportAgentTestCase):
    """
    High-Risk Online Transaction with Device Mismatch

    Covers escalation for a high-risk transaction with device anomaly and multiple fraud signals.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_BankingFraud_W3_TC1"
    title = "High-Risk Online Transaction with Device Mismatch"
    workflow = "W3"
    input_data = {
        "alert_id": "FA-883425",
        "customer_id": "CUST-334899",
        "alert_type": "card_not_present",
        "transaction_type": "online",
        "lookback_days": 180,
        "additional_context": {
            "device_id": "DEV-500005",
            "location": "Dallas, TX",
            "ip_address": "203.0.113.20"
        }
    }
    expected_tool_calls = [
        # Step 1: Retrieve transaction details, customer profile, transaction history
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883425"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-334899"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-334899",
                "lookback_days": 180
            }
        },
        # Step 2: Check device intelligence and cross-reference fraud databases
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-500005"
            }
        },
        {
            "name": "cross_reference_fraud_databases",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-50005",
                    "amount": 249.99,
                    "merchant_name": "OnlineElectro",
                    "merchant_mcc": "5732",
                    "location": "Dallas, TX",
                    "device_id": "DEV-500005",
                    "transaction_type": "online",
                    "timestamp": "2024-07-10T13:22:00Z",
                    "ip_address": "203.0.113.20"
                },
                "customer_profile": {
                    "name": "Jane Doe",
                    "age": 34,
                    "address": "123 Main St, Dallas, TX",
                    "home_state": "TX",
                    "account_tenure_years": 5.2,
                    "account_status": "good_standing",
                    "contact_email": "jane.doe@email.com",
                    "contact_phone": "+12145551234",
                    "typical_spending_range": {
                        "min_amount": 10.0,
                        "max_amount": 300.0,
                        "currency": "USD"
                    },
                    "recent_travel": ["Houston, TX", "Austin, TX"]
                }
            }
        },
        # Step 3: Calculate fraud risk score
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-50005",
                    "amount": 249.99,
                    "merchant_name": "OnlineElectro",
                    "merchant_mcc": "5732",
                    "location": "Dallas, TX",
                    "device_id": "DEV-500005",
                    "transaction_type": "online",
                    "timestamp": "2024-07-10T13:22:00Z",
                    "ip_address": "203.0.113.20"
                },
                "customer_profile": {
                    "name": "Jane Doe",
                    "age": 34,
                    "address": "123 Main St, Dallas, TX",
                    "home_state": "TX",
                    "account_tenure_years": 5.2,
                    "account_status": "good_standing",
                    "contact_email": "jane.doe@email.com",
                    "contact_phone": "+12145551234",
                    "typical_spending_range": {
                        "min_amount": 10.0,
                        "max_amount": 300.0,
                        "currency": "USD"
                    },
                    "recent_travel": ["Houston, TX", "Austin, TX"]
                },
                "transaction_history": {
                    "total_transactions": 50,
                    "avg_amount": 120.56,
                    "states_visited": ["TX", "OK", "LA"],
                    "merchant_categories": ["5732", "5999"],
                    "velocity_metrics": {
                        "max_per_hour": 3,
                        "max_per_day": 7
                    },
                    "anomalies": [
                        {
                            "type": "velocity_anomaly",
                            "description": "Multiple high-value purchases in short time frame",
                            "timestamp": "2024-07-10T13:20:00Z"
                        }
                    ]
                },
                "device_intelligence": {
                    "device_type": "desktop",
                    "os": "Windows 10",
                    "browser_fingerprint": "bf-abc123",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "203.0.113.20",
                    "location": "Dallas, TX",
                    "device_risk_score": 80,
                    "device_history": ["CUST-334899", "CUST-100200"]
                },
                "fraud_database_hits": {
                    "merchant_blacklist_hit": False,
                    "card_bin_attack": False,
                    "phone_fraud_list": False,
                    "fraud_database_notes": []
                }
            }
        },
        # Step 4: Route to analyst
        {
            "name": "route_to_analyst",
            "tool_inputs": {
                "alert_id": "FA-883425",
                "investigation_package": {
                    "transaction_id": "TX-50005",
                    "risk_factors": [
                        "device_mismatch",
                        "velocity_anomaly"
                    ],
                    "summary": "High-risk online purchase with device mismatch and rapid transaction velocity."
                },
                "recommended_action": "block_card"
            }
        },
        # Step 5: Confirm escalation and log summary
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Case escalated to analyst with full investigation package and recommended action.",
                "result_data": {
                    "fraud_risk_score": 85,
                    "case_status": "escalated",
                    "recommended_action": "block_card",
                    "investigation_package": {
                        "transaction_id": "TX-50005",
                        "risk_factors": [
                            "device_mismatch",
                            "velocity_anomaly"
                        ],
                        "summary": "High-risk online purchase with device mismatch and rapid transaction velocity."
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Transaction details, customer profile, and history retrieved",
            "expected_state": {
                "transaction_id": "TX-50005",
                "total_transactions": 50
            }
        },
        {
            "step": 2,
            "description": "Device intelligence and fraud database cross-referenced",
            "expected_state": {
                "device_risk_score": 80,
                "merchant_blacklist_hit": False
            }
        },
        {
            "step": 3,
            "description": "Fraud risk score calculated and investigation package compiled",
            "expected_state": {
                "fraud_risk_score": 85
            }
        },
        {
            "step": 4,
            "description": "Case routed to analyst",
            "expected_state": {
                "case_id": "CASE-50005",
                "escalation_level": "normal"
            }
        }
    ]
    description = "Covers escalation for a high-risk transaction with device anomaly and multiple fraud signals."
    difficulty = "hard"
    difficulty_reasoning = (
        "This test requires orchestrating multiple data enrichment steps, handling device and velocity anomalies, "
        "compiling a detailed investigation package, and ensuring correct escalation logic. "
        "The scenario involves high risk but not an outright blacklist or auto-decline, so the agent must "
        "demonstrate nuanced decision-making and comprehensive context gathering."
    )

class TestCase6_BankingFraudMonitoringSupportAgent_W3_medium(BaseBankingFraudMonitoringSupportAgentTestCase):
    """High-Risk Card Present Transaction with Location Anomaly

    Success path for escalation when physical transaction occurs in unusual location, but all data is available.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_BankingFraud_W3_TC2"
    title = "High-Risk Card Present Transaction with Location Anomaly"
    workflow = "W3"
    input_data = {
        "alert_id": "FA-883426",
        "customer_id": "CUST-102345",
        "alert_type": "card_present",
        "transaction_type": "card_present",
        "lookback_days": 120,
        "additional_context": {
            "device_id": "DEV-600006",
            "location": "Las Vegas, NV",
            "ip_address": "198.51.100.55"
        }
    }

    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883426"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-102345"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-102345",
                "lookback_days": 120
            }
        },
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-600006"
            }
        },
        {
            "name": "cross_reference_fraud_databases",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-60006",
                    "amount": 1200.00,
                    "merchant_name": "Las Vegas Casino",
                    "merchant_mcc": "7995",
                    "location": "Las Vegas, NV",
                    "device_id": "DEV-600006",
                    "transaction_type": "card_present",
                    "timestamp": "2025-07-01T18:20:00Z",
                    "ip_address": "198.51.100.55"
                },
                "customer_profile": {
                    "name": "Jane Doe",
                    "age": 42,
                    "address": "123 Main St, Los Angeles, CA",
                    "home_state": "CA",
                    "account_tenure_years": 7.2,
                    "account_status": "good_standing",
                    "contact_email": "jane.doe@email.com",
                    "contact_phone": "+15551234567",
                    "typical_spending_range": {
                        "min_amount": 20.0,
                        "max_amount": 500.0,
                        "currency": "USD"
                    },
                    "recent_travel": ["CA"]
                }
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-60006",
                    "amount": 1200.00,
                    "merchant_name": "Las Vegas Casino",
                    "merchant_mcc": "7995",
                    "location": "Las Vegas, NV",
                    "device_id": "DEV-600006",
                    "transaction_type": "card_present",
                    "timestamp": "2025-07-01T18:20:00Z",
                    "ip_address": "198.51.100.55"
                },
                "customer_profile": {
                    "name": "Jane Doe",
                    "age": 42,
                    "address": "123 Main St, Los Angeles, CA",
                    "home_state": "CA",
                    "account_tenure_years": 7.2,
                    "account_status": "good_standing",
                    "contact_email": "jane.doe@email.com",
                    "contact_phone": "+15551234567",
                    "typical_spending_range": {
                        "min_amount": 20.0,
                        "max_amount": 500.0,
                        "currency": "USD"
                    },
                    "recent_travel": ["CA"]
                },
                "transaction_history": {
                    "total_transactions": 320,
                    "avg_amount": 130.45,
                    "states_visited": ["CA", "NV"],
                    "merchant_categories": ["5411", "5812", "7995"],
                    "velocity_metrics": {"max_per_hour": 2, "max_per_day": 7},
                    "anomalies": [
                        {
                            "type": "location_anomaly",
                            "description": "Transaction in new state (NV) for customer.",
                            "timestamp": "2025-07-01T18:20:00Z"
                        }
                    ]
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "iOS 17.0",
                    "browser_fingerprint": "bf-abc123",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "198.51.100.55",
                    "location": "Las Vegas, NV",
                    "device_risk_score": 25,
                    "device_history": ["CUST-102345"]
                },
                "fraud_database_hits": {
                    "merchant_blacklist_hit": False,
                    "card_bin_attack": False,
                    "phone_fraud_list": False,
                    "fraud_database_notes": []
                }
            }
        },
        {
            "name": "route_to_analyst",
            "tool_inputs": {
                "alert_id": "FA-883426",
                "investigation_package": {
                    "transaction_id": "TX-60006",
                    "risk_factors": ["location_anomaly"],
                    "summary": "High-risk in-person transaction in new location for customer."
                },
                "recommended_action": "contact_customer"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Case escalated to analyst with full investigation package and recommended action.",
                "result_data": {
                    "final_status": "escalated",
                    "key_outputs": {
                        "fraud_risk_score": 90,
                        "case_status": "escalated",
                        "recommended_action": "contact_customer",
                        "investigation_package": {
                            "transaction_id": "TX-60006",
                            "risk_factors": ["location_anomaly"],
                            "summary": "High-risk in-person transaction in new location for customer."
                        }
                    }
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Transaction details, customer profile, and history retrieved",
            "expected_state": {
                "transaction_id": "TX-60006",
                "states_visited": [
                    "CA",
                    "NV"
                ]
            }
        },
        {
            "step": 2,
            "description": "Device intelligence and fraud database cross-referenced",
            "expected_state": {
                "device_risk_score": 25,
                "merchant_blacklist_hit": False
            }
        },
        {
            "step": 3,
            "description": "Fraud risk score calculated and investigation package compiled",
            "expected_state": {
                "fraud_risk_score": 90
            }
        },
        {
            "step": 4,
            "description": "Case routed to analyst",
            "expected_state": {
                "case_id": "CASE-60006",
                "escalation_level": "normal"
            }
        }
    ]

    description = (
        "Success path for escalation when physical transaction occurs in unusual location, "
        "but all data is available. Escalation due to location anomaly; device matches but "
        "transaction is physically out of pattern."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This scenario involves a high-risk, card-present transaction in a new location for the customer. "
        "Although device intelligence matches and there are no blacklist hits, the location anomaly triggers "
        "escalation. The test exercises the full data enrichment and risk scoring pipeline, but all data sources "
        "are available and consistent, making this a standard but non-trivial success path for escalation."
    )

class TestCase7_BankingFraudMonitoringSupportAgent_W4_medium(BaseBankingFraudMonitoringSupportAgentTestCase):
    """Moderate-Risk Transaction, Customer Verifies via SMS

    Covers approval path where risk score is moderate and customer successfully verifies via preferred method.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_W4_TC1"
    title = "Moderate-Risk Transaction, Customer Verifies via SMS"
    workflow = "W4"
    input_data = {
        "alert_id": "FA-883427",
        "customer_id": "CUST-334899",
        "alert_type": "card_not_present",
        "transaction_type": "online",
        "lookback_days": 90,
        "preferred_verification_method": "sms",
        "additional_context": {
            "device_id": "DEV-700007",
            "location": "Seattle, WA",
            "ip_address": "203.0.113.40"
        }
    }

    # The expected tool call sequence follows the W4 workflow, using realistic mock responses and input data.
    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883427"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-334899"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-334899",
                "lookback_days": 90
            }
        },
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-700007"
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-70007",
                    "amount": 120.50,
                    "merchant_name": "Seattle Books",
                    "merchant_mcc": "5942",
                    "location": "Seattle, WA",
                    "device_id": "DEV-700007",
                    "transaction_type": "online",
                    "timestamp": "2024-07-01T16:15:00Z",
                    "ip_address": "203.0.113.40"
                },
                "customer_profile": {
                    "name": "Jordan Smith",
                    "age": 38,
                    "address": "500 Pine St, Seattle, WA",
                    "home_state": "WA",
                    "account_tenure_years": 5.2,
                    "account_status": "good_standing",
                    "contact_email": "jordan.smith@email.com",
                    "contact_phone": "+12065551234",
                    "typical_spending_range": {
                        "min_amount": 30,
                        "max_amount": 300,
                        "currency": "USD"
                    },
                    "recent_travel": ["Portland, OR"]
                },
                "transaction_history": {
                    "total_transactions": 35,
                    "avg_amount": 110.75,
                    "states_visited": ["WA", "OR"],
                    "merchant_categories": ["5942", "5812"],
                    "velocity_metrics": {"max_per_hour": 2, "max_per_day": 4},
                    "anomalies": []
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "Android 12",
                    "browser_fingerprint": "bfp-1234567890",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "203.0.113.40",
                    "location": "Seattle, WA",
                    "device_risk_score": 40,
                    "device_history": ["CUST-334899"]
                },
                "fraud_database_hits": {
                    "merchant_blacklist_hit": False,
                    "card_bin_attack": False,
                    "phone_fraud_list": False,
                    "fraud_database_notes": []
                }
            }
        },
        {
            "name": "request_customer_verification",
            "tool_inputs": {
                "customer_id": "CUST-334899",
                "method": "sms",
                "alert_id": "FA-883427",
                "message_content": "We detected an online transaction flagged for review. Reply YES to verify or NO if unauthorized."
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Customer verified transaction via SMS; case marked as verified and approved.",
                "result_data": {
                    "fraud_risk_score": 65,
                    "case_status": "verified",
                    "recommended_action": "approve",
                    "customer_notification_status": "sent"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Transaction details and customer profile retrieved",
            "expected_state": {
                "transaction_id": "TX-70007",
                "account_status": "good_standing"
            }
        },
        {
            "step": 2,
            "description": "Transaction history and device intelligence analyzed",
            "expected_state": {
                "device_risk_score": 40
            }
        },
        {
            "step": 3,
            "description": "Fraud risk score calculated",
            "expected_state": {
                "fraud_risk_score": 65
            }
        },
        {
            "step": 4,
            "description": "Customer verification requested via SMS",
            "expected_state": {
                "delivery_status": "sent",
                "customer_response": "verified"
            }
        }
    ]

    description = (
        "Covers approval path where risk score is moderate (65) and customer successfully verifies via preferred method (SMS). "
        "Moderate risk triggers verification; customer verifies via SMS, transaction approved."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This test involves a moderate-risk scenario requiring coordinated multi-system data enrichment, "
        "risk scoring, and customer verification workflow. It exercises the verification branch and success path, "
        "with realistic data flows for a moderate-complexity fraud alert."
    )

    # No tool method overrides needed for this success path scenario.

class TestCase8_BankingFraudMonitoringSupportAgent_W4_medium(BaseBankingFraudMonitoringSupportAgentTestCase):
    """Moderate-Risk Transaction, Customer Verifies via Email

    Validates approval path using alternate verification method (email) with successful customer verification.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_W4_TC2"
    title = "Moderate-Risk Transaction, Customer Verifies via Email"
    workflow = "W4"
    input_data = {
        "alert_id": "FA-883428",
        "customer_id": "CUST-102345",
        "alert_type": "card_present",
        "transaction_type": "card_present",
        "lookback_days": 60,
        "preferred_verification_method": "email",
        "additional_context": {
            "device_id": "DEV-800008",
            "location": "Denver, CO",
            "ip_address": "198.51.100.80"
        }
    }
    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883428"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-102345"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-102345",
                "lookback_days": 60
            }
        },
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-800008"
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-80008",
                    "amount": 120.50,
                    "merchant_name": "Denver Books",
                    "merchant_mcc": "5942",
                    "location": "Denver, CO",
                    "device_id": "DEV-800008",
                    "transaction_type": "card_present",
                    "timestamp": "2024-06-15T14:32:00Z",
                    "ip_address": "198.51.100.80"
                },
                "customer_profile": {
                    "name": "Jessica Owen",
                    "age": 42,
                    "address": "123 Main St, Denver, CO",
                    "home_state": "CO",
                    "account_tenure_years": 7.5,
                    "account_status": "good_standing",
                    "contact_email": "jessica.owen@email.com",
                    "contact_phone": "+13035551234",
                    "typical_spending_range": {"min_amount": 20, "max_amount": 200, "currency": "USD"},
                    "recent_travel": ["Las Vegas, NV", "Dallas, TX"]
                },
                "transaction_history": {
                    "total_transactions": 48,
                    "avg_amount": 95.00,
                    "states_visited": ["CO", "NV", "TX"],
                    "merchant_categories": ["5942", "5411"],
                    "velocity_metrics": {"max_per_hour": 2, "max_per_day": 4},
                    "anomalies": []
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "iOS 17",
                    "browser_fingerprint": "bf-998877aa",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "198.51.100.80",
                    "location": "Denver, CO",
                    "device_risk_score": 30,
                    "device_history": ["CUST-102345"]
                },
                "fraud_database_hits": {
                    "merchant_blacklist_hit": False,
                    "card_bin_attack": False,
                    "phone_fraud_list": False,
                    "fraud_database_notes": []
                }
            }
        },
        {
            "name": "request_customer_verification",
            "tool_inputs": {
                "customer_id": "CUST-102345",
                "method": "email",
                "alert_id": "FA-883428",
                "message_content": "We detected a moderate-risk transaction on your account ending in 2345 at Denver Books for $120.50. Please confirm if this was you."
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Customer verified via email. Transaction approved and alert closed.",
                "result_data": {
                    "fraud_risk_score": 55,
                    "case_status": "verified",
                    "recommended_action": "approve",
                    "customer_notification_status": "sent"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Transaction details and customer profile retrieved",
            "expected_state": {
                "transaction_id": "TX-80008",
                "account_status": "good_standing"
            }
        },
        {
            "step": 2,
            "description": "Transaction history and device intelligence analyzed",
            "expected_state": {
                "device_risk_score": 30
            }
        },
        {
            "step": 3,
            "description": "Fraud risk score calculated",
            "expected_state": {
                "fraud_risk_score": 55
            }
        },
        {
            "step": 4,
            "description": "Customer verification requested via email",
            "expected_state": {
                "delivery_status": "sent",
                "customer_response": "verified"
            }
        }
    ]
    description = "Validates approval path using alternate verification method (email) with successful customer verification."
    difficulty = "medium"
    difficulty_reasoning = (
        "This test involves a moderate fraud risk score (55) that triggers the customer verification workflow (W4). "
        "It tests correct routing through all enrichment steps, use of the non-default 'email' verification channel, "
        "and proper handling of a positive customer response. The scenario is more complex than auto-approve/decline, "
        "but does not require escalation or failure handling, making it of medium difficulty."
    )

    # No tool overrides are necessary for this test case; all behavior follows the standard path for W4.

class TestCase9_BankingFraudMonitoringSupportAgent_W5_hard(BaseBankingFraudMonitoringSupportAgentTestCase):
    """Account Takeover - Immediate Block and Escalation"""

    test_case_id = "BankingFraudMonitoringSupportAgent_W5_TC1"
    title = "Account Takeover - Immediate Block and Escalation"
    workflow = "W5"

    input_data = {
        "alert_id": "FA-883429",
        "customer_id": "CUST-334899",
        "alert_type": "account_takeover",
        "transaction_type": "online",
        "lookback_days": 30,
        "additional_context": {
            "device_id": "DEV-900009",
            "location": "Boston, MA",
            "ip_address": "203.0.113.99"
        }
    }

    expected_tool_calls = [
        # Step 1: Retrieve transaction details and customer profile
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883429"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-334899"
            }
        },
        # Step 2: Check device intelligence and analyze transaction history
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-900009"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-334899",
                "lookback_days": 30
            }
        },
        # Step 3: Calculate fraud risk score
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-90009",
                    "amount": 5000.00,
                    "merchant_name": "N/A",
                    "merchant_mcc": "0000",
                    "location": "Boston, MA",
                    "device_id": "DEV-900009",
                    "transaction_type": "online",
                    "timestamp": "2025-04-01T10:00:00Z",
                    "ip_address": "203.0.113.99"
                },
                "customer_profile": {
                    "name": "Jane Doe",
                    "age": 42,
                    "address": "123 Main St, Boston, MA",
                    "home_state": "MA",
                    "account_tenure_years": 5.0,
                    "account_status": "good_standing",
                    "contact_email": "jane.doe@email.com",
                    "contact_phone": "+15555551234",
                    "typical_spending_range": {
                        "min_amount": 20.0,
                        "max_amount": 1000.0,
                        "currency": "USD"
                    },
                    "recent_travel": ["Boston, MA"]
                },
                "transaction_history": {
                    "total_transactions": 200,
                    "avg_amount": 120.00,
                    "states_visited": ["MA", "NH"],
                    "merchant_categories": ["5411", "5812"],
                    "velocity_metrics": {"max_per_hour": 2, "max_per_day": 8},
                    "anomalies": [
                        {
                            "type": "device_anomaly",
                            "description": "Unrecognized device used for login",
                            "timestamp": "2025-04-01T09:58:00Z"
                        }
                    ]
                },
                "device_intelligence": {
                    "device_type": "desktop",
                    "os": "Windows 10",
                    "browser_fingerprint": "bf-123456",
                    "vpn_detected": True,
                    "tor_detected": False,
                    "ip_address": "203.0.113.99",
                    "location": "Boston, MA",
                    "device_risk_score": 95,
                    "device_history": ["CUST-334899", "CUST-998877"]
                }
            }
        },
        # Step 4: Auto-decline and block account access
        {
            "name": "auto_decline_transaction",
            "tool_inputs": {
                "transaction_id": "TX-90009",
                "reason": "confirmed_account_takeover"
            }
        },
        # Step 5: Route case to analyst with urgent escalation
        {
            "name": "route_to_analyst",
            "tool_inputs": {
                "alert_id": "FA-883429",
                "investigation_package": {
                    "transaction_id": "TX-90009",
                    "risk_factors": [
                        "account_takeover",
                        "device_anomaly"
                    ],
                    "summary": "Account takeover confirmed via device and login anomalies."
                },
                "recommended_action": "close_account"
            }
        },
        # Step 6: Log action and notify (success)
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Account access blocked and case escalated to analyst urgently.",
                "result_data": {
                    "final_status": "blocked",
                    "fraud_risk_score": 97,
                    "case_status": "blocked",
                    "recommended_action": "close_account",
                    "investigation_package": {
                        "transaction_id": "TX-90009",
                        "risk_factors": [
                            "account_takeover",
                            "device_anomaly"
                        ],
                        "summary": "Account takeover confirmed via device and login anomalies."
                    }
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Login and transaction details, customer profile retrieved",
            "expected_state": {
                "transaction_id": "TX-90009",
                "account_status": "good_standing"
            }
        },
        {
            "step": 2,
            "description": "Device intelligence and recent account changes checked",
            "expected_state": {
                "device_risk_score": 95
            }
        },
        {
            "step": 3,
            "description": "Fraud risk score calculated",
            "expected_state": {
                "fraud_risk_score": 97
            }
        },
        {
            "step": 4,
            "description": "Account access blocked",
            "expected_state": {
                "block_status": "blocked",
                "notification_sent": True
            }
        },
        {
            "step": 5,
            "description": "Case routed to analyst with urgent escalation",
            "expected_state": {
                "escalation_level": "urgent"
            }
        }
    ]

    description = (
        "Covers urgent block and escalation for confirmed account takeover with device and login anomalies."
    )
    difficulty = "hard"
    difficulty_reasoning = (
        "This test case involves a high-severity fraud scenario (account takeover) requiring immediate multi-step automation: "
        "retrieval of multiple data sources, detection and handling of device anomalies, calculation of a high fraud risk score, "
        "automatic blocking of account access, and urgent escalation to an analyst with a complete investigation package. "
        "The workflow is complex, involves multiple tools with tightly coupled data, and must ensure regulatory notification and "
        "case handoff. All signals are present, so the system must act without ambiguity or human intervention."
    )

class TestCase10_BankingFraudMonitoringSupportAgent_W6_medium(BaseBankingFraudMonitoringSupportAgentTestCase):
    """
    Velocity Fraud - Rapid Transactions Across States

    Success path for velocity fraud with rapid multi-state transactions and high velocity metrics.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_W6_TC1"
    title = "Velocity Fraud - Rapid Transactions Across States"
    workflow = "W6"
    input_data = {
        "alert_id": "FA-883430",
        "customer_id": "CUST-102345",
        "alert_type": "velocity_fraud",
        "transaction_type": "card_not_present",
        "lookback_days": 7,
        "additional_context": {
            "device_id": "DEV-100010",
            "location": "Houston, TX",
            "ip_address": "198.51.100.101"
        }
    }
    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883430"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-102345",
                "lookback_days": 7
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-100010",
                    "amount": 250.00,
                    "merchant_name": "SpeedyMart",
                    "merchant_mcc": "5411",
                    "location": "Houston, TX",
                    "device_id": "DEV-100010",
                    "transaction_type": "card_not_present",
                    "timestamp": "2025-04-10T09:10:00Z",
                    "ip_address": "198.51.100.101"
                },
                "customer_profile": {
                    "name": "Jane Doe",
                    "age": 34,
                    "address": "123 Main St, Houston, TX",
                    "home_state": "TX",
                    "account_tenure_years": 4.2,
                    "account_status": "good_standing",
                    "contact_email": "jane.doe@email.com",
                    "contact_phone": "+18325551234",
                    "typical_spending_range": {
                        "min_amount": 15.0,
                        "max_amount": 600.0,
                        "currency": "USD"
                    },
                    "recent_travel": ["TX", "LA"]
                },
                "transaction_history": {
                    "total_transactions": 45,
                    "avg_amount": 70.50,
                    "states_visited": ["TX", "LA", "OK", "NM"],
                    "merchant_categories": ["5411", "5812", "5541"],
                    "velocity_metrics": {"max_per_hour": 10, "max_per_day": 25},
                    "anomalies": [
                        {
                            "type": "velocity_anomaly",
                            "description": "10 transactions in 1 hour",
                            "timestamp": "2025-04-10T09:00:00Z"
                        },
                        {
                            "type": "multi_state_usage",
                            "description": "Transactions in TX and OK within 30min",
                            "timestamp": "2025-04-10T08:45:00Z"
                        }
                    ]
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "Android 13",
                    "browser_fingerprint": "bf-fd1a2c",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "198.51.100.101",
                    "location": "Houston, TX",
                    "device_risk_score": 48,
                    "device_history": ["CUST-102345"]
                }
            }
        },
        {
            "name": "cross_reference_fraud_databases",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-100010",
                    "amount": 250.00,
                    "merchant_name": "SpeedyMart",
                    "merchant_mcc": "5411",
                    "location": "Houston, TX",
                    "device_id": "DEV-100010",
                    "transaction_type": "card_not_present",
                    "timestamp": "2025-04-10T09:10:00Z",
                    "ip_address": "198.51.100.101"
                }
            }
        },
        {
            "name": "route_to_analyst",
            "tool_inputs": {
                "alert_id": "FA-883430",
                "investigation_package": {
                    "transaction_id": "TX-100010",
                    "risk_factors": [
                        "velocity_anomaly",
                        "multi_state_usage"
                    ],
                    "summary": "Rapid transactions detected across multiple states."
                },
                "recommended_action": "block_card"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Velocity fraud escalation complete. Case routed to analyst with investigation package.",
                "result_data": {
                    "fraud_risk_score": 80,
                    "case_status": "escalated",
                    "recommended_action": "block_card",
                    "investigation_package": {
                        "transaction_id": "TX-100010",
                        "risk_factors": [
                            "velocity_anomaly",
                            "multi_state_usage"
                        ],
                        "summary": "Rapid transactions detected across multiple states."
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Transaction details and transaction history retrieved",
            "expected_state": {
                "transaction_id": "TX-100010",
                "velocity_metrics": {
                    "max_per_hour": 10
                }
            }
        },
        {
            "step": 2,
            "description": "Fraud risk score calculated",
            "expected_state": {
                "fraud_risk_score": 80
            }
        },
        {
            "step": 3,
            "description": "Fraud databases cross-referenced for merchant risk",
            "expected_state": {
                "merchant_blacklist_hit": False
            }
        },
        {
            "step": 4,
            "description": "Case routed to analyst",
            "expected_state": {
                "case_id": "CASE-100010",
                "escalation_level": "normal"
            }
        }
    ]
    description = (
        "Success path for velocity fraud with rapid multi-state transactions and high velocity metrics. "
        "Escalation based on velocity and geographic anomalies; all data available for analyst review."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This test case involves multiple data enrichment steps, velocity and geographic anomaly detection, "
        "risk scoring, blacklist checks, and escalation logic. It is more complex than a simple approval/decline, "
        "but follows a clear, successful escalation path with no ambiguous or failure conditions."
    )

class TestCase11_BankingFraudMonitoringSupportAgent_W7_medium(BaseBankingFraudMonitoringSupportAgentTestCase):
    """Synthetic Identity - New Account Device and Identity Anomalies

    Covers escalation for new account with synthetic identity signals and device anomalies.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_W7_TC1"
    title = "Synthetic Identity - New Account Device and Identity Anomalies"
    workflow = "W7"
    input_data = {
        "alert_id": "FA-883431",
        "customer_id": "CUST-334899",
        "alert_type": "synthetic_identity",
        "transaction_type": "online",
        "lookback_days": 1,
        "additional_context": {
            "device_id": "DEV-110011",
            "location": "Orlando, FL",
            "ip_address": "203.0.113.111"
        }
    }
    expected_tool_calls = [
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-334899"
            }
        },
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-110011"
            }
        },
        {
            "name": "cross_reference_fraud_databases",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-110011",
                    "amount": 2500.00,
                    "merchant_name": "New Account Funding",
                    "merchant_mcc": "6011",
                    "location": "Orlando, FL",
                    "device_id": "DEV-110011",
                    "transaction_type": "online",
                    "timestamp": "2025-01-11T13:01:00Z",
                    "ip_address": "203.0.113.111"
                },
                "customer_profile": {
                    "name": "Taylor Smith",
                    "age": 28,
                    "address": "101 Main St, Orlando, FL",
                    "home_state": "FL",
                    "account_tenure_years": 0.1,
                    "account_status": "good_standing",
                    "contact_email": "taylor.smith@email.com",
                    "contact_phone": "+14075550011",
                    "typical_spending_range": {
                        "min_amount": 100.00,
                        "max_amount": 4000.00,
                        "currency": "USD"
                    },
                    "recent_travel": []
                }
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-110011",
                    "amount": 2500.00,
                    "merchant_name": "New Account Funding",
                    "merchant_mcc": "6011",
                    "location": "Orlando, FL",
                    "device_id": "DEV-110011",
                    "transaction_type": "online",
                    "timestamp": "2025-01-11T13:01:00Z",
                    "ip_address": "203.0.113.111"
                },
                "customer_profile": {
                    "name": "Taylor Smith",
                    "age": 28,
                    "address": "101 Main St, Orlando, FL",
                    "home_state": "FL",
                    "account_tenure_years": 0.1,
                    "account_status": "good_standing",
                    "contact_email": "taylor.smith@email.com",
                    "contact_phone": "+14075550011",
                    "typical_spending_range": {
                        "min_amount": 100.00,
                        "max_amount": 4000.00,
                        "currency": "USD"
                    },
                    "recent_travel": []
                },
                "transaction_history": {
                    "total_transactions": 1,
                    "avg_amount": 2500.00,
                    "states_visited": ["FL"],
                    "merchant_categories": ["6011"],
                    "velocity_metrics": {
                        "max_per_hour": 1,
                        "max_per_day": 1
                    },
                    "anomalies": [
                        {
                            "type": "synthetic_identity",
                            "description": "New account with minimal history",
                            "timestamp": "2025-01-11T13:01:00Z"
                        }
                    ]
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "Android 13",
                    "browser_fingerprint": "bf-998877",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "203.0.113.111",
                    "location": "Orlando, FL",
                    "device_risk_score": 90,
                    "device_history": []
                },
                "fraud_database_hits": {
                    "merchant_blacklist_hit": False,
                    "card_bin_attack": False,
                    "phone_fraud_list": False,
                    "fraud_database_notes": []
                }
            }
        },
        {
            "name": "route_to_analyst",
            "tool_inputs": {
                "alert_id": "FA-883431",
                "investigation_package": {
                    "transaction_id": "TX-110011",
                    "risk_factors": [
                        "synthetic_identity",
                        "device_anomaly"
                    ],
                    "summary": "Synthetic identity signals detected for new account."
                },
                "recommended_action": "escalate_sar"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Synthetic identity alert escalated to analyst with full package.",
                "result_data": {
                    "final_status": "escalated",
                    "fraud_risk_score": 92,
                    "case_status": "escalated",
                    "recommended_action": "escalate_sar",
                    "investigation_package": {
                        "transaction_id": "TX-110011",
                        "risk_factors": [
                            "synthetic_identity",
                            "device_anomaly"
                        ],
                        "summary": "Synthetic identity signals detected for new account."
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Customer profile and identity details retrieved",
            "expected_state": {
                "account_tenure_years": 0.1
            }
        },
        {
            "step": 2,
            "description": "Device intelligence and identity databases checked",
            "expected_state": {
                "device_risk_score": 90
            }
        },
        {
            "step": 3,
            "description": "Fraud risk score calculated",
            "expected_state": {
                "fraud_risk_score": 92
            }
        },
        {
            "step": 4,
            "description": "Case routed to analyst",
            "expected_state": {
                "escalation_level": "normal"
            }
        }
    ]
    description = "Covers escalation for new account with synthetic identity signals and device anomalies."
    difficulty = "medium"
    difficulty_reasoning = (
        "The case involves multiple data sources (customer, device, fraud DBs), "
        "requires structured investigation packaging, and triggers escalation logic for synthetic identity—"
        "but all required data is present and the workflow is linear without ambiguous signals."
    )

class TestCase12_BankingFraudMonitoringSupportAgent_W8_easy(BaseBankingFraudMonitoringSupportAgentTestCase):
    """
    Test case for: Friendly Fraud - Chargeback Investigation, Evidence Provided

    Success path for friendly fraud chargeback investigation with all required evidence present.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_W8_TC1"
    title = "Friendly Fraud - Chargeback Investigation, Evidence Provided"
    workflow = "W8"
    input_data = {
        "alert_id": "FA-883432",
        "customer_id": "CUST-102345",
        "alert_type": "friendly_fraud",
        "transaction_type": "card_present",
        "lookback_days": 30,
        "additional_context": {
            "device_id": "DEV-120012",
            "location": "Phoenix, AZ",
            "ip_address": "198.51.100.120",
            "delivery_confirmation": True,
            "signature_match": True
        }
    }
    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883432"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-102345"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-102345",
                "lookback_days": 30
            }
        },
        {
            "name": "check_device_intelligence",
            "tool_inputs": {
                "device_id": "DEV-120012"
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-120012",
                    "amount": 125.00,
                    "merchant_name": "Phoenix Electronics",
                    "merchant_mcc": "5732",
                    "location": "Phoenix, AZ",
                    "device_id": "DEV-120012",
                    "transaction_type": "card_present",
                    "timestamp": "2024-07-01T14:22:00Z",
                    "ip_address": "198.51.100.120"
                },
                "customer_profile": {
                    "name": "Jane Smith",
                    "age": 36,
                    "address": "123 Main St, Phoenix, AZ",
                    "home_state": "AZ",
                    "account_tenure_years": 6.5,
                    "account_status": "good_standing",
                    "contact_email": "jane.smith@email.com",
                    "contact_phone": "+16025551234",
                    "typical_spending_range": {
                        "min_amount": 20.00,
                        "max_amount": 500.00,
                        "currency": "USD"
                    },
                    "recent_travel": ["Phoenix, AZ"]
                },
                "transaction_history": {
                    "total_transactions": 120,
                    "avg_amount": 110.00,
                    "states_visited": ["AZ", "CA"],
                    "merchant_categories": ["5732", "5411"],
                    "velocity_metrics": {
                        "max_per_hour": 2,
                        "max_per_day": 4
                    },
                    "anomalies": []
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "iOS",
                    "browser_fingerprint": "bf-123456",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "198.51.100.120",
                    "location": "Phoenix, AZ",
                    "device_risk_score": 10,
                    "device_history": ["CUST-102345"]
                }
            }
        },
        {
            "name": "route_to_analyst",
            "tool_inputs": {
                "alert_id": "FA-883432",
                "investigation_package": {
                    "transaction_id": "TX-120012",
                    "risk_factors": ["friendly_fraud"],
                    "summary": "Evidence supports legitimate transaction; chargeback dispute flagged as friendly fraud."
                },
                "recommended_action": "deny_chargeback"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Chargeback investigation package routed to analyst with evidence for review.",
                "result_data": {
                    "final_status": "escalated",
                    "fraud_risk_score": 10,
                    "case_status": "escalated",
                    "recommended_action": "deny_chargeback",
                    "investigation_package": {
                        "transaction_id": "TX-120012",
                        "risk_factors": ["friendly_fraud"],
                        "summary": "Evidence supports legitimate transaction; chargeback dispute flagged as friendly fraud."
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Transaction details and customer profile retrieved",
            "expected_state": {
                "transaction_id": "TX-120012",
                "delivery_confirmation": True
            }
        },
        {
            "step": 2,
            "description": "Transaction history and device intelligence analyzed",
            "expected_state": {
                "device_risk_score": 10
            }
        },
        {
            "step": 3,
            "description": "Evidence compiled and fraud risk score calculated",
            "expected_state": {
                "fraud_risk_score": 10
            }
        },
        {
            "step": 4,
            "description": "Case routed to analyst with evidence summary",
            "expected_state": {
                "case_id": "CASE-120012",
                "escalation_level": "normal"
            }
        }
    ]
    description = "Success path for friendly fraud chargeback investigation with all required evidence present."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows a straight-through, low-risk scenario for friendly fraud: "
        "all required evidence (delivery, signature, device match) is present, there are no anomalies, "
        "and the workflow is a direct escalation to analyst with a complete package. There are no ambiguous "
        "signals, missing data, or error handling required, making it a routine and low-complexity case."
    )

class TestCase13_BankingFraudMonitoringSupportAgent_W9_medium(BaseBankingFraudMonitoringSupportAgentTestCase):
    """
    APP Fraud - Large Wire Transfer Held and Escalated

    Covers success path for holding suspicious wire transfer and escalating for analyst review.
    """

    test_case_id = "BankingFraudMonitoringSupportAgent_W9_TC1"
    title = "APP Fraud - Large Wire Transfer Held and Escalated"
    workflow = "W9"
    input_data = {
        "alert_id": "FA-883433",
        "customer_id": "CUST-334899",
        "alert_type": "authorized_push_payment",
        "transaction_type": "wire",
        "lookback_days": 2,
        "additional_context": {
            "device_id": "DEV-130013",
            "location": "Atlanta, GA",
            "ip_address": "203.0.113.131",
            "call_recording": "customer sounded confused"
        }
    }
    expected_tool_calls = [
        {
            "name": "retrieve_transaction_details",
            "tool_inputs": {
                "alert_id": "FA-883433"
            }
        },
        {
            "name": "get_customer_profile",
            "tool_inputs": {
                "customer_id": "CUST-334899"
            }
        },
        {
            "name": "analyze_transaction_history",
            "tool_inputs": {
                "customer_id": "CUST-334899",
                "lookback_days": 2
            }
        },
        {
            "name": "cross_reference_fraud_databases",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-130013",
                    "amount": 10000.0,
                    "merchant_name": "Flagged Beneficiary",
                    "merchant_mcc": "9999",
                    "location": "Atlanta, GA",
                    "device_id": "DEV-130013",
                    "transaction_type": "wire",
                    "timestamp": "2025-10-09T10:00:00Z",
                    "ip_address": "203.0.113.131"
                },
                "customer_profile": {
                    "name": "Jane Doe",
                    "age": 67,
                    "address": "123 Main St, Atlanta, GA",
                    "home_state": "GA",
                    "account_tenure_years": 11.5,
                    "account_status": "good_standing",
                    "contact_email": "jane.doe@email.com",
                    "contact_phone": "+14045551212",
                    "typical_spending_range": {
                        "min_amount": 50.0,
                        "max_amount": 5000.0,
                        "currency": "USD"
                    },
                    "recent_travel": []
                }
            }
        },
        {
            "name": "calculate_fraud_risk_score",
            "tool_inputs": {
                "transaction_details": {
                    "transaction_id": "TX-130013",
                    "amount": 10000.0,
                    "merchant_name": "Flagged Beneficiary",
                    "merchant_mcc": "9999",
                    "location": "Atlanta, GA",
                    "device_id": "DEV-130013",
                    "transaction_type": "wire",
                    "timestamp": "2025-10-09T10:00:00Z",
                    "ip_address": "203.0.113.131"
                },
                "customer_profile": {
                    "name": "Jane Doe",
                    "age": 67,
                    "address": "123 Main St, Atlanta, GA",
                    "home_state": "GA",
                    "account_tenure_years": 11.5,
                    "account_status": "good_standing",
                    "contact_email": "jane.doe@email.com",
                    "contact_phone": "+14045551212",
                    "typical_spending_range": {
                        "min_amount": 50.0,
                        "max_amount": 5000.0,
                        "currency": "USD"
                    },
                    "recent_travel": []
                },
                "transaction_history": {
                    "total_transactions": 120,
                    "avg_amount": 355.25,
                    "states_visited": ["GA", "FL"],
                    "merchant_categories": ["6011", "5411"],
                    "velocity_metrics": {"max_per_hour": 2, "max_per_day": 5},
                    "anomalies": []
                },
                "device_intelligence": {
                    "device_type": "mobile",
                    "os": "iOS",
                    "browser_fingerprint": "fp-xyz",
                    "vpn_detected": False,
                    "tor_detected": False,
                    "ip_address": "203.0.113.131",
                    "location": "Atlanta, GA",
                    "device_risk_score": 20,
                    "device_history": ["CUST-334899"]
                },
                "fraud_database_hits": {
                    "merchant_blacklist_hit": True,
                    "card_bin_attack": False,
                    "phone_fraud_list": False,
                    "fraud_database_notes": ["Beneficiary flagged in fraud DB"]
                }
            }
        },
        {
            "name": "auto_decline_transaction",
            "tool_inputs": {
                "transaction_id": "TX-130013",
                "reason": "bad_merchant"
            }
        },
        {
            "name": "route_to_analyst",
            "tool_inputs": {
                "alert_id": "FA-883433",
                "investigation_package": {
                    "transaction_id": "TX-130013",
                    "risk_factors": [
                        "beneficiary_blacklist",
                        "call_context"
                    ],
                    "summary": "Large wire transfer held; beneficiary flagged and customer context suggests scam risk."
                },
                "recommended_action": "hold_transfer"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Wire transfer held, case escalated to analyst for urgent review.",
                "result_data": {
                    "fraud_risk_score": 93,
                    "case_status": "escalated",
                    "recommended_action": "hold_transfer",
                    "investigation_package": {
                        "transaction_id": "TX-130013",
                        "risk_factors": [
                            "beneficiary_blacklist",
                            "call_context"
                        ],
                        "summary": "Large wire transfer held; beneficiary flagged and customer context suggests scam risk."
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Transaction details and customer profile retrieved",
            "expected_state": {
                "transaction_id": "TX-130013",
                "amount": 10000.0
            }
        },
        {
            "step": 2,
            "description": "Transaction history and call recording context analyzed",
            "expected_state": {
                "call_recording": "customer sounded confused"
            }
        },
        {
            "step": 3,
            "description": "Fraud databases cross-referenced for beneficiary risk",
            "expected_state": {
                "merchant_blacklist_hit": True
            }
        },
        {
            "step": 4,
            "description": "Fraud risk score calculated",
            "expected_state": {
                "fraud_risk_score": 93
            }
        },
        {
            "step": 5,
            "description": "Wire transfer held for review",
            "expected_state": {
                "block_status": "blocked"
            }
        },
        {
            "step": 6,
            "description": "Case routed to analyst for urgent review",
            "expected_state": {
                "escalation_level": "urgent"
            }
        }
    ]
    description = (
        "Covers success path for holding suspicious wire transfer and escalating for analyst review. "
        "Wire transfer held due to beneficiary risk and suspicious customer context; escalated for urgent analyst review."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This test case involves multiple enrichment steps (transaction, customer, device, history), "
        "contextual analysis (call recording), blacklist checks, risk scoring, and a multi-step escalation workflow. "
        "The presence of fraud indicators and the need to hold and escalate the transfer adds moderate complexity."
    )