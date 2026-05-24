# ============================================================
# MAIN_ANALYSIS.PY
# Dự án: Bank Loan Credit Risk Analysis
# Tác giả: Phan Ngoc Kim Thoa
# Dữ liệu: financial_loan (38,576 khoản vay, năm 2021)
# Quy trình: Load dữ liệu → Feature Engineering → KPI Summary
#            → Vintage Analysis → Risk Segmentation
#            → PSI/CSI Monitoring → A/B Testing (LR Challenger)
#            → KS Test → Threshold Optimization
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import ks_2samp
import sqlite3
import warnings
warnings.filterwarnings('ignore')

# Dùng sns.set_theme() để đảm bảo tương thích với mọi phiên bản matplotlib
sns.set_theme(style='whitegrid', palette='husl')


# ============================================================
# 1. LOAD DATA
# ============================================================

# Load trực tiếp từ Excel để test local
df = pd.read_excel('data/raw/financial_loan.xlsx')

print(f"Dataset shape: {df.shape}")

# Cột term có khoảng trắng đầu (' 36 months') → strip trước khi dùng
df['term'] = df['term'].str.strip()

# Cột purpose không đồng nhất chữ hoa/thường ('Debt consolidation', 'debt_consolidation')
# → chuẩn hóa lowercase toàn bộ
df['purpose'] = df['purpose'].str.lower().str.strip()


# ============================================================
# 2. FEATURE ENGINEERING
# ============================================================

# Phân loại chất lượng khoản vay và biến target nhị phân
df['loan_quality'] = np.where(
    df['loan_status'].isin(['Fully Paid', 'Current']), 'Good', 'Bad'
)
df['is_bad'] = (df['loan_status'] == 'Charged Off').astype(int)

# Lợi nhuận thực tế trên từng khoản vay
df['profit'] = df['total_payment'] - df['loan_amount']

# Biến thời gian
df['issue_year']   = df['issue_date'].dt.year
df['issue_month']  = df['issue_date'].dt.month
df['cohort_label'] = df['issue_date'].dt.strftime('%Y-%m')  # dạng YYYY-MM để sort đúng

# Nhóm thâm niên làm việc
def map_age_group(emp):
    if pd.isna(emp):
        return 'Unknown'
    if emp in ['< 1 year', '1 year', '2 years']:
        return 'Young'
    elif emp in ['3 years', '4 years', '5 years', '6 years', '7 years']:
        return 'Mid-age'
    else:
        return 'Senior'

df['age_group'] = df['emp_length'].apply(map_age_group)

# Phân khúc rủi ro 3 tầng
# dti lưu dạng decimal (0.13 = 13%) nên ngưỡng so sánh là 0.25 và 0.40
def map_risk_segment(row):
    if row['grade'] in ['A', 'B'] and row['dti'] <= 0.25 and row['term'] == '36 months':
        return 'Low Risk'
    elif row['grade'] in ['C', 'D'] or (0.25 < row['dti'] <= 0.40):
        return 'Medium Risk'
    else:
        return 'High Risk'

df['risk_segment'] = df.apply(map_risk_segment, axis=1)

# Feature bổ sung cho mô hình
df['loan_to_dti']       = df['loan_amount'] / (df['dti'] + 0.001)
df['high_risk_purpose'] = df['purpose'].apply(
    lambda x: 1 if 'debt consolidation' in str(x) else 0
)

print("Feature Engineering hoàn tất.")
print(df[['risk_segment', 'age_group', 'loan_quality']].value_counts().head(10))


# ============================================================
# 3. CORE KPI SUMMARY
# ============================================================

# int_rate và dti lưu dạng decimal → nhân *100 để hiển thị dạng phần trăm
kpi = {
    'Total_Applications'  : len(df),
    'Total_Funded_$'      : f"${df['loan_amount'].sum():,.0f}",
    'Total_Profit_$'      : f"${df['profit'].sum():,.0f}",
    'Overall_Bad_Rate_%'  : round(df['is_bad'].mean() * 100, 2),
    'Avg_Interest_Rate_%' : round(df['int_rate'].mean() * 100, 2),
    'Avg_DTI_%'           : round(df['dti'].mean() * 100, 2),
}

print("\n=== Core KPI ===")
for k, v in kpi.items():
    print(f"  {k:<30} {v}")


