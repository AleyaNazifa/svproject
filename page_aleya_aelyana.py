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
    To evaluate the impact of insufficient sleep on academic performance, including concentration difficulties, fatigue, class attendance, and academic achievement indicators (GPA and self-rated performance).
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
* Most students (64) have moderate insomnia, with "Sometimes" (36 students) being the most common focus problem.
* Low / No Insomnia Group dominated by "Rarely" (9) and "Sometimes" (8) responses, serious disruptions ("Often"/"Always") are almost none.
* Severe Insomnia Group shows a concerning change which "Rarely" almost disappears (1 student), replaced by a sharp increase in "Often" and "Always".
* Zero (0) students reported "Never" experiencing concentration issues, proving that focus is a universal challenge, but it becomes chronic with poor sleep.

**Conclusion**
* There is a direct relationship between insomnia severity and difficulty maintaining focus. Severe insomnia doesn't just mean less sleep but it creates a high risk of academic failure due to ongoing cognitive impairment.
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
* As GPA decreases, the insomnia severity "box" shifts upward. Higher GPA is associated with more consistent and lower insomnia scores.
* GPA 3.70 - 4.00 category show lowest median insomnia score (4), placing these students in the "Low/No Insomnia" category.
* GPA 3.00 - 3.69 category show median score increases to 7. Interestingly, outliers reaching scores of 12-13 indicate that some students maintain good grades despite high insomnia.
* GPA 2.50 - 2.49 group show highest spread and maximum scores (reaching 14), indicating that this group experiences the strongest insomnia symptoms.

**Conclusion**
* Managing insomnia is a key factor in academic success. Students with the best grades tend to maintain the healthiest sleep profiles.
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
* Low / No Insomnia: Even with good sleep, only 3 students reported "No impact," with most feeling at least a "Minor impact" (8) on their work.
* Moderate Insomnia: A large spike in "Moderate" (28) and "Major" (13) impacts, indicating that sleep issues are starting to damage the quality of their assignment.
* Severe Insomnia: Negative impact is the standard.16 out of 21 students are "Moderate" or "Major" impacted, with only 1 student reporting "No impact".

**Conclusion**
* The insomnia severity is directly correlates with academic disruption. As sleep health worsens, the ability to complete coursework effectively is significantly compromised.
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
* Low / No Insomnia: Most students feel energized, with "Rarely" (11) or "Never" (4) being the top responses.
* Moderate Insomnia: A big shift where "Sometimes" (37) becomes the norm. The appearance of "Always" fatigued students (3) shows moderate issues can still cause persistent fatigue.
* Severe Insomnia: Fatigue is nearly universal. 20 out of 21 students reported fatigue "Sometimes" to "Always".

**Conclusion**
* There is a progressive increase in fatigue associated with sleep health. Fatigue acts as a barrier that may drive the concentration and performance issues seen throughout this study.
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
* Low/No Insomnia students feel the most confident, rating themselves between "Good" and "Very good".
* Moderate Insomnia causes ratings to spread out. The median remains "Good," but the range drops to "Average".
* Severe Insomnia shifts the entire box down to "Average" and "Good," with almost no representation of "Very good".

**Conclusion**
* Insomnia severity has a negative correlation with academic self perception. Severe insomnia acts as a "ceiling" that makes it harder to achieve or feel like a high achiever.
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
* Estimated sleep hours show a moderate positive correlation with Academic Performance (0.36), but have almost no relationship with actual GPA (0.05) or CGPA (0.01).
* There is a strong internal correlation between Daytime Fatigue and Concentration Difficulty (0.63). Also, Insomnia Severity is a significant predictor of Fatigue (0.54) and Concentration Difficulty (0.38).
* Insomnia Severity shows a notable negative correlation with GPA (-0.25) and CGPA (-0.17).
* There is a strong correlation between GPA and CGPA (0.65). Interestingly, Academic Performance correlates more strongly with GPA (0.40) than it does with any sleep-related metrics. *Missed Classes show very weak or slightly negative correlations with sleep issues, like -0.03 with Insomnia.

**Conclusion**
* The data shows that sleep quality (insomnia) is a much bigger threat to actual grades than just the number of hours slept. While more sleep may make students feel like they are performing better, the real issues are fatigue and concentration problems caused by insomnia, which lead to lower grades. To truly improve results, the focus should be on improving sleep quality and treating insomnia rather than just trying to spend more hours in bed.
        """.strip())
    else:
        st.warning("Not enough numeric variables available to generate correlation heatmap.")


render()
