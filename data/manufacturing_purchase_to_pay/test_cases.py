from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from system_tools_base import SystemToolsBaseClass


# TypedDicts for structured parameters and responses

class Item(TypedDict):
    """Item object for supplier contracts and purchase order creation."""
    item_code: str  # Item code (string)
    quantity: int   # Quantity (integer)
    unit_price: float  # Unit price (number, up to 2 decimals)

class ContactInfo(TypedDict, total=False):
    """Supplier contact details for PO transmission."""
    email: str  # Valid email address
    phone: str  # Phone number in E.164 format

class InvoiceTerms(TypedDict, total=False):
    """Terms for invoice, e.g., for early payment."""
    discount_available: bool

class MatchResult(TypedDict, total=False):
    """Match result object for 3-way match."""
    match_status: str  # exact|price_mismatch|quantity_mismatch|duplicate_detected|blanket_release|early_payment|exception
    variance_amount: float
    variance_type: str
    matched_items: List[Item]
    invoice_terms: InvoiceTerms

class BudgetValidationResult(TypedDict, total=False):
    """Budget validation result object."""
    status: str  # within_limit|exceeded
    available_balance: float
    exceeded_amount: Optional[float]

class ContractValidationResult(TypedDict, total=False):
    """Contract validation object."""
    contract_status: str  # preferred|non_preferred|expired|blanket
    contract_price: float
    terms: str
    contract_id: Optional[str]

class POObject(TypedDict, total=False):
    """PO object."""
    po_id: str
    items: List[Item]
    supplier_id: str
    delivery_date: str
    total_amount: float
    expedite: bool

class POConfirmation(TypedDict, total=False):
    """Confirmation object for PO transmission."""
    po_id: str
    delivery_status: str  # sent|queued|failed
    timestamp: str
    method: str

class ApprovalRoutingResult(TypedDict, total=False):
    """Approval routing object."""
    approval_status: str  # approved|pending|rejected|escalated
    approver: str
    scheduled_payment_date: str
    comments: str

class PaymentResult(TypedDict, total=False):
    """Payment result object."""
    payment_status: str  # completed|pending|failed
    payment_id: str
    timestamp: str
    amount: float

class ParsedRequisition(TypedDict, total=False):
    """Parsed requisition object returned by read_purchase_requisition."""
    items: List[Item]
    requester: str
    cost_center: str
    GL_account: str
    amount: float
    priority: str
    date: str


