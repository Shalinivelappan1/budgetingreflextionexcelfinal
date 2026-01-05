import streamlit as st
import pandas as pd
from io import BytesIO

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Smart Budget, Risk & Resilience Tracker",
    page_icon="💰",
    layout="centered"
)

st.title("💰 Smart Budget, Risk & Resilience Tracker")
st.caption("Finance × HR | India-focused | Risk-aware budgeting")

# ==================================================
# SCORING & LOGIC FUNCTIONS
# ==================================================
def calculate_financial_health_score(savings_rate, expense_ratio, needs_pct, wants_pct):
    score = 0
    score += min((savings_rate / 20) * 40, 40)

    if expense_ratio <= 70:
        score += 30
    elif expense_ratio <= 85:
        score += 15
    else:
        score += 5

    score += 10 if needs_pct <= 30 else 0
    score += 10 if wants_pct <= 30 else 0
    score += 10 if savings_rate >= 20 else 0
    return round(score)


def calculate_ctc_budget_alignment_score(fixed_pay, variable_pay, needs, savings, gross):
    score = 0
    coverage = fixed_pay / needs if needs else 1

    score += 40 if coverage >= 1.2 else 30 if coverage >= 1 else 15 if coverage >= 0.8 else 5

    var_ratio = variable_pay / gross if gross else 1
    score += 30 if var_ratio <= 0.2 else 20 if var_ratio <= 0.35 else 10 if var_ratio <= 0.5 else 5

    sav_ratio = savings / gross if gross else 0
    score += 30 if sav_ratio >= 0.25 else 20 if sav_ratio >= 0.15 else 10 if sav_ratio >= 0.1 else 5

    return round(score)


def calculate_stress_test_score(total_expenses, shocked_take_home, normal_savings, shocked_savings):
    score = 0

    score += 40 if shocked_take_home >= total_expenses else 25 if shocked_take_home >= 0.9 * total_expenses else 10
    score += 30 if shocked_savings > 0 else 15 if shocked_savings == 0 else 0

    if normal_savings > 0:
        ratio = shocked_savings / normal_savings
        score += 30 if ratio >= 0.75 else 20 if ratio >= 0.5 else 10 if ratio >= 0.25 else 5
    else:
        score += 5

    return round(score)


def get_resilience_grade(score):
    return "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"


def get_policy_recommendations_by_grade(
    grade, expense_ratio, savings_rate, variable_ratio, fixed_coverage_ratio
):
    recs = []

    base = {
        "A": [
            "Maintain your savings discipline and continue tracking expenses.",
            "Increase long-term investments (PF, NPS, mutual funds).",
            "Build a 6-month emergency fund."
        ],
        "B": [
            "Increase savings slightly to improve shock resilience.",
            "Reduce discretionary spending where possible.",
            "Avoid using variable pay for fixed expenses."
        ],
        "C": [
            "Reduce lifestyle and discretionary expenses immediately.",
            "Ensure fixed expenses are covered by fixed income.",
            "Avoid reliance on bonuses for regular spending."
        ],
        "D": [
            "Urgently reduce fixed commitments (rent, EMIs, subscriptions).",
            "Stop relying on variable pay for essentials.",
            "Start building an emergency fund, even with small amounts."
        ]
    }

    recs.extend(base[grade])

    if expense_ratio > 85:
        recs.append("Expense-to-income ratio is very high. Immediate expense control is needed.")
    if savings_rate < 10:
        recs.append("Savings are critically low. Aim for at least 10% initially.")
    if variable_ratio > 0.35:
        recs.append("High dependence on variable pay increases risk. Build buffers.")
    if fixed_coverage_ratio < 1:
        recs.append("Fixed income does not fully cover fixed needs — structural fragility exists.")

    return recs

# ==================================================
# EXCEL EXPORT
# ==================================================
def generate_excel(data):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, df in data.items():
            df.to_excel(writer, sheet_name=name, index=False)
    output.seek(0)
    return output

# ==================================================
# TABS
# ==================================================
tab1, tab2 = st.tabs(["📊 Dashboard", "🧠 Reflection & Submission"])

