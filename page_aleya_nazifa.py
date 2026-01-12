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

    short_n = int(df.get("SleepDurationCategory", pd.Series(dtype=str)).astype(str).eq("Short (<6h)").sum())
    late_n = int(df.get("BedTime", pd.Series(dtype=str)).astype(str).str.contains("After 12 AM", na=False).sum())
    poor_quality_n = int(df.get("SleepQuality_num", pd.Series(dtype=float)).isin([1, 2]).sum())

    both_n = 0
    if {"FrequentDifficultyFallingAsleep", "FrequentNightWakeups"}.issubset(df.columns):
        both_n = int((df["FrequentDifficultyFallingAsleep"] & df["FrequentNightWakeups"]).sum())

    col1.metric("⏳ Short Sleepers (<6h)", f"{pct(short_n, total):.1f}%", help="Percentage of students sleeping <6 hours.", border=True)
    col2.metric("🌙 Late Bedtime (After 12 AM)", f"{pct(late_n, total):.1f}%", help="Percentage sleeping after midnight on weekdays.", border=True)
    col3.metric("⭐ Poor Sleep Quality (1–2)", f"{pct(poor_quality_n, total):.1f}%", help="Percentage rating sleep quality as 1 or 2.", border=True)
    col4.metric("🚨 Frequent Dual Symptoms", f"{pct(both_n, total):.1f}%", help="Frequent difficulty falling asleep + night wakeups.", border=True)

    st.divider()

    # ============================================================
    # NEW FIGURE A1 (OLD A2) — Sleep Duration Categories
    # ============================================================
    st.subheader("Figure A1 — Sleep Duration Categories (Short / Adequate / Long)")

    if "SleepDurationCategory" in df.columns:
        cat_counts = (
            df["SleepDurationCategory"]
            .astype(str)
            .value_counts()
            .reindex(SLEEP_CAT_ORDER, fill_value=0)
            .reset_index()
        )
        cat_counts.columns = ["Category", "Count"]

        fig1 = px.bar(
            cat_counts,
            x="Category",
            y="Count",
            text="Count",
            title="Sleep Duration Category Distribution",
            category_orders={"Category": SLEEP_CAT_ORDER},
            color_discrete_sequence=SUNSET,
        )
        fig1.update_traces(textposition="outside", cliponaxis=False)
        fig1.update_layout(xaxis_title="Sleep Duration Category", yaxis_title="Number of Students", showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

        short_count = int(cat_counts.loc[cat_counts["Category"] == "Short (<6h)", "Count"].sum())
        adequate_count = int(cat_counts.loc[cat_counts["Category"] == "Adequate (6–8h)", "Count"].sum())
        long_count = int(cat_counts.loc[cat_counts["Category"] == "Long (>8h)", "Count"].sum())

        st.markdown(
            f"""
**Key Insights**
* **{short_count} students ({pct(short_count, total):.1f}%)** are **short sleepers** (<6 hours).
* **{adequate_count} students ({pct(adequate_count, total):.1f}%)** achieve **adequate sleep** (6–8 hours).
* **{long_count} students ({pct(long_count, total):.1f}%)** report **long sleep** (>8 hours).

**Conclusion**
* The dominance of short sleep suggests insufficient sleep is the norm, highlighting a large at-risk group for fatigue and reduced functioning.
            """.strip()
        )
    else:
        st.warning("SleepDurationCategory is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # ============================================================
    # NEW FIGURE A2 (OLD A3) — Weekday Bedtime Distribution
    # ============================================================
    st.subheader("Figure A2 — Weekday Bedtime Distribution")

    if "BedTime" in df.columns:
        tmp = df.copy()
        tmp["BedTime"] = tmp["BedTime"].astype(str).str.strip()
        tmp["BedTime"] = pd.Categorical(tmp["BedTime"], categories=BEDTIME_ORDER, ordered=True)

        fig2 = px.pie(
            tmp,
            names="BedTime",
            hole=0.45,
            title="Bedtime Distribution (Weekdays)",
            color_discrete_sequence=SUNSET,
        )
        fig2.update_layout(showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)

        bedtime_counts = tmp["BedTime"].value_counts(dropna=False)
        after_12 = int(bedtime_counts.get("After 12 AM", 0))
        between_11_12 = int(bedtime_counts.get("11 PM–12 AM", 0))
        between_10_11 = int(bedtime_counts.get("10–11 PM", 0))
        between_9_10 = int(bedtime_counts.get("9–10 PM", 0))

        st.markdown(
            f"""
**Key Insights**
* **{after_12} students ({pct(after_12, total):.1f}%)** go to bed **after 12 AM** on weekdays.
* **{between_11_12} students ({pct(between_11_12, total):.1f}%)** sleep between **11 PM–12 AM**.
* Earlier bedtimes are uncommon: **{between_10_11} ({pct(between_10_11, total):.1f}%)** between **10–11 PM**, and **{between_9_10} ({pct(between_9_10, total):.1f}%)** between **9–10 PM**.

**Conclusion**
* Late bedtime is extremely common and likely contributes to short sleep duration when students must wake early for classes.
            """.strip()
        )
    else:
        st.warning("BedTime is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # ============================================================
    # NEW FIGURE A3 (OLD A4) — Sleep Quality by Bedtime
    # ============================================================
    st.subheader("Figure A3 — Sleep Quality by Bedtime")

    if {"BedTime", "SleepQuality_num"}.issubset(df.columns):
        df_plot = df.copy()
        df_plot["BedTime"] = df_plot["BedTime"].astype(str).str.strip()
        df_plot["BedTime"] = pd.Categorical(df_plot["BedTime"], categories=BEDTIME_ORDER, ordered=True)

        fig3 = px.violin(
            df_plot,
            x="BedTime",
            y="SleepQuality_num",
            box=True,
            points=False,
            title="Sleep Quality Across Bedtime Categories",
            category_orders={"BedTime": BEDTIME_ORDER},
            color_discrete_sequence=SUNSET,
        )
        fig3.update_layout(
            xaxis_title="Bedtime Category",
            yaxis_title="Sleep Quality (1=Poor, 5=Excellent)",
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown(
            """
**Key Insights**
* Later bedtime groups (especially **After 12 AM**) tend to show lower sleep quality and wider variation.
* Earlier bedtime groups are more stable with better perceived quality.

**Conclusion**
* Delayed sleep timing appears linked to poorer sleep experience; promoting earlier consistent bedtimes may improve sleep satisfaction.
            """.strip()
        )
    else:
        st.warning("BedTime or SleepQuality_num is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # ============================================================
    # NEW FIGURE A4 (OLD A5) — Co-occurrence Heatmap
    # ============================================================
    st.subheader("Figure A4 — Co-occurrence of Insomnia Symptoms")

    if {"DifficultyFallingAsleep", "NightWakeups"}.issubset(df.columns):
        heat = pd.crosstab(df["DifficultyFallingAsleep"], df["NightWakeups"])
        fig4 = px.imshow(
            heat,
            text_auto=True,
            title="Difficulty Falling Asleep vs Night Wakeups",
            color_continuous_scale=SUNSET,
        )
        fig4.update_layout(
            xaxis_title="Night Wakeups Frequency",
            yaxis_title="Difficulty Falling Asleep Frequency",
        )
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown(
            f"""
**Key Insights**
* The largest numbers cluster where both symptoms appear at similar frequencies, showing symptoms often occur together.
* **{both_n} students ({pct(both_n, total):.1f}%)** report **frequent** difficulty falling asleep and **frequent** night wakeups.

**Conclusion**
* Co-occurring symptoms indicate more severe sleep disruption, suggesting a subgroup that may need targeted support rather than general advice.
            """.strip()
        )
    else:
        st.warning("DifficultyFallingAsleep or NightWakeups is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # ============================================================
    # NEW FIGURE A5 (OLD A6) — Bedtime vs Sleep Duration Category
    # ============================================================
    st.subheader("Figure A5 — Bedtime vs Sleep Duration Category")

    if {"BedTime", "SleepDurationCategory"}.issubset(df.columns):
        tmp = df.copy()
        tmp["BedTime"] = tmp["BedTime"].astype(str).str.strip()
        tmp["SleepDurationCategory"] = tmp["SleepDurationCategory"].astype(str).str.strip()

        # enforce consistent ordering
        tmp["BedTime"] = pd.Categorical(tmp["BedTime"], categories=BEDTIME_ORDER, ordered=True)
        tmp["SleepDurationCategory"] = pd.Categorical(tmp["SleepDurationCategory"], categories=SLEEP_CAT_ORDER, ordered=True)

        tab = pd.crosstab(tmp["BedTime"], tmp["SleepDurationCategory"]).reindex(BEDTIME_ORDER, fill_value=0)
        melted = tab.reset_index().melt(id_vars="BedTime", var_name="SleepDurationCategory", value_name="Count")

        fig5 = px.bar(
            melted,
            x="BedTime",
            y="Count",
            color="SleepDurationCategory",
            barmode="stack",
            title="Sleep Duration Category Distribution Across Bedtime Groups",
            category_orders={"BedTime": BEDTIME_ORDER, "SleepDurationCategory": SLEEP_CAT_ORDER},
            color_discrete_sequence=SUNSET,
            labels={"BedTime": "Weekday Bedtime", "Count": "Number of Students"},
        )
        st.plotly_chart(fig5, use_container_width=True)

        # Insight numbers
        after12_total = int(tab.loc["After 12 AM"].sum()) if "After 12 AM" in tab.index else 0
        after12_short = int(tab.loc["After 12 AM", "Short (<6h)"]) if ("After 12 AM" in tab.index and "Short (<6h)" in tab.columns) else 0
        max_bedtime = tab.sum(axis=1).idxmax() if len(tab) else "N/A"
        max_bedtime_n = int(tab.sum(axis=1).max()) if len(tab) else 0

        st.markdown(
            f"""
**Key Insights**
* The **largest bedtime group** is **{max_bedtime}** with **{max_bedtime_n} students**, showing where most respondents fall.
* For **After 12 AM**, **{after12_short} out of {after12_total}** students are **short sleepers (<6h)**, suggesting late bedtime strongly aligns with insufficient sleep.
* Earlier bedtime groups show much smaller counts overall, meaning fewer students maintain early sleep schedules during weekdays.

**Conclusion**
* This figure connects **sleep timing** with **sleep duration**: students who sleep later are much more likely to fall into the short-sleep risk group.
* Interventions that target bedtime (consistent earlier sleep time) could indirectly improve total sleep duration.
            """.strip()
        )
    else:
        st.warning("BedTime or SleepDurationCategory is missing. Please verify Nazifa cleaning module.")


render()
