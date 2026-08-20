# Evaluation Framework for Synthetic Agent Benchmark Datasets

**Company / Org:** Automation Anywhere  
**Challenge Advisor:** Sandra Wang  
**AI Studio Coach:** Ananya Devarakonda ([ananya.devarakonda@breakthroughtech.org](mailto:ananya.devarakonda@breakthroughtech.org))  
**Program:** Break Through Tech AI Studio - Fall 2026

---

## 🏢 About Automation Anywhere

Automation Anywhere is a leader in the Robotic Process Automation (RPA) industry, dedicated to empowering businesses with intelligent automation solutions. Our innovative software streamlines processes and enhances operational efficiency across various sectors.

---

## 🎯 The Challenge

### Project Summary
This project focuses on designing and building an evaluation framework to assess the quality, coverage, and usefulness of datasets intended for agent benchmarking. Students will apply their framework to two datasets — a high-quality real-world benchmark (tau-bench) and a provided synthetic dataset — and demonstrate that their metrics can meaningfully distinguish between them.

### Success Criteria

The evaluation framework is successful when it demonstrates:

1. **Discriminative Power** — Produces meaningfully different scores between τ-bench and the synthetic dataset on all chosen metrics.
2. **Score-to-Reality Alignment** — Scores correlate with actual quality differences; τ-bench consistently scores higher on dimensions where the synthetic dataset is weaker.
3. **Metric Validation** — Each chosen metric passes controlled validation tests and behaves correctly under known perturbations.
4. **Actionable Reporting** — Reports are clear enough that someone unfamiliar with either dataset can identify their relative strengths and weaknesses.
5. **Reproducibility** — Running the framework twice on the same dataset produces identical or near-identical results.

### Project Milestones

Use these milestones to guide your work. Your team will create a **GitHub Projects board** to track tasks within each milestone.

| Month | Milestone | Key Activities |
|-------|-----------|----------------|
| **September** | Understand & Define | Study τ-bench paper and dataset structure; review related work on dataset quality; formally define and operationalize 2 chosen metrics; document validation approach |
| **October** | Build & Apply | Implement evaluation suite with reproducible scripts; compute metrics for both datasets; run baseline agent on τ-bench; validate each metric |
| **November** | Compare, Score & Report | Design combined scoring system with justification; generate side-by-side comparison report; analyze intra-dataset variation; document weaknesses and concrete improvement recommendations |

> **Note for the team:** Please create a GitHub Projects board in this repository to break these milestones into weekly tasks. Go to the **Projects** tab → **New project** → Choose **Board** → Add columns for each month.

---

## 📊 Dataset

### Primary Dataset — τ-bench (tau-bench)

A realistic, high-quality benchmark for agent evaluation.

- **Format:** JSON (task records with multi-turn conversations, tool call traces, and expected outcomes)
- **Scale:** Medium-scale benchmark (~thousands of tasks; filterable by domain for quick iteration)
- **Domains:** Customer service interactions across **retail, telecom, and airline**
- **Source:** https://github.com/sierra-research/tau2-bench

### Comparison Dataset — Provided Synthetic Dataset

A lower-quality synthetic benchmark provided for comparison and validation.

- **Format:** Python scripts (.py) and JSON
- **Location:** `/data` folder in this repository
- **Purpose:** Serves as a comparison baseline to demonstrate the framework's ability to identify and quantify quality gaps
- **Domains and Coverage:**
  - **Banking:** customer onboarding (6 cases), fraud monitoring (13 cases), account_deposit (8 cases)
  - **Healthcare:** Patient onboarding (9 cases), prior authorization (9 cases)
  - **Insurance:** claims intake (10 cases)
  - **Manufacturing:** purchase to pay (9 cases),
  - **Total:** 64 test cases across 7 task categories

### Dataset Strategy

- **Practical Workflow:** Design your evaluation scripts to support filtering and sampling by domain and scenario. This enables fast iteration and domain-specific analysis.
- **Quality Contrast:** The synthetic dataset intentionally exhibits quality issues (gaps in coverage, inconsistent annotations, limited diversity) that your metrics should detect and quantify.
- **Documentation:** Consult the τ-bench GitHub repository for detailed schema documentation and task structure.

