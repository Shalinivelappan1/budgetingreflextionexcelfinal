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
st.caption("Developed by Prof.Shalini Velappan, IIM Trichy")

st.info(
    "ℹ️ Budgeting is done on a **monthly basis**. "
    "Salary (CTC) inputs are **annual** and converted to monthly for analysis."
)

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


def calculate_stress_test_score(total_expenses, take_home, normal_savings, shocked_savings):
    score = 0
    score += 40 if take_home >= total_expenses else 25 if take_home >= 0.9 * total_expenses else 10
    score += 30 if shocked_savings > 0 else 15 if shocked_savings == 0 else 0

    if normal_savings > 0:
        ratio = shocked_savings / normal_savings
        score += 30 if ratio >= 0.75 else 20 if ratio >= 0.5 else 10 if ratio >= 0.25 else 5
    else:
        score += 5
    return round(score)


def get_resilience_grade(score):
    return "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"


def suggest_fastest_resilience_fix(resilience_loss_pct, savings_rate, variable_ratio, fixed_coverage_ratio):
    if resilience_loss_pct <= 10:
        return "Maintain current discipline and avoid lifestyle inflation."
    if savings_rate < 10:
        return "Increase monthly savings slightly — this gives the fastest resilience gain."
    if variable_ratio > 0.35:
        return "Reduce dependence on variable pay for regular monthly expenses."
    if fixed_coverage_ratio < 1:
        return "Reduce fixed monthly expenses so they are covered by fixed income."
    return "Improve expense flexibility by reducing discretionary spending."

# ==================================================
# TABS
# ==================================================
tab1, tab2 = st.tabs(["📊 Dashboard", "🧠 Reflection & Submission"])

