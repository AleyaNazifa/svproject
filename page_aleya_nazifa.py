import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio

from data_loader import display_sidebar_info, get_df
from cleaning_nazifa import prepare_nazifa_data

pio.templates.default = "plotly_white"

SUNSET = px.colors.sequential.Sunset
SLEEP_CAT_ORDER = ["Short (<6h)", "Adequate (6–8h)", "Long (>8h)"]
BEDTIME_ORDER = ["9–10 PM", "10–11 PM", "11 PM–12 AM", "After 12 AM"]


def pct(n: int, total: int) -> float:
    return (n / total * 100) if total else 0.0


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

    short_n = int(df["SleepDurationCategory"].astype(str).eq("Short (<6h)").sum()) if "SleepDurationCategory" in df.columns else 0
    late_n = int(df["BedTime"].astype(str).str.contains("After 12 AM", na=False).sum()) if "BedTime" in df.columns else 0
    poor_quality_n = int(pd.to_numeric(df["SleepQuality_num"], errors="coerce").isin([1, 2]).sum()) if "SleepQuality_num" in df.columns else 0

    both_n = 0
    if {"FrequentDifficultyFallingAsleep", "FrequentNightWakeups"}.issubset(df.columns):
        both_n = int((df["FrequentDifficultyFallingAsleep"] & df["FrequentNightWakeups"]).sum())

    col1.metric("⏳ Short Sleepers (<6h)", f"{pct(short_n, total):.1f}%", help="Percentage of students sleeping <6 hours.", border=True)
    col2.metric("🌙 Late Bedtime (After 12 AM)", f"{pct(late_n, total):.1f}%", help="Percentage sleeping after midnight on weekdays.", border=True)
    col3.metric("⭐ Poor Sleep Quality (1–2)", f"{pct(poor_quality_n, total):.1f}%", help="Percentage rating sleep quality as 1 or 2.", border=True)
    col4.metric("🚨 Frequent Dual Symptoms", f"{pct(both_n, total):.1f}%", help="Frequent difficulty falling asleep + night wakeups.", border=True)

    st.divider()

    # -----------------------------
    # Figure A1 (UPDATED - Violin + Box + Points)
    # -----------------------------
    st.subheader("Figure A1 — Sleep Duration Distribution (Estimated Hours)")

    if "SleepHours_est" not in df.columns:
        st.warning("SleepHours_est is missing. Please verify Nazifa cleaning module.")
    else:
        a1 = pd.to_numeric(df["SleepHours_est"], errors="coerce").dropna()

        if a1.empty:
            st.warning("SleepHours_est has no valid numeric values.")
        else:
            mean_sleep = float(a1.mean())
            median_sleep = float(a1.median())
            q1 = float(a1.quantile(0.25))
            q3 = float(a1.quantile(0.75))

            a1_df = pd.DataFrame({"SleepHours_est": a1})
            a1_df["Group"] = "All Students"

            fig1 = px.violin(
                a1_df,
                x="SleepHours_est",
                y="Group",
                orientation="h",
                box=True,
                points="all",
                title="Distribution of Estimated Sleep Duration",
                color_discrete_sequence=[SUNSET[2]],
            )

            # Keep the axis clean
            fig1.update_layout(
                xaxis_title="Hours of Sleep (Estimated)",
                yaxis_title="",
                showlegend=False,
                height=380,
                margin=dict(l=20, r=20, t=60, b=20),
            )

            st.plotly_chart(fig1, use_container_width=True)

            st.caption(
                f"Summary: Mean = {mean_sleep:.2f}h | Median = {median_sleep:.2f}h | IQR = {q1:.2f}–{q3:.2f}h"
            )

            st.markdown(
                f"""
**Key Insights**
* Most points cluster around **5–6 hours**, showing that short sleep is common.
* **{short_n} students ({pct(short_n, total):.1f}%)** fall into the **short-sleep** group (<6 hours).
* The **median ({median_sleep:.2f}h)** indicates that “typical” sleep is still below recommended levels.

**Conclusion**
* Sleep duration is generally insufficient among respondents, suggesting risk for fatigue and reduced academic functioning.
* Interventions should focus on **increasing total sleep time** (earlier bedtime + consistent routine).
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
* Categorisation simplifies interpretation by grouping students into risk-relevant sleep categories.
* **{short_count} students ({pct(short_count, total):.1f}%)** are short sleepers (<6 hours).
* **{adequate_count} students ({pct(adequate_count, total):.1f}%)** achieve adequate sleep (6–8 hours).
* **{long_count} students ({pct(long_count, total):.1f}%)** report long sleep (>8 hours).

**Conclusion**
* The dominance of the short-sleep category shows insufficient sleep is the norm rather than the exception.
* This categorisation clearly identifies a high-risk group that may benefit most from sleep hygiene education and behavioural interventions.
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

        fig3 = px.pie(tmp, names="BedTime", hole=0.45, title="Bedtime Distribution (Weekdays)", color_discrete_sequence=SUNSET)
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
* Bedtime patterns show a strong shift toward late-night sleep schedules.
* **{after_12} students ({pct(after_12, total):.1f}%)** report going to bed after **12 AM** on weekdays.
* **{between_11_12} students ({pct(between_11_12, total):.1f}%)** sleep between **11 PM–12 AM**.
* Early bedtimes are uncommon: **{between_10_11} students ({pct(between_10_11, total):.1f}%)** between **10–11 PM** and **{between_9_10} students ({pct(between_9_10, total):.1f}%)** between **9–10 PM**.

**Conclusion**
* Delayed bedtime is extremely common and likely contributes to reduced total sleep duration, especially when early class schedules are present.
* Late-night sleep timing represents a key behavioural risk factor for chronic sleep deprivation among students.
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

        fig4 = px.violin(
            df_plot,
            x="BedTime",
            y="SleepQuality_num",
            box=True,
            points=False,
            title="Sleep Quality Across Bedtime Categories",
            category_orders={"BedTime": BEDTIME_ORDER},
            color_discrete_sequence=SUNSET,
        )
        fig4.update_layout(xaxis_title="Bedtime Category", yaxis_title="Sleep Quality (1=Poor, 5=Excellent)", showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown(
            """
**Key Insights**
* Sleep quality varies across bedtime categories.
* Later bedtimes (especially after 12 AM) tend to show lower sleep quality ratings and greater variability.

**Conclusion**
* Encouraging earlier and consistent bedtimes may improve perceived sleep quality.
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
        fig5 = px.imshow(heat, text_auto=True, title="Difficulty Falling Asleep vs Night Wakeups", color_continuous_scale=SUNSET)
        fig5.update_layout(xaxis_title="Night Wakeups Frequency", yaxis_title="Difficulty Falling Asleep Frequency")
        st.plotly_chart(fig5, use_container_width=True)

        st.markdown(
            f"""
**Key Insights**
* The heatmap shows insomnia symptoms often overlap.
* **{both_n} students ({pct(both_n, total):.1f}%)** show frequent difficulty falling asleep together with frequent night wakeups.

**Conclusion**
* Co-occurring symptoms suggest a subgroup with more severe sleep disruption and higher intervention need.
            """.strip()
        )
    else:
        st.warning("DifficultyFallingAsleep or NightWakeups is missing. Please verify Nazifa cleaning module.")


render()
