-- ============================================================
-- MAIN_WORKFLOW.SQL
-- Dự án: Bank Loan Credit Risk Analysis
-- Tác giả: Phan Ngoc Kim Thoa
-- Dữ liệu: financial_loan (38,576 khoản vay, năm 2021)
-- Quy trình: Chuẩn bị dữ liệu → Feature Engineering → KPI
--            → Vintage Analysis → Risk Segmentation
--            → PSI/CSI Monitoring → Export cho Python
-- ============================================================

USE bank_loan_data;


-- ============================================================
-- 1. DATA PREPARATION — ENRICHED VIEW
-- ============================================================
-- Tạo VIEW tổng hợp gồm cột gốc + các cột tính toán cần thiết
-- Liệt kê tường minh từng cột để VIEW không bị lỗi khi schema thay đổi

DROP VIEW IF EXISTS vw_financial_loan_enriched;

CREATE VIEW vw_financial_loan_enriched AS
SELECT
    -- Cột gốc
    id,
    address_state,
    application_type,
    emp_length,
    emp_title,
    grade,
    home_ownership,
    issue_date,
    last_credit_pull_date,
    last_payment_date,
    loan_status,
    next_payment_date,
    member_id,
    purpose,
    sub_grade,
    term,               -- lưu ý: giá trị có khoảng trắng đầu, ví dụ ' 36 months'
    verification_status,
    annual_income,
    dti,                -- lưu dạng decimal (ví dụ: 0.13 tương đương 13%)
    installment,
    int_rate,           -- lưu dạng decimal (ví dụ: 0.12 tương đương 12%)
    loan_amount,
    total_acc,
    total_payment,

    -- Phân loại chất lượng khoản vay
    CASE
        WHEN loan_status IN ('Fully Paid', 'Current') THEN 'Good'
        WHEN loan_status = 'Charged Off'              THEN 'Bad'
        ELSE 'Other'
    END AS loan_quality,

    -- Biến target nhị phân cho mô hình dự đoán (1 = nợ xấu)
    CASE WHEN loan_status = 'Charged Off' THEN 1 ELSE 0 END AS is_bad,

    -- Lợi nhuận thực tế = tiền thu về − số tiền giải ngân
    (total_payment - loan_amount) AS profit,

    -- Các biến thời gian để phân tích theo kỳ
    YEAR(issue_date)        AS issue_year,
    MONTH(issue_date)       AS issue_month,
    MONTHNAME(issue_date)   AS issue_month_name,

    -- Nhãn cohort dạng YYYY-MM giúp Power BI sort đúng thứ tự thời gian
    CONCAT(YEAR(issue_date), '-', LPAD(MONTH(issue_date), 2, '0')) AS cohort_label,

    -- Nhóm thâm niên làm việc
    CASE
        WHEN emp_length IN ('< 1 year', '1 year', '2 years')             THEN 'Young'
        WHEN emp_length IN ('3 years','4 years','5 years','6 years','7 years') THEN 'Mid-age'
        ELSE 'Senior'   -- bao gồm 8 years, 9 years, 10+ years và NULL
    END AS age_group,

    -- Phân khúc rủi ro 3 tầng dựa trên grade, DTI và kỳ hạn
    -- dti là decimal nên ngưỡng so sánh là 0.25 và 0.40 (không phải 25, 40)
    -- TRIM(term) để loại bỏ khoảng trắng thừa trước khi so sánh
    CASE
        WHEN grade IN ('A','B')
             AND dti <= 0.25
             AND TRIM(term) = '36 months' THEN 'Low Risk'
        WHEN grade IN ('C','D')
             OR  dti BETWEEN 0.25 AND 0.40 THEN 'Medium Risk'
        ELSE 'High Risk'
    END AS risk_segment

FROM financial_loan;


-- ============================================================
-- 2. CORE KPI MONITORING
-- ============================================================
-- Tính KPI tháng hiện tại và tháng trước bằng CTE + UNION ALL
-- int_rate và dti nhân *100 vì cột gốc lưu dạng decimal