# ==================================================
# TAB 1 — DASHBOARD
# ==================================================
with tab1:
    st.subheader("💸 Monthly Budget")

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

    st.metric("Monthly Savings", f"₹{savings:,.0f}")
    st.metric("Savings Rate", f"{savings_rate:.1f}%")

    # ==================================================
    # SALARY STRUCTURE (ANNUAL → MONTHLY)
    # ==================================================
    st.subheader("🏢 Salary Structure (Annual CTC)")

    basic = st.number_input("Basic Pay (Annual)", 0)
    hra = st.number_input("HRA (Annual)", 0)
    allowance = st.number_input("Special Allowance (Annual)", 0)
    variable = st.number_input("Variable Pay (Annual)", 0)
    pf = st.number_input("Employee PF (Annual)", 0)
    tax = st.number_input("Income Tax (Annual)", 0)
    pt = st.number_input("Professional Tax (Annual)", 0)

    fixed_pay_annual = basic + hra + allowance
    gross_annual = fixed_pay_annual + variable
    deductions_annual = pf + tax + pt

    # ---- Convert to MONTHLY ----
    fixed_pay = fixed_pay_annual / 12
    variable_monthly = variable / 12
    gross = gross_annual / 12
    deductions = deductions_annual / 12

    normal_take_home = gross - deductions
    normal_savings = normal_take_home - total_expenses

    # ==================================================
    # PIE CHARTS
    # ==================================================
    st.subheader("🔄 Income Structure vs Budget Allocation")
    col1, col2 = st.columns(2)

    with col1:
        values = [fixed_pay, variable_monthly, deductions]
        if sum(values) > 0:
            fig, ax = plt.subplots()
            ax.pie(values, labels=["Fixed Pay", "Variable Pay", "Deductions"],
                   autopct="%1.0f%%", startangle=90)
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.info("Enter salary details to view chart.")

    with col2:
        values = [needs_pct, wants_pct, savings_rate]
        if sum(values) > 0:
            fig, ax = plt.subplots()
            ax.pie(values, labels=["Needs", "Wants", "Savings"],
                   autopct="%1.0f%%", startangle=90)
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.info("Enter income & expenses to view chart.")

    # ==================================================
    # SCENARIO SHOCKS (MONTHLY-CONSISTENT)
    # ==================================================
    st.subheader("⚡ Scenario Shocks")

    bonus_shock = st.checkbox("❌ Bonus / Variable Pay NOT paid")
    tax_shock = st.checkbox("📈 Income Tax increases by 20%")

    shocked_variable = 0 if bonus_shock else variable_monthly
    shocked_tax = (tax * 1.2) / 12 if tax_shock else tax / 12

    shocked_take_home = (fixed_pay + shocked_variable) - (pf / 12 + shocked_tax + pt / 12)
    shocked_savings = shocked_take_home - total_expenses

    # ==================================================
    # SCORES
    # ==================================================
    budget_score = calculate_financial_health_score(
        savings_rate, expense_ratio, needs_pct, wants_pct
    )

    alignment_score = calculate_ctc_budget_alignment_score(
        fixed_pay, variable_monthly, needs, savings, gross
    )

    normal_stress_score = calculate_stress_test_score(
        total_expenses, normal_take_home, normal_savings, normal_savings
    )

    shocked_stress_score = calculate_stress_test_score(
        total_expenses, shocked_take_home, normal_savings, shocked_savings
    )

    normal_grade = get_resilience_grade(normal_stress_score)
    shocked_grade = get_resilience_grade(shocked_stress_score)

    resilience_loss_pct = (
        (normal_stress_score - shocked_stress_score) / normal_stress_score * 100
        if normal_stress_score > 0 else 0
    )

    variable_ratio = variable_monthly / gross if gross else 1
    fixed_coverage_ratio = fixed_pay / needs if needs else 0

    fastest_fix = suggest_fastest_resilience_fix(
        resilience_loss_pct, savings_rate, variable_ratio, fixed_coverage_ratio
    )

    # ==================================================
    # DISPLAY RESULTS
    # ==================================================
    st.subheader("📊 Normal vs Shocked (Side-by-Side)")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Normal**")
        st.metric("Savings", f"₹{normal_savings:,.0f}")
        st.metric("Stress-Test Score", normal_stress_score)
        st.metric("Grade", normal_grade)

    with c2:
        st.markdown("**After Shock**")
        st.metric("Savings", f"₹{shocked_savings:,.0f}",
                  delta=f"₹{shocked_savings - normal_savings:,.0f}")
        st.metric("Stress-Test Score", shocked_stress_score,
                  delta=shocked_stress_score - normal_stress_score)
        st.metric("Grade", shocked_grade)

    st.subheader("📉 Resilience Loss")

    if resilience_loss_pct <= 10:
        st.success(f"🟢 Resilience Loss: {resilience_loss_pct:.1f}%")
    elif resilience_loss_pct <= 30:
        st.warning(f"🟡 Resilience Loss: {resilience_loss_pct:.1f}%")
    else:
        st.error(f"🔴 Resilience Loss: {resilience_loss_pct:.1f}%")

    st.subheader("🚀 Fastest Way to Improve Resilience")
    st.info(fastest_fix)

# ==================================================
# TAB 2 — REFLECTION
# ==================================================
with tab2:
    st.subheader("🧠 Reflection")

    r1 = st.text_area("1️⃣ What surprised you most about your spending pattern?")
    r2 = st.text_area("2️⃣ Which expense would you reduce to improve savings? Why?")
    r3 = st.text_area("3️⃣ Did your budget broadly follow the 30–30–20 rule? Explain.")
    r4 = st.text_area("4️⃣ How did your income structure affect financial risk?")
    r5 = st.text_area("5️⃣ One financial habit you want to change after this exercise.")
    r6 = st.text_area(
        "6️⃣ Scenario Reflection: After the income shock, what changed and what would you adjust?"
    )
    r7 = st.text_area(
        "7️⃣ Targeted Action Reflection: "
        f"{fastest_fix} How realistic is this change for you?"
    )
