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
st.caption("Budgeting • Scenario risk • Income structure alignment")

# ==================================================
# FUNCTIONS
# ==================================================
def calculate_stress_test_score(expenses, income, normal_savings, shocked_savings):
    score = 0
    score += 40 if income >= expenses else 25 if income >= 0.9 * expenses else 10
    score += 30 if shocked_savings > 0 else 15 if shocked_savings == 0 else 0

    if normal_savings > 0:
        ratio = shocked_savings / normal_savings
        score += 30 if ratio >= 0.75 else 20 if ratio >= 0.5 else 10 if ratio >= 0.25 else 5
    else:
        score += 5

    return round(score)


def get_resilience_grade(score):
    return "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"


def calculate_ctc_alignment_score(
    fixed_pay_monthly,
    needs,
    variable_ratio,
    savings_rate
):
    score = 0

    # 1️⃣ Fixed pay covers needs (50)
    if fixed_pay_monthly >= needs:
        score += 50
    elif fixed_pay_monthly >= 0.8 * needs:
        score += 35
    elif fixed_pay_monthly >= 0.6 * needs:
        score += 20
    else:
        score += 5

    # 2️⃣ Variable dependence (30)
    if variable_ratio <= 0.2:
        score += 30
    elif variable_ratio <= 0.35:
        score += 20
    elif variable_ratio <= 0.5:
        score += 10
    else:
        score += 5

    # 3️⃣ Savings discipline (20)
    if savings_rate >= 20:
        score += 20
    elif savings_rate >= 10:
        score += 10
    else:
        score += 0

    return score


def generate_excel(summary_df, expenses_df, reflection_df, ctc_df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        expenses_df.to_excel(writer, sheet_name="Expenses", index=False)

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
        if needs + wants + others > 0:
            fig, ax = plt.subplots()
            ax.pie([needs, wants, others],
                   labels=["Needs", "Wants", "Others"],
                   autopct="%1.0f%%")
            ax.axis("equal")
            st.pyplot(fig)

    with col2:
        exp_part = min(total_expenses, shocked_income)
        sav_part = max(shocked_income - total_expenses, 0)
        if exp_part + sav_part > 0:
            fig, ax = plt.subplots()
            ax.pie([exp_part, sav_part],
                   labels=["Expenses", "Savings"],
                   autopct="%1.0f%%")
            ax.axis("equal")
            st.pyplot(fig)

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

    # ==================================================
    # CTC ALIGNMENT — MONTHLY INPUTS
    # ==================================================
    st.subheader("🏢 CTC Component Alignment (Monthly)")

    basic_m = st.number_input("Basic Pay (Monthly ₹)", 0, step=1000)
    hra_m = st.number_input("HRA (Monthly ₹)", 0, step=1000)
    allowance_m = st.number_input("Special Allowance (Monthly ₹)", 0, step=1000)
    variable_m = st.number_input("Variable Pay (Monthly ₹)", 0, step=1000)
    deductions_m = st.number_input("PF + Tax (Monthly ₹)", 0, step=1000)

    fixed_pay_monthly = basic_m + hra_m + allowance_m

    fixed_pay_annual = fixed_pay_monthly * 12
    variable_pay_annual = variable_m * 12
    deductions_annual = deductions_m * 12

    variable_ratio = (
        variable_pay_annual / (fixed_pay_annual + variable_pay_annual)
        if (fixed_pay_annual + variable_pay_annual) > 0 else 0
    )

    ctc_alignment_score = calculate_ctc_alignment_score(
        fixed_pay_monthly,
        needs,
        variable_ratio,
        savings_rate
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

    r1 = st.text_area("1️⃣ What surprised you most about your spending?")
    r2 = st.text_area("2️⃣ Which expense would you reduce and why?")
    r3 = st.text_area("3️⃣ How did the scenario shock change your thinking?")
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
            "Amount": [fixed_pay_annual, variable_pay_annual, deductions_annual]
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
