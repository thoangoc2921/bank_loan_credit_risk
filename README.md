# Bank Loan Credit Risk Analysis

---

## 1. Project Overview

Phân tích rủi ro tín dụng danh mục vay ngân hàng, kết hợp SQL reporting, Python modeling và Power BI dashboard nhằm trả lời câu hỏi: **chính sách phê duyệt hiện tại có đang chấp nhận quá nhiều rủi ro không, và nếu thay bằng mô hình dự đoán thì kết quả thay đổi thế nào?**

Dataset gồm 38,576 khoản vay phát sinh năm 2021. Phân tích phát hiện bad rate tổng thể ở mức 13.82%, trong đó nhóm High Risk có bad rate lên đến 21.14%. Mô hình Logistic Regression (Challenger) cho thấy nếu áp dụng ngưỡng phê duyệt dựa trên xác suất vỡ nợ, bad rate có thể giảm xuống 9.11% và kết quả có ý nghĩa thống kê (p < 0.05).

---

## 2. Objectives

- Xây dựng báo cáo KPI tháng và theo dõi xu hướng danh mục vay theo thời gian
- Phân khúc danh mục theo rủi ro (Low / Medium / High) dựa trên grade, DTI và kỳ hạn
- Thực hiện Vintage Analysis để theo dõi chất lượng danh mục theo cohort phát sinh
- Đo lường sự ổn định phân phối danh mục (PSI) giữa hai nửa năm
- Mô phỏng A/B Test Champion vs Challenger để đánh giá hiệu quả của chính sách phê duyệt mới
- Xác định ngưỡng phê duyệt tối ưu theo trade-off giữa bad rate và tỷ lệ phê duyệt

---

## 3. Project Scope & Tools

| Hạng mục | Chi tiết |
|----------|----------|
| **Dữ liệu** | 38,576 khoản vay, 24 cột, năm 2021 |
| **SQL** | MySQL — Data preparation, KPI monitoring, Vintage, PSI, Risk Segmentation |
| **Python** | Pandas, Scikit-learn, Scipy, Seaborn — Feature engineering, Logistic Regression, A/B Testing, KS Test |
| **BI** | Power BI — Dashboard 5 trang, DAX measures, interactive filtering |
| **Phương pháp** | PSI, Vintage Analysis, Champion-Challenger Simulation, KS Test, Welch t-test |

---

## 4. Repository Structure

```
bank-loan-credit-risk/
├── data/
│   └── raw/
│       └── financial_loan_data_excel.xlsx       # Dataset gốc
│   └── processed/                  # Kết quả export từ Python
│       ├── ab_testing_results.xlsx # Champion vs Challenger simulation
│       ├── psi_results.xlsx        # PSI monitoring H1 vs H2
│       └── threshold_analysis.xlsx # Threshold optimization analysis
├── queries/
│   └── final/
│       └── main_workflow.sql              # SQL chuẩn bị dữ liệu & tính KPI
├── notebooks/
│   └── main_analysis.py                   # Pipeline Python: EDA → Model → A/B Test
├── visuals/                        # Biểu đồ xuất từ Python
│   ├── vintage_analysis.png
│   ├── risk_segmentation.png
│   ├── ab_test_results.png
│   └── threshold_tradeoff.png
├── Bank Loan Credit Risk Report.pdf # Xuất báo cáo từ Power BI dashboard
└── README.md
```

---

## 5. Data Workflow

```
financial_loan_data_excel.xlsx
        │
        ▼
[SQL] vw_financial_loan_enriched
  - Tính is_bad, loan_quality, profit
  - Thêm cohort_label, risk_segment, age_group
  - Chuẩn hóa term (TRIM), purpose (LOWER)
        │
        ├──▶ [SQL] KPI Monitoring (MTD / PMTD)
        ├──▶ [SQL] Vintage Analysis theo cohort
        ├──▶ [SQL] Risk Segmentation
        ├──▶ [SQL] PSI/CSI (H1 vs H2)
        │
        ▼
[Python] Feature Engineering
  - loan_to_dti, high_risk_purpose
  - cross_val_predict (5-fold) → prob_bad
        │
        ├──▶ Logistic Regression (AUC = 0.68)
        ├──▶ KS Test (KS = 0.13, p < 0.001)
        ├──▶ A/B Test Champion vs Challenger
        └──▶ Threshold Optimization (0.20 – 0.50)
                │
                ▼
        [Power BI] Dashboard 5 trang
```

