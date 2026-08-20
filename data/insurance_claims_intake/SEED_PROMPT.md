# Insurance Claims Intake and Triage Agent - Seed Prompt

## Agent Overview
This agent automates First Notice of Loss (FNOL) processing by reading claims from emails, web forms, or phone transcripts, classifying claim types, extracting key data (date of loss, location, description), creating claims in the core system, and routing to appropriate adjusters or specialized teams.

## Business Context
Traditional claims intake requires manual data entry, classification, and routing—taking 30-60 minutes per claim and delaying customer service. This agent processes FNOL in under 5 minutes, ensures accurate data capture, applies proper routing rules, and initiates workflows (emergency services, vendor dispatch) based on claim characteristics.

## Real-World Scenario
**Trigger:** Customer emails: "Tree fell on my roof during last night's storm. Water leaking into bedroom. Need help ASAP."

**Stakes:** Fast response reduces claim severity (water damage spreads). Incorrect routing delays service. Missing data causes adjuster rework. Regulatory requirements mandate timely acknowledgment (24-48 hours).

**Process Chain:**
- Parse email/form to extract loss details
- Classify claim type (property damage, liability, auto, etc.)
- Extract structured data (date, location, cause, injuries, damages)
- Validate policy is active and covers loss type
- Assess urgency (emergency services needed)
- Create claim in system with all available information
- Route to appropriate team (CAT team, property adjuster, liability specialist)
- Trigger immediate actions (emergency repairs, rental car, medical provider)
- Send acknowledgment to customer

**Resolution:** Claim created and emergency vendor dispatched in 8 minutes vs. 45-minute manual intake, preventing further water damage.

## Agent Capabilities

### Core Tools (6-7 recommended)
1. **extract_loss_details** - Parse FNOL email/form using NLP (date, location, description, injuries)
2. **classify_claim_type** - Categorize as property, auto, liability, workers comp, etc.
3. **validate_policy_coverage** - Check policy is active, loss date within coverage, peril covered
4. **assess_claim_severity** - Determine if emergency response, total loss, catastrophe-related
5. **create_claim_record** - Generate claim number, populate claim system with extracted data
6. **route_to_adjuster** - Assign to appropriate team based on type, location, complexity, workload
7. **trigger_emergency_services** - Dispatch vendors (water mitigation, towing, temporary housing)
8. **send_claim_acknowledgment** - Email/SMS customer with claim number and next steps

### Integration Points
- **Claims Systems:** Guidewire ClaimCenter, Duck Creek Claims, Snapsheet
- **Email/Forms:** Outlook, Gmail, web forms, chatbots
- **Policy Admin:** Guidewire PolicyCenter, Duck Creek Policy
- **Vendor Networks:** ServiceMaster, Paul Davis, Enterprise Rent-A-Car
- **Catastrophe Management:** Verisk Xactanalysis, CoreLogic
- **Communication:** Twilio, SendGrid, customer portals

## Sample Workflows to Generate

### 1. Storm Damage - Emergency Water Mitigation (Happy Path)
**User Intent:** "Process FNOL email from john.smith@email.com"
**Steps:**
1. Extract loss details → Date: Feb 2, 2026, Location: 123 Oak St Dallas TX, Cause: tree fell on roof, water leaking
2. Classify claim type → Property damage (homeowners), storm/wind damage
3. Validate policy coverage → Policy #HO-887766 active, storm coverage confirmed
4. Assess claim severity → Emergency: active water intrusion (immediate mitigation needed)
5. Create claim record → Claim #2026-445521 created, "Emergency" flag set
6. Trigger emergency services → Water mitigation vendor (ServiceMaster) dispatched within 2 hours
7. Route to adjuster → Assigned to CAT team (catastrophe event - recent storm)
8. Send claim acknowledgment → Email sent: "Claim #2026-445521 created, vendor arriving 2-4 PM today"

### 2. Auto Accident - Liability Claim with Injuries
**User Intent:** "Process web form submission - auto accident"
**Steps:**
1. Extract loss details → Date: Feb 3, 2026, Location: I-95 Miami FL, rear-end collision, 2 vehicles
2. Classify claim type → Auto liability (claimant injured in other vehicle)
3. Extract loss details → Injury reported: neck pain, transported to hospital
4. Validate policy coverage → Policy active, liability coverage $250K/$500K
5. Assess claim severity → Bodily injury (BI) flag, requires liability investigation
6. Create claim record → Claim #2026-445534 created with injury flag
7. Route to adjuster → Assigned to BI adjuster (specialization in injury claims)
8. (Set reserves) → Initial reserve $25K for medical, $10K for liability exposure
9. Send claim acknowledgment → Letter to claimant with claim number, adjuster contact info