# ==================================================
# TAB 1 — DASHBOARD
# ==================================================
with tab1:
    period = st.radio("Budget Period", ["Monthly", "Yearly"], horizontal=True)
    income = st.number_input(f"{period} Income (₹)", min_value=0, step=1000)

    categories = ["Housing (Rent / EMI)", "Food", "Transport", "Utilities", "Lifestyle & Entertainment", "Others"]
    expenses = {c: st.number_input(c, min_value=0, step=500) for c in categories}
    df_exp = pd.DataFrame({"Category": expenses.keys(), "Amount": expenses.values()})

    total_expenses = df_exp["Amount"].sum()
    savings = income - total_expenses
    savings_rate = savings / income * 100 if income else 0
    expense_ratio = total_expenses / income * 100 if income else 0

    needs = df_exp[df_exp["Category"].isin(["Housing (Rent / EMI)", "Food", "Utilities"])]["Amount"].sum()
    wants = df_exp[df_exp["Category"] == "Lifestyle & Entertainment"]["Amount"].sum()
    needs_pct = needs / income * 100 if income else 0
    wants_pct = wants / income * 100 if income else 0

    st.subheader("📈 Budget Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Income", f"₹{income:,.0f}")
    c2.metric("Expenses", f"₹{total_expenses:,.0f}")
    c3.metric("Savings", f"₹{savings:,.0f}")

    st.subheader("🏢 Salary Structure (Annual)")
    basic = st.number_input("Basic Pay", 0, step=10000)
    hra = st.number_input("HRA", 0, step=10000)
    allowance = st.number_input("Special Allowance", 0, step=10000)
    variable = st.number_input("Variable Pay", 0, step=10000)
    pf = st.number_input("Employee PF", 0, step=5000)
    tax = st.number_input("Income Tax", 0, step=10000)
    pt = st.number_input("Professional Tax", 0, step=500)

    fixed_pay = basic + hra + allowance
    gross = fixed_pay + variable
    deductions = pf + tax + pt
    take_home = gross - deductions

    bonus_shock = st.checkbox("❌ Bonus / Variable Pay NOT paid")
    tax_shock = st.checkbox("📈 Income Tax increases by 20%")

    shocked_variable = 0 if bonus_shock else variable
    shocked_tax = tax * 1.2 if tax_shock else tax
    shocked_take_home = (fixed_pay + shocked_variable) - (pf + shocked_tax + pt)
    shocked_savings = shocked_take_home - total_expenses

    alignment_score = calculate_ctc_budget_alignment_score(
        fixed_pay, variable, needs, savings, gross
    )

    stress_score = calculate_stress_test_score(
        total_expenses, shocked_take_home, savings, shocked_savings
    )

    resilience_grade = get_resilience_grade(stress_score)

    budget_score = calculate_financial_health_score(
        savings_rate, expense_ratio, needs_pct, wants_pct
    )

    overall_score = round(0.6 * budget_score + 0.4 * alignment_score)

    variable_ratio = variable / gross if gross else 1
    fixed_coverage_ratio = fixed_pay / needs if needs else 0

    recommendations = get_policy_recommendations_by_grade(
        resilience_grade, expense_ratio, savings_rate, variable_ratio, fixed_coverage_ratio
    )

    st.subheader("🧮 Scores & Risk")
    st.metric("Overall Financial Health Score", overall_score)
    st.metric("Stress-Test Score", stress_score)
    st.metric("Resilience Grade", resilience_grade)

    st.subheader("📌 Policy Recommendations")
    for r in recommendations:
        st.write("•", r)

# ==================================================
# TAB 2 — REFLECTION & EXPORT
# ==================================================
with tab2:
    st.subheader("📊 Confidence Check")
    cb = st.slider("Confidence BEFORE", 0, 10, 5)
    ca = st.slider("Confidence AFTER", 0, 10, cb)
    st.bar_chart(pd.DataFrame({"Confidence": [cb, ca]}, index=["Before", "After"]))

    st.subheader("🧠 Reflection")
    r1 = st.text_area("What surprised you most about your spending?")
    r2 = st.text_area("Which expense would you reduce and why?")
    r3 = st.text_area("Did your budget follow the 30–30–20 rule?")
    r4 = st.text_area("What habit will you change?")
    r5 = st.text_area("How did income structure affect risk under shock?")

    name = st.text_input("Student Name")
    course = st.text_input("Course / Section")

    if st.button("⬇️ Download Excel Submission"):
        excel_data = {
            "Budget_Summary": pd.DataFrame({
                "Metric": ["Income", "Expenses", "Savings", "Overall Score", "Stress Score", "Grade"],
                "Value": [income, total_expenses, savings, overall_score, stress_score, resilience_grade]
            }),
            "Expenses": df_exp,
            "Policy_Recommendations": pd.DataFrame({"Recommendation": recommendations}),
            "Reflection": pd.DataFrame({
                "Question": ["Q1", "Q2", "Q3", "Q4", "Q5"],
                "Response": [r1, r2, r3, r4, r5]
            })
        }
        file = generate_excel(excel_data)

        st.download_button(
            "📥 Download Excel",
            file,
            f"{name.replace(' ', '_')}_Budget_Resilience.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
