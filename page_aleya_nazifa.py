import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from data_loader import display_sidebar_info, get_df
from cleaning_nazifa import prepare_nazifa_data

pio.templates.default = "plotly_white"

SUNSET = px.colors.sequential.Sunset
SLEEP_CAT_ORDER = ["Short (<6h)", "Adequate (6–8h)", "Long (>8h)"]
BEDTIME_ORDER = ["9–10 PM", "10–11 PM", "11 PM–12 AM", "After 12 AM"]


def pct(n: int, total: int) -> float:
    return (n / total * 100) if total else 0.0


def _safe_int(x) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def render():
    display_sidebar_info()

    raw = get_df()
    df = prepare_nazifa_data(raw)

    if df is None or df.empty:
        st.error("No data available.")
        return

    total = len(df)

    st.title("Interpretation Dashboard: Sleep Patterns & Insomnia Symptoms (Nazifa)")
    st.markdown(
        "This page explores **sleep duration**, **bedtime timing**, **sleep quality**, and **core insomnia symptoms** "
        "to identify sleep-risk patterns among UMK students."
    )

    st.markdown(
        """
<div class="card">
  <div class="card-title">Objective (Sleep Patterns)</div>
  <div class="interpretation">
    To analyze sleep patterns and insomnia severity among UMK students by examining sleep duration, sleep quality,
    bedtime habits, and insomnia-related symptoms.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # ==========================
    # Key Metrics
    # ==========================
    st.subheader("Key Findings: Sleep Pattern Risk Indicators")
    col1, col2, col3, col4 = st.columns(4)

    short_n = _safe_int(df["SleepDurationCategory"].astype(str).eq("Short (<6h)").sum()) if "SleepDurationCategory" in df.columns else 0
    late_n = _safe_int(df["BedTime"].astype(str).str.contains("After 12 AM", na=False).sum()) if "BedTime" in df.columns else 0
    poor_quality_n = _safe_int(pd.to_numeric(df.get("SleepQuality_num", np.nan), errors="coerce").isin([1, 2]).sum()) if "SleepQuality_num" in df.columns else 0

    both_n = 0
    if {"FrequentDifficultyFallingAsleep", "FrequentNightWakeups"}.issubset(df.columns):
        both_n = _safe_int((df["FrequentDifficultyFallingAsleep"] & df["FrequentNightWakeups"]).sum())

    col1.metric("⏳ Short Sleepers (<6h)", f"{pct(short_n, total):.1f}%", help="Percentage of students sleeping <6 hours.", border=True)
    col2.metric("🌙 Late Bedtime (After 12 AM)", f"{pct(late_n, total):.1f}%", help="Percentage sleeping after midnight on weekdays.", border=True)
    col3.metric("⭐ Poor Sleep Quality (1–2)", f"{pct(poor_quality_n, total):.1f}%", help="Percentage rating sleep quality as 1 or 2.", border=True)
    col4.metric("🚨 Frequent Dual Symptoms", f"{pct(both_n, total):.1f}%", help="Frequent difficulty falling asleep + night wakeups.", border=True)

    st.divider()

    # -----------------------------
    # Figure A1 (UPDATED - Lollipop Chart)
    # -----------------------------
    st.subheader("Figure A1 — Sleep Duration Distribution (Estimated Hours)")

    if "SleepHours_est" not in df.columns:
        st.warning("SleepHours_est is missing. Please verify Nazifa cleaning module.")
    else:
        a1 = pd.to_numeric(df["SleepHours_est"], errors="coerce").dropna()

        if a1.empty:
            st.warning("SleepHours_est has no valid numeric values.")
        else:
            # Counts by estimated hours (3.5, 4.5, 5.5, 6.5, 7.5, 8.5...)
            counts = a1.value_counts().sort_index()
            a1_counts = pd.DataFrame({"SleepHours_est": counts.index.astype(float), "Count": counts.values})

            mean_sleep = float(a1.mean())
            median_sleep = float(a1.median())

            # Lollipop using graph_objects
            fig1 = go.Figure()

            # Stems (lines)
            fig1.add_trace(
                go.Scatter(
                    x=a1_counts["SleepHours_est"],
                    y=a1_counts["Count"],
                    mode="lines",
                    line=dict(width=3),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            # Dots
            fig1.add_trace(
                go.Scatter(
                    x=a1_counts["SleepHours_est"],
                    y=a1_counts["Count"],
                    mode="markers+text",
                    text=a1_counts["Count"],
                    textposition="top center",
                    marker=dict(size=14),
                    name="Students",
                )
            )

            fig1.update_layout(
                title="Distribution of Estimated Sleep Duration (Lollipop Frequency)",
                xaxis_title="Hours of Sleep (Estimated)",
                yaxis_title="Number of Students",
                showlegend=False,
                height=420,
                margin=dict(l=20, r=20, t=70, b=30),
            )

            # Add mean/median as subtle vertical reference lines
            fig1.add_vline(x=mean_sleep, line_width=2, line_dash="solid", annotation_text=f"Mean {mean_sleep:.2f}h", annotation_position="top right")
            fig1.add_vline(x=median_sleep, line_width=2, line_dash="dash", annotation_text=f"Median {median_sleep:.2f}h", annotation_position="top left")

            st.plotly_chart(fig1, use_container_width=True)

            # Most common sleep duration (mode)
            mode_sleep = float(a1.mode().iloc[0]) if not a1.mode().empty else np.nan
            mode_count = int(counts.get(mode_sleep, 0)) if not np.isnan(mode_sleep) else 0

            st.markdown(
                f"""
**Key Insights**
* The most common sleep duration is **{mode_sleep:.1f} hours** (**{mode_count} students**, {pct(mode_count, total):.1f}%), showing where responses concentrate.
* Overall average sleep is **{mean_sleep:.2f} hours** and the median is **{median_sleep:.2f} hours**, indicating that “typical” sleep is still below recommended levels for many students.
* **{short_n} students ({pct(short_n, total):.1f}%)** are in the **short sleep** group (<6 hours), highlighting a sizeable at-risk population.

**Conclusion**
* The lollipop chart makes it clear that sleep duration is concentrated in a few common ranges (especially around **5–6 hours**).
* This supports the conclusion that insufficient sleep is widespread and may contribute to fatigue and reduced academic functioning, especially among short sleepers.
                """.strip()
            )

    st.divider()

    # -----------------------------
    # Figure A2
    # -----------------------------
    st.subheader("Figure A2 — Sleep Duration Categories (Short / Adequate / Long)")

    if "SleepDurationCategory" in df.columns:
        cat_counts = (
            df["SleepDurationCategory"].astype(str)
            .value_counts()
            .reindex(SLEEP_CAT_ORDER, fill_value=0)
            .reset_index()
        )
        cat_counts.columns = ["Category", "Count"]

        fig2 = px.bar(
            cat_counts,
            x="Category",
            y="Count",
            text="Count",
            title="Sleep Duration Category Distribution",
            category_orders={"Category": SLEEP_CAT_ORDER},
            color_discrete_sequence=SUNSET,
        )
        fig2.update_traces(textposition="outside", cliponaxis=False)
        fig2.update_layout(xaxis_title="Sleep Duration Category", yaxis_title="Number of Students", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        short_count = int(cat_counts.loc[cat_counts["Category"] == "Short (<6h)", "Count"].sum())
        adequate_count = int(cat_counts.loc[cat_counts["Category"] == "Adequate (6–8h)", "Count"].sum())
        long_count = int(cat_counts.loc[cat_counts["Category"] == "Long (>8h)", "Count"].sum())

        st.markdown(
            f"""
**Key Insights**
* The **largest group** is **Short (<6h)**: **{short_count} students ({pct(short_count, total):.1f}%)**, meaning insufficient sleep is common.
* Only **{adequate_count} students ({pct(adequate_count, total):.1f}%)** fall into the **Adequate (6–8h)** range.
* **Long (>8h)** sleepers are a **small minority**: **{long_count} students ({pct(long_count, total):.1f}%)**.

**Conclusion**
* A2 is useful for a lecturer because it **summarizes risk groups clearly** (short vs adequate vs long).
* It strongly supports the conclusion that sleep deprivation (short sleep) is the dominant pattern among respondents.
            """.strip()
        )
    else:
        st.warning("SleepDurationCategory is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # -----------------------------
    # Figure A3
    # -----------------------------
    st.subheader("Figure A3 — Weekday Bedtime Distribution")

    if "BedTime" in df.columns:
        tmp = df.copy()
        tmp["BedTime"] = tmp["BedTime"].astype(str).str.strip()

        fig3 = px.pie(
            tmp,
            names="BedTime",
            hole=0.45,
            title="Bedtime Distribution (Weekdays)",
            color_discrete_sequence=SUNSET,
        )
        fig3.update_layout(showlegend=True)
        st.plotly_chart(fig3, use_container_width=True)

        bedtime_counts = tmp["BedTime"].value_counts()
        after_12 = int(bedtime_counts.get("After 12 AM", 0))
        between_11_12 = int(bedtime_counts.get("11 PM–12 AM", 0))
        between_10_11 = int(bedtime_counts.get("10–11 PM", 0))
        between_9_10 = int(bedtime_counts.get("9–10 PM", 0))

        st.markdown(
            f"""
**Key Insights**
* Bedtime is heavily concentrated in late-night categories.
* **After 12 AM** is the dominant group: **{after_12} students ({pct(after_12, total):.1f}%)**.
* The next most common is **11 PM–12 AM**: **{between_11_12} students ({pct(between_11_12, total):.1f}%)**.
* Early bedtimes are rare: **{between_10_11}** ({pct(between_10_11, total):.1f}%) and **{between_9_10}** ({pct(between_9_10, total):.1f}%).

**Conclusion**
* Late bedtime is a major behavioural risk factor and likely contributes to short sleep—especially when students must wake up early for classes.
* This suggests that improving bedtime consistency (sleep timing) may be as important as increasing total sleep hours.
            """.strip()
        )
    else:
        st.warning("BedTime is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # -----------------------------
    # Figure A4
    # -----------------------------
    st.subheader("Figure A4 — Sleep Quality by Bedtime")

    if {"BedTime", "SleepQuality_num"}.issubset(df.columns):
        df_plot = df.copy()
        df_plot["BedTime"] = pd.Categorical(
            df_plot["BedTime"].astype(str).str.strip(),
            categories=BEDTIME_ORDER,
            ordered=True,
        )
        df_plot["SleepQuality_num"] = pd.to_numeric(df_plot["SleepQuality_num"], errors="coerce")

        fig4 = px.violin(
            df_plot.dropna(subset=["BedTime", "SleepQuality_num"]),
            x="BedTime",
            y="SleepQuality_num",
            box=True,
            points=False,
            title="Sleep Quality Across Bedtime Categories",
            category_orders={"BedTime": BEDTIME_ORDER},
            color_discrete_sequence=SUNSET,
        )
        fig4.update_layout(
            xaxis_title="Bedtime Category",
            yaxis_title="Sleep Quality (1=Poor, 5=Excellent)",
            showlegend=False,
        )
        st.plotly_chart(fig4, use_container_width=True)

        # Compute average sleep quality by bedtime (for numeric insight)
        quality_means = (
            df_plot.dropna(subset=["BedTime", "SleepQuality_num"])
            .groupby("BedTime")["SleepQuality_num"]
            .mean()
            .reindex(BEDTIME_ORDER)
        )

        best_group = quality_means.idxmax() if quality_means.notna().any() else "N/A"
        worst_group = quality_means.idxmin() if quality_means.notna().any() else "N/A"

        st.markdown(
            f"""
**Key Insights**
* Sleep quality differs across bedtime groups (visible through different median levels and spread).
* The bedtime group with the **highest average sleep quality** is **{best_group}**.
* The bedtime group with the **lowest average sleep quality** is **{worst_group}**.
* Late bedtime groups often show wider spread, suggesting more inconsistent sleep experiences.

**Conclusion**
* Bedtime timing appears linked to subjective sleep quality.
* Encouraging earlier and more stable bedtimes could improve how students perceive their sleep quality.
            """.strip()
        )
    else:
        st.warning("BedTime or SleepQuality_num is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # -----------------------------
    # Figure A5
    # -----------------------------
    st.subheader("Figure A5 — Co-occurrence of Insomnia Symptoms")

    if {"DifficultyFallingAsleep", "NightWakeups"}.issubset(df.columns):
        heat = pd.crosstab(df["DifficultyFallingAsleep"], df["NightWakeups"])

        fig5 = px.imshow(
            heat,
            text_auto=True,
            title="Difficulty Falling Asleep vs Night Wakeups",
            color_continuous_scale=SUNSET,
        )
        fig5.update_layout(
            xaxis_title="Night Wakeups Frequency",
            yaxis_title="Difficulty Falling Asleep Frequency",
        )
        st.plotly_chart(fig5, use_container_width=True)

        # Define "frequent" overlap (Often/Always for both)
        frequent_labels = ["Often (5–6 times a week)", "Often (5-6 times a week)", "Always (every night)"]

        frequent_overlap = 0
        if not heat.empty:
            rows = [r for r in heat.index if str(r).strip() in frequent_labels]
            cols = [c for c in heat.columns if str(c).strip() in frequent_labels]
            if rows and cols:
                frequent_overlap = int(heat.loc[rows, cols].values.sum())

        st.markdown(
            f"""
**Key Insights**
* The heatmap highlights that insomnia symptoms often occur together (not independently).
* The largest numbers cluster around similar frequency levels (e.g., “Sometimes” with “Sometimes”), showing symptom co-occurrence.
* **{frequent_overlap} students ({pct(frequent_overlap, total):.1f}%)** fall into the **frequent+frequent** overlap (Often/Always for both symptoms), representing the most concerning subgroup.

**Conclusion**
* Students experiencing both symptoms frequently are likely facing more severe sleep disruption.
* This subgroup may require targeted support (sleep counselling, stress management, or clinical screening), beyond general sleep hygiene advice.
            """.strip()
        )
    else:
        st.warning("DifficultyFallingAsleep or NightWakeups is missing. Please verify Nazifa cleaning module.")


render()
