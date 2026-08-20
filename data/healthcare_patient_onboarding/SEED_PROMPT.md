# Healthcare Patient Onboarding Agent - Seed Prompt

## Agent Overview
This agent automates new patient onboarding by extracting data from intake forms, verifying insurance eligibility and benefits, creating or updating patient records in the EHR (Electronic Health Record), and scheduling initial appointments based on availability and patient preferences.

## Business Context
Traditional patient registration requires staff to manually enter data from paper forms, call insurers to verify coverage, create EHR records, and coordinate scheduling—taking 15-30 minutes per patient. This agent reduces onboarding to under 5 minutes, eliminates data entry errors, ensures insurance verification before appointments, and improves patient experience.

## Real-World Scenario
**Trigger:** New patient Maria Gonzalez completes online intake form for primary care appointment.

**Stakes:** Manual entry errors cause claim denials. Insurance not verified leads to billing issues. Scheduling delays frustrate patients. HIPAA compliance requires accurate data handling.

**Process Chain:**
- Extract patient demographics from intake form (name, DOB, address, contact)
- Parse insurance information (carrier, policy number, group number)
- Verify insurance eligibility via payer API (active coverage, copay, deductible)
- Extract medical history (allergies, medications, conditions)
- Create patient record in EHR with demographics and insurance
- Check provider availability and schedule appointment
- Send confirmation with appointment details and preparation instructions

**Resolution:** Patient onboarded and scheduled in 6 minutes vs. 25-minute manual process, with insurance verified before visit.

## Agent Capabilities

### Core Tools (6-7 recommended)
1. **extract_patient_demographics** - Parse intake forms for name, DOB, SSN, address, contact info
2. **extract_insurance_info** - Pull insurance carrier, policy number, group number, subscriber details
3. **verify_insurance_eligibility** - Query payer eligibility API (270/271 transaction)
4. **extract_medical_history** - Parse allergies, medications, conditions, surgical history
5. **create_ehr_patient_record** - Create patient in EHR with demographics, insurance, history
6. **check_provider_availability** - Query scheduling system for open appointment slots
7. **schedule_appointment** - Book appointment, send confirmation, add to provider calendar
8. **send_patient_communication** - Email/SMS confirmation with instructions and forms

### Integration Points
- **EHR Systems:** Epic, Cerner, Allscripts, athenahealth, NextGen
- **Payer APIs:** Availity, Change Healthcare, Waystar (270/271 eligibility)
- **Scheduling:** Acuity, Zocdoc, SimplePractice, EHR-integrated schedulers
- **Forms:** JotForm, Typeform, Google Forms, patient portals
- **Communication:** Twilio, SendGrid, patient engagement platforms
- **OCR:** Google Document AI, AWS Textract (for paper forms)

## Sample Workflows to Generate

### 1. New Primary Care Patient - Full Onboarding (Happy Path)
**User Intent:** "Onboard new patient from intake form #PAT-98765"
**Steps:**
1. Extract patient demographics → Name: Maria Gonzalez, DOB: 05/12/1985, Phone: 555-0123, Email: maria.g@email.com
2. Extract insurance info → Aetna PPO, Policy #W1234567, Group #GRP-8899, Subscriber: Self
3. Verify insurance eligibility → Active coverage, $30 copay, $500 deductible ($200 met)
4. Extract medical history → Allergies: penicillin, Medications: lisinopril 10mg, Conditions: hypertension
5. Create EHR patient record → Patient ID #876543 created in Epic with all data
6. Check provider availability → Dr. Smith has openings Feb 10, 12, 15
7. Schedule appointment → Booked Feb 12, 2:00 PM for annual physical
8. Send patient communication → Confirmation email with prep instructions (fasting blood work)

### 2. Pediatric Patient - Parent as Subscriber
**User Intent:** "Register new pediatric patient form #PAT-98778"
**Steps:**
1. Extract patient demographics → Patient: Emma Johnson, DOB: 03/15/2018 (age 7), Parent: Sarah Johnson
2. Extract insurance info → Blue Cross Blue Shield, Policy #BC445566, Subscriber: Sarah Johnson (parent)
3. Verify insurance eligibility → Dependent active, $20 pediatric copay, family deductible $1,000 (met)
4. Extract medical history → Allergies: none, Immunizations: up to date, Conditions: asthma (mild)
5. Create EHR patient record → Pediatric patient record created, linked to parent guarantor
6. Schedule appointment → Well-child visit scheduled with Dr. Martinez (pediatrician)
7. Send patient communication → Confirmation to parent email with vaccine requirements