---

## 6. Data Model & Schema

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | int | Mã định danh khoản vay |
| `loan_status` | str | Trạng thái: Fully Paid / Current / Charged Off |
| `loan_amount` | int | Số tiền giải ngân (USD) |
| `total_payment` | int | Tổng tiền thu về |
| `int_rate` | float | Lãi suất (decimal, ví dụ 0.12 = 12%) |
| `dti` | float | Debt-to-Income ratio (decimal, ví dụ 0.13 = 13%) |
| `grade` | str | Xếp hạng tín dụng A–G |
| `term` | str | Kỳ hạn: 36 months / 60 months |
| `purpose` | str | Mục đích vay (14 loại) |
| `is_bad` *(derived)* | int | 1 nếu Charged Off |
| `profit` *(derived)* | int | total_payment − loan_amount |
| `risk_segment` *(derived)* | str | Low / Medium / High Risk |
| `cohort_label` *(derived)* | str | Dạng YYYY-MM để sort đúng thứ tự |

---

## 7. Analysis & Metrics

### KPI Tổng quan (năm 2021)

| Metric | Giá trị |
|--------|---------|
| Total Applications | 38,576 |
| Total Funded Amount | $436M |
| Total Amount Received | $473M |
| Overall Bad Rate | 13.82% |
| Avg Interest Rate | 12.05% |
| Avg DTI | 13.33% |

### Risk Segmentation

| Segment | Số khoản vay | Bad Rate |
|---------|-------------|----------|
| Low Risk | 17,992 | 7.84% |
| Medium Risk | 13,610 | 17.87% |
| High Risk | 6,974 | 21.14% |

### PSI Monitoring (H1 vs H2 năm 2021)

| Variable | PSI | Trạng thái |
|----------|-----|-----------|
| grade | 0.003 | Stable |
| purpose | 0.012 | Stable |
| risk_segment | 0.004 | Stable |

Phân phối danh mục ổn định giữa hai nửa năm — không có dấu hiệu population shift.

### A/B Test: Champion vs Challenger (threshold = 0.35)

| Strategy | Approval Rate | Bad Rate | Total Profit |
|----------|--------------|----------|-------------|
| Champion (approve all) | 100% | 13.82% | $37.3M |
| Challenger (LR model) | 30.4% | 9.11% | $4.8M |

Mô hình: Logistic Regression, AUC = 0.68, KS = 0.13 (p < 0.001)  
Kiểm định: Welch t-test p < 0.05 → sự khác biệt có ý nghĩa thống kê

---

## 8. Key Insights

**1. Tỷ lệ nợ xấu 13.8% — thấp hơn ngưỡng nguy hiểm nhưng cần theo dõi chặt**  
Trong 38,600+ đơn vay, 5,333 đơn bị Charged Off (13.8%). Good Loan chiếm 86.2% với tổng tiền thu hồi đạt $435.8M trên $370.2M giải ngân, tức là danh mục vẫn sinh lời. Tuy nhiên tổng thiệt hại từ Bad Loan là $65.5M giải ngân với chỉ $37.3M thu hồi được, so với chênh lệch $28.2M là rủi ro thực sự cần kiểm soát.

**2. Bad rate phân hóa rõ rệt theo segment — không thể dùng một chính sách cho tất cả**  
High Risk chiếm 19.44% danh mục nhưng có bad rate 21.14%, gấp gần 3 lần nhóm Low Risk (7.84%). Một chính sách phê duyệt đồng nhất đang để lộ rủi ro tập trung ở nhóm này mà không có cơ chế kiểm soát riêng.

**3. Debt Consolidation chiếm 47% tổng đơn — phân khúc lớn nhất và cần giám sát riêng**  
Gần một nửa danh mục là vay để trả nợ cũ, vừa là nhu cầu hợp lệ vừa là dấu hiệu khách hàng đang có áp lực tài chính. Tỷ lệ Charged Off trong nhóm này cần được so sánh riêng với các mục đích vay khác (credit card, home improvement...) để đánh giá rủi ro chính xác hơn.