class BaseManufacturingPurchaseToPayAutomationAgentTestCase(SystemToolsBaseClass):
    """
    Base class containing common methods for all Manufacturing Procurement & Finance test cases.
    """

    # Agent context attributes from agent description
    role = (
        "You are a Purchase-to-Pay (P2P) automation agent that orchestrates the end-to-end "
        "procurement process for manufacturing, from requisition intake to payment processing, "
        "including budget validation, supplier contract compliance, purchase order creation, "
        "invoice matching, exception handling, and payment execution."
    )

    goal = (
        "Your goal is to minimize manual intervention and cycle time in the manufacturing "
        "P2P process by ensuring requisitions are validated, purchase orders are compliant "
        "and timely, invoices are accurately matched, exceptions are routed efficiently, "
        "and payments are processed promptly, all while maintaining auditability and compliance.\n"
    )

    action_plan = {
        "assumptions": [
            "ERP and procurement systems are integrated and accessible for data retrieval and updates.",
            "Supplier contracts, budget data, and payment platforms are up-to-date and available via API or EDI."
        ],
        "tools_and_resources": [
            {"tool": "read_purchase_requisition", "purpose": "Extract and parse requisition details from ERP/procurement system."},
            {"tool": "validate_budget_availability", "purpose": "Check cost center/GL account budget for requisition approval."},
            {"tool": "check_supplier_contracts", "purpose": "Evaluate supplier compliance, contract pricing, and preferred vendor status."},
            {"tool": "create_purchase_order", "purpose": "Generate and record purchase orders with line items and terms."},
            {"tool": "send_po_to_supplier", "purpose": "Transmit purchase orders to suppliers via EDI, email, or portal."},
            {"tool": "match_invoice_to_po", "purpose": "Perform 3-way match between PO, goods receipt, and supplier invoice."},
            {"tool": "route_payment_approval", "purpose": "Submit matched invoices for payment or flag exceptions for review."},
            {"tool": "process_payment", "purpose": "Initiate payment to supplier via ACH, wire, or check."}
        ],
        "guidelines": [
            "Auto-approve requisitions within budget and authority limits; escalate overruns.",
            "Enforce preferred supplier compliance and log exceptions for audit.",
            "Apply 3-way match tolerance rules for invoice variances.",
            "Reject duplicate invoices based on PO, amount, and payment history.",
            "Recommend early payment when terms offer discounts and cash flow allows.",
            "Maintain segregation of duties and audit trail for all approvals and overrides."
        ],
        "workflow_selection": [
            {
                "condition": 'if requisition_type == "standard" and budget_status == "within_limit" and supplier_contract_status == "preferred"',
                "logic": "Standard requisition, budget validated, preferred supplier; trigger full 3-way match workflow.",
                "workflow": "W1"
            },
            {
                "condition": 'if budget_status == "exceeded"',
                "logic": "Budget overrun detected; escalate for approval and reallocation before PO creation.",
                "workflow": "W2"
            },
            {
                "condition": 'if invoice_match_status == "price_mismatch" and variance_amount > 500',
                "logic": "Invoice price mismatch exceeds tolerance; route exception for AP review and resolution.",
                "workflow": "W3"
            },
            {
                "condition": 'if invoice_match_status == "quantity_mismatch"',
                "logic": "Quantity discrepancy detected; hold payment, initiate partial payment if backorder confirmed.",
                "workflow": "W4"
            },
            {
                "condition": 'if invoice_duplicate_status == "duplicate_detected"',
                "logic": "Duplicate invoice detected; reject invoice and notify supplier.",
                "workflow": "W5"
            },
            {
                "condition": 'if invoice_terms.discount_available == true and cash_position == "sufficient"',
                "logic": "Early payment discount available and cash flow supports; recommend accelerated payment.",
                "workflow": "W6"
            },
            {
                "condition": 'if requisition_type == "blanket_release"',
                "logic": "Blanket PO release; validate release limits, process as ongoing supply agreement.",
                "workflow": "W7"
            },
            {
                "condition": 'if requisition_priority == "urgent"',
                "logic": "Emergency requisition flagged; expedite processing, bypass standard supplier bidding.",
                "workflow": "W8"
            },
            {
                "condition": "if workflow cannot be determined or exception is outside tolerance rules",
                "logic": "Escalate to human for review (edge cases, complex exceptions).",
                "workflow": "W9"
            }
        ],
        "failure_points": [
            {
                "scenario": "Budget data unavailable or outdated",
                "recovery": "Escalate to finance for manual validation and update system records."
            },
            {
                "scenario": "Supplier contract not found or expired",
                "recovery": "Escalate to procurement for contract review or alternate supplier selection."
            },
            {
                "scenario": "Invoice variance unresolved after AP review",
                "recovery": "Escalate to manager for final decision or dispute resolution."
            },
            {
                "scenario": "Payment processing error (bank API failure)",
                "recovery": "Retry payment, notify finance, and escalate if unresolved."
            },
            {
                "scenario": "Duplicate invoice not detected due to missing reference data",
                "recovery": "Escalate to AP for manual duplicate check and audit log update."
            }
        ],
        "success_criteria": [
            "Requisition-to-payment cycle completed within target SLA (hours, not days).",
            "No budget overruns, duplicate payments, or maverick spend.",
            "All exceptions resolved or properly escalated.",
            "Audit trail maintained for all approvals, changes, and overrides.",
            "Supplier relationships improved through timely, accurate payments."
        ]
    }

    # Domain tool methods

    def read_purchase_requisition(self, requisition_id: str) -> ParsedRequisition:
        """
        Extract and parse requisition details from ERP/procurement system.

        Args:
            requisition_id: Unique requisition identifier. Format: REQ-XXXXXX where X is alphanumeric.
                            Example: REQ-445521

        Returns:
            ParsedRequisition: Parsed requisition object containing:
                - items (List[Item])
                - requester (str)
                - cost_center (str)
                - GL_account (str)
                - amount (float)
                - priority (str)
                - date (str, ISO 8601)
        """
        print(f"--- Running read_purchase_requisition ---")
        print(f"requisition_id: {requisition_id}")
        # Mocked response
        return {
            "items": [
                {"item_code": "RM-1001", "quantity": 10, "unit_price": 50.0}
            ],
            "requester": "John Doe",
            "cost_center": "CC-50100",
            "GL_account": "GL-50100",
            "amount": 500.0,
            "priority": "normal",
            "date": "2024-06-01"
        }

    def validate_budget_availability(
        self, cost_center: str, GL_account: str, amount: float
    ) -> BudgetValidationResult:
        """
        Check cost center/GL account budget for requisition approval.

        Args:
            cost_center: Cost center code. Format: CC-XXXX. Example: CC-50100
            GL_account: General ledger account code. Format: GL-XXXXX. Example: GL-50100
            amount: Requisition amount in USD, must be >= 0, max 2 decimal places

        Returns:
            BudgetValidationResult: Budget validation object:
                - status: 'within_limit' or 'exceeded'
                - available_balance: float
                - exceeded_amount: float (optional, present if status == 'exceeded')
        """
        print(f"--- Running validate_budget_availability ---")
        print(f"cost_center: {cost_center}, GL_account: {GL_account}, amount: {amount}")
        # Mocked logic
        if amount <= 10000:
            return {"status": "within_limit", "available_balance": 25000.0}
        else:
            return {"status": "exceeded", "available_balance": 5000.0, "exceeded_amount": amount - 5000.0}

    def check_supplier_contracts(
        self, supplier_id: str, item_list: List[Item]
    ) -> ContractValidationResult:
        """
        Evaluate supplier compliance, contract pricing, and preferred vendor status.

        Args:
            supplier_id: Unique supplier identifier. Format: SUP-XXXXXX. Example: SUP-ABC123
            item_list: List of item objects: item_code (string), quantity (integer), unit_price (number)

        Returns:
            ContractValidationResult: Contract validation object:
                - contract_status: preferred|non_preferred|expired|blanket
                - contract_price: float
                - terms: str
                - contract_id: str (optional)
        """
        print(f"--- Running check_supplier_contracts ---")
        print(f"supplier_id: {supplier_id}, item_list: {item_list}")
        # Mocked logic: preferred for SUP-ABC123
        if supplier_id == "SUP-ABC123":
            return {
                "contract_status": "preferred",
                "contract_price": sum(item["unit_price"] * item["quantity"] for item in item_list),
                "terms": "Net 30",
                "contract_id": "CONT-123456"
            }
        else:
            return {
                "contract_status": "non_preferred",
                "contract_price": sum(item["unit_price"] * item["quantity"] for item in item_list),
                "terms": "Net 45"
            }

    def create_purchase_order(
        self,
        requisition_id: str,
        supplier_id: str,
        item_list: List[Item],
        delivery_date: str,
        contract_id: Optional[str] = None,
        expedite: bool = False
    ) -> POObject:
        """
        Generate and record purchase orders with line items and terms.

        Args:
            requisition_id: Unique requisition identifier. Format: REQ-XXXXXX
            supplier_id: Unique supplier identifier. Format: SUP-XXXXXX
            item_list: List of item objects: item_code (string), quantity (integer), unit_price (number)
            delivery_date: Requested delivery date. ISO 8601 format (YYYY-MM-DD)
            contract_id: Supplier contract identifier. Format: CONT-XXXXXX (optional)
            expedite: Expedite flag for urgent purchases (default: False)

        Returns:
            POObject: PO object:
                - po_id (str)
                - items (List[Item])
                - supplier_id (str)
                - delivery_date (str)
                - total_amount (float)
                - expedite (bool)
        """
        print(f"--- Running create_purchase_order ---")
        print(f"requisition_id: {requisition_id}, supplier_id: {supplier_id}, item_list: {item_list}, "
              f"delivery_date: {delivery_date}, contract_id: {contract_id}, expedite: {expedite}")
        total_amount = sum(item["unit_price"] * item["quantity"] for item in item_list)
        return {
            "po_id": "PO-100001",
            "items": item_list,
            "supplier_id": supplier_id,
            "delivery_date": delivery_date,
            "total_amount": total_amount,
            "expedite": expedite
        }

    def send_po_to_supplier(
        self,
        po_id: str,
        delivery_method: str,
        contact_info: Optional[ContactInfo] = None
    ) -> POConfirmation:
        """
        Transmit purchase orders to suppliers via EDI, email, or portal.

        Args:
            po_id: Unique purchase order identifier. Format: PO-XXXXXX
            delivery_method: Preferred delivery channel. Valid values: ['edi', 'email', 'portal', 'fax']
            contact_info: Supplier contact details. Optional. Keys: email (str), phone (str, E.164 format)

        Returns:
            POConfirmation: Confirmation object:
                - po_id (str)
                - delivery_status (sent|queued|failed)
                - timestamp (ISO 8601)
                - method (str)
        """
        valid_methods = ['edi', 'email', 'portal', 'fax']
        if delivery_method not in valid_methods:
            raise ValueError(f"Invalid delivery_method: {delivery_method}. Must be one of {valid_methods}")
        print(f"--- Running send_po_to_supplier ---")
        print(f"po_id: {po_id}, delivery_method: {delivery_method}, contact_info: {contact_info}")
        return {
            "po_id": po_id,
            "delivery_status": "sent",
            "timestamp": "2024-06-01T10:00:00Z",
            "method": delivery_method
        }

    def match_invoice_to_po(
        self,
        po_id: str,
        receipt_id: str,
        invoice_id: str
    ) -> MatchResult:
        """
        Perform 3-way match between PO, goods receipt, and supplier invoice.

        Args:
            po_id: Unique purchase order identifier. Format: PO-XXXXXX
            receipt_id: Goods receipt identifier. Format: GR-XXXXXX
            invoice_id: Supplier invoice identifier. Format: INV-XXXXXX

        Returns:
            MatchResult: Match result object:
                - match_status: exact|price_mismatch|quantity_mismatch|duplicate_detected|blanket_release|early_payment|exception
                - variance_amount: float
                - variance_type: str
                - matched_items: List[Item]
                - invoice_terms: InvoiceTerms
        """
        print(f"--- Running match_invoice_to_po ---")
        print(f"po_id: {po_id}, receipt_id: {receipt_id}, invoice_id: {invoice_id}")
        # Mocked result: exact match
        return {
            "match_status": "exact",
            "variance_amount": 0.0,
            "variance_type": "none",
            "matched_items": [
                {"item_code": "RM-1001", "quantity": 10, "unit_price": 50.0}
            ],
            "invoice_terms": {"discount_available": False}
        }

    def route_payment_approval(
        self,
        invoice_id: str,
        match_status: str,
        variance_amount: Optional[float] = None,
        approval_level: Optional[str] = None
    ) -> ApprovalRoutingResult:
        """
        Submit matched invoices for payment or flag exceptions for review.

        Args:
            invoice_id: Supplier invoice identifier. Format: INV-XXXXXX
            match_status: Result of 3-way match. Valid values: ['exact', 'small_variance', 'medium_variance', 'large_variance', 'exception', 'duplicate']
            variance_amount: Variance amount in USD, must be >= 0, max 2 decimal places (optional)
            approval_level: Approval level required. Valid values: ['auto', 'buyer', 'manager', 'cfo', 'ap'] (optional)

        Returns:
            ApprovalRoutingResult: Approval routing object:
                - approval_status (approved|pending|rejected|escalated)
                - approver (str)
                - scheduled_payment_date (ISO 8601)
                - comments (str)
        """
        valid_statuses = ['exact', 'small_variance', 'medium_variance', 'large_variance', 'exception', 'duplicate']
        if match_status not in valid_statuses:
            raise ValueError(f"Invalid match_status: {match_status}. Must be one of {valid_statuses}")
        valid_approval_levels = ['auto', 'buyer', 'manager', 'cfo', 'ap', None]
        if approval_level and approval_level not in valid_approval_levels:
            raise ValueError(f"Invalid approval_level: {approval_level}. Must be one of {valid_approval_levels}")
        print(f"--- Running route_payment_approval ---")
        print(f"invoice_id: {invoice_id}, match_status: {match_status}, variance_amount: {variance_amount}, approval_level: {approval_level}")
        return {
            "approval_status": "approved" if match_status == "exact" else "pending",
            "approver": approval_level or "auto",
            "scheduled_payment_date": "2024-06-05",
            "comments": "Auto-approved" if match_status == "exact" else "Pending AP review"
        }

    def process_payment(
        self,
        invoice_id: str,
        payment_method: str,
        amount: float,
        scheduled_date: str
    ) -> PaymentResult:
        """
        Initiate payment to supplier via ACH, wire, or check.

        Args:
            invoice_id: Supplier invoice identifier. Format: INV-XXXXXX
            payment_method: Payment method. Valid values: ['ach', 'wire', 'check', 'card']
            amount: Payment amount in USD, must be >= 0, max 2 decimal places
            scheduled_date: Scheduled payment date. ISO 8601 format (YYYY-MM-DD)

        Returns:
            PaymentResult: Payment result object:
                - payment_status (completed|pending|failed)
                - payment_id (str)
                - timestamp (ISO 8601)
                - amount (float)
        """
        valid_methods = ['ach', 'wire', 'check', 'card']
        if payment_method not in valid_methods:
            raise ValueError(f"Invalid payment_method: {payment_method}. Must be one of {valid_methods}")
        print(f"--- Running process_payment ---")
        print(f"invoice_id: {invoice_id}, payment_method: {payment_method}, amount: {amount}, scheduled_date: {scheduled_date}")
        return {
            "payment_status": "completed",
            "payment_id": "PAY-20240601-001",
            "timestamp": f"{scheduled_date}T12:00:00Z",
            "amount": amount
        }

