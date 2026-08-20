# Healthcare Prior Authorization Agent - Seed Prompt

## Agent Overview
This agent automates prior authorization (PA) requests by reading provider authorization requests, checking payer medical necessity criteria, gathering required clinical documentation, preparing and submitting PA submissions through payer portals or APIs, and tracking approval/denial decisions.

## Business Context
Prior authorization is one of the most time-consuming administrative burdens in healthcare, requiring staff to review payer criteria, gather clinical notes, submit forms, and follow up—taking 15-45 minutes per request. Delays in PA approval postpone patient care. This agent reduces PA processing time to 5-10 minutes and improves approval rates through complete documentation.

## Real-World Scenario
**Trigger:** Orthopedic surgeon orders MRI for patient with chronic back pain.

**Stakes:** PA denial delays diagnosis and treatment. Incomplete submissions cause denials requiring resubmission. Manual processing delays patient care by days or weeks. Patient satisfaction suffers.

**Process Chain:**
- Receive PA request from provider (CPT code, diagnosis, clinical indication)
- Identify payer and check if PA required for procedure
- Retrieve payer's medical necessity criteria
- Gather supporting clinical data from EHR (notes, prior treatments, imaging)
- Complete PA request form with clinical justification
- Submit through payer portal or API (278 transaction)
- Track decision (auto-approved, pended for review, denied)
- Notify provider and patient of decision

**Resolution:** PA submitted in 8 minutes vs. 35-minute manual process, with complete documentation improving approval odds.

## Agent Capabilities

### Core Tools (6-7 recommended)
1. **check_pa_requirements** - Query if procedure requires PA for specific payer/plan
2. **retrieve_medical_necessity_criteria** - Get payer's criteria for specific CPT code/diagnosis
3. **gather_clinical_documentation** - Pull relevant EHR notes, labs, imaging, treatment history
4. **validate_clinical_criteria** - Check if patient meets payer's medical necessity requirements
5. **prepare_pa_submission** - Complete PA request form with clinical justification
6. **submit_pa_request** - Submit via payer portal or 278 EDI transaction
7. **track_pa_status** - Monitor decision status (approved, pended, denied, expired)
8. **appeal_pa_denial** - Prepare appeal with additional documentation if denied

### Integration Points
- **Payer Portals:** Availity, Change Healthcare, Waystar, Surescripts
- **EHR:** Epic, Cerner, athenahealth (clinical data extraction)
- **EDI:** 278 (prior authorization), 275 (attachments)
- **Criteria Databases:** MCG, InterQual, eviCore guidelines
- **Workflow:** Case management systems, worklists

## Sample Workflows to Generate

### 1. MRI Prior Authorization - Approved (Happy Path)
**User Intent:** "Process PA request for lumbar MRI - Patient #445566"
**Steps:**
1. Check PA requirements → Anthem BCBS requires PA for CPT 72148 (lumbar MRI without contrast)
2. Retrieve medical necessity criteria → Criteria: 6+ weeks conservative treatment, red flags ruled out
3. Gather clinical documentation → EHR notes: 8 weeks back pain, failed PT (12 sessions), NSAIDs tried
4. Validate clinical criteria → Criteria met: >6 weeks symptoms, conservative treatment documented
5. Prepare PA submission → Form completed with diagnosis M54.5, clinical summary, treatment timeline
6. Submit PA request → Submitted via Availity portal, reference #PA-778899
7. Track PA status → Auto-approved (criteria clearly met), auth #AUTH-556677 valid 90 days
8. (Notify provider) → EHR notification: "MRI approved, schedule patient"

### 2. Sleep Study PA - Additional Documentation Requested
**User Intent:** "Submit PA for home sleep study - Patient #445578"
**Steps:**
1. Check PA requirements → UnitedHealthcare requires PA for CPT 95800 (sleep study)
2. Retrieve medical necessity criteria → Criteria: OSA symptoms, BMI, Epworth Sleepiness Scale score
3. Gather clinical documentation → Found: snoring, daytime fatigue documented, BMI 34
4. (Missing data) → Epworth score not documented in EHR
5. (Request from provider) → Message provider to complete Epworth assessment
6. (Provider completes) → Epworth score 14 (moderate sleepiness) documented
7. Prepare PA submission → Complete form with all criteria including Epworth score
8. Submit PA request → Submitted, approved with complete documentation

### 3. Specialty Drug PA - Complex Clinical Review
**User Intent:** "Request PA for Humira (adalimumab) - Patient #445589"
**Steps:**
1. Check PA requirements → Cigna requires PA for specialty biologics (high cost)
2. Retrieve medical necessity criteria → Criteria: moderate-severe rheumatoid arthritis, failed DMARD
3. Gather clinical documentation → Diagnosis RA (M06.9), failed methotrexate 6 months, high CRP/ESR
4. Validate clinical criteria → Criteria met: disease severity documented, first-line therapy failed
5. Prepare PA submission → Submit with rheumatologist notes, lab results, DMARD trial timeline
6. Submit PA request → Submitted via payer portal
7. Track PA status → Pended for clinical review (typical for specialty drugs)
8. (Review completed) → Approved after 48 hours, auth valid 12 months with renewal option