WITH CurrentMonth AS (
    SELECT
        MAX(issue_year)  AS max_year,
        MAX(issue_month) AS max_month
    FROM vw_financial_loan_enriched
),
PreviousMonth AS (
    -- Xử lý trường hợp tháng 1 → quay về tháng 12 năm trước
    SELECT
        CASE WHEN max_month = 1 THEN max_year - 1 ELSE max_year  END AS prev_year,
        CASE WHEN max_month = 1 THEN 12           ELSE max_month - 1 END AS prev_month
    FROM CurrentMonth
)

SELECT
    'Current Month'         AS period,
    COUNT(id)               AS total_applications,
    SUM(loan_amount)        AS total_funded,
    SUM(profit)             AS total_profit,
    AVG(is_bad) * 100       AS bad_rate_pct,
    AVG(int_rate) * 100     AS avg_interest_rate_pct,
    AVG(dti) * 100          AS avg_dti_pct
FROM vw_financial_loan_enriched
WHERE issue_year  = (SELECT max_year  FROM CurrentMonth)
  AND issue_month = (SELECT max_month FROM CurrentMonth)

UNION ALL

SELECT
    'Previous Month',
    COUNT(id),
    SUM(loan_amount),
    SUM(profit),
    AVG(is_bad) * 100,
    AVG(int_rate) * 100,
    AVG(dti) * 100
FROM vw_financial_loan_enriched
WHERE issue_year  = (SELECT prev_year  FROM PreviousMonth)
  AND issue_month = (SELECT prev_month FROM PreviousMonth);


-- ============================================================
-- 3. GOOD LOAN vs BAD LOAN SUMMARY
-- ============================================================
SELECT
    loan_quality,
    COUNT(id)           AS loan_count,
    SUM(loan_amount)    AS funded_amount,
    SUM(profit)         AS total_profit,
    AVG(is_bad) * 100   AS bad_rate_pct,
    AVG(profit)         AS avg_profit_per_loan
FROM vw_financial_loan_enriched
GROUP BY loan_quality;


-- ============================================================
-- 4. VINTAGE ANALYSIS
-- ============================================================
-- Theo dõi chất lượng danh mục theo từng cohort phát sinh vay
-- cohort_label dạng YYYY-MM giúp sort đúng thứ tự trên dashboard

SELECT
    cohort_label,
    issue_year,
    issue_month,
    COUNT(id)           AS cohort_size,
    SUM(loan_amount)    AS funded_amount,
    AVG(is_bad) * 100   AS bad_rate_pct,
    SUM(profit)         AS total_profit,
    AVG(profit)         AS avg_profit_per_loan
FROM vw_financial_loan_enriched
GROUP BY cohort_label, issue_year, issue_month
ORDER BY cohort_label ASC;


-- ============================================================
-- 5. RISK SEGMENTATION ANALYSIS
-- ============================================================
SELECT
    risk_segment,
    COUNT(id)                                                   AS applications,
    AVG(is_bad) * 100                                           AS bad_rate_pct,
    SUM(profit)                                                 AS total_profit,
    AVG(loan_amount)                                            AS avg_loan_amount,
    AVG(dti) * 100                                              AS avg_dti_pct,
    COUNT(CASE WHEN loan_quality = 'Good' THEN id END) * 100.0
        / COUNT(id)                                             AS good_loan_pct
FROM vw_financial_loan_enriched
GROUP BY risk_segment
ORDER BY bad_rate_pct DESC;


-- ============================================================
-- 6. BREAKDOWN ANALYSIS — nguồn dữ liệu cho Power BI Dashboard
-- ============================================================
-- LOWER(purpose): chuẩn hóa chữ hoa/thường vì dữ liệu không đồng nhất
--                 ví dụ 'Debt consolidation' và 'debt_consolidation'
-- TRIM(term): bỏ khoảng trắng đầu để hiển thị sạch trên dashboard

SELECT
    grade,
    LOWER(purpose)      AS purpose,
    TRIM(term)          AS term,
    address_state,
    risk_segment,
    age_group,
    COUNT(id)           AS total_applications,
    AVG(is_bad) * 100   AS bad_rate_pct,
    SUM(profit)         AS total_profit,
    AVG(int_rate) * 100 AS avg_interest_rate_pct
