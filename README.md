---

# Bank Loan Credit Risk Analysis

---

## 1. Project Overview

This project analyzes the credit risk of a bank loan portfolio by combining SQL reporting, Python modeling, and a Power BI dashboard to answer a central question: **is the current approval policy accepting too much risk, and if replaced by a predictive model, how would the outcomes change?**

The dataset contains **38,576 loans originated in 2021**. The analysis found an overall default rate of **13.82%**, with the High Risk tier reaching **21.14%**. A Logistic Regression model (Challenger policy) showed that if an approval threshold based on predicted default probability were applied, the default rate could drop to **9.11%**, and the difference is statistically significant (**p < 0.05**).

---

## 2. Objectives

- Build monthly KPI reports and track portfolio trends over time
- Segment the portfolio into risk tiers (Low / Medium / High) based on grade, DTI, and loan term
- Perform Vintage Analysis to monitor loan quality by origination cohort
- Measure portfolio distribution stability (PSI) between the two halves of the year
- Simulate a Champion vs. Challenger A/B Test to evaluate the effectiveness of a new approval policy
- Identify the optimal approval threshold based on the trade-off between default rate and approval rate

---

## 3. Project Scope & Tools

| Category | Details |
|----------|---------|
| **Data** | 38,576 loans, 24 columns, year 2021 |
| **SQL** | MySQL — Data preparation, KPI monitoring, Vintage, PSI, Risk Segmentation |
| **Python** | Pandas, Scikit-learn, Scipy, Seaborn — Feature engineering, Logistic Regression, A/B Testing, KS Test |
| **BI** | Power BI — 5-page dashboard, DAX measures, interactive filtering |
| **Methods** | PSI, Vintage Analysis, Champion-Challenger Simulation, KS Test, Welch t-test |

---

## 4. Repository Structure

```
bank-loan-credit-risk/
├── data/
│   └── raw/
│       └── financial_loan_data_excel.xlsx       # Original dataset
│   └── processed/                  # Output files exported from Python
│       ├── ab_testing_results.xlsx # Champion vs. Challenger simulation results
│       ├── psi_results.xlsx        # PSI monitoring H1 vs H2
│       └── threshold_analysis.xlsx # Threshold optimization analysis
├── queries/
│   └── final/
│       └── main_workflow.sql              # SQL for data preparation & KPI calculation
├── notebooks/
│   └── main_analysis.py                   # Python pipeline: EDA → Model → A/B Test
├── visuals/                        # Charts exported from Python
│   ├── vintage_analysis.png
│   ├── risk_segmentation.png
│   ├── ab_test_results.png
│   └── threshold_tradeoff.png
├── Bank Loan Credit Risk Report.pdf # Power BI dashboard export
└── README.md
```

---

## 5. Data Workflow

```
financial_loan_data_excel.xlsx
        │
        ▼
[SQL] vw_financial_loan_enriched
  - Calculate binary default indicator, loan performance classification, net return
  - Add monthly origination cohort, risk tier, employment seniority group
  - Normalize term (TRIM), purpose (LOWER)
        │
        ├──▶ [SQL] KPI Monitoring (MTD / PMTD)
        ├──▶ [SQL] Vintage Analysis by cohort
        ├──▶ [SQL] Risk Segmentation
        ├──▶ [SQL] PSI/CSI (H1 vs H2)
        │
        ▼
[Python] Feature Engineering
  - loan_to_dti, high_risk_purpose
  - cross_val_predict (5-fold) → predicted default probability
        │
        ├──▶ Logistic Regression (AUC = 0.68)
        ├──▶ KS Test (KS = 0.13, p < 0.001)
        ├──▶ A/B Test Champion vs. Challenger
        └──▶ Threshold Optimization (0.20 – 0.50)
                │
                ▼
        [Power BI] 5-page Dashboard
```

---

## 6. Data Model & Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Loan identifier |
| `loan_status` | str | Status: Fully Paid / Current / Charged Off |
| `loan_amount` | int | Disbursed amount (USD) |
| `total_payment` | int | Total amount received |
| `int_rate` | float | Interest rate (decimal, e.g. 0.12 = 12%) |
| `dti` | float | Debt-to-Income ratio (decimal, e.g. 0.13 = 13%) |
| `grade` | str | Credit grade A–G |
| `term` | str | Loan term: 36 months / 60 months |
| `purpose` | str | Loan purpose (14 categories) |
| `is_bad` *(derived)* | int | Binary default indicator: 1 if loan was written off as uncollectible |
| `profit` *(derived)* | int | Net return = total payment received minus disbursed amount |
| `risk_segment` *(derived)* | str | 3-tier risk classification: Low / Medium / High Risk |
| `cohort_label` *(derived)* | str | Monthly origination cohort in YYYY-MM format for correct time-series sorting |