### 4. PA Denied - Criteria Not Met
**User Intent:** "Process PA for CT scan - Patient #445601"
**Steps:**
1. Check PA requirements → Aetna requires PA for CT abdomen/pelvis (CPT 74177)
2. Retrieve medical necessity criteria → Criteria: specific clinical indications (trauma, acute abdomen, etc.)
3. Gather clinical documentation → Indication: chronic abdominal pain, no acute symptoms
4. Validate clinical criteria → Criteria NOT met: chronic pain doesn't meet acute indication threshold
5. Prepare PA submission → Submit with available documentation
6. Submit PA request → Submitted
7. Track PA status → Denied: "Does not meet medical necessity criteria for imaging"
8. (Notify provider) → Provider can: accept denial, order different test, or appeal with more evidence

### 5. Durable Medical Equipment (DME) PA - Home Oxygen
**User Intent:** "Request PA for home oxygen concentrator - Patient #445615"
**Steps:**
1. Check PA requirements → Medicare requires PA for oxygen equipment (E1390)
2. Retrieve medical necessity criteria → Criteria: O2 saturation ≤88% at rest, COPD/lung disease
3. Gather clinical documentation → Diagnosis: severe COPD, pulse ox 85% on room air, ABG results
4. Validate clinical criteria → Criteria met: documented hypoxemia, qualifying diagnosis
5. Prepare PA submission → Submit with pulmonary function tests, ABG, sleep study if applicable
6. Submit PA request → Submitted to Medicare via DME supplier
7. Track PA status → Approved for 12 months, re-eval required for renewal
8. (Notify DME supplier) → Auth approved, can deliver equipment

### 6. Urgent PA - Expedited Review Requested
**User Intent:** "URGENT: PA for cardiac cath - Patient #445628"
**Steps:**
1. Check PA requirements → PA required for cardiac catheterization (CPT 93458)
2. (Assess urgency) → Patient in ER with NSTEMI (non-ST elevation MI), urgent procedure
3. Gather clinical documentation → ER notes, EKG showing ischemia, troponin elevated
4. Prepare PA submission → Complete urgent PA request, mark "Expedited - Emergency"
5. Submit PA request → Submit via phone/fax for immediate review (not standard portal)
6. Track PA status → Expedited review completed in 30 minutes, approved
7. (Notify cath lab) → Authorization obtained, proceed with urgent cath

### 7. PA for Bariatric Surgery - Multi-Step Approval
**User Intent:** "Submit PA for gastric bypass surgery - Patient #445641"
**Steps:**
1. Check PA requirements → Anthem requires extensive PA for bariatric surgery (CPT 43644)
2. Retrieve medical necessity criteria → Criteria: BMI ≥40 or ≥35 with comorbidities, 6-month medically supervised weight loss
3. Gather clinical documentation → BMI 42, diabetes, hypertension, 6-month diet program completed
4. (Check program completion) → Nutrition counseling, psych eval, cardiac clearance all documented
5. Validate clinical criteria → All criteria met, complete documentation package
6. Prepare PA submission → Submit comprehensive packet (may be 20+ pages)
7. Submit PA request → Submitted for clinical committee review
8. Track PA status → Approved after 2-week review, auth valid 6 months (allows scheduling)

### 8. PA Tracking - Status Follow-Up
**User Intent:** "Check status of pending PA requests"
**Steps:**
1. Track PA status → Query payer portals for 15 pending PAs
2. (Categorize results) → 8 approved, 3 denied, 2 pended awaiting info, 2 no response >5 days
3. (Process approved) → Update EHR, notify providers, schedule procedures
4. (Address denied) → Notify providers, offer appeal option
5. (Follow up pended) → Contact payers for missing info requirements
6. (Escalate delayed) → Call payer for 2 requests >5 days old (SLA breach)

## Key Decisions
- Auto-submit PAs when criteria clearly met (high approval probability)
- Request additional documentation from providers when criteria borderline
- Recommend alternative procedures when PA likely to be denied
- Expedite urgent/emergency requests via phone vs. standard portal
- Initiate appeals when denial appears incorrect or additional evidence available
- Track and escalate overdue PA responses

## Common PA Denials and Solutions
- **Incomplete documentation:** Request missing clinical notes before submission
- **Criteria not met:** Recommend additional conservative treatment or alternative procedure
- **Experimental/investigational:** Check for peer-reviewed evidence to support
- **Not medically necessary:** Provide stronger clinical justification or appeal
- **Duplicate service:** Check if recent similar service already performed
