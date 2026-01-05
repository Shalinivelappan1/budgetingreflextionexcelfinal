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
st.caption("Simple • Intuitive • Classroom-safe")

# ==================================================
# SCORING FUNCTIONS
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


# ==================================================
# EXCEL EXPORT
# ==================================================
def generate_excel(summary_df, expenses_df, reflection_df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        expenses_df.to_excel(writer, sheet_name="Expenses", index=False)
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
       overUtilities",
        "Lifestyle & Entertainment",
        "Others"
    ]

    expenses = {
        c: st.number_input(c, min_value=0, step=500)
        for c in categories
    }

    df_exp = pd.DataFrame({
        "Category": expenses.keys(),
        "Amount (₹)": expenses.values()
    })

    total_expenses = df_exp["Amount (₹)"].sum()
    normal_savings = income - total_expenses
    savings_rate = (normal_savings / income * 100) if income else 0

    st.metric("Monthly Savings", f"₹{normal_savings:,.0f}")
    st.metric("Savings Rate", f"{savings_rate:.1f}%")

    # =============================
    # Scenario Shocks (SIMPLE)
    # =============================
    st.subheader("⚡ Scenario Shocks")

    bonus_shock = st.checkbox("❌ Bonus / Variable Pay NOT paid")
    tax_shock = st.checkbox("📈 Income Tax increases by 20%")

    # Assume variable pay is part of income (approx 10%)
    estimated_variable = 0.10 * income

    shocked_income = income
    if bonus_shock:
        shocked_income -= estimated_variable
    if tax_shock:
        shocked_income -= 0.05 * income  # simple tax shock

    shocked_savings = shocked_income - total_expenses

    # =============================
    # Stress Scores
    # =============================
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

    # =============================
    # DISPLAY
    # =============================
    st.subheader("📊 Normal vs Shocked (Side-by-Side)")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Normal**")
        st.metric("Income", f"₹{income:,.0f}")
        st.metric("Savings", f"₹{normal_savings:,.0f}")
        st.metric("Stress Score", normal_stress)
        st.metric("Grade", normal_grade)

    with c2:
        st.markdown("**After Shock**")
        st.metric(
            "Income",
            f"₹{shocked_income:,.0f}",
            delta=f"₹{shocked_income - income:,.0f}"
        )
        st.metric(
            "Savings",
            f"₹{shocked_savings:,.0f}",
            delta=f"₹{shocked_savings - normal_savings:,.0f}"
        )
        st.metric(
            "Stress Score",
            shocked_stress,
            delta=shocked_stress - normal_stress
        )
        st.metric("Grade", shocked_grade)

    st.subheader("📉 Resilience Loss")
    if resilience_loss <= 10:
        st.success(f"🟢 Resilience Loss: {resilience_loss:.1f}%")
    elif resilience_loss <= 30:
        st.warning(f"🟡 Resilience Loss: {resilience_loss:.1f}%")
    else:
        st.error(f"🔴 Resilience Loss: {resilience_loss:.1f}%")

# ==================================================
# TAB 2 — REFLECTION & DOWNLOAD
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
                "Income", "Expenses", "Savings",
                "Savings Rate (%)",
                "Normal Stress Score", "Shocked Stress Score",
                "Normal Grade", "Shocked Grade",
                "Resilience Loss (%)"
            ],
            "Value": [
                income, total_expenses, normal_savings,
                round(savings_rate, 1),
                normal_stress, shocked_stress,
                normal_grade, shocked_grade,
                round(resilience_loss, 1)
            ]
        })

        reflection_df = pd.DataFrame({
            "Response": [r1, r2, r3, r4]
        })

        excel = generate_excel(summary_df, df_exp, reflection_df)

        st.download_button(
            "📥 Download Excel File",
            excel,
            file_name="Budget_Resilience_Submission.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