FROM vw_financial_loan_enriched
GROUP BY grade, LOWER(purpose), TRIM(term), address_state, risk_segment, age_group
ORDER BY bad_rate_pct DESC;


-- ============================================================
-- 7. PSI / CSI MONITORING
-- ============================================================
-- Đo lường sự thay đổi phân phối danh mục giữa 2 kỳ (Population Stability Index)
-- Dữ liệu chỉ có 1 năm 2021 → so sánh H1 (tháng 1-6) với H2 (tháng 7-12)
-- Dùng LN() (natural log) và NULLIF để tránh lỗi chia cho 0

-- PSI cho Risk Segment
WITH H2 AS (
    SELECT
        risk_segment,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER() AS pct
    FROM vw_financial_loan_enriched
    WHERE issue_month BETWEEN 7 AND 12
    GROUP BY risk_segment
),
H1 AS (
    SELECT
        risk_segment,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER() AS pct
    FROM vw_financial_loan_enriched
    WHERE issue_month BETWEEN 1 AND 6
    GROUP BY risk_segment
)
SELECT
    'Risk_Segment' AS variable,
    ROUND(
        SUM(
            (h2.pct - h1.pct)
            * LN( h2.pct / COALESCE(NULLIF(h1.pct, 0), 0.0001) )
        ), 4
    ) AS psi_value,
    CASE
        WHEN SUM((h2.pct - h1.pct) * LN(h2.pct / COALESCE(NULLIF(h1.pct,0),0.0001))) > 0.25
            THEN 'Significant Shift'
        WHEN SUM((h2.pct - h1.pct) * LN(h2.pct / COALESCE(NULLIF(h1.pct,0),0.0001))) > 0.10
            THEN 'Moderate Shift'
        ELSE 'Stable'
    END AS stability_status
FROM H2
JOIN H1 USING (risk_segment);


-- PSI cho Grade
WITH H2_grade AS (
    SELECT
        grade,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER() AS pct
    FROM vw_financial_loan_enriched
    WHERE issue_month BETWEEN 7 AND 12
    GROUP BY grade
),
H1_grade AS (
    SELECT
        grade,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER() AS pct
    FROM vw_financial_loan_enriched
    WHERE issue_month BETWEEN 1 AND 6
    GROUP BY grade
)
SELECT
    'Grade' AS variable,
    ROUND(
        SUM(
            (h2.pct - h1.pct)
            * LN( h2.pct / COALESCE(NULLIF(h1.pct, 0), 0.0001) )
        ), 4
    ) AS psi_value,
    CASE
        WHEN SUM((h2.pct-h1.pct)*LN(h2.pct/COALESCE(NULLIF(h1.pct,0),0.0001))) > 0.25
            THEN 'Significant Shift'
        WHEN SUM((h2.pct-h1.pct)*LN(h2.pct/COALESCE(NULLIF(h1.pct,0),0.0001))) > 0.10
            THEN 'Moderate Shift'
        ELSE 'Stable'
    END AS stability_status
FROM H2_grade h2
JOIN H1_grade h1 USING (grade);


-- ============================================================
-- 8. EXPORT DATA CHO PYTHON
-- ============================================================
-- Chạy query này để export CSV → import vào notebook phân tích
-- LOWER(purpose) và TRIM(term) áp dụng trước để Python không cần xử lý thêm

SELECT
    id,
    loan_amount,
    total_payment,
    int_rate,           -- giữ nguyên decimal, Python sẽ StandardScale
    dti,                -- giữ nguyên decimal, Python sẽ StandardScale
    grade,
    LOWER(purpose)      AS purpose,
    TRIM(term)          AS term,
    home_ownership,
    emp_length,
    address_state,
    annual_income,
    sub_grade,
    verification_status,
    issue_year,
    issue_month,
    cohort_label,
    loan_status,
    loan_quality,
    is_bad,
    profit,
    risk_segment,
    age_group
FROM vw_financial_loan_enriched
ORDER BY id;
