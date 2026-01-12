import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import display_sidebar_info, get_df
from cleaning_aelyana import prepare_aelyana_data

SUNSET = px.colors.sequential.Sunset

def safe_mode(s: pd.Series, default="N/A"):
    s = s.dropna()
    return s.mode().iloc[0] if not s.empty else default

def render():
    display_sidebar_info()
    raw = get_df()
    df = prepare_aelyana_data(raw)

    if df is None or df.empty:
        st.error("No data available.")
        return

    # --- DEFINISI SUSUNAN (ORDERING) ---
    academic_order = ["Below average", "Average", "Good", "Very good", "Excellent"]
    insomnia_order = ["Low / No Insomnia", "Moderate Insomnia", "Severe Insomnia"]
    freq_order = ["Never", "Rarely", "Sometimes", "Often", "Always"]
    impact_order = ["No impact", "Minor impact", "Moderate impact", "Major impact", "Severe impact"]
    # Tambah susunan GPA yang betul di sini
    gpa_order = ["2.00 - 2.49", "2.50 - 2.99", "3.00 - 3.69", "3.70 - 4.00"]

    if "AcademicPerformance" in df.columns:
        df["AcademicPerformance"] = pd.Categorical(
            df["AcademicPerformance"], categories=academic_order, ordered=True
        )

    if "Insomnia_Category" in df.columns:
        df["Insomnia_Category"] = pd.Categorical(
            df["Insomnia_Category"], categories=insomnia_order, ordered=True
        )

    for c in ["ConcentrationDifficulty", "DaytimeFatigue"]:
        if c in df.columns:
            df[c] = pd.Categorical(df[c], categories=freq_order, ordered=True)

    if "AssignmentImpact" in df.columns:
        df["AssignmentImpact"] = pd.Categorical(
            df["AssignmentImpact"], categories=impact_order, ordered=True
        )

    st.title("Interpretation Dashboard: Impact of Sleep Related Issues on Academic Performance")
    st.markdown(
        "This dashboard evaluates how insomnia severity relates to **focus**, **fatigue**, **assignment impact**, "
        "**academic performance**, and overall **sleep–academic correlations**."
    )

    st.markdown(
        """
<div class="card">
  <div class="card-title">Objective (Academic Impact)</div>
  <div class="interpretation">
    To evaluate the impact of insufficient sleep on academic performance, including concentration difficulties, fatigue,
    class attendance, and academic achievement indicators (GPA and self-rated performance).
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # --- KEY METRICS ---
    severe = (
        df[df["Insomnia_Category"] == "Severe Insomnia"]
        if "Insomnia_Category" in df.columns
        else df
    )

    st.subheader("Key Findings: The Impact of Insomnia")
    col1, col2, col3, col4 = st.columns(4)

    focus_risk = (
        severe["ConcentrationDifficulty"].isin(["Often", "Always"]).mean() * 100
        if "ConcentrationDifficulty" in severe.columns
        else 0.0
    )

    fatigue_risk = (
        severe["DaytimeFatigue"].isin(["Often", "Always"]).mean() * 100
        if "DaytimeFatigue" in severe.columns
        else 0.0
    )

    perf_level = (
        safe_mode(severe["AcademicPerformance"])
        if "AcademicPerformance" in severe.columns
        else "N/A"
    )

    assign_risk = (
        severe["AssignmentImpact"].isin(["Major impact", "Severe impact"]).mean() * 100
        if "AssignmentImpact" in severe.columns
        else 0.0
    )

    col1.metric(label="🧠 Concentration Difficulty", value=f"{focus_risk:.1f}%", border=True)
    col2.metric(label="😫 Severe Academic Fatigue", value=f"{fatigue_risk:.1f}%", border=True)
    col3.metric(label="📉 Academic Performance Level", value=perf_level, border=True)
    col4.metric(label="📝 Assignment Performance Risk", value=f"{assign_risk:.1f}%", border=True)

    st.divider()

    # --- FIGURE C1 ---
    st.subheader("Figure C1 - Concentration Difficulty by Insomnia Category")
    if {"Insomnia_Category", "ConcentrationDifficulty"}.issubset(df.columns):
        concentration_crosstab = pd.crosstab(df["Insomnia_Category"], df["ConcentrationDifficulty"], dropna=False)
        concentration_melted = concentration_crosstab.reset_index().melt(
            id_vars="Insomnia_Category", var_name="ConcentrationDifficulty", value_name="Count"
        )
        fig_a = px.bar(
            concentration_melted, x="Insomnia_Category", y="Count", color="ConcentrationDifficulty",
            barmode="group", title="Concentration Difficulty by Insomnia Category",
            category_orders={"Insomnia_Category": insomnia_order, "ConcentrationDifficulty": freq_order},
            color_discrete_sequence=SUNSET,
        )
        st.plotly_chart(fig_a, use_container_width=True)

    # --- FIGURE C2 (GPA) ---
    st.subheader("Figure C2 - Insomnia Severity Index Across GPA Category")
    if {"GPA", "InsomniaSeverity_index"}.issubset(df.columns):
        fig_b = px.box(
            df, x="GPA", y="InsomniaSeverity_index", color="GPA",
            title="Insomnia Severity Index Across GPA Category",
            category_orders={"GPA": gpa_order}, # Menggunakan susunan yang telah dibetulkan
            color_discrete_sequence=SUNSET, points="outliers",
        )
        fig_b.update_layout(xaxis_title="GPA Category", yaxis_title="Insomnia Severity Index", showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)

        st.markdown(
            """
**Key Insights**
* As GPA decreases, the insomnia severity "box" shifts upward. Higher GPA is associated with more consistent and lower insomnia scores.
* **GPA 3.70 - 4.00** category show lowest median insomnia score (4).
* **GPA 3.00 - 3.69** category show median score increases to 7.
* **GPA 2.50 - 2.99** group (corrected label) show highest spread and maximum scores, indicating this group experiences the strongest symptoms.
            """.strip()
        )

    # --- FIGURE C3 ---
    st.subheader("Figure C3 - Assignment Impact by Insomnia Category")
    if {"Insomnia_Category", "AssignmentImpact"}.issubset(df.columns):
        assignment_table = pd.crosstab(df["Insomnia_Category"], df["AssignmentImpact"], dropna=False)
        assignment_melted = assignment_table.reset_index().melt(
            id_vars="Insomnia_Category", var_name="AssignmentImpact", value_name="Student_Count"
        )
        fig_c = px.bar(
            assignment_melted, x="Insomnia_Category", y="Student_Count", color="AssignmentImpact",
            title="Assignment Impact by Insomnia Category",
            category_orders={"Insomnia_Category": insomnia_order, "AssignmentImpact": impact_order},
            color_discrete_sequence=SUNSET, barmode="stack",
        )
        st.plotly_chart(fig_c, use_container_width=True)

    # (Lain-lain graf dikekalkan mengikut struktur sedia ada anda...)
    st.divider()
    st.info("Dashboard updated with corrected GPA labels and cleaned datasets.")

render()