### 3. Insurance Eligibility Failed - Inactive Coverage
**User Intent:** "Onboard patient from form #PAT-98789"
**Steps:**
1. Extract patient demographics → Name: John Davis, DOB: 07/22/1978
2. Extract insurance info → UnitedHealthcare, Policy #UHC778899
3. Verify insurance eligibility → Eligibility check returned: "Coverage terminated 01/15/2026"
4. (Hold onboarding) → Cannot proceed without active insurance
5. (Contact patient) → Call/email patient to update insurance or arrange self-pay
6. (Patient provides new insurance) → Updated to Cigna, verification successful
7. Create EHR patient record → Record created with correct active insurance
8. Schedule appointment → Appointment scheduled after insurance resolved

### 4. Specialty Referral - Prior Authorization Required
**User Intent:** "Schedule specialist appointment from referral #PAT-98801"
**Steps:**
1. Extract patient demographics → Existing patient ID #765432 (from PCP records)
2. (Check referral) → Referral from Dr. Thompson (PCP) for orthopedic consult
3. Verify insurance eligibility → Active, but specialist requires prior auth
4. (Initiate prior auth) → Prior authorization request submitted for orthopedic visit
5. (Hold scheduling) → Cannot schedule until auth approved (typically 2-5 days)
6. (Auth approved) → Payer approves auth #AUTH-556677
7. Schedule appointment → Orthopedic appointment booked with Dr. Lee
8. Send patient communication → Confirmation with auth number and appointment details

### 5. Self-Pay Patient - No Insurance
**User Intent:** "Register self-pay patient #PAT-98815"
**Steps:**
1. Extract patient demographics → Name: Robert Chen, uninsured (self-pay selected)
2. (Skip insurance verification) → No insurance to verify
3. Extract medical history → Allergies: sulfa drugs, Conditions: diabetes type 2
4. Create EHR patient record → Self-pay patient record created
5. (Provide pricing estimate) → Annual physical self-pay rate: $250
6. Schedule appointment → Appointment scheduled, payment required at visit
7. Send patient communication → Confirmation with self-pay pricing and payment options

### 6. Duplicate Patient Detection - Merge Required
**User Intent:** "Onboard patient form #PAT-98828"
**Steps:**
1. Extract patient demographics → Name: Sarah Martinez, DOB: 11/08/1990, SSN: XXX-XX-5678
2. (Search existing records) → Found existing patient: Sarah Martinez, DOB: 11/08/1990, ID #887766
3. (Detect duplicate) → Same name, DOB, similar address (likely same person)
4. (Update existing record) → Update record #887766 with new phone/email from form
5. (Merge insurance) → Add new insurance info to existing patient
6. Schedule appointment → Schedule under existing patient ID
7. (Notify staff) → Alert: potential duplicate merged, review recommended

### 7. Complex Medical History - Multiple Conditions
**User Intent:** "Register high-risk patient #PAT-98841"
**Steps:**
1. Extract patient demographics → Name: William Thompson, age 68
2. Extract medical history → Conditions: CHF, diabetes, COPD, CKD stage 3, prior MI
3. Extract medical history → Medications: 12 active prescriptions listed
4. Verify insurance eligibility → Medicare + secondary (Medigap), active coverage
5. Create EHR patient record → High-risk patient flag, care coordination needed
6. (Assign care coordinator) → Patient assigned to chronic disease management program
7. Schedule appointment → Extended visit (60 min) scheduled for comprehensive assessment
8. Send patient communication → Welcome packet with disease management resources

### 8. Incomplete Form - Request Additional Information
**User Intent:** "Process incomplete intake form #PAT-98854"
**Steps:**
1. Extract patient demographics → Name, phone provided, but missing DOB and address
2. Extract insurance info → Insurance card photo illegible (blur)
3. (Identify missing data) → Required fields incomplete: DOB, address, insurance details
4. (Request completion) → Email sent with link to complete missing fields
5. (Patient completes form) → Updated form received with all required data
6. Verify insurance eligibility → Verification successful
7. Create EHR patient record → Patient record created after completion
8. Schedule appointment → Appointment scheduled

## Key Decisions
- Auto-create EHR records for complete, valid submissions
- Hold onboarding for inactive insurance or missing required data
- Flag duplicate patients for manual review and merge
- Initiate prior authorization requests when required
- Assign care coordinators for high-risk/complex patients
- Provide self-pay pricing estimates for uninsured patients

## Data Validation Rules
- Required demographics: Full name, DOB, contact info (phone or email)
- Insurance: Policy number, group number (if applicable), subscriber info
- Medical history: Allergies (even if "none"), current medications
- HIPAA compliance: Secure storage, access logging, encryption
- Duplicate detection: Match on name + DOB, or SSN if provided
