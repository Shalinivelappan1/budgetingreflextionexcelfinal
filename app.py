import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Smart Budget & Resilience Tracker",
    page_icon="💰",
    layout="centered"
)

st.title("💰 Smart Budget & Resilience Tracker")
st.caption("Student-safe budgeting • Scenario awareness • Structural alignment")

# ==================================================
# FUNCTIONS
# ==================================================
def calculate_stress_test_score(expenses, income, normal_savings, shocked_savings):
    score = 0

    # Coverage
    score += 40 if income >= expenses else 25 if income >= 0.9 * expenses else 10

    # Savings sign
    score += 30 if shocked_savings > 0 else 15 if shocked_savings == 0 else 0

    # Shock absorption
    if normal_savings > 0:
        ratio = shocked_savings / normal_savings
        score += 30 if ratio >= 0.75 else 20 if ratio >= 0.5 else 10 if ratio >= 0.25 else 5
    else:
        score += 5

    return round(score)


def get_resilience_grade(score):
    return "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"


def calculate_ctc_alignment_score(fixed_pay_monthly, needs, variable_ratio):
    score = 0

    # Fixed pay vs needs (60 points)
    if fixed_pay_monthly >= needs:
        score += 60
    elif fixed_pay_monthly >= 0.8 * needs:
        score += 45
    elif fixed_pay_monthly >= 0.6 * needs:
        score += 30
    else:
        score += 10

    # Variable dependence (40 points)
    if variable_ratio <= 0.2:
        score += 40
    elif variable_ratio <= 0.35:
        score += 30
    elif variable_ratio <= 0.5:
        score += 20
    else:
        score += 10

    return score


