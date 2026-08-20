# Manufacturing Purchase-to-Pay Agent - Seed Prompt

## Agent Overview
This agent automates the procure-to-pay (P2P) process by reading purchase requisitions, validating budget availability, creating purchase orders, confirming with suppliers, matching invoices to receipts, and routing payment exceptions for resolution.

## Business Context
Traditional P2P requires manual requisition approvals, PO creation, 3-way matching (PO-receipt-invoice), and exception handling—taking days per transaction and causing payment delays. This agent reduces processing time from 3-5 days to hours, prevents maverick spending, ensures accurate matching, and improves supplier relationships through timely payment.

## Real-World Scenario
**Trigger:** Production manager submits requisition for $15,000 of raw materials (steel sheets) for manufacturing line.

**Stakes:** Budget overruns without validation. Delayed POs cause production stoppages. Invoice mismatches create payment disputes. Manual errors cause duplicate payments or missed discounts.

**Process Chain:**
- Receive purchase requisition from requester
- Validate against approved budget and spending authority
- Check if preferred supplier contract exists
- Create purchase order with line items, pricing, delivery date
- Send PO to supplier for confirmation
- Receive goods and record receipt in system
- Match supplier invoice to PO and receipt (3-way match)
- Route for payment approval if matched, flag exceptions if mismatched
- Process payment via ACH/check when approved

**Resolution:** Requisition to PO in 15 minutes vs. 2-day manual approval process, with budget validation preventing $3K overspend.

## Agent Capabilities

### Core Tools (8 tools)

#### 1. read_purchase_requisition
**Purpose:** Parse requisition details from ERP or procurement system
**Input:** `requisition_id`
**Returns:**
```
{
  requisition_id, requester_id, requester_name, cost_center, GL_account,
  supplier_id, submission_date, amount, requisition_type, urgency, status,
  items: [
    { item_code, description, quantity, unit_price, unit_of_measure }
  ]
}
```

#### 2. validate_budget_availability
**Purpose:** Check budget balance for cost center and GL account
**Input:** `cost_center`, `GL_account`, `amount`
**Returns:**
```
{
  cost_center, GL_account, budget_amount, spent_amount, available_balance,
  requested_amount, sufficient_funds (boolean), approval_required (boolean)
}
```

#### 3. check_supplier_contracts
**Purpose:** Verify preferred supplier status, contract pricing, and terms
**Input:** `supplier_id`, `items` (list of item codes/descriptions)
**Returns:**
```
{
  supplier_id, supplier_name, contract_id, contract_status, is_preferred,
  pricing: [
    { item_code, contract_price, unit_of_measure, min_quantity }
  ],
  payment_terms, delivery_terms, contract_expiration
}
```

#### 4. create_purchase_order
**Purpose:** Generate PO with line items, pricing, and delivery terms
**Input:** `requisition_id`, `supplier_id`, `line_items`, `delivery_date`, `expedited` (optional)
**Returns:**
```
{
  po_id, requisition_id, supplier_id, contract_id, total_amount,
  delivery_date, status, expedited,
  line_items: [
    { item_code, description, quantity, unit_price }
  ],
  created_date
}
```

#### 5. send_po_to_supplier
**Purpose:** Transmit PO via EDI, email, or supplier portal
**Input:** `po_id`, `supplier_id`, `delivery_method`
**Returns:**
```
{
  delivery_id, po_id, supplier_id, delivery_method, delivery_status,
  sent_timestamp, acknowledgment_received (boolean), acknowledgment_timestamp
}
```

#### 6. match_invoice_to_po
**Purpose:** Perform 3-way match between PO, goods receipt, and supplier invoice
**Input:** `invoice_id`, `po_id`, `receipt_id`
**Returns:**
```
{
  match_id, invoice_id, po_id, receipt_id, match_status (exact|variance|mismatch),
  po_amount, receipt_amount, invoice_amount,
  variance_amount, variance_percent, variance_reason,
  recommended_action (auto_approve|review|reject)
}
```

#### 7. route_payment_approval
**Purpose:** Submit matched invoices for payment approval or flag exceptions
**Input:** `invoice_id`, `match_status`, `variance_details` (optional), `payment_terms` (optional)
**Returns:**
```
{
  approval_id, invoice_id, match_status, approval_status (approved|pending|rejected),
  approver_id, approval_timestamp, scheduled_payment_date, payment_amount,
  notes, early_payment_discount_available, discount_amount
}
```

#### 8. process_payment
**Purpose:** Generate payment to supplier via ACH, wire, or check
**Input:** `invoice_id`, `payment_amount`, `payment_method`, `scheduled_date`
**Returns:**
```
{
  payment_id, invoice_id, payment_amount, payment_method, payment_status,
  payment_date, confirmation_number, supplier_id
}
```

### Integration Points
- **ERP:** SAP, Oracle, NetSuite, Microsoft Dynamics
- **Procurement:** Coupa, Ariba, Jaggaer, Ivalua
- **Supplier Networks:** Ariba Network, Taulia, Tradeshift
- **EDI:** 850 (PO), 810 (invoice), 855 (PO acknowledgment)
- **Payment:** ACH processors, banking APIs, payment cards
- **Budgeting:** Adaptive Insights, Anaplan, ERP budget modules

