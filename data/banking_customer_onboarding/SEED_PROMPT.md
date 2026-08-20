# Banking Customer Onboarding Agent - Seed Prompt

## Agent Overview
This agent automates the customer onboarding process by reading uploaded KYC (Know Your Customer) documents, extracting required fields, validating against sanction lists and compliance databases, creating customer profiles in core banking and CRM systems, and sending welcome communications.

## Business Context
Traditional customer onboarding in banking requires manual document review, data entry across multiple systems, compliance checks, and can take 3-5 days to complete. This agent reduces onboarding time to under 30 minutes while ensuring regulatory compliance (AML, sanctions screening, identity verification) and improving customer experience.

## Real-World Scenario
**Trigger:** New customer Sarah Chen submits online account application with ID documents, proof of address, and employment verification.

**Stakes:** Competitive banking market means slow onboarding leads to customer abandonment. Regulatory penalties for incomplete KYC can reach millions. Customer expects instant account access.

**Process Chain:**
- Customer uploads driver's license, utility bill, W-2 form
- Agent extracts personal data (name, DOB, SSN, address)
- Validates identity against government databases
- Screens against OFAC, UN sanctions lists
- Performs AML risk assessment
- Creates customer profile in core banking system
- Sets up account in CRM with risk tier
- Sends personalized welcome email with account details

**Resolution:** Complete onboarding with regulatory compliance in 20 minutes vs. 2-3 days manual process.

## Agent Capabilities

### Core Tools (6-7 recommended)
1. **extract_kyc_documents** - Use OCR/document AI to extract data from ID, passport, utility bills (PDF/images)
2. **validate_identity** - Verify identity against government databases (DMV, SSA) and fraud detection services
3. **screen_sanctions_lists** - Check customer against OFAC, UN, EU sanctions lists and PEP databases
4. **calculate_aml_risk_score** - Assess anti-money laundering risk based on profile, geography, occupation
5. **create_core_banking_customer** - Create customer record in core banking system with account settings
6. **create_crm_profile** - Create customer in CRM with KYC documents, risk tier, and relationship data
7. **send_welcome_communication** - Generate and send personalized welcome email with account credentials

### Integration Points
- **Document AI:** Google Document AI, AWS Textract, Azure Form Recognizer
- **Identity Verification:** LexisNexis, Jumio, Onfido, ID.me
- **Sanctions Screening:** Dow Jones Risk & Compliance, Refinitiv World-Check
- **Core Banking:** Temenos T24, FIS Profile, Finastra Fusion
- **CRM:** Salesforce Financial Services Cloud, Microsoft Dynamics 365
- **Communication:** SendGrid, Twilio, Amazon SES

## Sample Workflows to Generate

### 1. Standard Personal Account Onboarding (Happy Path)
**User Intent:** "Onboard new customer application #APP-2045"
**Steps:**
1. Extract KYC documents → Driver's license: Sarah Chen, DOB 03/15/1988, address extracted
2. Extract KYC documents → Utility bill: Address confirmed at 123 Main St, Boston MA
3. Validate identity → DMV check passed, SSN verified with SSA
4. Screen sanctions lists → No matches on OFAC, UN, EU lists
5. Calculate AML risk score → Low risk (US citizen, employed, no high-risk factors)
6. Create core banking customer → Customer ID CUST-887234 created with checking account
7. Create CRM profile → Profile created with Low risk tier, documents attached
8. Send welcome communication → Welcome email sent with online banking credentials

### 2. High-Risk Customer - Enhanced Due Diligence Required
**User Intent:** "Process onboarding for application #APP-2156"
**Steps:**
1. Extract KYC documents → Passport extracted: Name, nationality (high-risk country)
2. Validate identity → Passport verified authentic via security features
3. Screen sanctions lists → No exact match, but similar name flagged for review
4. Calculate AML risk score → High risk (foreign national, cash-intensive business owner)
5. (Escalate for manual review) → Case routed to Compliance Officer with evidence
6. (Human decision required) → Compliance approves with enhanced monitoring
7. Create core banking customer → Account created with enhanced monitoring flag
8. Create CRM profile → Profile marked for quarterly reviews
9. Send welcome communication → Account opened, in-person visit requested

### 3. Failed Identity Verification - Fraud Prevention
**User Intent:** "Onboard application #APP-2198"
**Steps:**
1. Extract KYC documents → Driver's license data extracted
2. Validate identity → DMV check failed - license number invalid
3. (Fraud detected) → Document appears altered or fake
4. (Reject application) → Application rejected, fraud alert filed
5. Send communication → Rejection email sent, advise to visit branch with original documents

### 4. Business Account Onboarding - Multiple Documents
**User Intent:** "Process business account application #APP-2201"
**Steps:**
1. Extract KYC documents → Articles of incorporation, EIN letter, owner IDs extracted
2. Extract KYC documents → Business license and owner addresses confirmed
3. Validate identity → All 3 beneficial owners verified
4. Screen sanctions lists → Business and all owners screened - clear
5. Calculate AML risk score → Medium risk (cash business - restaurant)
6. Create core banking customer → Business account created with 3 authorized signers
7. Create CRM profile → Business profile with ownership structure documented
8. Send welcome communication → Welcome packet sent to business email and owners

### 5. Sanctions Match - Immediate Escalation
**User Intent:** "Onboard application #APP-2215"
**Steps:**
1. Extract KYC documents → Passport and address proof extracted
2. Validate identity → Identity verified successfully
3. Screen sanctions lists → Exact match on OFAC SDN list (Specially Designated National)
4. (Immediate escalation) → Case escalated to Compliance and Legal teams
5. (Freeze application) → Application frozen, no account created
6. (Regulatory filing) → SAR (Suspicious Activity Report) filed with FinCEN

### 6. Incomplete Documentation - Customer Follow-up
**User Intent:** "Process application #APP-2178"
**Steps:**
1. Extract KYC documents → Driver's license extracted successfully
2. Extract KYC documents → Proof of address missing or illegible
3. (Request additional documents) → Email sent requesting utility bill or bank statement
4. (Customer uploads new doc) → Clear utility bill received
5. Validate identity → Full verification completed
6. Screen sanctions lists → Clear
7. Calculate AML risk score → Low risk
8. Create core banking customer → Account created
9. Send welcome communication → Welcome email with account details

### 7. Address Mismatch - Data Reconciliation
**User Intent:** "Onboard application #APP-2189"
**Steps:**
1. Extract KYC documents → Driver's license shows address: 456 Oak Ave, Miami FL
2. Extract KYC documents → Utility bill shows different address: 789 Pine St, Miami FL
3. Validate identity → Identity verified but address discrepancy flagged
4. (Request explanation) → Customer contacted about address difference
5. (Customer explains) → Recently moved, driver's license not yet updated
6. Extract KYC documents → Lease agreement provided for new address
7. Screen sanctions lists → Clear
8. Create core banking customer → Account created with current address
9. Send welcome communication → Welcome email sent

## Key Decisions
- Approve standard onboarding (automated for low-risk)
- Escalate high-risk customers for enhanced due diligence
- Reject fraudulent or non-compliant applications
- Request additional documentation when incomplete
- File suspicious activity reports when required

## Compliance Requirements
- PATRIOT Act compliance (identity verification)
- Bank Secrecy Act (AML monitoring)
- OFAC sanctions screening
- Customer Identification Program (CIP)
- Enhanced due diligence for high-risk customers
- Record retention (7 years minimum)