---

## 7. Analysis & Metrics

### Overall KPIs (Year 2021)

| Metric | Value |
|--------|-------|
| Total Applications | 38,576 |
| Total Funded Amount | $436M |
| Total Amount Received | $473M |
| Overall Default Rate | 13.82% |
| Avg Interest Rate | 12.05% |
| Avg DTI | 13.33% |

### Risk Segmentation

| Segment | Number of Loans | Default Rate |
|---------|----------------|--------------|
| Low Risk | 17,992 | 7.84% |
| Medium Risk | 13,610 | 17.87% |
| High Risk | 6,974 | 21.14% |

### PSI Monitoring (H1 vs H2 of 2021)

| Variable | PSI | Status |
|----------|-----|--------|
| grade | 0.003 | Stable |
| purpose | 0.012 | Stable |
| risk_segment | 0.004 | Stable |

Portfolio distribution remained stable between the two halves of the year — no signs of population shift detected.

### A/B Test: Champion vs. Challenger (threshold = 0.35)

| Strategy | Approval Rate | Default Rate | Total Net Return |
|----------|--------------|--------------|-----------------|
| Champion (approve all) | 100% | 13.82% | $37.3M |
| Challenger (LR model) | 30.4% | 9.11% | $4.8M |

Model: Logistic Regression, AUC = 0.68, KS = 0.13 (p < 0.001)
Statistical test: Welch t-test p < 0.05 — the difference is statistically significant.

---

## 8. Key Insights

**1. Default rate of 13.8%, below the danger threshold but requires close monitoring**  
Out of 38,600+ loan applications, **5,333 loans were written off as uncollectible (13.8%)**. Performing loans account for **86.2%** with total received payments of **$435.8M** against **$370.2M** disbursed, meaning the portfolio remains profitable. However, total losses from non-performing loans amount to **$65.5M** disbursed with only **$37.3M** recovered, leaving a **$28.2M** gap as the real risk to control.

**2. Default rates vary significantly by risk tier, a single policy cannot apply to all segments**  
The High Risk tier makes up **19.44%** of the portfolio but carries a default rate of **21.14%**, nearly three times that of the Low Risk tier (**7.84%**). A uniform approval policy is exposing concentrated risk in this tier without any dedicated control mechanism.

**3. Debt Consolidation accounts for 47% of all applications, the largest segment and one that requires separate monitoring**  
Nearly half the portfolio consists of loans used to repay existing debt, which is both a legitimate need and a signal of financial pressure. The default rate within this group should be compared separately against other loan purposes (credit card, home improvement, etc.) for a more accurate risk assessment.

**4. 60-month loans have a higher default rate than 36-month loans**  
Borrowers who choose longer terms tend to have lower monthly repayment capacity, leading to risk that compounds over time. The 60-month segment should have stricter DTI requirements applied during the approval process.

**5. December recorded the highest monthly application volume, over 4,300 applications, up 6.91% month-over-month**  
There is a clear seasonality pattern: loan demand rises sharply at year-end, likely driven by holiday spending, investment needs, or short-term liquidity demands. This is important information for planning capital allocation and underwriting capacity in Q4 each year.

**6. Default rates fluctuate seasonally, not in a linear trend**  
Vintage Analysis shows default rates ranging from **11.58% (April) to 15.08% (February)** without a simple directional pattern. This suggests risk is tied to the characteristics of each origination batch, loan purpose mix, borrower segment composition by season, rather than an overall trend.

**7. Grade A–B concentrates performing loans; Grade E–G concentrates non-performing loans, the grading system is working in the right direction**  
However, it is worth verifying whether Grade E–G loans are being approved without additional tightening conditions, particularly within the Debt Consolidation, 60-month term segment.

**8. Portfolio remained stable throughout the year, a solid foundation for model benchmarking**  
PSI values for all variables are below **0.05** (Stable threshold < 0.10), indicating that the distribution of grade, purpose, and risk tier did not change meaningfully between H1 and H2. This is a favorable condition for a model trained on historical data to be applied to future periods.

**9. Challenger policy reduces default rate by 34%, but at the cost of a significantly lower approval rate**  
At threshold **0.35**, the Challenger policy reduces the default rate from **13.82% to 9.11%**, but approves only **30.4%** of loans. This is not a "better model" in absolute terms, it is a tool for management to set a risk threshold aligned with the strategy of each business phase. At threshold **0.40**, approval rate reaches **39.4%** while the default rate holds at **10.07%**, which may represent a more balanced operating point.