**4. Vay 60 tháng có tỷ lệ nợ xấu cao hơn vay 36 tháng**  
Khách hàng chọn kỳ hạn dài thường có khả năng trả nợ hàng tháng thấp hơn, dẫn đến rủi ro tích lũy theo thời gian. Phân khúc 60 tháng cần được áp dụng tiêu chí DTI chặt hơn trong quá trình phê duyệt.

**5. Tháng 12 có MTD cao nhất năm — 4,300+ đơn, tăng 6.91% MoM**  
Có seasonality rõ rệt: nhu cầu vay tăng mạnh cuối năm, có thể do mua sắm, đầu tư hoặc nhu cầu thanh khoản ngắn hạn. Đây là thông tin quan trọng để lên kế hoạch nguồn vốn và nhân lực thẩm định cho Q4 hàng năm.

**6. Bad rate dao động theo mùa vụ, không phải xu hướng tuyến tính**  
Vintage analysis cho thấy bad rate dao động từ 11.58% (tháng 4) đến 15.08% (tháng 2) mà không theo pattern đơn giản. Điều này gợi ý rủi ro liên quan đến đặc điểm từng đợt phát vay — mục đích vay, phân khúc khách hàng theo mùa — hơn là xu hướng tổng thể.

**7. Grade A–B tập trung Good Loan, Grade E–G tập trung Bad Loan — hệ thống xếp hạng hoạt động đúng hướng**  
Tuy nhiên cần kiểm tra xem Grade E-G có đang được phê duyệt mà không kèm điều kiện thắt chặt bổ sung hay không, đặc biệt trong nhóm vay Debt Consolidation kỳ hạn 60 tháng.

**8. Danh mục ổn định trong năm — nền tảng tốt để xây benchmark mô hình**  
PSI của tất cả biến đều dưới 0.05 (ngưỡng Stable < 0.10), cho thấy phân phối grade, purpose và risk_segment không thay đổi đáng kể giữa H1 và H2. Đây là điều kiện thuận lợi để mô hình học từ dữ liệu lịch sử và áp dụng sang kỳ tiếp theo.

**9. Challenger policy giảm bad rate 34% nhưng đánh đổi bằng tỷ lệ phê duyệt thấp hơn nhiều**  
Tại threshold 0.35, Challenger giảm bad rate từ 13.82% xuống 9.11%, nhưng chỉ phê duyệt 30.4% khoản vay. Đây không phải "mô hình tốt hơn" theo nghĩa tuyệt đối mà là công cụ để ban quản lý đặt ngưỡng rủi ro theo chiến lược từng giai đoạn. Tại threshold 0.40, approval rate đạt 39.4% trong khi bad rate vẫn giữ ở 10.07% — có thể là vùng cân bằng hợp lý hơn.

---

## 9. Recommendations

**1. Thắt chặt tiêu chí phê duyệt cho vay Debt Consolidation kỳ hạn 60 tháng**  
Kết hợp 2 yếu tố rủi ro cao nhất (mục đích + kỳ hạn): yêu cầu DTI ≤ 30% và lịch sử tín dụng tối thiểu 2 năm không có Charged Off trước đó. *(Credit Risk)*

**2. Áp dụng chính sách khác biệt theo segment thay vì đồng nhất**  
Với nhóm High Risk (bad rate 21.14%), cân nhắc yêu cầu tài sản đảm bảo bổ sung hoặc giới hạn hạn mức. Với nhóm Low Risk (bad rate 7.84%), có thể nới lỏng điều kiện để tăng khả năng tiếp cận tín dụng. *(Credit Policy)*

**3. Pilot Challenger policy trong 3 tháng ở phân khúc rủi ro cao nhất**  
Thay vì áp dụng toàn diện, thử nghiệm với khoản vay Grade D–G hoặc Debt Consolidation, là nhóm chiếm phần lớn bad loan. Đo lường bad rate và approval rate thực tế trước khi mở rộng. Threshold 0.40–0.45 là vùng cân bằng nên xem xét đầu tiên. *(Risk Management)*

