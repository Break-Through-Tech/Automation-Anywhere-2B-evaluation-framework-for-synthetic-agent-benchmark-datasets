# Banking Accounts and Deposits Agent - Seed Prompt

## Agent Overview
This agent automates the account opening process by processing digital account applications, validating customer identity, performing AML (Anti-Money Laundering) checks, configuring account products with appropriate limits and fees, and generating required disclosures and documentation.

## Business Context
Traditional account opening requires branch visits, paper forms, manual data entry, and compliance reviews taking hours or days. This agent enables instant digital account opening while ensuring regulatory compliance (KYC, AML, USA PATRIOT Act) and proper product configuration, reducing time-to-open from 2-3 days to under 15 minutes.

## Real-World Scenario
**Trigger:** Customer David Martinez applies online for a high-yield savings account with initial deposit of $10,000.

**Stakes:** Digital account opening is table stakes for competitive banking. Compliance failures result in regulatory penalties. Poor product configuration leads to customer complaints and operational losses.

**Process Chain:**
- Customer completes online form with personal info and funding source
- Agent validates identity against databases (credit bureaus, DMV)
- Performs AML risk assessment and OFAC sanctions screening
- Determines account tier based on deposit amount and customer profile
- Configures account limits (withdrawal, transfer, transaction)
- Sets fee schedule based on balance and account type
- Generates required disclosures (Truth in Savings, privacy notice, fee schedule)
- Links funding source (external bank, wire, check)
- Opens account and sends confirmation

**Resolution:** Account opened in 12 minutes with full compliance documentation vs. 2-day manual process.

## Agent Capabilities

### Core Tools (6-7 recommended)
1. **validate_customer_identity** - Verify identity using credit bureau data, ID verification services
2. **perform_aml_screening** - Check customer against OFAC, sanctions lists, PEP databases
3. **calculate_account_tier** - Determine product tier based on deposit amount, relationship value
4. **configure_account_limits** - Set withdrawal limits, transfer limits, overdraft settings
5. **configure_fee_schedule** - Apply fee waivers, maintenance fees, transaction fees based on tier
6. **generate_account_disclosures** - Create Truth in Savings, fee schedule, privacy notices
7. **link_funding_source** - Connect external bank account, verify micro-deposits or instant verification
8. **open_account** - Create account in core banking system with all configurations

### Integration Points
- **Identity Verification:** LexisNexis, Experian, ID.me, Jumio
- **AML/Sanctions:** Dow Jones, Refinitiv World-Check, OFAC API
- **Core Banking:** Temenos T24, FIS Profile, Jack Henry Symitar
- **Account Opening:** Alkami, Q2, Backbase, nCino
- **Funding Verification:** Plaid, Yodlee, MX, Finicity
- **Document Generation:** DocuSign, Adobe Sign, Templafy

## Sample Workflows to Generate

### 1. Premium Savings Account Opening (Happy Path)
**User Intent:** "Open savings account from application #ACC-8821"
**Steps:**
1. Validate customer identity → Identity verified via credit bureau match (David Martinez, SSN, DOB)
2. Perform AML screening → Clear OFAC/sanctions screening, low risk
3. Calculate account tier → $10K deposit qualifies for Premium tier (>$5K)
4. Configure account limits → $50K daily withdrawal, unlimited transfers
5. Configure fee schedule → $0 monthly fee (waived for Premium), $3 ATM fee waived
6. Generate account disclosures → Truth in Savings (2.5% APY), privacy notice, fee schedule
7. Link funding source → External Wells Fargo account linked via Plaid, verified instantly
8. Open account → Account #4455-6677-8899 opened, $10K transfer initiated

### 2. Student Checking Account - Special Fee Structure
**User Intent:** "Process student checking application #ACC-8834"
**Steps:**
1. Validate customer identity → Student status verified via .edu email and enrollment verification
2. Perform AML screening → Clear, low risk (age 19, no adverse findings)
3. Calculate account tier → Student tier (age <25, enrolled student)
4. Configure account limits → $500 daily ATM withdrawal, $2K daily debit purchase
5. Configure fee schedule → $0 monthly fee, $0 overdraft fees, free ATM network
6. Generate account disclosures → Student checking disclosures, no minimum balance requirement
7. Link funding source → Parent's account linked for initial $500 deposit
8. Open account → Student checking opened with special fee waivers

