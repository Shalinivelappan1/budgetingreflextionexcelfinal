import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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
# SCORING FUNCTIONS
# ==================================================
def calculate_financial_health_score(savings_rate, expense_ratio, needs_pct, wants_pct):
    score = 0
    score += min((savings_rate / 20) * 40, 40)
    score += 30 if expense_ratio <= 70 else 15 if expense_ratio <= 85 else 5
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
    base = {
        "A": [
            "Maintain savings discipline and avoid lifestyle inflation.",
            "Increase long-term investments (PF, NPS, mutual funds).",
            "Build a 6-month emergency fund."
        ],
        "B": [
            "Increase savings to improve shock resilience.",
            "Reduce discretionary expenses.",
            "Avoid using variable pay for fixed expenses."
        ],
        "C": [
            "Cut lifestyle expenses immediately.",
            "Ensure fixed expenses are covered by fixed income.",
            "Do not rely on bonuses for essentials."
        ],
        "D": [
            "Urgently reduce fixed commitments.",
            "Stop relying on variable pay for necessities.",
            "Start emergency savings immediately."
        ]
    }

    recs = base[grade].copy()
    if expense_ratio > 85:
        recs.append("Expense-to-income ratio is critically high.")
    if savings_rate < 10:
        recs.append("Savings are too low. Target at least 10%.")
    if variable_ratio > 0.35:
        recs.append("High dependence on variable pay increases risk.")
    if fixed_coverage_ratio < 1:
        recs.append("Fixed income does not fully cover fixed needs.")

    return recs