## Sample Workflows to Generate

### W1. Standard Raw Materials Purchase - 3-Way Match (Happy Path)
**User Intent:** "Process requisition #REQ-445521 for steel materials"
**Steps:**
1. Read purchase requisition → 500 sheets steel @ $30/sheet, total $15,000
2. Validate budget availability → Budget sufficient, no approval needed
3. Check supplier contracts → Preferred supplier with contract price $28/sheet
4. Create purchase order → PO created with contract pricing
5. Send PO to supplier → Transmitted via EDI, acknowledgment received
6. Match invoice to PO → Exact 3-way match (PO = receipt = invoice)
7. Route payment approval → Auto-approved for exact match
8. Process payment → ACH payment processed
9. SUCCESS

### W2. Budget Override Required
**User Intent:** "Process requisition that exceeds budget"
**Steps:**
1. Read purchase requisition → $25,000 equipment purchase
2. Validate budget availability → Budget exceeded by $7,000
3. HUMAN_IN_THE_LOOP → Escalate for budget override approval

### W3. Invoice Variance - Exception Routing
**User Intent:** "Match invoice with price discrepancy"
**Steps:**
1. Match invoice to PO → Invoice $500 higher than PO (5% variance)
2. Route payment approval → Flag for AP review due to variance
3. HUMAN_IN_THE_LOOP → Route to accounts payable for investigation

### W4. Partial Receipt - Quantity Discrepancy
**User Intent:** "Process receipt where quantity differs from PO"
**Steps:**
1. Match invoice to PO → Received 450 units, billed for 500 units
2. Route payment approval → Approve partial payment for received quantity
3. Process payment → Pay for 450 units, hold balance for backorder
4. SUCCESS (partial)

### W5. Duplicate Invoice Detection
**User Intent:** "Check if invoice is duplicate"
**Steps:**
1. Match invoice to PO → Detect same amount/PO/date as previous paid invoice
2. Route payment approval → Reject as duplicate
3. FAILED → Invoice rejected, supplier notified

### W6. Early Payment Discount
**User Intent:** "Process invoice with 2/10 net 30 terms"
**Steps:**
1. Match invoice to PO → Exact match, $50,000 invoice
2. Route payment approval → Calculate $1,000 early payment discount available
3. Process payment → Pay $49,000 within 10 days to capture discount
4. SUCCESS

### W7. Blanket PO Release
**User Intent:** "Process release against blanket purchase order"
**Steps:**
1. Read purchase requisition → Request against blanket agreement
2. Check supplier contracts → Validate against blanket PO limits
3. Create purchase order → Create release against blanket PO
4. Send PO to supplier → Send release notice
5. Match invoice to PO → Match to blanket PO pricing
6. Route payment approval → Auto-approve per blanket terms
7. Process payment → Process payment
8. SUCCESS

### W8. Emergency Purchase - Expedited Processing
**User Intent:** "URGENT: Process emergency requisition for critical part"
**Steps:**
1. Read purchase requisition → Critical machine part, production down
2. Validate budget availability → Budget available, bypass standard approval
3. Create purchase order → Create with expedite flag
4. Send PO to supplier → Urgent transmission, confirm same-day ship
5. Match invoice to PO → Match with expedited shipping charges
6. Route payment approval → Approve with expedite surcharge
7. Process payment → Expedited payment processing
8. SUCCESS

## Key Decision Points
- Auto-approve requisitions within budget and authority limits
- Escalate budget overruns to appropriate approval level (HUMAN_IN_THE_LOOP)
- Route invoice variances based on tolerance thresholds
- Recommend early payment when discounts available and cash flow permits
- Reject duplicate invoices automatically (FAILED)
- Expedite critical purchases bypassing standard workflows

## 3-Way Match Tolerance Rules
- **Exact match:** Auto-approve for payment
- **Small variance (<2% or <$100):** Auto-approve with notification
- **Medium variance (2-10% or $100-$1000):** Route to buyer for review
- **Large variance (>10% or >$1000):** Route to manager for approval
- **Quantity mismatch:** Hold payment until discrepancy resolved

## Compliance Requirements
- Segregation of duties (requester ≠ approver ≠ receiver)
- Budget authorization levels (dollar limits by role)
- Preferred supplier compliance (maverick spend tracking)
- Audit trail (all approvals, changes, overrides logged)
- Tax compliance (accurate GL coding, 1099 reporting)
- Payment terms (honor early payment discounts, avoid late fees)

## Data Entities Required

### Primary Entities
- **PurchaseRequisition** - with `items` array containing line item details
- **Supplier** - supplier master data
- **SupplierContract** - contract terms and pricing
- **Budget** - budget allocations by cost center/GL account

### Transactional Entities
- **PurchaseOrder** - with `line_items` array
- **PODelivery** - PO transmission/acknowledgment records
- **GoodsReceipt** - receiving records
- **Invoice** - supplier invoices

### Process Result Entities
- **InvoiceMatch** - 3-way match results
- **PaymentApproval** - approval routing results
- **Payment** - payment execution records

### Audit Entities
- **AuditLog** - all transactions and approvals
- **Exception** - exception cases for review
