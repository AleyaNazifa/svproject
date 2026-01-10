import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import display_sidebar_info, get_df
from cleaning_aelyana import prepare_aelyana_data

SUNSET = px.colors.sequential.Sunset  # use real palette (not string)

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

    academic_order = ["Below average", "Average", "Good", "Very good", "Excellent"]
    insomnia_order = ["Low / No Insomnia", "Moderate Insomnia", "Severe Insomnia"]
    freq_order = ["Never", "Rarely", "Sometimes", "Often", "Always"]
    impact_order = ["No impact", "Minor impact", "Moderate impact", "Major impact", "Severe impact"]

    # Categorical for order stability
    if "AcademicPerformance" in df.columns:
        df["AcademicPerformance"] = pd.Categorical(df["AcademicPerformance"], categories=academic_order, ordered=True)
    if "Insomnia_Category" in df.columns:
        df["Insomnia_Category"] = pd.Categorical(df["Insomnia_Category"], categories=insomnia_order, ordered=True)
    for c in ["ConcentrationDifficulty", "DaytimeFatigue"]:
        if c in df.columns:
            df[c] = pd.Categorical(df[c], categories=freq_order, ordered=True)
    if "AssignmentImpact" in df.columns:
        df["AssignmentImpact"] = pd.Categorical(df["AssignmentImpact"], categories=impact_order, ordered=True)

    st.title("Interpretation Dashboard: Academic Impact of Sleep-Related Issues (Aelyana)")
    st.markdown(
        "This page evaluates how insomnia severity relates to **focus**, **fatigue**, **assignments**, **performance**, "
        "and overall **sleep–academic correlations**."
    )

    # Objective: per-page
    st.markdown(
        """
<div class="card">
  <div class="card-title">Objective (Academic Impact)</div>
  <div class="interpretation">
    To evaluate the impact of insomnia severity on academic outcomes by visualising:
    (a) concentration difficulty, (b) ISI across GPA categories, (c) assignment impact,
    (d) daytime fatigue, (e) academic performance distribution, and (f) correlations across key academic/sleep indicators.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # -----------------------------
    # Metrics (severe insomnia group)
    # -----------------------------
    severe = df[df["Insomnia_Category"] == "Severe Insomnia"] if "Insomnia_Category" in df.columns else df

    st.subheader("Key Findings: The Impact of Insomnia")
    col1, col2, col3, col4 = st.columns(4)

    focus_risk = severe["ConcentrationDifficulty"].isin(["Often", "Always"]).mean() * 100 if "ConcentrationDifficulty" in severe.columns else 0.0
    fatigue_risk = severe["DaytimeFatigue"].isin(["Often", "Always"]).mean() * 100 if "DaytimeFatigue" in severe.columns else 0.0
    perf_level = safe_mode(severe["AcademicPerformance"]) if "AcademicPerformance" in severe.columns else "N/A"
    assign_risk = severe["AssignmentImpact"].isin(["Major impact", "Severe impact"]).mean() * 100 if "AssignmentImpact" in severe.columns else 0.0

    col1.metric("🧠 Concentration Difficulty", f"{focus_risk:.1f}%", help="Severe insomnia students reporting Often/Always concentration difficulty.", border=True)
    col2.metric("😫 Severe Academic Fatigue", f"{fatigue_risk:.1f}%", help="Severe insomnia students reporting Often/Always fatigue.", border=True)
    col3.metric("📉 Most Common Academic Performance", perf_level, help="Most frequent self-rated academic performance among severe insomnia group.", border=True)
    col4.metric("📝 Assignment Performance Risk", f"{assign_risk:.1f}%", help="Severe insomnia students reporting Major/Severe assignment impact.", border=True)

    st.divider()

    # -----------------------------
    # a) Concentration Difficulty
    # -----------------------------
    st.subheader("a) Concentration Difficulty by Insomnia Category")
    if {"Insomnia_Category", "ConcentrationDifficulty"}.issubset(df.columns):
        tab = pd.crosstab(df["Insomnia_Category"], df["ConcentrationDifficulty"], dropna=False)
        melted = tab.reset_index().melt(id_vars="Insomnia_Category", var_name="ConcentrationDifficulty", value_name="Count")

        fig = px.bar(
            melted,
            x="Insomnia_Category",
            y="Count",
            color="ConcentrationDifficulty",
            barmode="group",
            title="Concentration Difficulty by Insomnia Category",
            category_orders={"Insomnia_Category": insomnia_order, "ConcentrationDifficulty": freq_order},
            color_discrete_sequence=SUNSET,
            labels={"Count": "Number of Students", "Insomnia_Category": "Insomnia Level"},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
**Key Insights**
* Most students have moderate insomnia, with "Sometimes" being the most common focus problem.
* Low / No Insomnia students rarely report serious disruptions ("Often"/"Always").
* Severe insomnia shows a sharp shift toward "Often" and "Always", indicating higher cognitive disruption.

**Conclusion**
* There is a direct relationship between insomnia severity and difficulty maintaining focus, increasing academic risk through persistent attention impairment.
        """.strip())
        st.divider()
    else:
        st.warning("Missing columns for Chart a).")

    # -----------------------------
    # b) ISI Across GPA
    # -----------------------------
    st.subheader("b) Insomnia Severity Index Across GPA Categories")
    if {"GPA", "InsomniaSeverity_index"}.issubset(df.columns):
        gpa_order = sorted(df["GPA"].dropna().unique().tolist())

        fig = px.box(
            df,
            x="GPA",
            y="InsomniaSeverity_index",
            color="GPA",
            title="Insomnia Severity Index Across GPA Categories",
            category_orders={"GPA": gpa_order},
            color_discrete_sequence=SUNSET,
            points="outliers",
        )
        fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