# ==================================================
# EXCEL EXPORT (WITH PIE CHARTS)
# ==================================================
def generate_excel(
    income, total_expenses, savings, savings_rate, expense_ratio,
    budget_score, alignment_score, stress_score, resilience_grade,
    df_exp, needs_pct, wants_pct,
    fixed_pay, variable, deductions,
    recommendations, reflections
):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # -------- Budget Summary --------
        summary = pd.DataFrame({
            "Metric": [
                "Income", "Expenses", "Savings",
                "Savings Rate (%)", "Expense Ratio (%)",
                "Budget Score", "Alignment Score",
                "Stress-Test Score", "Resilience Grade"
            ],
            "Value": [
                income, total_expenses, savings,
                round(savings_rate, 2), round(expense_ratio, 2),
                budget_score, alignment_score,
                stress_score, resilience_grade
            ]
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)

        # -------- Expenses --------
        df_exp.to_excel(writer, sheet_name="Expenses", index=False)

        # -------- CTC Structure --------
        ctc_df = pd.DataFrame({
            "Component": ["Fixed Pay", "Variable Pay", "Deductions"],
            "Amount": [fixed_pay, variable, deductions]
        })
        ctc_df.to_excel(writer, sheet_name="CTC_Structure", index=False)
        ws1 = writer.sheets["CTC_Structure"]

        chart1 = workbook.add_chart({"type": "pie"})
        chart1.add_series({
            "categories": "=CTC_Structure!A2:A4",
            "values": "=CTC_Structure!B2:B4",
            "data_labels": {"percentage": True}
        })
        chart1.set_title({"name": "CTC Composition"})
        ws1.insert_chart("D2", chart1)

        # -------- Budget Allocation --------
        alloc_df = pd.DataFrame({
            "Category": ["Needs", "Wants", "Savings"],
            "Percentage": [needs_pct, wants_pct, savings_rate]
        })
        alloc_df.to_excel(writer, sheet_name="Budget_Allocation", index=False)
        ws2 = writer.sheets["Budget_Allocation"]

        chart2 = workbook.add_chart({"type": "pie"})
        chart2.add_series({
            "categories": "=Budget_Allocation!A2:A4",
            "values": "=Budget_Allocation!B2:B4",
            "data_labels": {"percentage": True}
        })
        chart2.set_title({"name": "Needs vs Wants vs Savings"})
        ws2.insert_chart("D2", chart2)

        # -------- Recommendations --------
        pd.DataFrame({"Recommendation": recommendations}).to_excel(
            writer, sheet_name="Recommendations", index=False
        )

        # -------- Reflection --------
        pd.DataFrame({"Response": reflections}).to_excel(
            writer, sheet_name="Reflection", index=False
        )

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
    income = st.number_input("Monthly Income (₹)", min_value=0, step=1000)

    categories = [
        "Housing (Rent / EMI)", "Food", "Transport",
        "Utilities", "Lifestyle & Entertainment", "Others"
    ]
    expenses = {c: st.number_input(c, min_value=0, step=500) for c in categories}
    df_exp = pd.DataFrame({"Category": expenses.keys(), "Amount": expenses.values()})

    total_expenses = df_exp["Amount"].sum()
    savings = income - total_expenses
    savings_rate = savings / income * 100 if income else 0
    expense_ratio = total_expenses / income * 100 if income else 0

    needs = df_exp[df_exp["Category"].isin(
        ["Housing (Rent / EMI)", "Food", "Utilities"]
    )]["Amount"].sum()
    wants = df_exp[df_exp["Category"] == "Lifestyle & Entertainment"]["Amount"].sum()

    needs_pct = needs / income * 100 if income else 0
    wants_pct = wants / income * 100 if income else 0

    st.subheader("📈 Budget Summary")
    st.metric("Income", f"₹{income:,.0f}")
    st.metric("Expenses", f"₹{total_expenses:,.0f}")
    st.metric("Savings", f"₹{savings:,.0f}")

    st.subheader("🏢 Salary Structure (Annual)")
    basic = st.number_input("Basic Pay", 0)
    hra = st.number_input("HRA", 0)
    allowance = st.number_input("Special Allowance", 0)
    variable = st.number_input("Variable Pay", 0)
    pf = st.number_input("Employee PF", 0)
    tax = st.number_input("Income Tax", 0)
    pt = st.number_input("Professional Tax", 0)

    fixed_pay = basic + hra + allowance
    gross = fixed_pay + variable
    deductions = pf + tax + pt

    st.subheader("🔄 Income vs Budget (Pie Charts)")

    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots()
        ax1.pie(
            [fixed_pay, variable, deductions],
            labels=["Fixed Pay", "Variable Pay", "Deductions"],
            autopct="%1.0f%%", startangle=90
        )
        ax1.axis("equal")
        st.pyplot(fig1)

    with col2:
        fig2, ax2 = plt.subplots()
        ax2.pie(
            [needs_pct, wants_pct, savings_rate],
            labels=["Needs", "Wants", "Savings"],
            autopct="%1.0f%%", startangle=90
        )
        ax2.axis("equal")
        st.pyplot(fig2)

    bonus_shock = st.checkbox("❌ Bonus NOT paid")
    tax_shock = st.checkbox("📈 Tax increases by 20%")

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

    variable_ratio = variable / gross if gross else 1
    fixed_coverage_ratio = fixed_pay / needs if needs else 0

    recommendations = get_policy_recommendations_by_grade(
        resilience_grade, expense_ratio, savings_rate,
        variable_ratio, fixed_coverage_ratio
    )

    st.subheader("🧮 Scores & Risk")
    st.metric("Budget Score", budget_score)
    st.metric("Alignment Score", alignment_score)
    st.metric("Stress-Test Score", stress_score)
    st.metric("Resilience Grade", resilience_grade)

    st.subheader("📌 Policy Recommendations")
    for r in recommendations:
        st.write("•", r)

# ==================================================
# TAB 2 — REFLECTION & EXPORT
# ==================================================
with tab2:
    r1 = st.text_area("What surprised you most about your spending?")
    r2 = st.text_area("Which expense would you reduce and why?")
    r3 = st.text_area("How did income structure affect risk?")
    r4 = st.text_area("What changed after the stress test?")

    if st.button("⬇️ Download Excel Submission"):
        excel = generate_excel(
            income, total_expenses, savings, savings_rate, expense_ratio,
            budget_score, alignment_score, stress_score, resilience_grade,
            df_exp, needs_pct, wants_pct,
            fixed_pay, variable, deductions,
            recommendations, [r1, r2, r3, r4]
        )

        st.download_button(
            "📥 Download Excel",
            excel,
            "Budget_Risk_Resilience.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