### 3. Business Checking - Multi-Signer Setup
**User Intent:** "Open business checking from application #ACC-8847"
**Steps:**
1. Validate customer identity → All 3 business owners verified (EIN, business license, personal IDs)
2. Perform AML screening → Business and all owners cleared, medium risk (cash business)
3. Calculate account tier → Business Basic tier ($5K initial deposit)
4. Configure account limits → $25K daily ACH, 200 free transactions/month
5. Configure fee schedule → $15/month maintenance, $0.50/transaction over 200
6. Generate account disclosures → Business account agreement, fee schedule, CIP notice
7. Link funding source → Wire transfer of $5K from business savings
8. Open account → Business account opened with 3 authorized signers

### 4. High-Risk Customer - Enhanced Monitoring Required
**User Intent:** "Process account application #ACC-8855"
**Steps:**
1. Validate customer identity → Identity verified successfully
2. Perform AML screening → Customer from high-risk country, cash-intensive business (money services)
3. Calculate account tier → Standard tier but flagged for enhanced due diligence (EDD)
4. (Escalate for review) → Case routed to Compliance for manual review
5. (Compliance approves with conditions) → Approved with transaction monitoring
6. Configure account limits → Lower limits: $5K daily withdrawal, $10K daily transfers
7. Configure fee schedule → Standard fees apply
8. Open account → Account opened with enhanced monitoring flag, quarterly reviews required

### 5. Failed Identity Verification - Decline
**User Intent:** "Process application #ACC-8862"
**Steps:**
1. Validate customer identity → Identity verification failed (SSN doesn't match name/DOB)
2. (Request additional documents) → Customer asked to provide government ID and proof of SSN
3. (Customer provides documents) → Documents appear fraudulent (altered SSN card)
4. (Fraud detected) → Identity theft suspected
5. (Decline application) → Application declined for security reasons
6. (File fraud report) → Incident reported to fraud team and FinCEN

### 6. Joint Account Opening - Multiple Owners
**User Intent:** "Open joint savings account #ACC-8871"
**Steps:**
1. Validate customer identity → Both owners verified (married couple)
2. Perform AML screening → Both cleared
3. Calculate account tier → Premium tier ($25K initial deposit)
4. Configure account limits → Both owners have full access, equal signing authority
5. Configure fee schedule → Premium tier fee waivers apply
6. Generate account disclosures → Joint account agreement, survivorship rights disclosure
7. Link funding source → Transfer from existing individual account
8. Open account → Joint savings opened with rights of survivorship

### 7. Funding Source Verification Failed - Hold Account
**User Intent:** "Open checking account from application #ACC-8883"
**Steps:**
1. Validate customer identity → Identity verified
2. Perform AML screening → Clear
3. Calculate account tier → Standard tier
4. Link funding source → External account provided for $2K initial deposit
5. (Micro-deposit verification) → Micro-deposits sent (2-3 business days)
6. Configure account limits → Limited access until funding verified
7. Open account → Account opened in restricted mode (no withdrawals until verified)
8. Generate account disclosures → Disclosure includes funding verification requirements

### 8. Same-Day Account Opening with Cash Deposit
**User Intent:** "Open account for walk-in customer #ACC-8891"
**Steps:**
1. Validate customer identity → ID scanned, identity verified at branch
2. Perform AML screening → Clear, customer bringing $15K cash (CTR threshold)
3. (File CTR) → Currency Transaction Report filed for cash deposit >$10K
4. Calculate account tier → Premium tier
5. Configure account limits → Full access immediately (in-person verification)
6. Configure fee schedule → Premium fee waivers
7. Generate account disclosures → Paper disclosures provided and signed
8. Open account → Account opened, $15K cash deposit processed, CTR filed

## Key Decisions
- Approve standard account openings (automated for low-risk)
- Escalate high-risk customers for enhanced due diligence
- Decline fraudulent applications or identity verification failures
- Determine account tier and fee structure based on deposit and profile
- Require additional verification for funding sources
- File CTRs for cash deposits ≥$10K

## Compliance Requirements
- USA PATRIOT Act (Customer Identification Program)
- Bank Secrecy Act (AML, CTR, SAR filing)
- OFAC sanctions screening
- Truth in Savings Act (deposit disclosures)
- Regulation CC (funds availability)
- Regulation E (electronic fund transfers)
- Privacy regulations (Gramm-Leach-Bliley Act)