**Key Insights**
* As GPA decreases, insomnia severity tends to increase (higher medians and broader spread).
* High GPA categories show lower median ISI, suggesting healthier sleep profiles.
* Some high-performing outliers still experience high insomnia, indicating resilience is possible but not typical.

**Conclusion**
* Managing insomnia is strongly associated with maintaining better academic performance, especially in overall grade outcomes.
        """.strip())
        st.divider()
    else:
        st.warning("Missing columns for Chart b).")

    # -----------------------------
    # c) Assignment Impact
    # -----------------------------
    st.subheader("c) Assignment Impact by Insomnia Category")
    if {"Insomnia_Category", "AssignmentImpact"}.issubset(df.columns):
        tab = pd.crosstab(df["Insomnia_Category"], df["AssignmentImpact"], dropna=False)
        melted = tab.reset_index().melt(id_vars="Insomnia_Category", var_name="AssignmentImpact", value_name="Student_Count")

        fig = px.bar(
            melted,
            x="Insomnia_Category",
            y="Student_Count",
            color="AssignmentImpact",
            title="Assignment Impact by Insomnia Category",
            category_orders={"Insomnia_Category": insomnia_order, "AssignmentImpact": impact_order},
            color_discrete_sequence=SUNSET,
            barmode="stack",
            labels={"Student_Count": "Number of Students"},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
**Key Insights**
* Impact shifts upward with insomnia severity: moderate/severe insomnia groups report more moderate-to-severe assignment disruption.
* Severe insomnia group rarely reports “No impact”, indicating academic disruption becomes the norm.

**Conclusion**
* As insomnia severity increases, students become significantly more likely to experience difficulty meeting deadlines and completing coursework effectively.
        """.strip())
        st.divider()
    else:
        st.warning("Missing columns for Chart c).")

    # -----------------------------
    # d) Fatigue
    # -----------------------------
    st.subheader("d) Fatigue Level by Insomnia Severity")
    if {"Insomnia_Category", "DaytimeFatigue"}.issubset(df.columns):
        tab = pd.crosstab(df["Insomnia_Category"], df["DaytimeFatigue"], dropna=False)
        melted = tab.reset_index().melt(id_vars="Insomnia_Category", var_name="DaytimeFatigue", value_name="Count")

        fig = px.bar(
            melted,
            x="Insomnia_Category",
            y="Count",
            color="DaytimeFatigue",
            title="Fatigue Level by Insomnia Severity",
            category_orders={"Insomnia_Category": insomnia_order, "DaytimeFatigue": freq_order},
            color_discrete_sequence=SUNSET,
            barmode="stack",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
**Key Insights**
* Fatigue increases progressively with insomnia severity.
* Severe insomnia group shows fatigue as near-universal, often reported “Sometimes” to “Always”.

**Conclusion**
* Daytime fatigue appears as a critical pathway linking insomnia to academic disruption, reducing attentional capacity and study endurance.
        """.strip())
        st.divider()
    else:
        st.warning("Missing columns for Chart d).")

    # -----------------------------
    # e) Academic Performance
    # -----------------------------
    st.subheader("e) Academic Performance by Insomnia Category")
    if {"Insomnia_Category", "AcademicPerformance"}.issubset(df.columns):
        fig = px.box(
            df,
            x="Insomnia_Category",
            y="AcademicPerformance",
            color="Insomnia_Category",
            title="Academic Performance by Insomnia Category",
            category_orders={"Insomnia_Category": insomnia_order, "AcademicPerformance": academic_order},
            color_discrete_sequence=SUNSET,
            points="outliers",
        )
        fig.update_layout(showlegend=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
**Key Insights**
* Low/No insomnia students cluster in higher self-rated performance categories.
* Severe insomnia shifts ratings downward toward “Average/Good” with reduced presence of “Very good/Excellent”.

**Conclusion**
* Insomnia severity negatively correlates with academic self-perception, potentially reflecting reduced confidence and sustained cognitive strain.
        """.strip())
    else:
        st.warning("Missing columns for Chart e).")

    # -----------------------------
    # f) Correlation Heatmap
    # -----------------------------
    st.divider()
    st.subheader("f) Correlation Heatmap: Sleep Issues vs. Academic Outcomes")

    corr_columns = [
        "SleepHours_est",
        "InsomniaSeverity_index",
        "DaytimeFatigue_numeric",
        "ConcentrationDifficulty_numeric",
        "MissedClasses_numeric",
        "AcademicPerformance_numeric",
        "GPA_numeric",
        "CGPA_numeric",
    ]
    existing_cols = [c for c in corr_columns if c in df.columns]

    if len(existing_cols) >= 2:
        corr_matrix = df[existing_cols].corr()

        fig = px.imshow(
            corr_matrix,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale=SUNSET,  # FIXED: real palette, not string
            zmin=-1,
            zmax=1,
            title="Correlation Heatmap: Sleep Issues vs. Academic Outcomes",
        )
        fig.update_layout(height=600, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", title_font_size=18)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
**Key Insights**
* Insomnia severity relates strongly to fatigue and concentration difficulty, showing a clear functional pathway.
* Relationships between “sleep hours” and GPA/CGPA may be weaker than “sleep quality/insomnia”, implying quality is the primary risk driver.
* GPA and CGPA remain strongly correlated, as expected, but sleep variables contribute via fatigue and cognitive impairment.

**Conclusion**
* Improving sleep quality and reducing insomnia symptoms appears more impactful for academic outcomes than focusing only on increasing sleep duration.
        """.strip())
    else:
        st.warning("Not enough numeric variables available to generate correlation heatmap.")


render()