# ============================================================
# 4. VINTAGE ANALYSIS
# ============================================================

vintage = (
    df.groupby(['issue_year', 'issue_month', 'cohort_label'])
    .agg(
        cohort_size   = ('id',          'count'),
        bad_rate_pct  = ('is_bad',      lambda x: round(x.mean() * 100, 2)),
        total_profit  = ('profit',      'sum'),
        funded_amount = ('loan_amount', 'sum')
    )
    .reset_index()
    .sort_values('cohort_label')
)

print("\n=== Vintage Analysis ===")
print(vintage.to_string(index=False))

plt.figure(figsize=(14, 6))
sns.lineplot(
    data=vintage, x='issue_month', y='bad_rate_pct',
    hue='issue_year', marker='o', linewidth=2
)
plt.title('Vintage Analysis — Bad Rate theo Cohort phát sinh vay (2021)', fontsize=14)
plt.xlabel('Tháng phát sinh')
plt.ylabel('Bad Rate (%)')
plt.xticks(range(1, 13))
plt.legend(title='Năm')
plt.tight_layout()
plt.savefig('vintage_analysis.png', dpi=150)
plt.show()


# ============================================================
# 5. RISK SEGMENTATION
# ============================================================

risk_seg = (
    df.groupby('risk_segment')
    .agg(
        applications    = ('id',          'count'),
        bad_rate_pct    = ('is_bad',      lambda x: round(x.mean() * 100, 2)),
        total_profit    = ('profit',      'sum'),
        avg_loan_amount = ('loan_amount', 'mean'),
        avg_dti_pct     = ('dti',         lambda x: round(x.mean() * 100, 2))
    )
    .reset_index()
    .sort_values('bad_rate_pct', ascending=False)
)

print("\n=== Risk Segmentation ===")
print(risk_seg.to_string(index=False))

plt.figure(figsize=(8, 5))
sns.barplot(
    data=risk_seg, x='risk_segment', y='bad_rate_pct',
    order=['High Risk', 'Medium Risk', 'Low Risk']
)
plt.title('Bad Rate theo Risk Segment')
plt.ylabel('Bad Rate (%)')
plt.tight_layout()
plt.savefig('risk_segmentation.png', dpi=150)
plt.show()


# ============================================================
# 6. PSI / CSI MONITORING
# ============================================================
# Đo lường sự ổn định phân phối danh mục giữa 2 kỳ (H1 vs H2 năm 2021)
# Dữ liệu chỉ có 1 năm nên không thể so sánh year-over-year

def calculate_psi(expected_dist: pd.Series, actual_dist: pd.Series) -> float:
    """
    Tính Population Stability Index giữa 2 phân phối.
    Đặt epsilon vào cả tử lẫn mẫu để tránh log(0) và chia cho 0.
    """
    eps = 1e-6
    psi = np.sum(
        (actual_dist - expected_dist)
        * np.log((actual_dist + eps) / (expected_dist + eps))
    )
    return float(psi)


def psi_by_variable(df: pd.DataFrame, variable: str) -> dict:
    """PSI so sánh H1 (tháng 1-6) và H2 (tháng 7-12)."""
    h1 = df[df['issue_month'].isin([1,2,3,4,5,6])][variable].value_counts(normalize=True)
    h2 = df[df['issue_month'].isin([7,8,9,10,11,12])][variable].value_counts(normalize=True)

    # Align đầy đủ các category, điền 0 cho category không xuất hiện
    all_cats = sorted(set(h1.index) | set(h2.index))
    h1 = h1.reindex(all_cats, fill_value=0.0)
    h2 = h2.reindex(all_cats, fill_value=0.0)

    psi_val = calculate_psi(h1, h2)

    if psi_val < 0.10:
        status = 'Stable'
    elif psi_val < 0.25:
        status = 'Moderate Shift'
    else:
        status = 'Significant Shift'

    return {'Variable': variable, 'PSI': round(psi_val, 4), 'Status': status}


psi_results = pd.DataFrame([
    psi_by_variable(df, 'risk_segment'),
    psi_by_variable(df, 'grade'),
    psi_by_variable(df, 'purpose'),
])

print("\n=== PSI Monitoring (H1 vs H2 – 2021) ===")
print(psi_results.to_string(index=False))


