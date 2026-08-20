# Banking Fraud Monitoring Support Agent - Seed Prompt

## Agent Overview
This agent supports fraud investigation by triaging fraud alerts, gathering contextual data across multiple systems (transaction history, customer profiles, device data, geographic patterns), calculating risk scores, and routing suspicious cases to fraud analysts with comprehensive case summaries.

## Business Context
Banks receive thousands of fraud alerts daily from rule-based systems and ML models. Manual triage requires analysts to check 5-10 systems per alert, taking 15-30 minutes per case. This agent automates alert enrichment, reduces false positive review time from 15 minutes to 2 minutes, and escalates true fraud cases with complete investigation packages, enabling analysts to focus on complex cases and customer contact.

## Real-World Scenario
**Trigger:** Fraud alert triggered on debit card transaction: $2,500 purchase at electronics store in Miami, FL (customer's home state: California).

**Stakes:** Fraud losses average $500 per incident. False declines damage customer relationships and cause revenue loss. Slow response allows fraudsters to continue spending. Regulatory requirements mandate timely fraud detection and customer notification.

**Process Chain:**
- Alert received from fraud detection system
- Pull customer profile, account history, typical spending patterns
- Retrieve transaction details, merchant info, device data
- Check recent account activity, login patterns, geolocation history
- Identify anomalies (location, amount, merchant category, velocity)
- Calculate risk score using multiple fraud signals
- Cross-reference with known fraud patterns and blacklists
- Route high-risk cases to analysts with full context
- Auto-decline obvious fraud, auto-approve legitimate patterns

**Resolution:** Alert triaged in 90 seconds with complete investigation package vs. 15 minutes manual lookup, enabling analyst to contact customer immediately.

## Agent Capabilities

### Core Tools (6-7 recommended)
1. **retrieve_transaction_details** - Get transaction amount, merchant, MCC, location, device data
2. **get_customer_profile** - Pull customer demographics, account tenure, typical behaviors
3. **analyze_transaction_history** - Review 90-day spending patterns, velocity, geographic usage
4. **check_device_intelligence** - Verify device ID, IP address, browser fingerprint, VPN usage
5. **calculate_fraud_risk_score** - Score based on amount, location, merchant, velocity, device signals
6. **cross_reference_fraud_databases** - Check merchant against blacklist, card against BIN attack lists
7. **route_to_analyst** - Escalate high-risk cases with investigation summary and recommended action
8. **auto_decline_transaction** - Block obvious fraud (stolen card, known bad merchant)
9. **request_customer_verification** - Trigger SMS/email verification for suspicious but uncertain cases

### Integration Points
- **Fraud Detection:** FICO Falcon, SAS Fraud Management, Feedzai, NICE Actimize
- **Transaction Systems:** Core banking, card processor (Visa, Mastercard)
- **Device Intelligence:** ThreatMetrix, Kount, Sift, Arkose Labs
- **Geolocation:** MaxMind, IP2Location, Google Maps API
- **Case Management:** Salesforce, ServiceNow, Pega
- **Communication:** Twilio (SMS), SendGrid (email), mobile app push

## Sample Workflows to Generate

### 1. Out-of-Pattern Purchase - Legitimate (False Positive)
**User Intent:** "Triage fraud alert #FA-883421"
**Steps:**
1. Retrieve transaction details → $2,500 debit card purchase, Best Buy Miami, FL, 2:15 PM EST
2. Get customer profile → Sarah Johnson, CA resident, account 8 years, good standing
3. Analyze transaction history → Typical spending $300-800, mostly CA merchants
4. Check device intelligence → Same device ID as previous purchases, same mobile app
5. (Check additional context) → Customer has flight booking to Miami 2 days ago (same card)
6. Calculate fraud risk score → Score: 35/100 (low risk - travel detected)
7. (Auto-approve) → Transaction approved, no customer contact needed

### 2. Card-Not-Present Fraud - High Risk Escalation
**User Intent:** "Investigate alert #FA-883445"
**Steps:**
1. Retrieve transaction details → $1,200 online purchase, crypto exchange, IP: Romania
2. Get customer profile → David Martinez, TX resident, account 3 years
3. Analyze transaction history → No prior crypto purchases, never used international IPs
4. Check device intelligence → New device, VPN detected, browser fingerprint doesn't match
5. Calculate fraud risk score → Score: 92/100 (high risk)
6. Cross reference fraud databases → Merchant on watch list (frequent fraud complaints)
7. Route to analyst → Case escalated with summary: "Likely stolen card - new device, foreign IP, high-risk merchant"
8. (Analyst action) → Card blocked, customer contacted for verification

### 3. Account Takeover - Login from New Location
**User Intent:** "Review alert #FA-883456"
**Steps:**
1. (Check login activity) → Login from Moscow, Russia (customer location: Ohio)
2. Get customer profile → Michael Chen, 15-year customer, never traveled internationally
3. Check device intelligence → New device, different OS, suspicious user agent
4. (Check recent activity) → Password change requested 10 minutes before login
5. (Check email access) → Email forwarding rule added to external address
6. Calculate fraud risk score → Score: 98/100 (account takeover)
7. (Auto-block account) → Online banking access suspended immediately
8. Route to analyst → Urgent escalation: "Account takeover in progress - password changed, email forwarded"
9. (Analyst contacts customer) → Customer confirms unauthorized access, account secured

### 4. Velocity Fraud - Multiple Small Transactions
**User Intent:** "Analyze alert #FA-883467"
**Steps:**
1. Retrieve transaction details → 15 transactions in 2 hours: gas stations, convenience stores
2. Analyze transaction history → Transactions across 5 states (CA, NV, AZ, TX, FL) in 2 hours
3. Calculate fraud risk score → Score: 88/100 (impossible travel pattern)
4. (Check card present/not present) → All card-present with PIN (suggests skimmed card)
5. Cross reference fraud databases → 3 merchants on fraud hot-list for skimming
6. Route to analyst → Case escalated: "Card skimming - multiple states, high-risk merchants"
7. (Analyst blocks card) → Card deactivated, new card issued
8. (Customer notification) → SMS sent: "We detected fraud on your card ending in 5678"

### 5. Friendly Fraud - Chargeback Investigation
**User Intent:** "Investigate chargeback dispute #FA-883478"
**Steps:**
1. Retrieve transaction details → $850 purchase at jewelry store, customer claims "not authorized"
2. Get customer profile → Lisa Anderson, customer 5 years, no prior disputes
3. Analyze transaction history → Same merchant used 3 times in past year, no issues
4. Check device intelligence → Transaction from customer's registered device, home IP address
5. (Check additional evidence) → Item delivered to customer's address, signature on file
6. Calculate fraud risk score → Score: 15/100 (likely friendly fraud)
7. Route to analyst → Case summary: "Likely friendly fraud - customer's device, home address, prior purchases at merchant"
8. (Analyst denies chargeback) → Evidence supports merchant, chargeback denied

### 6. Synthetic Identity Fraud - New Account
**User Intent:** "Review new account alert #FA-883489"
**Steps:**
1. Get customer profile → New account opened online, Robert Williams, SSN provided
2. (Verify identity) → SSN valid but only 2 years of credit history (red flag)
3. Check device intelligence → Device linked to 5 other recent account applications
4. (Check identity databases) → Address doesn't match SSN records, phone number is VOIP
5. Calculate fraud risk score → Score: 94/100 (synthetic identity)
6. Cross reference fraud databases → Phone number appears on fraud database
7. Route to analyst → Urgent: "Synthetic identity suspected - mismatched data, device used in multiple applications"
8. (Analyst closes account) → Account closed, application rejected, fraud report filed

### 7. Authorized Push Payment (APP) Fraud - Wire Transfer
**User Intent:** "Investigate wire transfer alert #FA-883492"
**Steps:**
1. Retrieve transaction details → $15,000 wire to "TechSupport Solutions LLC"
2. Get customer profile → Elderly customer, 82 years old, never sent wires before
3. Analyze transaction history → First wire ever, initiated via phone banking
4. (Check call recording) → Customer called from verified number, sounded confused
5. Cross reference fraud databases → Beneficiary "TechSupport Solutions" on scam list
6. Calculate fraud risk score → Score: 85/100 (elder fraud/scam)
7. (Hold wire transfer) → Wire placed on 24-hour security hold
8. Route to analyst → Case escalated: "Possible elder scam - first wire, suspicious beneficiary"
9. (Analyst contacts customer) → Customer confirms scam, wire cancelled, funds saved

### 8. False Positive - Vacation Spending Pattern
**User Intent:** "Triage alert batch - 45 alerts from single customer"
**Steps:**
1. Retrieve transaction details → 45 transactions over 5 days, all in Hawaii
2. Get customer profile → Customer in New York, no recent travel history in system
3. Analyze transaction history → Spending pattern normal for vacation (restaurants, hotels, activities)
4. (Check travel indicators) → Found: Hawaii flight booking 1 week ago (same card)
5. Check device intelligence → Same device used, legitimate mobile app activity
6. Calculate fraud risk score → Score: 20/100 (low risk - travel)
7. (Batch approve) → Auto-approve all 45 transactions, add travel note to profile
8. (No customer contact) → Transactions approved silently, no disruption to vacation

## Key Decisions
- Auto-approve low-risk alerts (score <30) to reduce false positives
- Auto-decline obvious fraud (score >95) to prevent losses
- Escalate medium/high-risk cases (30-95) to analysts with context
- Request customer verification for uncertain cases (50-70)
- Block accounts immediately for account takeover signals
- Place security holds on large transfers with fraud indicators
- File SARs for patterns indicating money laundering or elder fraud

## Fraud Indicators
- **Location anomalies:** Foreign country, impossible travel, high-fraud regions
- **Velocity:** Multiple transactions in short time, exceeds daily limits
- **Device:** New device, VPN, TOR, device linked to fraud
- **Merchant:** High-risk MCC, merchant on fraud blacklist
- **Amount:** Significantly higher than typical spending
- **Customer:** New account, frequent disputes, synthetic identity signals
- **Behavioral:** First-time activity (wire, crypto, P2P), unusual hours

## Compliance Requirements
- Regulation E (electronic fund transfer error resolution, 60 days)
- Fair Credit Billing Act (credit card dispute rights)
- Gramm-Leach-Bliley Act (safeguard customer information)
- Red Flags Rule (identity theft prevention)
- FinCEN guidance (SAR filing for fraud patterns)
- Card network rules (Visa, Mastercard chargeback timelines)
- Customer notification requirements (state breach laws)