### 3. Catastrophe Event - Hurricane Claims Surge
**User Intent:** "Process batch of 250 FNOL emails from Hurricane Milton"
**Steps:**
1. (Identify catastrophe) → Hurricane Milton landfall Feb 1, declared CAT event #2026-003
2. Extract loss details → Parse 250 emails, extract dates (all Feb 1-2), locations (FL panhandle)
3. Classify claim type → Mix: 180 property damage, 50 auto, 20 business interruption
4. Validate policy coverage → Batch validate policies, 5 lapsed policies flagged
5. Assess claim severity → 40 marked emergency (roof damage, flooding), 210 standard
6. Create claim record → Bulk create 250 claims, all tagged with CAT #2026-003
7. Route to adjuster → All routed to CAT team, emergency claims prioritized
8. Trigger emergency services → 40 emergency vendor dispatches (tarping, water mitigation)
9. Send claim acknowledgment → Batch emails sent with CAT hotline number

### 4. Workers Compensation - Injured Employee
**User Intent:** "Process WC claim from employer portal"
**Steps:**
1. Extract loss details → Employee: Maria Garcia, Date: Feb 3, 2026, Injury: fell from ladder, broken wrist
2. Classify claim type → Workers compensation (occupational injury)
3. Extract loss details → Medical treatment: ER visit, orthopedic referral needed
4. Validate policy coverage → WC policy active, construction class code matches
5. Assess claim severity → Lost time injury (employee out 6-8 weeks)
6. Create claim record → WC claim #2026-WC-1123 created
7. (Initiate medical management) → Nurse case manager assigned, orthopedic provider network accessed
8. Route to adjuster → WC adjuster assigned, indemnity specialist looped in
9. Send claim acknowledgment → Letter to employee with medical provider list, adjuster contact

### 5. Liability Claim - Slip and Fall at Business
**User Intent:** "Process claimant attorney letter"
**Steps:**
1. Extract loss details → Date: Jan 15, 2026, Location: ABC Grocery Store, claimant slipped on wet floor
2. Classify claim type → General liability (premises liability)
3. Extract loss details → Injury: fractured hip, surgery required, represented by attorney
4. Validate policy coverage → Commercial GL policy active, premises coverage confirmed
5. Assess claim severity → High severity: attorney-represented, significant injury, potential litigation
6. Create claim record → GL claim #2026-445556 created, "Litigation" flag
7. Route to adjuster → Assigned to senior liability adjuster, legal team notified
8. (Document preservation) → Letter to insured requesting incident reports, video footage
9. Send claim acknowledgment → Letter to attorney (not claimant directly due to representation)

### 6. Denied Claim - Policy Lapsed
**User Intent:** "Process FNOL for policy #HO-998877"
**Steps:**
1. Extract loss details → Date: Feb 3, 2026, house fire
2. Classify claim type → Property damage (fire)
3. Validate policy coverage → Policy #HO-998877 cancelled for non-payment on Jan 15, 2026
4. (Coverage denial) → Loss occurred after policy cancellation (no coverage)
5. Create claim record → Claim created as "Denied - No Coverage"
6. (Generate denial letter) → Letter explaining policy lapsed, loss not covered
7. Send claim acknowledgment → Denial letter sent to customer (required by state law)

### 7. Duplicate Claim - Already Reported
**User Intent:** "Process FNOL email from customer"
**Steps:**
1. Extract loss details → Date: Feb 1, 2026, auto accident on I-10
2. (Check existing claims) → Search finds claim #2026-445501 for same date, customer, description
3. (Identify duplicate) → Customer already reported via phone, duplicate FNOL via email
4. (Link communications) → Attach email to existing claim #2026-445501
5. Send claim acknowledgment → Reply: "Your claim was already reported as #2026-445501, adjuster will contact you"

### 8. Complex Commercial Claim - Business Interruption
**User Intent:** "Process commercial property FNOL"
**Steps:**
1. Extract loss details → Date: Feb 2, 2026, warehouse fire, building 50% damaged
2. Classify claim type → Commercial property + business interruption
3. Extract loss details → Manufacturing operations halted, 50 employees idle
4. Validate policy coverage → Property $5M, BI coverage $2M with 72-hour waiting period
5. Assess claim severity → Large loss, likely exceeds $1M, BI claim expected
6. Create claim record → Two linked claims: property damage + business interruption
7. Route to adjuster → Large loss unit assigned, BI specialist added
8. (Engage specialists) → Forensic accountant assigned for BI, engineer for cause/origin
9. Trigger emergency services → Board-up service, security, salvage coordinator
10. Send claim acknowledgment → Letter to insured with adjuster, accountant, engineer contacts

## Key Decisions
- Route to standard adjusters vs. specialized teams (CAT, large loss, BI, fraud)
- Trigger immediate emergency services for active perils (fire, water, injury)
- Set initial claim reserves based on severity and exposure
- Identify potential fraud indicators (delayed reporting, exaggerated damages)
- Determine if legal counsel needed (attorney-represented claimants, litigation risk)
- Escalate high-severity or high-complexity claims to supervisors

## Compliance Requirements
- Timely acknowledgment (state laws vary: 10-30 days)
- Proper documentation of loss details and coverage determination
- Privacy protection (HIPAA for medical data, state insurance privacy laws)
- Fair claims practices (prompt investigation, good faith settlement)
- Catastrophe response protocols (expedited handling)
- Attorney representation protocols (all communication through counsel)
