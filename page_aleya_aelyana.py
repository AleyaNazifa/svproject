# page_aleya_aelyana.py

import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import display_sidebar_info, get_df
from cleaning_aelyana import prepare_aelyana_data

# NOTE: do not call st.set_page_config() here (app.py already does it)

SUNSET = px.colors.sequential.Sunset  # real palette list (safe for plotly)


def safe_mode(s: pd.Series, default="N/A"):
    s = s.dropna()
    return s.mode().iloc[0] if not s.empty else default


def render():
    # Sidebar (live data status / refresh)
    display_sidebar_info()

    raw = get_df()
    df = prepare_aelyana_data(raw)

    # -----------------------------
    if df is not None:
        df['GPA'] = df['GPA'].replace('2.50 - 2.49', '2.50 - 2.99')
        df['CGPA'] = df['CGPA'].replace('2.50 - 2.49', '2.50 - 2.99')
    # -----------------------------

    if df is None or df.empty:
        st.error("No data available.")
        return

    # ------------------------------------------
    # Orders for consistent plots
    # ------------------------------------------
    academic_order = ["Below average", "Average", "Good", "Very good", "Excellent"]
    insomnia_order = ["Low / No Insomnia", "Moderate Insomnia", "Severe Insomnia"]
    freq_order = ["Never", "Rarely", "Sometimes", "Often", "Always"]
    impact_order = ["No impact", "Minor impact", "Moderate impact", "Major impact", "Severe impact"]

    # Enforce categorical ordering (stable visuals)
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

    # ------------------------------------------
    # Header
    # ------------------------------------------
    st.title("Interpretation Dashboard: Impact of Sleep Related Issues on Academic Performance")
    st.divider()

    # ==============================================
    # 🎯 OBJECTIVE 3
    # ==============================================
    st.markdown(
        """
<div class="card">
  <div class="card-title">🎯 Objective 3 (Academic Impact)</div>
  <div class="interpretation">
    To evaluate the impact of insufficient sleep on academic performance, including concentration difficulties, fatigue, class attendance and academic achievement indicators (GPA and self-rated performance).
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # ------------------------------------------
    # Key Metrics (Severe insomnia subgroup)
    # ------------------------------------------
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

    col1.metric(
        label="🧠 Concentration Difficulty",
        value=f"{focus_risk:.1f}%",
        help="Percentage of students with severe insomnia who report Often/Always difficulty concentrating.",
        border=True,
    )
    col2.metric(
        label="😫 Severe Academic Fatigue",
        value=f"{fatigue_risk:.1f}%",
        help="Percentage of students with severe insomnia who report Often/Always daytime fatigue.",
        border=True,
    )
    col3.metric(
        label="📉 Academic Performance Level",
        value=perf_level,
        help="Most frequently reported academic performance category among students with severe insomnia.",
        border=True,
    )
    col4.metric(
        label="📝 Assignment Performance Risk",
        value=f"{assign_risk:.1f}%",
        help="Percentage of students with severe insomnia reporting Major/Severe assignment impact.",
        border=True,
    )

    st.divider()

    # ------------------------------------------
    # a) Concentration Difficulty (Grouped bar)
    # ------------------------------------------
    st.subheader("Figure C1 - Concentration Difficulty by Insomnia Category")

    if {"Insomnia_Category", "ConcentrationDifficulty"}.issubset(df.columns):
        concentration_crosstab = pd.crosstab(
            df["Insomnia_Category"], df["ConcentrationDifficulty"], dropna=False
        )
        concentration_melted = concentration_crosstab.reset_index().melt(
            id_vars="Insomnia_Category",
            var_name="ConcentrationDifficulty",
            value_name="Count",
        )

        fig_a = px.bar(
            concentration_melted,
            x="Insomnia_Category",
            y="Count",
            color="ConcentrationDifficulty",
            barmode="group",
            title="Concentration Difficulty by Insomnia Category",
            category_orders={
                "Insomnia_Category": insomnia_order,
                "ConcentrationDifficulty": freq_order,
            },
            color_discrete_sequence=SUNSET,
            labels={"Count": "Number of Students", "Insomnia_Category": "Insomnia Category"},
        )
        st.plotly_chart(fig_a, use_container_width=True)

        st.markdown(
            """
**Interpretation and Analysis**
* There is a direct relationship between insomnia severity and difficulty maintaining focus. 
* Severe insomnia significantly increases the risk of cognitive impairment, which can lead to academic failure.
            """.strip()
        )
        st.divider()
    else:
        st.warning("Missing columns for Chart a).")
        st.divider()

    # ------------------------------------------
    # b) GPA vs Insomnia Index (Box plot)
    # ------------------------------------------
    st.subheader("Figure C2 - Insomnia Severity Index Across GPA Category")

    if {"GPA", "InsomniaSeverity_index"}.issubset(df.columns):
        gpa_order = ["2.00 - 2.49", "2.50 - 2.99", "3.00 - 3.69", "3.70 - 4.00"]

        fig_b = px.box(
            df,
            x="GPA",
            y="InsomniaSeverity_index",
            color="GPA",
            title="Insomnia Severity Index Across GPA Category",
            category_orders={"GPA": gpa_order},
            color_discrete_sequence=SUNSET,
            points="outliers",
        )
        fig_b.update_layout(
            xaxis_title="GPA Category",
            yaxis_title="Insomnia Severity Index",
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_b, use_container_width=True)

        st.markdown(
            """
**Interpretation and Analysis**
* Better academic performance is closely linked to lower levels of insomnia. 
* Students with the highest grades tend to maintain the healthiest sleep profiles.
            """.strip()
        )
        st.divider()
    else:
        st.warning("Missing columns for Chart b).")
        st.divider()

    # ------------------------------------------
    # c) Assignment Impact (Stacked bar)
    # ------------------------------------------
    st.subheader("Figure C3 - Assignment Impact by Insomnia Category")

    if {"Insomnia_Category", "AssignmentImpact"}.issubset(df.columns):
        assignment_table = pd.crosstab(
            df["Insomnia_Category"], df["AssignmentImpact"], dropna=False
        )
        assignment_melted = assignment_table.reset_index().melt(
            id_vars="Insomnia_Category",
            var_name="AssignmentImpact",
            value_name="Student_Count",
        )

        fig_c = px.bar(
            assignment_melted,
            x="Insomnia_Category",
            y="Student_Count",
            color="AssignmentImpact",
            title="Assignment Impact by Insomnia Category",
            category_orders={
                "Insomnia_Category": insomnia_order,
                "AssignmentImpact": impact_order,
            },
            color_discrete_sequence=SUNSET,
            labels={"Student_Count": "Number of Students"},
        )
        fig_c.update_layout(
            barmode="stack",
            xaxis_title="Insomnia Category",
            yaxis_title="Number of Students",
        )
        st.plotly_chart(fig_c, use_container_width=True)

        st.markdown(
            """
**Interpretation and Analysis**
* The insomnia severity is directly correlated with academic disruption. 
* As sleep health worsens, the ability to complete coursework effectively is significantly compromised.
            """.strip()
        )
        st.divider()
    else:
        st.warning("Missing columns for Chart c).")
        st.divider()

    # ------------------------------------------
    # d) Daytime Fatigue (Stacked bar)
    # ------------------------------------------
    st.subheader("Figure C4 - Fatigue Level by Insomnia Category")

    if {"Insomnia_Category", "DaytimeFatigue"}.issubset(df.columns):
        fatigue_table = pd.crosstab(df["Insomnia_Category"], df["DaytimeFatigue"], dropna=False)
        fatigue_melted = fatigue_table.reset_index().melt(
            id_vars="Insomnia_Category",
            var_name="DaytimeFatigue",
            value_name="Count",
        )

        fig_d = px.bar(
            fatigue_melted,
            x="Insomnia_Category",
            y="Count",
            color="DaytimeFatigue",
            title="Fatigue Level by Insomnia Category",
            category_orders={"DaytimeFatigue": freq_order, "Insomnia_Category": insomnia_order},
            color_discrete_sequence=SUNSET,
            barmode="stack",
        )
        st.plotly_chart(fig_d, use_container_width=True)

        st.markdown(
            """
**Interpretation and Analysis**
* There is a progressive increase in fatigue as sleep health declines. 
* Chronic daytime fatigue acts as a major barrier, likely driving the concentration and performance issues seen in this study.
            """.strip()
        )
        st.divider()
    else:
        st.warning("Missing columns for Chart d).")
        st.divider()

    # ------------------------------------------
    # e) Academic Performance (Box plot)
    # ------------------------------------------
    st.subheader("Figure C5 - Academic Performance by Insomnia Category")

    if {"Insomnia_Category", "AcademicPerformance"}.issubset(df.columns):
        fig_e = px.box(
            df,
            x="Insomnia_Category",
            y="AcademicPerformance",
            color="Insomnia_Category",
            title="Academic Performance by Insomnia Category",
            category_orders={"AcademicPerformance": academic_order, "Insomnia_Category": insomnia_order},
            color_discrete_sequence=SUNSET,
            points="outliers",
        )
        fig_e.update_layout(
            xaxis_title="Insomnia Category",
            yaxis_title="Academic Performance",
            showlegend=False,
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_e, use_container_width=True)

        st.markdown(
            """
**Interpretation and Analysis**
* Insomnia severity has a negative correlation with academic self-perception. 
* Severe insomnia acts as a barrier that makes it more difficult for students to feel like high achievers.
            """.strip()
        )
    else:
        st.warning("Missing columns for Chart e).")

    st.divider()

    # ------------------------------------------
    # f) Correlation Heatmap
    # ------------------------------------------
    st.subheader("Figure C6 - Correlation Heatmap: Sleep Issues vs. Academic Outcomes")

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

        fig_f = px.imshow(
            corr_matrix,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale=SUNSET,  # must be a real palette
            zmin=-1,
            zmax=1,
            title="Correlation Heatmap: Sleep Issues vs. Academic Outcomes",
        )
        fig_f.update_layout(
            height=600,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            title_font_size=18,
        )
        st.plotly_chart(fig_f, use_container_width=True)

        st.markdown(
            """
**Interpretation and Analysis**
* Insomnia is a much greater threat to grades than the sleep hours.
* Fatigue and concentration problems caused by insomnia are the major drivers of lower academic performance.
* The focus should be on treating insomnia quality rather than just increasing hours in bed.
            """.strip()
        )
    else:
        st.warning("Not enough numeric variables available to generate correlation heatmap.")


render()