# ============================================================
# 7. A/B TESTING — LOGISTIC REGRESSION CHALLENGER
# ============================================================

from sklearn.model_selection import train_test_split, cross_val_predict
from sklearn.linear_model    import LogisticRegression
from sklearn.preprocessing   import OneHotEncoder, StandardScaler
from sklearn.compose         import ColumnTransformer
from sklearn.pipeline        import Pipeline
from sklearn.metrics         import roc_auc_score, classification_report

cat_features = ['grade', 'purpose', 'term', 'home_ownership', 'age_group', 'risk_segment']
num_features = ['loan_amount', 'int_rate', 'dti']
# int_rate và dti giữ nguyên decimal; StandardScaler trong pipeline sẽ chuẩn hóa

X = df[cat_features + num_features].copy()
y = df['is_bad']

# Pipeline xử lý dữ liệu + Logistic Regression
preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False), cat_features),
    ('num', StandardScaler(), num_features)
])

model = Pipeline([
    ('prep', preprocessor),
    ('clf',  LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42))
])

# Train/test split theo tỷ lệ 70/30, stratify để giữ tỷ lệ is_bad
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
model.fit(X_train, y_train)

y_pred_proba_test = model.predict_proba(X_test)[:, 1]
print(f"\nAUC Score (test set): {roc_auc_score(y_test, y_pred_proba_test):.4f}")
print(classification_report(y_test, (y_pred_proba_test > 0.5).astype(int)))

# Dùng cross_val_predict (5-fold) để tạo prob_bad cho toàn bộ dataset
# mà không bị data leakage — mỗi row chỉ được predict khi model chưa học từ nó
print("\nĐang tính prob_bad bằng cross_val_predict (5-fold)...")
prob_bad_cv = cross_val_predict(
    model, X, y, cv=5, method='predict_proba', n_jobs=-1
)[:, 1]
df['prob_bad'] = prob_bad_cv


# Hàm mô phỏng Champion vs Challenger
def ab_test_simulation(df: pd.DataFrame, threshold: float = 0.35) -> pd.DataFrame:
    """
    Champion  : phê duyệt tất cả khoản vay (chính sách hiện tại).
    Challenger: chỉ phê duyệt khi prob_bad < threshold (mô hình Logistic Regression).
    """
    df_sim = df.copy()
    np.random.seed(42)
    df_sim['ab_group']            = np.random.choice(['A_Champion', 'B_Challenger'], size=len(df_sim))
    df_sim['champion_approved']   = 1
    df_sim['challenger_approved'] = (df_sim['prob_bad'] < threshold).astype(int)

    results = []
    for strategy, col in [('Champion', 'champion_approved'), ('Challenger', 'challenger_approved')]:
        sub = df_sim[df_sim[col] == 1]
        results.append({
            'Strategy'        : strategy,
            'Threshold'       : '-' if strategy == 'Champion' else threshold,
            'Approved'        : len(sub),
            'Approval_Rate_%' : round(len(sub) / len(df_sim) * 100, 2),
            'Bad_Rate_%'      : round(sub['is_bad'].mean() * 100, 2),
            'Total_Profit'    : round(sub['profit'].sum(), 0),
            'Avg_Profit'      : round(sub['profit'].mean(), 2),
            'Expected_Loss'   : round((sub['loan_amount'] * sub['is_bad']).sum(), 0),
        })
    return pd.DataFrame(results)


ab_results = ab_test_simulation(df, threshold=0.35)
print("\n=== A/B Test Results (threshold = 0.35) ===")
print(ab_results.to_string(index=False))

# Biểu đồ so sánh 3 chỉ số chính
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, metric, title, color in zip(
    axes,
    ['Bad_Rate_%', 'Approval_Rate_%', 'Total_Profit'],
    ['Bad Rate (%)', 'Approval Rate (%)', 'Total Profit ($)'],
    ['#e74c3c', '#2ecc71', '#3498db']
):
    sns.barplot(data=ab_results, x='Strategy', y=metric, ax=ax, color=color)
    ax.set_title(title, fontsize=12)
    ax.set_xlabel('')

