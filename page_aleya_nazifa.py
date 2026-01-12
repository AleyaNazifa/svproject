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


def pct(n, total):
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

    # Debug marker (remove later if you want)
    st.caption("Nazifa page version: FIXED-INDENT + UPDATED-A1 ✅")

    # Objective
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
    poor_quality_n = int(df["SleepQuality_num"].isin([1, 2]).sum()) if "SleepQuality_num" in df.columns else 0

    both_n = 0
    if {"FrequentDifficultyFallingAsleep", "FrequentNightWakeups"}.issubset(df.columns):
        both_n = int((df["FrequentDifficultyFallingAsleep"] & df["FrequentNightWakeups"]).sum())

    col1.metric("⏳ Short Sleepers (<6h)", f"{pct(short_n, total):.1f}%", help="Percentage of students sleeping <6 hours.", border=True)
    col2.metric("🌙 Late Bedtime (After 12 AM)", f"{pct(late_n, total):.1f}%", help="Percentage sleeping after midnight on weekdays.", border=True)
    col3.metric("⭐ Poor Sleep Quality (1–2)", f"{pct(poor_quality_n, total):.1f}%", help="Percentage rating sleep quality as 1 or 2.", border=True)
    col4.metric("🚨 Frequent Dual Symptoms", f"{pct(both_n, total):.1f}%", help="Frequent difficulty falling asleep + night wakeups.", border=True)

    st.divider()

    # -----------------------------
    # Figure A1 (UPDATED)
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

            # Histogram + rug + mean/median lines
            fig1 = px.histogram(
                a1.to_frame(name="SleepHours_est"),
                x="SleepHours_est",
                nbins=12,
                title="Distribution of Estimated Sleep Duration",
                opacity=0.9,
                marginal="rug",
                color_discrete_sequence=[SUNSET[2]],
            )

            fig1.add_vline(
                x=mean_sleep,
                line_width=3,
                line_dash="solid",
                annotation_text=f"Mean: {mean_sleep:.2f}h",
                annotation_position="top right",
            )
            fig1.add_vline(
                x=median_sleep,
                line_width=3,
                line_dash="dash",
                annotation_text=f"Median: {median_sleep:.2f}h",
                annotation_position="top left",
            )

            fig1.update_layout(
                xaxis_title="Hours of Sleep (Estimated)",
                yaxis_title="Number of Students",
                showlegend=False,
            )

            st.plotly_chart(fig1, use_container_width=True)

            st.markdown(
                f"""
**Key Insights**
* Most students cluster around the **5–6 hour** range, indicating a common sleep pattern below recommended levels.
* **{short_n} students ({pct(short_n, total):.1f}%)** fall into the **short sleep** category (<6 hours).
* The **mean** sleep duration is **{mean_sleep:.2f} hours**, while the **median** is **{median_sleep:.2f} hours**, suggesting insufficient sleep is typical.

**Conclusion**
* Short sleep is widespread among UMK students and may increase risk of fatigue and reduced academic functioning.
* Improving total sleep time should be a priority for sleep awareness and intervention.
                """.strip()
            )

    st.divider()

    # -----------------------------
    # Figure A2
    # -----------------------------
    st.subheader("Figure A2 — Sleep Duration Categories (Short / Adequate / Long)")

    if "SleepDurationCategory" not in df.columns:
        st.warning("SleepDurationCategory is missing. Please verify Nazifa cleaning module.")
    else:
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
        fig2.update_layout(
            xaxis_title="Sleep Duration Category",
            yaxis_title="Number of Students",
            showlegend=False,
        )
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

    st.divider()

    # -----------------------------
    # Figure A3
    # -----------------------------
    st.subheader("Figure A3 — Weekday Bedtime Distribution")

    if "BedTime" not in df.columns:
        st.warning("BedTime is missing. Please verify Nazifa cleaning module.")
    else:
        tmp = df.copy()
        tmp["BedTime"] = tmp["BedTime"].astype(str).str.strip()
        tmp["BedTime"] = pd.Categorical(tmp["BedTime"], categories=BEDTIME_ORDER, ordered=True)

        # counts based on the defined order
        bedtime_counts = tmp["BedTime"].value_counts(dropna=False).reindex(BEDTIME_ORDER, fill_value=0)
        after_12 = int(bedtime_counts.get("After 12 AM", 0))
        between_11_12 = int(bedtime_counts.get("11 PM–12 AM", 0))
        between_10_11 = int(bedtime_counts.get("10–11 PM", 0))
        between_9_10 = int(bedtime_counts.get("9–10 PM", 0))

        fig3 = px.pie(
            tmp.dropna(subset=["BedTime"]),
            names="BedTime",
            hole=0.45,
            title="Bedtime Distribution (Weekdays)",
            color_discrete_sequence=SUNSET,
        )
        fig3.update_layout(showlegend=True)
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown(
            f"""
**Key Insights**
* Bedtime patterns show a strong shift toward late-night sleep schedules.
* **{after_12} students ({pct(after_12, total):.1f}%)** report going to bed after **12 AM** on weekdays.
* **{between_11_12} students ({pct(between_11_12, total):.1f}%)** sleep between **11 PM–12 AM**.
* Early bedtimes are uncommon: **{between_10_11} students ({pct(between_10_11, total):.1f}%)** between **10–11 PM** and **{between_9_10} students ({pct(between_9_10, total):.1f}%)** between **9–10 PM**.

**Conclusion**
* Delayed bedtime is extremely common and likely contributes to reduced total sleep duration, especially with early class schedules.
* Late-night sleep timing represents a key behavioural risk factor for chronic sleep deprivation among students.
            """.strip()
        )

    st.divider()

    # -----------------------------
    # Figure A4
    # -----------------------------
    st.subheader("Figure A4 — Sleep Quality by Bedtime")

    if not {"BedTime", "SleepQuality_num"}.issubset(df.columns):
        st.warning("BedTime or SleepQuality_num is missing. Please verify Nazifa cleaning module.")
    else:
        df_plot = df.copy()
        df_plot["BedTime"] = pd.Categorical(
            df_plot["BedTime"].astype(str).str.strip(),
            categories=BEDTIME_ORDER,
            ordered=True,
        )

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

        st.markdown(
            """
**Key Insights**
* Sleep quality varies across bedtime categories.
* Later bedtime groups (especially **After 12 AM**) tend to show lower ratings and greater variability.
* Earlier bedtime groups are generally more stable and report better perceived sleep quality.

**Conclusion**
* Delayed sleep timing appears associated with poorer subjective sleep experience.
* Encouraging earlier and more consistent bedtimes may improve sleep satisfaction among students.
            """.strip()
        )

    st.divider()

    # -----------------------------
    # Figure A5
    # -----------------------------
    st.subheader("Figure A5 — Co-occurrence of Insomnia Symptoms")

    if not {"DifficultyFallingAsleep", "NightWakeups"}.issubset(df.columns):
        st.warning("DifficultyFallingAsleep or NightWakeups is missing. Please verify Nazifa cleaning module.")
    else:
        heat = pd.crosstab(df["DifficultyFallingAsleep"], df["NightWakeups"])

        fig5 = px.imshow(
            heat,
            text_auto=True,
            title="Difficulty Falling Asleep vs Night Wakeups",
            color_continuous_scale=SUNSET,
            aspect="auto",
        )
        fig5.update_layout(
            xaxis_title="Night Wakeups Frequency",
            yaxis_title="Difficulty Falling Asleep Frequency",
        )
        st.plotly_chart(fig5, use_container_width=True)

        st.markdown(
            f"""
**Key Insights**
* The heatmap shows insomnia symptoms often **co-occur** rather than appear independently.
* Higher counts cluster where both symptoms happen at similar frequencies (showing overlap).
* **{both_n} students ({pct(both_n, total):.1f}%)** report **frequent** difficulty falling asleep together with **frequent** night awakenings, indicating a higher-risk subgroup.

**Conclusion**
* Co-occurring symptoms suggest compounded sleep disruption, not isolated issues.
* This subgroup may benefit from targeted support beyond general sleep advice.
            """.strip()
        )


render()