def generate_excel(summary_df, expenses_df, reflection_df, ctc_df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        expenses_df.to_excel(writer, sheet_name="Expenses", index=False)

        # ---- CTC Sheet + Pie ----
        ctc_df.to_excel(writer, sheet_name="CTC_Structure", index=False)
        ws = writer.sheets["CTC_Structure"]

        if ctc_df["Amount"].sum() > 0:
            chart = workbook.add_chart({"type": "pie"})
            chart.add_series({
                "categories": "=CTC_Structure!A2:A4",
                "values": "=CTC_Structure!B2:B4",
                "data_labels": {"percentage": True}
            })
            chart.set_title({"name": "CTC Composition"})
            ws.insert_chart("D2", chart)

        reflection_df.to_excel(writer, sheet_name="Reflection", index=False)

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
    st.subheader("💸 Monthly Budget")

    income = st.number_input("Monthly Income (₹)", min_value=0, step=1000)

    categories = [
        "Housing (Rent / EMI)",
        "Food",
        "Transport",
        "Utilities",
        "Lifestyle & Entertainment",
        "Others"
    ]

    expenses = {c: st.number_input(c, min_value=0, step=500) for c in categories}

    df_exp = pd.DataFrame({
        "Category": expenses.keys(),
        "Amount (₹)": expenses.values()
    })

    total_expenses = df_exp["Amount (₹)"].sum()
    normal_savings = income - total_expenses
    savings_rate = (normal_savings / income * 100) if income else 0

    st.metric("Monthly Savings", f"₹{normal_savings:,.0f}")
    st.metric("Savings Rate", f"{savings_rate:.1f}%")

    # -------- Expense Groups --------
    needs = expenses["Housing (Rent / EMI)"] + expenses["Food"] + expenses["Utilities"]
    wants = expenses["Lifestyle & Entertainment"]
    others = total_expenses - needs - wants

    # ==================================================
    # SCENARIO SHOCKS
    # ==================================================
    st.subheader("⚡ Scenario Shocks")

    bonus_shock = st.checkbox("❌ Bonus / Variable Pay NOT paid")
    tax_shock = st.checkbox("📈 Income Tax increases")

    shocked_income = income
    if bonus_shock:
        shocked_income -= 0.10 * income
    if tax_shock:
        shocked_income -= 0.05 * income

    shocked_savings = shocked_income - total_expenses

    # ==================================================
    # PIE CHARTS
    # ==================================================
    st.subheader("📊 Visual Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Expenses: Needs / Wants / Others**")
        values = [needs, wants, others]
        if sum(values) > 0:
            fig, ax = plt.subplots()
            ax.pie(values, labels=["Needs", "Wants", "Others"], autopct="%1.0f%%")
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.info("Enter expenses to view chart.")

    with col2:
        st.markdown("**Income Allocation (After Shock)**")
        exp_part = min(total_expenses, shocked_income)
        sav_part = max(shocked_income - total_expenses, 0)
        if exp_part + sav_part > 0:
            fig, ax = plt.subplots()
            ax.pie([exp_part, sav_part], labels=["Expenses", "Savings"], autopct="%1.0f%%")
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.info("Income too low to show allocation.")

    # ==================================================
    # STRESS TEST
    # ==================================================
    normal_stress = calculate_stress_test_score(
        total_expenses, income, normal_savings, normal_savings
    )
    shocked_stress = calculate_stress_test_score(
        total_expenses, shocked_income, normal_savings, shocked_savings
    )

    normal_grade = get_resilience_grade(normal_stress)
    shocked_grade = get_resilience_grade(shocked_stress)

    resilience_loss = (
        (normal_stress - shocked_stress) / normal_stress * 100
        if normal_stress > 0 else 0
    )

    st.subheader("📊 Normal vs Shocked")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Normal Savings", f"₹{normal_savings:,.0f}")
        st.metric("Stress Score", normal_stress)
        st.metric("Grade", normal_grade)

    with c2:
        st.metric("Shocked Savings", f"₹{shocked_savings:,.0f}",
                  delta=f"₹{shocked_savings - normal_savings:,.0f}")
        st.metric("Stress Score", shocked_stress,
                  delta=shocked_stress - normal_stress)
        st.metric("Grade", shocked_grade)

    if resilience_loss <= 10:
        st.success(f"🟢 Resilience Loss: {resilience_loss:.1f}%")
    elif resilience_loss <= 30:
        st.warning(f"🟡 Resilience Loss: {resilience_loss:.1f}%")
    else:
        st.error(f"🔴 Resilience Loss: {resilience_loss:.1f}%")

    # ==================================================
    # CTC ALIGNMENT (DESCRIPTIVE)
    # ==================================================
    st.subheader("🏢 CTC Component Alignment (Annual)")

    basic = st.number_input("Basic Pay (Annual ₹)", 0)
    hra = st.number_input("HRA (Annual ₹)", 0)
    allowance = st.number_input("Special Allowance (Annual ₹)", 0)
    variable_pay = st.number_input("Variable Pay (Annual ₹)", 0)
    pf = st.number_input("PF + Tax (Annual ₹)", 0)

    fixed_pay_annual = basic + hra + allowance
    fixed_pay_monthly = fixed_pay_annual / 12
    variable_ratio = (
        variable_pay / (fixed_pay_annual + variable_pay)
        if (fixed_pay_annual + variable_pay) > 0 else 0
    )

    ctc_alignment_score = calculate_ctc_alignment_score(
        fixed_pay_monthly, needs, variable_ratio
    )

    st.metric("CTC–Budget Alignment Score", f"{ctc_alignment_score} / 100")

    if fixed_pay_monthly < needs:
        st.error("🚨 Fixed pay does NOT cover essential monthly expenses.")
    else:
        st.success("✅ Fixed pay covers essential monthly expenses.")

# ==================================================
# TAB 2 — REFLECTION & EXPORT
# ==================================================
with tab2:
    st.subheader("🧠 Reflection")

    r1 = st.text_area("1️⃣ What surprised you most about your spending pattern?")
    r2 = st.text_area("2️⃣ Which expense would you reduce and why?")
    r3 = st.text_area("3️⃣ How did the income shock change your thinking?")
    r4 = st.text_area("4️⃣ One financial habit you want to change.")

    if st.button("⬇️ Download Excel Submission"):
        summary_df = pd.DataFrame({
            "Metric": [
                "Monthly Income",
                "Total Expenses",
                "Monthly Savings",
                "Savings Rate (%)",
                "Normal Stress Score",
                "Shocked Stress Score",
                "Resilience Loss (%)",
                "CTC–Budget Alignment Score"
            ],
            "Value": [
                income,
                total_expenses,
                normal_savings,
                round(savings_rate, 1),
                normal_stress,
                shocked_stress,
                round(resilience_loss, 1),
                ctc_alignment_score
            ]
        })

        ctc_df = pd.DataFrame({
            "Component": ["Fixed Pay", "Variable Pay", "Deductions"],
            "Amount": [fixed_pay_annual, variable_pay, pf]
        })

        reflection_df = pd.DataFrame({
            "Reflection Response": [r1, r2, r3, r4]
        })

        excel = generate_excel(summary_df, df_exp, reflection_df, ctc_df)

        st.download_button(
            "📥 Download Excel File",
            excel,
            file_name="Budget_Resilience_Submission.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