class TestCase1_ManufacturingPurchaseToPayAutomationAgent_W1_Standard_Raw_Materials_Purchase_3_Way_Match_easy(BaseManufacturingPurchaseToPayAutomationAgentTestCase):
    """
    TestCase 1: Standard requisition, preferred supplier, exact invoice match

    This test case covers the typical happy path for a standard procurement in manufacturing,
    where the requisition is within budget, uses a preferred supplier, and the invoice matches exactly,
    resulting in auto-approval and prompt payment processing.
    """

    test_case_id = "ManufacturingPurchaseToPayAutomationAgent_P2P_W1_TC1"
    title = "Standard requisition, preferred supplier, exact invoice match"
    workflow = "W1"
    input_data = {
        "requisition_id": "REQ-445521",
        "requisition_type": "standard",
        "amount": 15000.0,
        "cost_center": "CC-50100",
        "GL_account": "GL-50100",
        "supplier_id": "SUP-ABC123",
        "priority": "normal",
        "invoice_id": "INV-556677",
        "receipt_id": "GR-887812"
    }
    expected_tool_calls = [
        {
            "name": "read_purchase_requisition",
            "tool_inputs": {
                "requisition_id": "REQ-445521"
            }
        },
        {
            "name": "validate_budget_availability",
            "tool_inputs": {
                "cost_center": "CC-50100",
                "GL_account": "GL-50100",
                "amount": 15000.0
            }
        },
        {
            "name": "check_supplier_contracts",
            "tool_inputs": {
                "supplier_id": "SUP-ABC123",
                "item_list": [
                    {
                        "item_code": "RM-1001",
                        "quantity": 100,
                        "unit_price": 150.0
                    }
                ]
            }
        },
        {
            "name": "create_purchase_order",
            "tool_inputs": {
                "requisition_id": "REQ-445521",
                "supplier_id": "SUP-ABC123",
                "item_list": [
                    {
                        "item_code": "RM-1001",
                        "quantity": 100,
                        "unit_price": 150.0
                    }
                ],
                "delivery_date": "2024-02-25",
                "contract_id": "CONT-PRF12345",
                "expedite": False
            }
        },
        {
            "name": "send_po_to_supplier",
            "tool_inputs": {
                "po_id": "PO-123456",
                "delivery_method": "edi"
            }
        },
        # Step 6: Goods receipt recorded (no tool call, system event)
        {
            "name": "match_invoice_to_po",
            "tool_inputs": {
                "po_id": "PO-123456",
                "receipt_id": "GR-887812",
                "invoice_id": "INV-556677"
            }
        },
        {
            "name": "route_payment_approval",
            "tool_inputs": {
                "invoice_id": "INV-556677",
                "match_status": "exact",
                "variance_amount": 0,
                "approval_level": "auto"
            }
        },
        {
            "name": "process_payment",
            "tool_inputs": {
                "invoice_id": "INV-556677",
                "payment_method": "ach",
                "amount": 15000.0,
                "scheduled_date": "2024-02-28"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Workflow completed successfully.",
                "result_data": {
                    "workflow_status": "completed",
                    "audit_log": {
                        "steps": [
                            "read_purchase_requisition",
                            "validate_budget_availability",
                            "check_supplier_contracts",
                            "create_purchase_order",
                            "send_po_to_supplier",
                            "match_invoice_to_po",
                            "route_payment_approval",
                            "process_payment"
                        ],
                        "approvals": ["auto"],
                        "exceptions": []
                    },
                    "payment_details": {
                        "invoice_id": "INV-556677",
                        "payment_status": "completed",
                        "amount": 15000.0,
                        "scheduled_date": "2024-02-28",
                        "method": "ach"
                    },
                    "approval_status": "approved"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Purchase requisition read and parsed",
            "expected_state": {
                "requisition_valid": True
            }
        },
        {
            "step": 2,
            "description": "Budget validated and within limit",
            "expected_state": {
                "budget_status": "within_limit",
                "available_balance": 20000.0
            }
        },
        {
            "step": 3,
            "description": "Supplier contract checked and preferred",
            "expected_state": {
                "contract_status": "preferred",
                "contract_price": 15000.0
            }
        },
        {
            "step": 4,
            "description": "PO created with contract terms",
            "expected_state": {
                "po_id": "PO-123456",
                "items": [
                    {
                        "item_code": "RM-1001",
                        "quantity": 100,
                        "unit_price": 150.0
                    }
                ],
                "expedite": False
            }
        },
        {
            "step": 5,
            "description": "PO sent to supplier via EDI",
            "expected_state": {
                "delivery_status": "sent",
                "method": "edi"
            }
        },
        {
            "step": 6,
            "description": "Goods receipt recorded",
            "expected_state": {
                "receipt_id": "GR-887812",
                "received_quantity": 100
            }
        },
        {
            "step": 7,
            "description": "Invoice matched to PO and receipt (exact match)",
            "expected_state": {
                "match_status": "exact",
                "variance_amount": 0
            }
        },
        {
            "step": 8,
            "description": "Auto-approval routed for payment",
            "expected_state": {
                "approval_status": "approved",
                "approver": "auto"
            }
        },
        {
            "step": 9,
            "description": "Payment processed via ACH",
            "expected_state": {
                "payment_status": "completed",
                "method": "ach"
            }
        },
        {
            "step": 10,
            "description": "Workflow completion signaled",
            "expected_state": {
                "workflow_status": "completed"
            }
        }
    ]
    description = (
        "Covers the typical happy path for standard procurement with exact match and auto-approval. "
        "This path exercises the exact match branch, auto-approval for payment, and preferred supplier compliance."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This is a straightforward, non-exceptional workflow: all validations pass, "
        "preferred supplier is used, invoice matches exactly, and auto-approval triggers payment without escalation or manual intervention."
    )

class TestCase2_ManufacturingPurchaseToPayAutomationAgent_W1_Standard_Raw_Materials_Purchase_3_Way_Match_easy(BaseManufacturingPurchaseToPayAutomationAgentTestCase):
    """
    Standard requisition, preferred supplier, small price variance within tolerance.

    Covers the workflow path where an invoice has a small price variance but remains within auto-approval tolerance.
    """

    test_case_id = "ManufacturingPurchaseToPayAutomationAgent_P2P_W1_TC2"
    title = "Standard requisition, preferred supplier, small price variance within tolerance"
    workflow = "W1 - Standard Raw Materials Purchase - 3-Way Match"

    input_data = {
        "requisition_id": "REQ-445534",
        "requisition_type": "standard",
        "amount": 5000.0,
        "cost_center": "CC-60500",
        "GL_account": "GL-60500",
        "supplier_id": "SUP-OFFICEDEPOT",
        "priority": "normal",
        "invoice_id": "INV-887799",
        "receipt_id": "GR-445501"
    }

    expected_tool_calls = [
        {
            "name": "read_purchase_requisition",
            "tool_inputs": {
                "requisition_id": "REQ-445534"
            }
        },
        {
            "name": "validate_budget_availability",
            "tool_inputs": {
                "cost_center": "CC-60500",
                "GL_account": "GL-60500",
                "amount": 5000.0
            }
        },
        {
            "name": "check_supplier_contracts",
            "tool_inputs": {
                "supplier_id": "SUP-OFFICEDEPOT",
                "item_list": [
                    {
                        "item_code": "RM-2002",
                        "quantity": 50,
                        "unit_price": 100.0
                    }
                ]
            }
        },
        {
            "name": "create_purchase_order",
            "tool_inputs": {
                "requisition_id": "REQ-445534",
                "supplier_id": "SUP-OFFICEDEPOT",
                "item_list": [
                    {
                        "item_code": "RM-2002",
                        "quantity": 50,
                        "unit_price": 100.0
                    }
                ],
                "delivery_date": "2024-02-28",
                "contract_id": "CONT-123456",
                "expedite": False
            }
        },
        {
            "name": "send_po_to_supplier",
            "tool_inputs": {
                "po_id": "PO-654321",
                "delivery_method": "edi"
            }
        },
        {
            "name": "match_invoice_to_po",
            "tool_inputs": {
                "po_id": "PO-654321",
                "receipt_id": "GR-445501",
                "invoice_id": "INV-887799"
            }
        },
        {
            "name": "route_payment_approval",
            "tool_inputs": {
                "invoice_id": "INV-887799",
                "match_status": "small_variance",
                "variance_amount": 50,
                "approval_level": "auto"
            }
        },
        {
            "name": "process_payment",
            "tool_inputs": {
                "invoice_id": "INV-887799",
                "payment_method": "ach",
                "amount": 5050.0,
                "scheduled_date": "2024-03-01"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Workflow completed successfully.",
                "result_data": {
                    "workflow_status": "completed",
                    "audit_log": {
                        "steps": [
                            "read_purchase_requisition",
                            "validate_budget_availability",
                            "check_supplier_contracts",
                            "create_purchase_order",
                            "send_po_to_supplier",
                            "match_invoice_to_po",
                            "route_payment_approval",
                            "process_payment"
                        ],
                        "approvals": [
                            "auto"
                        ],
                        "exceptions": [
                            {
                                "type": "price_variance",
                                "variance_amount": 50,
                                "resolution": "auto-approved"
                            }
                        ]
                    },
                    "payment_details": {
                        "invoice_id": "INV-887799",
                        "payment_status": "completed",
                        "amount": 5050.0,
                        "scheduled_date": "2024-03-01",
                        "method": "ach"
                    },
                    "approval_status": "approved"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Purchase requisition read and parsed",
            "expected_state": {
                "requisition_valid": True
            }
        },
        {
            "step": 2,
            "description": "Budget validated and within limit",
            "expected_state": {
                "budget_status": "within_limit",
                "available_balance": 10000.0
            }
        },
        {
            "step": 3,
            "description": "Supplier contract checked and preferred",
            "expected_state": {
                "contract_status": "preferred",
                "contract_price": 5000.0
            }
        },
        {
            "step": 4,
            "description": "PO created with contract terms",
            "expected_state": {
                "po_id": "PO-654321",
                "items": [
                    {
                        "item_code": "RM-2002",
                        "quantity": 50,
                        "unit_price": 100.0
                    }
                ],
                "expedite": False
            }
        },
        {
            "step": 5,
            "description": "PO sent to supplier via EDI",
            "expected_state": {
                "delivery_status": "sent",
                "method": "edi"
            }
        },
        {
            "step": 6,
            "description": "Goods receipt recorded",
            "expected_state": {
                "receipt_id": "GR-445501",
                "received_quantity": 50
            }
        },
        {
            "step": 7,
            "description": "Invoice matched to PO and receipt (small price variance)",
            "expected_state": {
                "match_status": "small_variance",
                "variance_amount": 50
            }
        },
        {
            "step": 8,
            "description": "Auto-approval routed for payment",
            "expected_state": {
                "approval_status": "approved",
                "approver": "auto"
            }
        },
        {
            "step": 9,
            "description": "Payment processed via ACH",
            "expected_state": {
                "payment_status": "completed",
                "method": "ach"
            }
        },
        {
            "step": 10,
            "description": "Workflow completion signaled",
            "expected_state": {
                "workflow_status": "completed"
            }
        }
    ]

    description = (
        "Covers path where invoice has a small price variance but remains within auto-approval tolerance. "
        "This path exercises the small price variance branch, which is auto-approved due to being within tolerance limits."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test follows the standard, straight-through processing path with only a minor (within-tolerance) price variance, "
        "triggering auto-approval. No exceptions, escalations, or manual interventions are required."
    )

class TestCase3_ManufacturingPurchaseToPayAutomationAgent_W2_Budget_Exceeded_Approval_Required_medium(BaseManufacturingPurchaseToPayAutomationAgentTestCase):
    """
    Validates successful path for budget overrun with override approval and subsequent PO creation.
    This test case exercises the workflow for handling a purchase requisition where the budget is exceeded,
    a CFO override is granted, and the PO is created and sent to the supplier.
    """

    test_case_id = "ManufacturingPurchaseToPayAutomationAgent_P2P_W2_TC1"
    title = "Budget exceeded, CFO override granted, PO created and sent"
    workflow = "W2"
    input_data = {
        "requisition_id": "REQ-445600",
        "requisition_type": "standard",
        "amount": 22000.0,
        "cost_center": "CC-50100",
        "GL_account": "GL-50100",
        "supplier_id": "SUP-ABC123",
        "priority": "high"
    }
    expected_tool_calls = [
        {
            "name": "read_purchase_requisition",
            "tool_inputs": {
                "requisition_id": "REQ-445600"
            }
        },
        {
            "name": "validate_budget_availability",
            "tool_inputs": {
                "cost_center": "CC-50100",
                "GL_account": "GL-50100",
                "amount": 22000.0
            }
        },
        {
            "name": "HUMAN_IN_THE_LOOP",
            "tool_inputs": {
                "ai_message": (
                    "Budget exceeded by $2,000.00 for requisition REQ-445600. "
                    "Requesting CFO override approval to proceed."
                )
            }
        },
        {
            "name": "check_supplier_contracts",
            "tool_inputs": {
                "supplier_id": "SUP-ABC123",
                "item_list": [
                    {
                        "item_code": "ITEM-001",
                        "quantity": 10,
                        "unit_price": 2200.0
                    }
                ]
            }
        },
        {
            "name": "create_purchase_order",
            "tool_inputs": {
                "requisition_id": "REQ-445600",
                "supplier_id": "SUP-ABC123",
                "item_list": [
                    {
                        "item_code": "ITEM-001",
                        "quantity": 10,
                        "unit_price": 2200.0
                    }
                ],
                "delivery_date": "2024-04-15",
                "contract_id": "CONT-123456",
                "expedite": True
            }
        },
        {
            "name": "send_po_to_supplier",
            "tool_inputs": {
                "po_id": "PO-222222",
                "delivery_method": "email",
                "contact_info": {
                    "email": "supplier@abc123.com",
                    "phone": "+15555551234"
                }
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Workflow completed successfully. PO created and sent after CFO override.",
                "result_data": {
                    "workflow_status": "completed",
                    "audit_log": {
                        "steps": [
                            "read_purchase_requisition",
                            "validate_budget_availability",
                            "check_supplier_contracts",
                            "create_purchase_order",
                            "send_po_to_supplier"
                        ],
                        "approvals": [
                            "CFO"
                        ],
                        "exceptions": [
                            {
                                "type": "budget_exceeded",
                                "variance_amount": 2000.0,
                                "resolution": "override approved"
                            }
                        ]
                    }
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Purchase requisition read and parsed",
            "expected_state": {
                "requisition_valid": True
            }
        },
        {
            "step": 2,
            "description": "Budget validated and exceeded",
            "expected_state": {
                "budget_status": "exceeded",
                "exceeded_amount": 2000.0
            }
        },
        {
            "step": 3,
            "description": "Budget override approval granted by CFO",
            "expected_state": {
                "approval_status": "approved",
                "approver": "CFO"
            }
        },
        {
            "step": 4,
            "description": "Supplier contract checked for compliance",
            "expected_state": {
                "contract_status": "preferred"
            }
        },
        {
            "step": 5,
            "description": "PO created and sent via email",
            "expected_state": {
                "po_id": "PO-222222",
                "delivery_status": "sent",
                "method": "email"
            }
        },
        {
            "step": 6,
            "description": "Workflow completion signaled",
            "expected_state": {
                "workflow_status": "completed"
            }
        }
    ]
    description = (
        "Validates successful path for budget overrun with override approval and subsequent PO creation. "
        "This path exercises budget override approval and email PO transmission, not auto-approval."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "The scenario involves handling a budget overrun (requiring escalation and CFO override approval), "
        "ensuring proper audit logging of the exception and approval, and then resuming the workflow for compliant PO creation and transmission. "
        "It is more complex than a straight-through case but does not involve multi-exception handling or payment processing."
    )

    def check_supplier_contracts(self, supplier_id: str, item_list: list[dict]) -> dict:
        """
        Override to simulate supplier contract is preferred and contract details returned.

        Args:
            supplier_id: Unique supplier identifier. Format: SUP-XXXXXX
            item_list: List of item objects (item_code, quantity, unit_price)

        Returns:
            dict: Contract validation object with preferred status, contract price, terms, and contract_id.
        """
        print(f"--- [Override] Checking supplier contracts for supplier_id: {supplier_id} ---")
        print(f"Item list: {item_list}")
        return {
            "contract_status": "preferred",
            "contract_price": 2200.0,
            "terms": "Net 30",
            "contract_id": "CONT-123456"
        }

    def create_purchase_order(self, requisition_id: str, supplier_id: str, item_list: list[dict], delivery_date: str, contract_id: str = None, expedite: bool = False) -> dict:
        """
        Override to simulate PO creation with a fixed PO ID for test traceability.

        Args:
            requisition_id: Unique requisition identifier. Format: REQ-XXXXXX
            supplier_id: Unique supplier identifier. Format: SUP-XXXXXX
            item_list: List of item objects (item_code, quantity, unit_price)
            delivery_date: Requested delivery date (YYYY-MM-DD)
            contract_id: Supplier contract identifier (optional)
            expedite: Expedite flag for urgent purchases (default: False)

        Returns:
            dict: PO object with po_id, items, supplier_id, delivery_date, total_amount, expedite
        """
        print(f"--- [Override] Creating purchase order for requisition_id: {requisition_id} ---")
        print(f"Supplier: {supplier_id}, Contract: {contract_id}, Expedite: {expedite}")
        total_amount = sum(item.get("quantity", 0) * item.get("unit_price", 0.0) for item in item_list)
        return {
            "po_id": "PO-222222",
            "items": item_list,
            "supplier_id": supplier_id,
            "delivery_date": delivery_date,
            "total_amount": total_amount,
            "expedite": expedite
        }

    def send_po_to_supplier(self, po_id: str, delivery_method: str, contact_info: dict = None) -> dict:
        """
        Override to simulate sending PO via email and return fixed confirmation.

        Args:
            po_id: Unique purchase order identifier. Format: PO-XXXXXX
            delivery_method: Preferred delivery channel. Valid values: ['edi', 'email', 'portal', 'fax']
            contact_info: Supplier contact details (optional)

        Returns:
            dict: Confirmation object with po_id, delivery_status, timestamp, method
        """
        valid_methods = ['edi', 'email', 'portal', 'fax']
        if delivery_method not in valid_methods:
            raise ValueError(f"Invalid delivery_method: {delivery_method}")
        print(f"--- [Override] Sending PO {po_id} via {delivery_method} ---")
        return {
            "po_id": po_id,
            "delivery_status": "sent",
            "timestamp": "2024-04-10T10:00:00Z",
            "method": delivery_method
        }

class TestCase4_ManufacturingPurchaseToPayAutomationAgent_W3_InvoicePriceMismatchExceptionRouting_medium(BaseManufacturingPurchaseToPayAutomationAgentTestCase):
    """
    Invoice price mismatch > $500, AP resolves and payment processed.

    Validates successful exception handling for price variance above tolerance, resolved by AP.
    """

    test_case_id = "ManufacturingPurchaseToPayAutomationAgent_P2P_W3_TC1"
    title = "Invoice price mismatch > $500, AP resolves and payment processed"
    workflow = "W3 - Invoice Price Mismatch - Exception Routing"
    input_data = {
        "requisition_id": "REQ-445700",
        "requisition_type": "standard",
        "amount": 12000.0,
        "cost_center": "CC-60500",
        "GL_account": "GL-60500",
        "supplier_id": "SUP-XYZ789",
        "priority": "normal",
        "invoice_id": "INV-999888",
        "receipt_id": "GR-123456"
    }
    expected_tool_calls = [
        {
            "name": "match_invoice_to_po",
            "tool_inputs": {
                "po_id": "PO-TO-BE-DETERMINED",  # Normally, PO would be known or fetched from context
                "receipt_id": "GR-123456",
                "invoice_id": "INV-999888"
            }
        },
        {
            "name": "route_payment_approval",
            "tool_inputs": {
                "invoice_id": "INV-999888",
                "match_status": "large_variance",  # For price mismatch > $500, it's treated as "large_variance"
                "variance_amount": 800,
                "approval_level": "ap"
            }
        },
        {
            "name": "process_payment",
            "tool_inputs": {
                "invoice_id": "INV-999888",
                "payment_method": "ach",
                "amount": 12800.0,
                "scheduled_date": "2024-04-01"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Workflow completed successfully.",
                "result_data": {
                    "workflow_status": "completed",
                    "audit_log": {
                        "steps": [
                            "match_invoice_to_po",
                            "route_payment_approval",
                            "process_payment"
                        ],
                        "approvals": ["AP"],
                        "exceptions": [
                            {
                                "type": "price_mismatch",
                                "variance_amount": 800,
                                "resolution": "approved by AP"
                            }
                        ]
                    },
                    "payment_details": {
                        "invoice_id": "INV-999888",
                        "payment_status": "completed",
                        "amount": 12800.0,
                        "scheduled_date": "2024-04-01",
                        "method": "ach"
                    },
                    "approval_status": "approved"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Invoice matched to PO and receipt (price mismatch > $500)",
            "expected_state": {
                "match_status": "price_mismatch",
                "variance_amount": 800
            }
        },
        {
            "step": 2,
            "description": "Exception routed to AP for review",
            "expected_state": {
                "approval_status": "approved",
                "approver": "AP"
            }
        },
        {
            "step": 3,
            "description": "Payment processed after AP approval",
            "expected_state": {
                "payment_status": "completed",
                "method": "ach"
            }
        },
        {
            "step": 4,
            "description": "Workflow completion signaled",
            "expected_state": {
                "workflow_status": "completed"
            }
        }
    ]
    description = (
        "Validates successful exception handling for price variance above tolerance, resolved by AP. "
        "Exercises AP review and approval for price mismatch above tolerance, payment processed after exception resolution."
    )
    difficulty = "medium"
    difficulty_reasoning = (
        "This test involves an exception scenario (price mismatch > $500) requiring AP review and approval, "
        "rather than straight-through processing. It tests exception routing, approval, and payment processing, "
        "but does not require escalation to human or simulate payment failure, placing it at medium complexity."
    )

    def match_invoice_to_po(self, po_id: str, receipt_id: str, invoice_id: str) -> dict:
        """
        Perform 3-way match between PO, goods receipt, and supplier invoice.

        Args:
            po_id: Unique purchase order identifier. Format: PO-XXXXXX
            receipt_id: Goods receipt identifier. Format: GR-XXXXXX
            invoice_id: Supplier invoice identifier. Format: INV-XXXXXX

        Returns:
            dict: Match result object with match_status, variance_amount, variance_type, matched_items, invoice_terms
        """
        print(f"--- Running match_invoice_to_po ---")
        print(f"po_id: {po_id}, receipt_id: {receipt_id}, invoice_id: {invoice_id}")
        # Simulate price mismatch > $500
        return {
            "match_status": "price_mismatch",
            "variance_amount": 800,
            "variance_type": "price",
            "matched_items": [
                # Simulated matched items
                {"item_code": "ITEM-001", "quantity": 10, "unit_price": 1200.0}
            ],
            "invoice_terms": {
                "discount_available": False,
                "due_date": "2024-04-10"
            }
        }

    def route_payment_approval(
        self,
        invoice_id: str,
        match_status: str,
        variance_amount: float = None,
        approval_level: str = None
    ) -> dict:
        """
        Submit matched invoices for payment or flag exceptions for review.

        Args:
            invoice_id: Supplier invoice identifier. Format: INV-XXXXXX
            match_status: Result of 3-way match. Valid values:
                ['exact', 'small_variance', 'medium_variance', 'large_variance', 'exception', 'duplicate']
            variance_amount: Variance amount in USD, must be >= 0, max 2 decimal places
            approval_level: Approval level required. Valid values: ['auto', 'buyer', 'manager', 'cfo', 'ap']

        Returns:
            dict: Approval routing object with approval_status, approver, scheduled_payment_date, comments
        """
        valid_match_status = [
            "exact", "small_variance", "medium_variance", "large_variance", "exception", "duplicate"
        ]
        valid_approval_level = ["auto", "buyer", "manager", "cfo", "ap"]
        if match_status not in valid_match_status:
            raise ValueError(f"Invalid match_status: {match_status}")
        if approval_level and approval_level.lower() not in valid_approval_level:
            raise ValueError(f"Invalid approval_level: {approval_level}")
        print(f"--- Running route_payment_approval ---")
        print(f"invoice_id: {invoice_id}, match_status: {match_status}, variance_amount: {variance_amount}, approval_level: {approval_level}")
        # Simulate AP approval for large price variance
        return {
            "approval_status": "approved",
            "approver": "AP",
            "scheduled_payment_date": "2024-04-01",
            "comments": "Price variance approved by AP"
        }

    def process_payment(
        self,
        invoice_id: str,
        payment_method: str,
        amount: float,
        scheduled_date: str
    ) -> dict:
        """
        Initiate payment to supplier via ACH, wire, or check.

        Args:
            invoice_id: Supplier invoice identifier. Format: INV-XXXXXX
            payment_method: Payment method. Valid values: ['ach', 'wire', 'check', 'card']
            amount: Payment amount in USD, must be >= 0, max 2 decimal places
            scheduled_date: Scheduled payment date. ISO 8601 format (YYYY-MM-DD)

        Returns:
            dict: Payment result object with payment_status, payment_id, timestamp, amount
        """
        valid_payment_methods = ["ach", "wire", "check", "card"]
        if payment_method not in valid_payment_methods:
            raise ValueError(f"Invalid payment_method: {payment_method}")
        print(f"--- Running process_payment ---")
        print(f"invoice_id: {invoice_id}, payment_method: {payment_method}, amount: {amount}, scheduled_date: {scheduled_date}")
        # Simulate successful payment
        return {
            "payment_status": "completed",
            "payment_id": "PAY-20240401-001",
            "timestamp": "2024-04-01T10:00:00Z",
            "amount": amount
        }

class TestCase5_ManufacturingPurchaseToPayAutomationAgent_W4_Quantity_Discrepancy_Partial_Receipt_medium(BaseManufacturingPurchaseToPayAutomationAgentTestCase):
    """Partial receipt, quantity mismatch, backorder received and payments processed

    Validates successful handling of partial receipt and backorder reconciliation with two payments.
    """

    test_case_id = "ManufacturingPurchaseToPayAutomationAgent_P2P_W4_TC1"
    title = "Partial receipt, quantity mismatch, backorder received and payments processed"
    workflow = "W4 - Quantity Discrepancy - Partial Receipt"

    input_data = {
        "requisition_id": "REQ-445800",
        "requisition_type": "standard",
        "amount": 10000.0,
        "cost_center": "CC-50100",
        "GL_account": "GL-50100",
        "supplier_id": "SUP-ABC123",
        "priority": "normal",
        "invoice_id": "INV-777666",
        "receipt_id": "GR-654321"
    }

    expected_tool_calls = [
        # Step 2: Match invoice to PO and receipt (quantity mismatch)
        {
            "name": "match_invoice_to_po",
            "tool_inputs": {
                "po_id": "PO-REQ-445800",  # Assuming PO created as PO-<requisition_id>
                "receipt_id": "GR-654321",
                "invoice_id": "INV-777666"
            }
        },
        # Step 4: Route payment approval for partial payment
        {
            "name": "route_payment_approval",
            "tool_inputs": {
                "invoice_id": "INV-777666",
                "match_status": "quantity_mismatch",
                "variance_amount": 40,
                "approval_level": "auto"
            }
        },
        # Step 5: Partial payment processed
        {
            "name": "process_payment",
            "tool_inputs": {
                "invoice_id": "INV-777666",
                "payment_method": "ach",
                "amount": 6000.0,
                "scheduled_date": "2024-04-20"
            }
        },
        # Step 6: Final payment after backorder
        {
            "name": "process_payment",
            "tool_inputs": {
                "invoice_id": "INV-777666",
                "payment_method": "ach",
                "amount": 4000.0,
                "scheduled_date": "2024-05-01"
            }
        },
        # Step 7: Signal workflow completion
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Partial and final payments processed, all units reconciled.",
                "result_data": {
                    "workflow_status": "completed",
                    "audit_log": {
                        "steps": [
                            "match_invoice_to_po",
                            "route_payment_approval",
                            "process_payment",
                            "process_payment"
                        ],
                        "approvals": [
                            "auto"
                        ],
                        "exceptions": [
                            {
                                "type": "quantity_mismatch",
                                "resolution": "partial and final payments processed"
                            }
                        ]
                    },
                    "payment_details": {
                        "invoice_id": "INV-777666",
                        "payment_status": "completed",
                        "amount": 10000.0,
                        "scheduled_date": "2024-05-01",
                        "method": "ach"
                    },
                    "approval_status": "approved"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Partial goods receipt recorded",
            "expected_state": {
                "receipt_id": "GR-654321",
                "received_quantity": 60,
                "ordered_quantity": 100
            }
        },
        {
            "step": 2,
            "description": "Invoice matched to PO and receipt (quantity mismatch)",
            "expected_state": {
                "match_status": "quantity_mismatch",
                "variance_amount": 40
            }
        },
        {
            "step": 3,
            "description": "Payment approval routed for partial payment",
            "expected_state": {
                "approval_status": "approved",
                "approver": "auto"
            }
        },
        {
            "step": 4,
            "description": "Partial payment processed",
            "expected_state": {
                "payment_status": "completed",
                "amount": 6000.0
            }
        },
        {
            "step": 5,
            "description": "Backorder received and reconciled",
            "expected_state": {
                "receipt_id": "GR-654322",
                "received_quantity": 40
            }
        },
        {
            "step": 6,
            "description": "Final payment processed",
            "expected_state": {
                "payment_status": "completed",
                "amount": 4000.0
            }
        },
        {
            "step": 7,
            "description": "Workflow completion signaled",
            "expected_state": {
                "workflow_status": "completed"
            }
        }
    ]

    description = "Validates successful handling of partial receipt and backorder reconciliation with two payments."
    difficulty = "medium"
    difficulty_reasoning = (
        "This test involves handling a quantity mismatch scenario with a partial goods receipt, "
        "requiring the agent to split payments (partial and final) and reconcile backorders. "
        "It tests exception handling, state tracking, and correct audit logging, making it more complex than a standard straight-through case."
    )

    # Optionally override process_payment to simulate two payments if needed
    def process_payment(self, invoice_id: str, payment_method: str, amount: float, scheduled_date: str) -> dict:
        """
        Initiate payment to supplier via ACH, wire, or check.

        Args:
            invoice_id: Supplier invoice identifier. Format: INV-XXXXXX
            payment_method: Payment method. Valid values: ['ach', 'wire', 'check', 'card']
            amount: Payment amount in USD, must be >= 0, max 2 decimal places
            scheduled_date: Scheduled payment date. ISO 8601 format (YYYY-MM-DD)

        Returns:
            dict: Payment result object: payment_status (completed|pending|failed),
                  payment_id (string), timestamp (ISO 8601), amount (number)
        """
        valid_methods = ['ach', 'wire', 'check', 'card']
        if payment_method not in valid_methods:
            raise ValueError(f"Invalid payment_method: {payment_method}. Must be one of {valid_methods}")

        print(f"--- Processing payment ---")
        print(f"Invoice ID: {invoice_id}, Method: {payment_method}, Amount: {amount}, Scheduled: {scheduled_date}")

        # Simulate payment_id and timestamp
        payment_id = f"PAY-{invoice_id}-{int(amount)}"
        timestamp = "2024-04-20T10:00:00Z" if amount == 6000.0 else "2024-05-01T10:00:00Z"

        return {
            "payment_status": "completed",
            "payment_id": payment_id,
            "timestamp": timestamp,
            "amount": amount
        }

class TestCase6_ManufacturingPurchaseToPayAutomationAgent_W5_DuplicateInvoiceDetection_easy(BaseManufacturingPurchaseToPayAutomationAgentTestCase):
    """
    Duplicate invoice detected and rejected, supplier notified.

    Validates successful detection and rejection of duplicate invoice, preventing double payment.
    """

    test_case_id = "ManufacturingPurchaseToPayAutomationAgent_P2P_W5_TC1"
    title = "Duplicate invoice detected and rejected, supplier notified"
    workflow = "W5 - Duplicate Invoice Detection"

    input_data = {
        "requisition_id": "REQ-445900",
        "requisition_type": "standard",
        "amount": 8000.0,
        "cost_center": "CC-60500",
        "GL_account": "GL-60500",
        "supplier_id": "SUP-XYZ789",
        "priority": "normal",
        "invoice_id": "INV-333444",
        "receipt_id": "GR-999888"
    }

    expected_tool_calls = [
        {
            "name": "match_invoice_to_po",
            "tool_inputs": {
                "po_id": "PO-PLACEHOLDER",  # PO should be determined from process context; use placeholder for test
                "receipt_id": "GR-999888",
                "invoice_id": "INV-333444"
            }
        },
        {
            "name": "route_payment_approval",
            "tool_inputs": {
                "invoice_id": "INV-333444",
                "match_status": "duplicate",
                "variance_amount": 0,
                "approval_level": "ap"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Duplicate invoice detected, rejected, and supplier notified. Workflow completed.",
                "result_data": {
                    "workflow_status": "completed",
                    "audit_log": {
                        "steps": [
                            "match_invoice_to_po",
                            "route_payment_approval"
                        ],
                        "approvals": [],
                        "exceptions": [
                            {
                                "type": "duplicate_invoice",
                                "resolution": "rejected and supplier notified"
                            }
                        ]
                    },
                    "approval_status": "rejected"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Invoice matched to PO and payment history (duplicate detected)",
            "expected_state": {
                "match_status": "duplicate_detected",
                "invoice_id": "INV-333444"
            }
        },
        {
            "step": 2,
            "description": "Invoice rejected and supplier notified",
            "expected_state": {
                "approval_status": "rejected",
                "comments": "Duplicate invoice"
            }
        },
        {
            "step": 3,
            "description": "Workflow completion signaled",
            "expected_state": {
                "workflow_status": "completed"
            }
        }
    ]

    description = (
        "Validates successful detection and rejection of duplicate invoice, preventing double payment. "
        "Exercises duplicate detection and rejection path, supplier notified, no payment processed."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows a straightforward exception path: a duplicate invoice is detected, "
        "rejected, and the supplier is notified. No complex approval or payment processing is required, "
        "making it an easy scenario."
    )

    def match_invoice_to_po(self, po_id: str, receipt_id: str, invoice_id: str) -> dict:
        """
        Perform 3-way match between PO, goods receipt, and supplier invoice.

        Args:
            po_id: Unique purchase order identifier. Format: PO-XXXXXX
            receipt_id: Goods receipt identifier. Format: GR-XXXXXX
            invoice_id: Supplier invoice identifier. Format: INV-XXXXXX

        Returns:
            dict: Match result object with match_status, variance_amount, variance_type, matched_items, invoice_terms
        """
        print(f"--- Running match_invoice_to_po ---")
        print(f"po_id: {po_id}, receipt_id: {receipt_id}, invoice_id: {invoice_id}")

        # Simulate duplicate detected scenario
        return {
            "match_status": "duplicate_detected",
            "variance_amount": 0,
            "variance_type": None,
            "matched_items": [],
            "invoice_terms": {}
        }

    def route_payment_approval(
        self,
        invoice_id: str,
        match_status: str,
        variance_amount: float = 0,
        approval_level: str = "ap"
    ) -> dict:
        """
        Submit matched invoices for payment or flag exceptions for review.

        Args:
            invoice_id: Supplier invoice identifier. Format: INV-XXXXXX
            match_status: Result of 3-way match. Valid values: ['exact', 'small_variance', 'medium_variance', 'large_variance', 'exception', 'duplicate']
            variance_amount: Variance amount in USD, must be >= 0, max 2 decimal places
            approval_level: Approval level required. Valid values: ['auto', 'buyer', 'manager', 'cfo', 'ap']

        Returns:
            dict: Approval routing object with approval_status, approver, scheduled_payment_date, comments
        """
        valid_match_statuses = [
            "exact", "small_variance", "medium_variance", "large_variance", "exception", "duplicate"
        ]
        if match_status not in valid_match_statuses:
            raise ValueError(f"Invalid match_status: {match_status}. Must be one of {valid_match_statuses}")

        valid_approval_levels = ["auto", "buyer", "manager", "cfo", "ap"]
        if approval_level not in valid_approval_levels:
            raise ValueError(f"Invalid approval_level: {approval_level}. Must be one of {valid_approval_levels}")

        print(f"--- Running route_payment_approval ---")
        print(f"invoice_id: {invoice_id}, match_status: {match_status}, variance_amount: {variance_amount}, approval_level: {approval_level}")

        # Simulate rejection and supplier notification for duplicate
        if match_status == "duplicate":
            return {
                "approval_status": "rejected",
                "approver": "AP System",
                "scheduled_payment_date": None,
                "comments": "Duplicate invoice"
            }
        else:
            # Fallback for other statuses
            return {
                "approval_status": "pending",
                "approver": approval_level,
                "scheduled_payment_date": None,
                "comments": "Pending review"
            }

class TestCase7_ManufacturingPurchaseToPayAutomationAgent_W6_Early_Payment_Discount_Optimize_Cash_Flow_easy(BaseManufacturingPurchaseToPayAutomationAgentTestCase):
    """Early payment discount available, cash sufficient, payment processed early

    Validates capturing early payment discount when cash position allows.
    Exercises early payment discount branch, payment processed on accelerated schedule.
    """

    test_case_id = "ManufacturingPurchaseToPayAutomationAgent_P2P_W6_TC1"
    title = "Early payment discount available, cash sufficient, payment processed early"
    workflow = "W6 - Early Payment Discount - Optimize Cash Flow"

    input_data = {
        "requisition_id": "REQ-446000",
        "requisition_type": "standard",
        "amount": 7000.0,
        "cost_center": "CC-50100",
        "GL_account": "GL-50100",
        "supplier_id": "SUP-ABC123",
        "priority": "normal",
        "invoice_id": "INV-555666",
        "receipt_id": "GR-888777"
    }

    expected_tool_calls = [
        # Step 1: Match invoice to PO and receipt (discount available)
        {
            "name": "match_invoice_to_po",
            "tool_inputs": {
                "po_id": "PO-100001",  # Mock PO ID (would be created earlier in real workflow)
                "receipt_id": "GR-888777",
                "invoice_id": "INV-555666"
            }
        },
        # Step 2: Route payment approval recommending early payment
        {
            "name": "route_payment_approval",
            "tool_inputs": {
                "invoice_id": "INV-555666",
                "match_status": "exact",  # For discount branch, match_status could be "exact" or "early_payment"
                "approval_level": "auto"
            }
        },
        # Step 3: Process payment on recommended schedule (with discount applied)
        {
            "name": "process_payment",
            "tool_inputs": {
                "invoice_id": "INV-555666",
                "payment_method": "ach",
                "amount": 6930.0,  # 7000 - 1% discount = 6930
                "scheduled_date": "2024-03-15"
            }
        },
        # Step 4: Signal workflow completion
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Early payment discount captured, payment processed successfully.",
                "result_data": {
                    "workflow_status": "completed",
                    "audit_log": {
                        "steps": [
                            "match_invoice_to_po",
                            "route_payment_approval",
                            "process_payment"
                        ],
                        "approvals": [
                            "auto"
                        ],
                        "exceptions": [
                            {
                                "type": "early_payment_discount",
                                "resolution": "discount captured"
                            }
                        ]
                    },
                    "payment_details": {
                        "invoice_id": "INV-555666",
                        "payment_status": "completed",
                        "amount": 6930.0,
                        "scheduled_date": "2024-03-15",
                        "method": "ach"
                    },
                    "approval_status": "approved"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Invoice matched to PO and receipt (discount available)",
            "expected_state": {
                "match_status": "early_payment",
                "invoice_terms": {
                    "discount_available": True,
                    "discount_rate": 1
                }
            }
        },
        {
            "step": 2,
            "description": "Payment approval routed recommending early payment",
            "expected_state": {
                "approval_status": "approved",
                "approver": "auto"
            }
        },
        {
            "step": 3,
            "description": "Payment processed on recommended schedule",
            "expected_state": {
                "payment_status": "completed",
                "amount": 6930.0
            }
        },
        {
            "step": 4,
            "description": "Workflow completion signaled",
            "expected_state": {
                "workflow_status": "completed"
            }
        }
    ]

    description = "Validates capturing early payment discount when cash position allows."
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the happy path for early payment discount: all required data is present, "
        "cash is sufficient, the discount is available, and no exceptions or escalations occur. "
        "The scenario exercises a common workflow branch without complex exception handling."
    )

    # Override match_invoice_to_po to simulate early payment discount match
    def match_invoice_to_po(self, po_id: str, receipt_id: str, invoice_id: str) -> dict:
        """
        Simulate matching invoice to PO and receipt, with early payment discount terms present.
        """
        print(f"--- Matching invoice {invoice_id} to PO {po_id} and receipt {receipt_id} ---")
        return {
            "match_status": "early_payment",
            "variance_amount": 0.0,
            "variance_type": None,
            "matched_items": [
                {"item_code": "ITEM-001", "quantity": 100, "unit_price": 70.0}
            ],
            "invoice_terms": {
                "discount_available": True,
                "discount_rate": 1  # 1% discount
            }
        }

    # Override route_payment_approval to simulate auto-approval for early payment
    def route_payment_approval(
        self,
        invoice_id: str,
        match_status: str,
        variance_amount: float = 0.0,
        approval_level: str = "auto"
    ) -> dict:
        """
        Simulate auto-approval of payment with early payment recommendation.
        """
        valid_match_statuses = [
            "exact", "small_variance", "medium_variance", "large_variance", "exception", "duplicate"
        ]
        if match_status not in valid_match_statuses and match_status != "early_payment":
            raise ValueError(f"Invalid match_status: {match_status}")

        valid_approval_levels = ["auto", "buyer", "manager", "cfo", "ap"]
        if approval_level not in valid_approval_levels:
            raise ValueError(f"Invalid approval_level: {approval_level}")

        print(f"--- Routing payment approval for invoice {invoice_id} ---")
        print(f"Match status: {match_status}, Approval level: {approval_level}")
        return {
            "approval_status": "approved",
            "approver": "auto",
            "scheduled_payment_date": "2024-03-15",
            "comments": "Early payment discount recommended and approved."
        }

    # Override process_payment to simulate discounted payment
    def process_payment(
        self,
        invoice_id: str,
        payment_method: str,
        amount: float,
        scheduled_date: str
    ) -> dict:
        """
        Simulate payment processing with early payment discount applied.
        """
        valid_methods = ["ach", "wire", "check", "card"]
        if payment_method not in valid_methods:
            raise ValueError(f"Invalid payment_method: {payment_method}")

        print(f"--- Processing payment for invoice {invoice_id} ---")
        print(f"Method: {payment_method}, Amount: {amount}, Scheduled date: {scheduled_date}")
        return {
            "payment_status": "completed",
            "payment_id": "PAY-123456",
            "timestamp": "2024-03-15T09:00:00Z",
            "amount": amount
        }

class TestCase8_ManufacturingPurchaseToPayAutomationAgent_W7_BlanketPOReleaseOngoingSupplyAgreement_easy(BaseManufacturingPurchaseToPayAutomationAgentTestCase):
    """
    Test case for: Blanket PO release, within limits, auto-approval and payment

    Validates successful blanket PO release and payment under ongoing supply agreement.
    Exercises blanket PO release branch, auto-approval for payment when within release limits.
    """

    test_case_id = "ManufacturingPurchaseToPayAutomationAgent_P2P_W7_TC1"
    title = "Blanket PO release, within limits, auto-approval and payment"
    workflow = "W7 - Blanket PO Release - Ongoing Supply Agreement"

    input_data = {
        "requisition_id": "REQ-446100",
        "requisition_type": "blanket_release",
        "amount": 3000.0,
        "cost_center": "CC-60500",
        "GL_account": "GL-60500",
        "supplier_id": "SUP-XYZ789",
        "priority": "normal",
        "invoice_id": "INV-222333",
        "receipt_id": "GR-444555"
    }

    expected_tool_calls = [
        {
            "name": "read_purchase_requisition",
            "tool_inputs": {
                "requisition_id": "REQ-446100"
            }
        },
        {
            "name": "check_supplier_contracts",
            "tool_inputs": {
                "supplier_id": "SUP-XYZ789",
                "item_list": [
                    {
                        "item_code": "RM-3003",
                        "quantity": 30,
                        "unit_price": 100.0
                    }
                ]
            }
        },
        {
            "name": "create_purchase_order",
            "tool_inputs": {
                "requisition_id": "REQ-446100",
                "supplier_id": "SUP-XYZ789",
                "item_list": [
                    {
                        "item_code": "RM-3003",
                        "quantity": 30,
                        "unit_price": 100.0
                    }
                ],
                "delivery_date": "2024-06-01",
                "contract_id": "CONT-BLANKET-001",
                "expedite": False
            }
        },
        {
            "name": "send_po_to_supplier",
            "tool_inputs": {
                "po_id": "PO-777777",
                "delivery_method": "edi"
            }
        },
        {
            "name": "match_invoice_to_po",
            "tool_inputs": {
                "po_id": "PO-777777",
                "receipt_id": "GR-444555",
                "invoice_id": "INV-222333"
            }
        },
        {
            "name": "route_payment_approval",
            "tool_inputs": {
                "invoice_id": "INV-222333",
                "match_status": "exact",
                "variance_amount": 0,
                "approval_level": "auto"
            }
        },
        {
            "name": "process_payment",
            "tool_inputs": {
                "invoice_id": "INV-222333",
                "payment_method": "ach",
                "amount": 3000.0,
                "scheduled_date": "2024-06-01"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Blanket PO release and payment completed successfully.",
                "result_data": {
                    "workflow_status": "completed",
                    "audit_log": {
                        "steps": [
                            "read_purchase_requisition",
                            "check_supplier_contracts",
                            "create_purchase_order",
                            "send_po_to_supplier",
                            "match_invoice_to_po",
                            "route_payment_approval",
                            "process_payment"
                        ],
                        "approvals": ["auto"],
                        "exceptions": []
                    },
                    "payment_details": {
                        "invoice_id": "INV-222333",
                        "payment_status": "completed",
                        "amount": 3000.0,
                        "scheduled_date": "2024-06-01",
                        "method": "ach"
                    },
                    "approval_status": "approved"
                }
            }
        }
    ]

    milestones = [
        {
            "step": 1,
            "description": "Blanket PO release requisition read",
            "expected_state": {
                "requisition_valid": True
            }
        },
        {
            "step": 2,
            "description": "Supplier contract checked for blanket status and limits",
            "expected_state": {
                "contract_status": "blanket",
                "release_limit": 5000.0
            }
        },
        {
            "step": 3,
            "description": "PO release created",
            "expected_state": {
                "po_id": "PO-777777",
                "items": [
                    {
                        "item_code": "RM-3003",
                        "quantity": 30,
                        "unit_price": 100.0
                    }
                ]
            }
        },
        {
            "step": 4,
            "description": "PO release sent to supplier",
            "expected_state": {
                "delivery_status": "sent",
                "method": "edi"
            }
        },
        {
            "step": 5,
            "description": "Goods receipt recorded",
            "expected_state": {
                "receipt_id": "GR-444555",
                "received_quantity": 30
            }
        },
        {
            "step": 6,
            "description": "Invoice matched to blanket PO and release",
            "expected_state": {
                "match_status": "blanket_release",
                "variance_amount": 0
            }
        },
        {
            "step": 7,
            "description": "Auto-approval routed for payment",
            "expected_state": {
                "approval_status": "approved",
                "approver": "auto"
            }
        },
        {
            "step": 8,
            "description": "Payment processed",
            "expected_state": {
                "payment_status": "completed",
                "method": "ach"
            }
        },
        {
            "step": 9,
            "description": "Workflow completion signaled",
            "expected_state": {
                "workflow_status": "completed"
            }
        }
    ]

    description = (
        "Validates successful blanket PO release and payment under ongoing supply agreement. "
        "Exercises blanket PO release branch, auto-approval for payment when within release limits."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test case follows the straightforward path for a blanket PO release within pre-approved limits, "
        "requiring no exception handling, escalation, or manual intervention. All steps are auto-approved and "
        "the scenario does not test edge cases, errors, or complex business logic."
    )

class TestCase9_ManufacturingPurchaseToPayAutomationAgent_W8___Emergency_Purchase___Expedited_Processing_easy(BaseManufacturingPurchaseToPayAutomationAgentTestCase):
    """
    Test Case 9: Urgent requisition, expedited PO and payment, production resumes

    Validates successful emergency purchase path with expedited PO and payment.
    Exercises urgent requisition branch, expedited PO creation, and payment processing.
    """

    test_case_id = "ManufacturingPurchaseToPayAutomationAgent_P2P_W8_TC1"
    title = "Urgent requisition, expedited PO and payment, production resumes"
    workflow = "W8 - Emergency Purchase - Expedited Processing"
    input_data = {
        "requisition_id": "REQ-446200",
        "requisition_type": "standard",
        "amount": 18000.0,
        "cost_center": "CC-50100",
        "GL_account": "GL-50100",
        "supplier_id": "SUP-ABC123",
        "priority": "urgent",
        "invoice_id": "INV-888999",
        "receipt_id": "GR-555666"
    }
    expected_tool_calls = [
        {
            "name": "read_purchase_requisition",
            "tool_inputs": {
                "requisition_id": "REQ-446200"
            }
        },
        {
            "name": "validate_budget_availability",
            "tool_inputs": {
                "cost_center": "CC-50100",
                "GL_account": "GL-50100",
                "amount": 18000.0
            }
        },
        {
            "name": "check_supplier_contracts",
            "tool_inputs": {
                "supplier_id": "SUP-ABC123",
                "item_list": [
                    {
                        "item_code": "RM-EXP-001",
                        "quantity": 100,
                        "unit_price": 180.0
                    }
                ]
            }
        },
        {
            "name": "create_purchase_order",
            "tool_inputs": {
                "requisition_id": "REQ-446200",
                "supplier_id": "SUP-ABC123",
                "item_list": [
                    {
                        "item_code": "RM-EXP-001",
                        "quantity": 100,
                        "unit_price": 180.0
                    }
                ],
                "delivery_date": "2024-03-01",
                "contract_id": "CONT-PRF001",
                "expedite": True
            }
        },
        {
            "name": "send_po_to_supplier",
            "tool_inputs": {
                "po_id": "PO-888888",
                "delivery_method": "email",
                "contact_info": {
                    "email": "expedite@supplier.com",
                    "phone": "+15551234567"
                }
            }
        },
        {
            "name": "match_invoice_to_po",
            "tool_inputs": {
                "po_id": "PO-888888",
                "receipt_id": "GR-555666",
                "invoice_id": "INV-888999"
            }
        },
        {
            "name": "route_payment_approval",
            "tool_inputs": {
                "invoice_id": "INV-888999",
                "match_status": "exact",
                "variance_amount": 0,
                "approval_level": "auto"
            }
        },
        {
            "name": "process_payment",
            "tool_inputs": {
                "invoice_id": "INV-888999",
                "payment_method": "ach",
                "amount": 18000.0,
                "scheduled_date": "2024-03-02"
            }
        },
        {
            "name": "SUCCESS",
            "tool_inputs": {
                "message": "Emergency purchase completed, payment processed, and production resumed.",
                "result_data": {
                    "workflow_status": "completed",
                    "audit_log": {
                        "steps": [
                            "read_purchase_requisition",
                            "validate_budget_availability",
                            "check_supplier_contracts",
                            "create_purchase_order",
                            "send_po_to_supplier",
                            "match_invoice_to_po",
                            "route_payment_approval",
                            "process_payment"
                        ],
                        "approvals": [
                            "auto"
                        ],
                        "exceptions": [
                            {
                                "type": "expedited",
                                "resolution": "urgent purchase processed"
                            }
                        ]
                    },
                    "payment_details": {
                        "invoice_id": "INV-888999",
                        "payment_status": "completed",
                        "amount": 18000.0,
                        "scheduled_date": "2024-03-02",
                        "method": "ach"
                    },
                    "approval_status": "approved"
                }
            }
        }
    ]
    milestones = [
        {
            "step": 1,
            "description": "Emergency purchase requisition read",
            "expected_state": {
                "requisition_valid": True,
                "priority": "urgent"
            }
        },
        {
            "step": 2,
            "description": "Budget validated for expedited purchase",
            "expected_state": {
                "budget_status": "within_limit"
            }
        },
        {
            "step": 3,
            "description": "Supplier contract checked (bidding bypassed)",
            "expected_state": {
                "contract_status": "preferred"
            }
        },
        {
            "step": 4,
            "description": "Expedited PO created with overnight shipping",
            "expected_state": {
                "po_id": "PO-888888",
                "expedite": True
            }
        },
        {
            "step": 5,
            "description": "PO sent to supplier via call and email",
            "expected_state": {
                "delivery_status": "sent",
                "method": "email"
            }
        },
        {
            "step": 6,
            "description": "Goods receipt recorded",
            "expected_state": {
                "receipt_id": "GR-555666",
                "received_quantity": 100
            }
        },
        {
            "step": 7,
            "description": "Invoice matched to PO including expedited charges",
            "expected_state": {
                "match_status": "exact",
                "variance_amount": 0
            }
        },
        {
            "step": 8,
            "description": "Payment approval routed for expedited payment",
            "expected_state": {
                "approval_status": "approved",
                "approver": "auto"
            }
        },
        {
            "step": 9,
            "description": "Payment processed",
            "expected_state": {
                "payment_status": "completed",
                "method": "ach"
            }
        },
        {
            "step": 10,
            "description": "Workflow completion signaled",
            "expected_state": {
                "workflow_status": "completed"
            }
        }
    ]
    description = (
        "Validates successful emergency purchase path with expedited PO and payment. "
        "Exercises urgent requisition branch, expedited PO creation, and payment processing."
    )
    difficulty = "easy"
    difficulty_reasoning = (
        "This test follows the happy path for an urgent requisition: all data is valid, "
        "budget is within limits, supplier is preferred, and no exceptions or failures occur. "
        "No escalations or manual steps are required."
    )

    # No tool method overrides are required for this test case as it follows the happy path.