---

## 🛠️ Suggested Approach

**ML Problem Type:** Dataset Quality Evaluation & Benchmarking Framework (Agent-based)

**Recommended Libraries:**
- Python
- Data visualization (distributions, radar charts, per-metric breakdowns)
- LLM baseline agents (e.g., ReAct-prompted models for difficulty validation)
- GitHub Projects for task tracking

**Evaluation Metrics (Choose 2)**

Each metric must include a validation strategy to confirm correct behavior under controlled conditions:

**Coverage**  
Measures the variety and breadth of task types, tool calls, and scenario categories.  
*Potantial validation approach:* Subsample a single domain or a few scenarios from τ-bench; the coverage score should decrease proportionally.

**Difficulty**  
Measures the complexity distribution of tasks.  
*Potantial validation approach:* Correlate difficulty scores with a baseline agent's success rates; tasks scored as harder should show lower success rates.

**Correctness**  
Measures the internal consistency and reliability of expected outputs.  
*Potantial validation approach:* Inject a known percentage of corrupted labels into τ-bench; the correctness score should degrade proportionally.

**Tool Usage Diversity**  
Measures the variety and distribution of tool interactions across tasks.  
*Potantial validation approach:* Create a subset using only single-tool tasks; the diversity score should drop measurably.

**For each chosen metric, you must:**
1. **Define** what it measures and why it matters for dataset quality.
2. **Operationalize** the metric: specify the computation approach and any parameters.
3. **Validate** by passing the test above, demonstrating correct behavior under known perturbations.

---

## 🔍 Methodology

### Phase 1 — Understand & Define (September)

**Goal:** Build a solid conceptual foundation before implementation.

**Activities:**
- Study the τ-bench paper and dataset structure (task types, tool schemas, conversation formats, ground truth).
- Review related work on dataset quality metrics and agent benchmarking frameworks.
- Select 2 metrics from the candidate list and formally define each: what it measures, why it matters, and what constitutes a good score.
- Design the operationalization and validation approach for each metric.

**Milestone deliverable:**  
Metric specification document: definitions, operationalization approach, and validation plan for each of your 2 chosen metrics.

### Phase 2 — Build & Apply (October)

**Goal:** Implement and validate the framework on both datasets.

**Activities:**
- Develop reproducible scripts to compute each metric on any dataset.
- Generate summaries and visualizations: metric distributions, radar charts, per-domain breakdowns.
- Run each metric's validation test on τ-bench; confirm expected behavior under controlled conditions.
- Execute the full framework on both datasets; capture scores and diagnostic outputs.
- Run a baseline agent (e.g., ReAct-prompted LLM) on τ-bench tasks; collect per-task success rates for difficulty metric correlation analysis.

**Milestone deliverable:**  
Working evaluation suite: reproducible scripts, validation test results, and metric outputs for both τ-bench and synthetic datasets.

### Phase 3 — Compare, Score & Report (November)

**Goal:** Synthesize results and demonstrate framework value.

**Activities:**
- Design a combined scoring system that merges your two metrics into an overall dataset quality score. Justify weighting choices and reasoning.
- Create a side-by-side comparison report: τ-bench vs. synthetic dataset. Highlight where each dataset excels and falls short.
- Conduct an intra-dataset analysis (e.g., retail vs. airline within τ-bench) to demonstrate that your metrics detect meaningful variation.
- Write a **weaknesses and improvement recommendations** section for the synthetic dataset. For each weakness identified by your metrics, provide concrete, actionable suggestions for dataset refinement.

**Milestone deliverable:**  
Final report with: (1) scoring system and rationale, (2) side-by-side comparison, (3) intra-dataset analysis, and (4) prioritized improvement recommendations.

### Stretch Goal — Iterative Improvement Pipeline *(Optional)*

If core work is completed early, close the feedback loop by improving the synthetic dataset.

**Activities:**
- Use your improvement recommendations to propose heuristics or automated fixes for dataset generation.
- Generate or simulate an improved synthetic dataset version.
- Re-run the evaluation framework on the revised dataset; document score improvements.
- Reflect on the iteration process: what worked, what didn't, and lessons learned.