---

## 9. Recommendations

**1. Tighten approval criteria for Debt Consolidation loans with a 60-month term**
This combination carries the two highest individual risk factors (loan purpose and loan term). Recommended requirements: DTI of 35% or below, and a minimum credit history of 2 years without any prior written-off loans. *(Credit Risk)*

**2. Apply differentiated policies by risk tier instead of a uniform standard**
For the High Risk tier (default rate **21.14%**), consider requiring additional collateral or capping the loan limit. For the Low Risk tier (default rate **7.84%**), eligibility criteria could be relaxed to improve credit accessibility. *(Credit Policy)*

**3. Pilot the Challenger policy for 3 months within the highest-risk segment**
Rather than a full rollout, test with Grade D–G or Debt Consolidation loans, which account for the majority of non-performing loans. Measure actual default rate and approval rate before scaling. **Threshold 0.40–0.45** is the balanced zone recommended for initial evaluation. *(Risk Management)*

**4. Build an Early Warning System for at-risk loans**
Currently, the portfolio only flags loans after they have been written off as uncollectible. Monitoring intermediate signals such as first days past due and number of payment extensions would enable intervention before a loan transitions to non-performing status, particularly for Grade E–G loans still showing as current. *(Risk Management)*

**5. Plan Q4 capital based on seasonal demand patterns**
Loan demand increases by approximately **7% in December** each year. The treasury and capital team should prepare **2–3 months in advance** to ensure approval rates are not constrained by liquidity shortfalls during peak season. *(Treasury / Capital Planning)*

**6. Monitor PSI on a regular cadence to detect population shifts early**
PSI is currently stable (all values below **0.05**), but continuous monitoring is needed, particularly when macroeconomic policies change or new loan products are launched. It is recommended to review approval thresholds quarterly based on actual vintage results. *(Data Analytics)*

---

## 10. Assumptions & Limitations

**Assumptions:**
- `is_bad = 1` when `loan_status = 'Charged Off'`; loans with status `Current` are excluded as their final outcome is not yet determined
- The 3-tier risk classification is rule-based (grade, DTI, term) and not derived from a statistical model
- The A/B Test is a retrospective simulation on historical data, not a live experiment; results reflect a "what if" scenario and do not guarantee real-world performance upon deployment

**Limitations:**
- The dataset covers only one year (2021), so year-over-year comparison is not possible; PSI is measured H1 vs. H2 instead of against a prior year
- Logistic Regression achieved AUC = 0.68, acceptable but with room for improvement, particularly with tree-based models (XGBoost, LightGBM)
- Credit history variables are absent (prior delinquency count, total outstanding debt at other institutions), which could significantly improve predictive accuracy
- KS = 0.13 indicates limited discriminatory power compared to standard bank scorecards (KS > 0.30)
- A/B groups were randomly assigned across the full dataset in the simulation; in practice, a time-based split would be required to avoid look-ahead bias

---

## 11. Future Enhancements

- Experiment with XGBoost and LightGBM to improve AUC and KS
- Add Weight of Evidence (WoE) and Information Value (IV) to assess the predictive power of each variable
- Build a points-based scorecard instead of a probability threshold for easier operational deployment
- Expand the analysis to multi-year data to enable year-over-year PSI and long-horizon vintage tracking
- Integrate SHAP values to explain individual approval decisions (model explainability)

---

## 12. Deliverables

| File | Description |
|------|-------------|
| `main_workflow.sql` | SQL: enriched view, KPI monitoring, Vintage, Risk Segmentation, PSI, data export |
| `main_analysis.py` | Python: feature engineering, Logistic Regression model, A/B test, KS test, threshold optimization |
| `Bank_Loan_Credit_Risk_Report.pdf` | Power BI dashboard export — 5 pages: Summary, Overview, Details, Risk Monitoring, A/B Testing |
| `ab_testing_results.xlsx` | Champion vs. Challenger simulation results |
| `threshold_analysis.xlsx` | Comparison across 7 threshold levels from 0.20 to 0.50 |
| `psi_results.xlsx` | PSI values for grade, purpose, and risk tier |

---

## 13. Author

**Phan Ngoc Kim Thoa**
- 📧 thoaphan2921@gmail.com
- 💼 [LinkedIn](https://www.linkedin.com/in/thoangoc2906)
- 🐙 [GitHub](https://github.com/thoangoc2921)