plt.suptitle('Champion vs Challenger (threshold = 0.35)', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig('ab_test_results.png', dpi=150, bbox_inches='tight')
plt.show()

# Kiểm định thống kê sự khác biệt bad rate giữa 2 nhóm (Welch t-test)
champion_bad   = df['is_bad']
challenger_bad = df[df['prob_bad'] < 0.35]['is_bad']
t_stat, p_val  = stats.ttest_ind(champion_bad, challenger_bad, equal_var=False)
print(f"\nWelch t-test → t={t_stat:.4f}  p={p_val:.6f}")
print(f"Có ý nghĩa thống kê (p < 0.05): {p_val < 0.05}")


# ============================================================
# 8. MODEL VALIDATION — KS TEST & THRESHOLD OPTIMIZATION
# ============================================================

# KS Test: đo khả năng phân biệt Good Loan và Bad Loan của mô hình
# prob_bad từ cross_val_predict nên kết quả đáng tin cậy trên toàn bộ dataset
good_prob = df[df['is_bad'] == 0]['prob_bad']
bad_prob  = df[df['is_bad'] == 1]['prob_bad']

ks_stat, ks_p = ks_2samp(good_prob, bad_prob)
print(f"\n=== KS Test ===")
print(f"KS Statistic : {ks_stat:.4f}")
print(f"p-value      : {ks_p:.6f}")

if ks_stat > 0.4:
    print("→ Mô hình có khả năng phân biệt TỐT (Good Discrimination)")
elif ks_stat > 0.3:
    print("→ Mô hình có khả năng phân biệt KHÁ (Acceptable)")
else:
    print("→ Mô hình cần cải thiện thêm")

# So sánh kết quả tại nhiều mức threshold khác nhau
print("\n=== Threshold Optimization ===")
thresholds = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
th_results = []

for th in thresholds:
    approved = df[df['prob_bad'] < th]
    th_results.append({
        'Threshold'           : th,
        'Approval_Rate_%'     : round(len(approved) / len(df) * 100, 2),
        'Bad_Rate_%'          : round(approved['is_bad'].mean() * 100, 2),
        'Total_Profit_$'      : round(approved['profit'].sum(), 0),
        'Avg_Profit_per_Loan' : round(approved['profit'].mean(), 2),
        'Expected_Loss_$'     : round((approved['loan_amount'] * approved['is_bad']).sum(), 0),
    })

th_df = pd.DataFrame(th_results)
print(th_df.to_string(index=False))

# Biểu đồ trade-off giữa Bad Rate và Approval Rate theo từng ngưỡng
fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.set_xlabel('Probability Threshold', fontsize=12)
ax1.set_ylabel('Bad Rate (%)', color='#e74c3c', fontsize=12)
ax1.plot(th_df['Threshold'], th_df['Bad_Rate_%'],
         color='#e74c3c', marker='o', linewidth=2, label='Bad Rate')
ax1.tick_params(axis='y', labelcolor='#e74c3c')
ax1.axvline(x=0.35, color='gray', linestyle='--', alpha=0.6, label='Ngưỡng khuyến nghị 0.35')

ax2 = ax1.twinx()
ax2.set_ylabel('Approval Rate (%)', color='#2980b9', fontsize=12)
ax2.plot(th_df['Threshold'], th_df['Approval_Rate_%'],
         color='#2980b9', marker='s', linewidth=2, label='Approval Rate')
ax2.tick_params(axis='y', labelcolor='#2980b9')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')

plt.title('Trade-off: Bad Rate vs Approval Rate theo Threshold', fontsize=13)
plt.grid(True, alpha=0.4)
plt.tight_layout()
plt.savefig('threshold_tradeoff.png', dpi=150)
plt.show()


# ============================================================
# EXPORT KẾT QUẢ
# ============================================================
ab_results.to_excel('ab_testing_results.xlsx', index=False)
th_df.to_excel('threshold_analysis.xlsx', index=False)
psi_results.to_excel('psi_results.xlsx', index=False)

print("\nExport hoàn tất:")
print("  ab_testing_results.xlsx  — kết quả mô phỏng Champion vs Challenger")
print("  threshold_analysis.xlsx  — so sánh các mức threshold")
print("  psi_results.xlsx         — kết quả PSI monitoring")
print("  vintage_analysis.png")
print("  risk_segmentation.png")
print("  ab_test_results.png")
print("  threshold_tradeoff.png")