**4. Xây dựng Early Warning System cho danh mục có nguy cơ**  
Hiện tại chỉ biết khi đã Charged Off. Cần theo dõi chỉ số trung gian: số ngày trễ hạn đầu tiên, số lần gia hạn để can thiệp trước khi chuyển thành nợ xấu, đặc biệt với nhóm Grade E–G đang còn Current. *(Risk Management)*

**5. Lên kế hoạch nguồn vốn Q4 dựa trên seasonality**  
Nhu cầu vay tăng ~7% vào tháng 12 hàng năm. Bộ phận nguồn vốn nên chuẩn bị trước 2–3 tháng để đảm bảo tỷ lệ phê duyệt không bị siết do thiếu thanh khoản đúng vào peak season. *(Treasury / Capital Planning)*

**6. Theo dõi PSI định kỳ để phát hiện population shift sớm**  
Hiện tại PSI ổn định (tất cả < 0.05), nhưng cần theo dõi liên tục, đặc biệt khi có thay đổi chính sách kinh tế vĩ mô hoặc ra mắt sản phẩm vay mới. Đề xuất review ngưỡng threshold theo quý dựa trên kết quả vintage thực tế. *(Data Analytics)*

---

## 10. Assumptions & Limitations

**Assumptions:**
- `is_bad = 1` khi `loan_status = 'Charged Off'`, bỏ qua trạng thái `Current` (khoản vay chưa đáo hạn, kết quả chưa xác định)
- Risk segment được xây dựng theo rule-based đơn giản (grade + DTI + term), không dựa trên mô hình thống kê
- A/B Test là simulation hồi tố (retrospective) trên dữ liệu lịch sử, không phải live experiment, kết quả phản ánh **what if** chứ không đảm bảo performance thực tế khi triển khai

**Limitations:**
- Dataset 1 năm (2021) nên không thể so sánh year-over-year; PSI được đo H1 vs H2 thay vì so với năm trước
- Mô hình Logistic Regression có AUC = 0.68 — mức chấp nhận được nhưng còn dư địa cải thiện, đặc biệt với các mô hình tree-based (XGBoost, LightGBM)
- Không có thông tin về lịch sử tín dụng (số lần trễ hạn trước đây, tổng dư nợ các tổ chức khác), các biến quan trọng này có thể cải thiện đáng kể khả năng dự đoán
- KS = 0.13 cho thấy khả năng phân biệt của mô hình còn hạn chế so với scorecard chuẩn ngân hàng (KS > 0.30)
- A/B group được assign ngẫu nhiên trên toàn bộ dataset trong simulation, thực tế cần phân nhóm theo thời gian (time-based split) để tránh look-ahead bias

---

## 11. Future Enhancements

- Thử nghiệm mô hình XGBoost, LightGBM để cải thiện AUC và KS
- Thêm weight of evidence (WoE) và information value (IV) để đánh giá predictive power của từng biến
- Xây dựng scorecard dạng điểm số thay vì ngưỡng xác suất để dễ áp dụng hơn trong thực tế vận hành
- Mở rộng phân tích sang dữ liệu đa năm để có thể thực hiện year-over-year PSI và vintage dài hạn
- Tích hợp SHAP values để giải thích từng quyết định phê duyệt (model explainability)

---

## 12. Deliverables

| File | Mô tả |
|------|-------|
| `main_workflow.sql` | SQL: VIEW, KPI, Vintage, Risk Segment, PSI, Export |
| `main_analysis.py` | Python: Feature engineering, LR model, A/B test, KS test, Threshold optimization |
| `Bank_Loan_Credit_Risk_Report.pdf` | Dashboard Power BI 5 trang: Summary, Overview, Details, Risk Monitoring, A/B Testing |
| `ab_testing_results.xlsx` | Kết quả Champion vs Challenger |
| `threshold_analysis.xlsx` | So sánh 7 mức threshold từ 0.20 đến 0.50 |
| `psi_results.xlsx` | PSI của grade, purpose, risk_segment |

---

## 13. Author

**Phan Ngoc Kim Thoa**
- 📧 thoaphan2921@gmail.com
- 💼 [LinkedIn](https://www.linkedin.com/in/thoangoc2906)
- 🐙 [GitHub](https://github.com/thoangoc2921)