**Stretch deliverable:**  
Documented iteration cycle with before/after metric comparisons and lessons on dataset refinement.

---

## 📝 Deliverables Summary

| Deliverable | Due | Contents |
|---|---|---|
| **Metric Specification Document** | End of September | Formal definitions of 2 chosen metrics; operationalization approach; validation strategy and expected outcomes |
| **Evaluation Suite** | End of October | Reproducible Python scripts for metric computation; validation test code; outputs and diagnostics for both datasets |
| **Dataset Comparison Report** | End of November | Side-by-side metric scores; analysis of gaps and strengths; within-τ-bench variation; weaknesses and improvement roadmap |
| **Scoring System** | End of November | Combined quality score design; weighting rationale; justification for choices |
| ***(Stretch)* Iterative Improvement Cycle** | End of November | Before/after metric comparison; improved dataset generation; iteration lessons learned |

---

## 📚 Resources to Get Started

The following resources will help your team understand the problem space and potential technical approaches for this project:

**Background Reading:**
- τ-bench paper and τ-bench GitHub repository: https://github.com/sierra-research/tau2-bench
- Related work on dataset quality evaluation and agent benchmarking
    - [Dataset Cartography: Mapping and Diagnosing Datasets with Training Dynamics](https://arxiv.org/abs/2009.10795)
    - [SynAE: A Framework for Measuring the Quality of Synthetic Data for Tool-Calling Agent Evaluations](https://arxiv.org/abs/2605.22564)
    - [DataPerf: Benchmark Suite for ML Datasets and Data-Centric Algorithms](https://www.dataperf.org/about)


*Feel free to explore beyond these, and share anything interesting you find with me!*

---

## 🔗 LLM and Baseline Agent Expectations

The project includes a baseline agent run to validate the **Difficulty** metric.

- **Baseline setup:** Use a simple, well-documented prompting strategy (e.g., ReAct) and keep it fixed across datasets.
- **Reproducibility:** Log model name/version, prompt template, decoding parameters, and run seed where available.
- **Cost and runtime awareness:** Start with sampled subsets for quick iteration before full runs.
- **Fair comparison:** Use the same agent configuration for both datasets to ensure valid difficulty correlation analysis.

This context will be covered in preliminary sessions so the team can execute LLM-based validation without tooling gaps.

---

## 🎯 Expected Outcomes

**By the end of this project, you will have:**

1. **A reusable evaluation framework** for assessing dataset quality on two well-defined metrics, with clear validation.
2. **Quantified evidence** that the framework reliably distinguishes high-quality benchmarks from lower-quality synthetic datasets.
3. **Actionable insights** into τ-bench's strengths as a production benchmark and concrete gaps in the synthetic dataset.
4. **Technical confidence** in designing and validating custom metrics for domain-specific evaluation.
5. *(Stretch)* **An improvement pipeline template** showing how metrics can guide iterative dataset refinement.

---

## 🤝 How We'll Work Together

**Check-ins:** Biweekly 45-minute AI Studio Lab Section meetings (2nd and 4th week of every month)  
**Communication:** Break Through Tech Discord and email
- Email: sandra.wang@automationanywhere.com

**Response time:** Within 48 hours on weekdays  

**Recommended Tools:**
- **Coding:** VS Code, Jupyter notebooks
- **Collaboration:** GitHub (this repository), GitHub Projects board
- **Version Control:** Git/GitHub for all code and documentation

---

## 🚀 Getting Started

1. **Read this overview document** carefully; note questions for our first meeting.
2. **Clone this repository** and explore the folder structure, especially the `/data` directory.
3. **Study the τ-bench paper and dataset** to understand task structure, domains, and expected format.
4. **Explore the comparison dataset** in the `/data` folder; understand its scope and structure.
5. **Read the background papers** (Dataset Cartography, SynAE, DataPerf) to ground yourself in dataset quality evaluation.
6. **Consider metric candidates** — which 2 resonate most with you? Why?
7. **Create a GitHub Projects board** to organize work by month (September, October, November). Go to **Projects** tab → **New project** → **Board**.

---

## ❓ Questions?

Please bring any questions to our first meeting during the week of August 24th (Break Through Tech's Bridge to Studio - Session C).

---
