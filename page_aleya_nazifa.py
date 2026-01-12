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


def _count(series: pd.Series, value: str) -> int:
    return int(series.astype(str).eq(value).sum())


def render():
    # Sidebar status + cached auto-refresh logic lives in data_loader.py
    display_sidebar_info()

    raw = get_df()
    df = prepare_nazifa_data(raw)

    if df is None or df.empty:
        st.error("No data available.")
        return

    total = len(df)

    # -----------------------------
    # Header
    # -----------------------------
    st.title("Interpretation Dashboard: Sleep Patterns & Insomnia Symptoms (Nazifa)")
    st.markdown(
        "This page explores **sleep duration**, **bedtime timing**, **sleep quality**, and **core insomnia symptoms** "
        "to identify sleep-risk patterns among UMK students."
    )

    # Objective card (moved from Home)
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

    # -----------------------------
    # Key Metrics
    # -----------------------------
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

    # =========================================================
    # Figure A1 — Boxplot (SleepHours_est)
    # =========================================================
    st.subheader("Figure A1 — Sleep Duration (Estimated Hours) — Boxplot")

    if "SleepHours_est" in df.columns:
        a1 = pd.to_numeric(df["SleepHours_est"], errors="coerce").dropna()

        if a1.empty:
            st.warning("SleepHours_est has no valid numeric values.")
        else:
            mean_sleep = float(a1.mean())
            median_sleep = float(a1.median())
            q1 = float(a1.quantile(0.25))
            q3 = float(a1.quantile(0.75))
            min_sleep = float(a1.min())
            max_sleep = float(a1.max())

            # Boxplot
            fig1 = px.box(
                df,
                y="SleepHours_est",
                points="all",  # show individual students (better for discrete survey bins)
                title="Distribution of Sleep Duration (Estimated Hours)",
                color_discrete_sequence=[SUNSET[3]],
            )
            fig1.update_layout(
                yaxis_title="Hours of Sleep (Estimated)",
                xaxis_title="",
                showlegend=False,
            )
            st.plotly_chart(fig1, use_container_width=True)

            st.markdown(
                f"""
**Key Insights**
* The **median** sleep duration is **{median_sleep:.2f} hours**, which is below recommended levels for young adults.
* The middle 50% of students (IQR) sleep between **{q1:.2f} and {q3:.2f} hours**, showing that short sleep is typical for many respondents.
* The overall range spans from **{min_sleep:.2f} to {max_sleep:.2f} hours**, with visible extreme values indicating very low or very high sleepers.
* Mean sleep is **{mean_sleep:.2f} hours**, supporting that average sleep in the sample is below ideal duration.

**Conclusion**
* The boxplot confirms that insufficient sleep is common across the sample—not driven by only a few outliers.
* This pattern suggests elevated risk of fatigue and reduced daytime functioning, reinforcing the need for targeted sleep hygiene awareness.
                """.strip()
            )
    else:
        st.warning("SleepHours_est is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # =========================================================
    # Figure A2 — Sleep Duration Categories
    # =========================================================
    st.subheader("Figure A2 — Sleep Duration Categories (Short / Adequate / Long)")

    if "SleepDurationCategory" in df.columns:
        cat_counts = (
            df["SleepDurationCategory"]
            .astype(str)
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
* Categorisation groups students into clear risk-relevant sleep duration bands.
* **{short_count} students ({pct(short_count, total):.1f}%)** are **short sleepers** (<6 hours).
* **{adequate_count} students ({pct(adequate_count, total):.1f}%)** achieve **adequate sleep** (6–8 hours).
* **{long_count} students ({pct(long_count, total):.1f}%)** report **long sleep** (>8 hours).

**Conclusion**
* The dominance of short sleep indicates that insufficient sleep is widespread among respondents.
* This categorisation cleanly identifies the priority at-risk subgroup for sleep improvement interventions.
            """.strip()
        )
    else:
        st.warning("SleepDurationCategory is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # =========================================================
    # Figure A3 — Bedtime Distribution
    # =========================================================
    st.subheader("Figure A3 — Weekday Bedtime Distribution")

    if "BedTime" in df.columns:
        tmp = df.copy()
        tmp["BedTime"] = tmp["BedTime"].astype(str).str.strip()
        tmp["BedTime"] = pd.Categorical(tmp["BedTime"], categories=BEDTIME_ORDER, ordered=True)

        fig3 = px.pie(
            tmp.dropna(subset=["BedTime"]),
            names="BedTime",
            hole=0.45,
            title="Bedtime Distribution (Weekdays)",
            color_discrete_sequence=SUNSET,
        )
        fig3.update_layout(showlegend=True)
        st.plotly_chart(fig3, use_container_width=True)

        bedtime_counts = tmp["BedTime"].value_counts(dropna=False)

        after_12 = int(bedtime_counts.get("After 12 AM", 0))
        between_11_12 = int(bedtime_counts.get("11 PM–12 AM", 0))
        between_10_11 = int(bedtime_counts.get("10–11 PM", 0))
        between_9_10 = int(bedtime_counts.get("9–10 PM", 0))

        st.markdown(
            f"""
**Key Insights**
* Bedtime timing is heavily skewed toward late-night schedules.
* **{after_12} students ({pct(after_12, total):.1f}%)** report going to bed **after 12 AM**.
* **{between_11_12} students ({pct(between_11_12, total):.1f}%)** sleep between **11 PM–12 AM**.
* Early bedtimes are uncommon: **{between_10_11} students ({pct(between_10_11, total):.1f}%)** (10–11 PM) and **{between_9_10} students ({pct(between_9_10, total):.1f}%)** (9–10 PM).

**Conclusion**
* Delayed bedtime is highly prevalent and is likely a major contributor to short sleep duration—especially with early class schedules.
* Bedtime timing represents a practical behavioural target for improving sleep duration and sleep regularity.
            """.strip()
        )
    else:
        st.warning("BedTime is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # =========================================================
    # Figure A4 — Sleep Quality by Bedtime
    # =========================================================
    st.subheader("Figure A4 — Sleep Quality by Bedtime")

    if {"BedTime", "SleepQuality_num"}.issubset(df.columns):
        df_plot = df.copy()
        df_plot["BedTime"] = df_plot["BedTime"].astype(str).str.strip()
        df_plot["BedTime"] = pd.Categorical(df_plot["BedTime"], categories=BEDTIME_ORDER, ordered=True)

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
* Sleep quality differs across bedtime categories, with later bedtime groups typically showing lower ratings or greater variability.
* Earlier bedtime groups tend to have more stable sleep quality scores.

**Conclusion**
* Delayed sleep timing is likely linked to poorer subjective sleep experience.
* Promoting earlier and more consistent bedtimes may improve perceived sleep quality and overall sleep satisfaction.
            """.strip()
        )
    else:
        st.warning("BedTime or SleepQuality_num is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # =========================================================
    # Figure A5 — Symptom Co-occurrence Heatmap
    # =========================================================
    st.subheader("Figure A5 — Co-occurrence of Insomnia Symptoms")

    if {"DifficultyFallingAsleep", "NightWakeups"}.issubset(df.columns):
        heat = pd.crosstab(df["DifficultyFallingAsleep"].astype(str), df["NightWakeups"].astype(str))
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
* The heatmap shows that insomnia symptoms often overlap rather than occur independently.
* Higher counts appear where both symptoms occur at similar frequencies (suggesting co-occurrence).
* **{both_n} students ({pct(both_n, total):.1f}%)** report **frequent** difficulty falling asleep together with **frequent** night awakenings.

**Conclusion**
* Co-occurring symptoms indicate more severe sleep disruption and a higher-risk subgroup.
* This group may require more targeted support (structured sleep strategies) rather than general sleep advice.
            """.strip()
        )
    else:
        st.warning("DifficultyFallingAsleep or NightWakeups is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # =========================================================
    # Figure A6 — Bedtime vs Sleep Duration Category (NEW)
    # =========================================================
    st.subheader("Figure A6 — Bedtime vs Sleep Duration Category")

    if {"BedTime", "SleepDurationCategory"}.issubset(df.columns):
        df_a6 = df.copy()
        df_a6["BedTime"] = df_a6["BedTime"].astype(str).str.strip()
        df_a6["BedTime"] = pd.Categorical(df_a6["BedTime"], categories=BEDTIME_ORDER, ordered=True)
        df_a6["SleepDurationCategory"] = pd.Categorical(
            df_a6["SleepDurationCategory"].astype(str),
            categories=SLEEP_CAT_ORDER,
            ordered=True,
        )

        tab_a6 = pd.crosstab(df_a6["BedTime"], df_a6["SleepDurationCategory"]).reindex(BEDTIME_ORDER, fill_value=0)
        melted_a6 = tab_a6.reset_index().melt(id_vars="BedTime", var_name="SleepDurationCategory", value_name="Count")

        fig6 = px.bar(
            melted_a6,
            x="BedTime",
            y="Count",
            color="SleepDurationCategory",
            barmode="stack",
            title="Sleep Duration Category Distribution Across Bedtime Groups",
            category_orders={"BedTime": BEDTIME_ORDER, "SleepDurationCategory": SLEEP_CAT_ORDER},
            color_discrete_sequence=SUNSET,
            labels={"Count": "Number of Students", "BedTime": "Weekday Bedtime"},
        )
        fig6.update_layout(xaxis_title="Weekday Bedtime", yaxis_title="Number of Students")
        st.plotly_chart(fig6, use_container_width=True)

        # Simple highlight: short sleepers among after-12 group
        after12_short = int(tab_a6.loc["After 12 AM", "Short (<6h)"]) if "After 12 AM" in tab_a6.index and "Short (<6h)" in tab_a6.columns else 0
        after12_total = int(tab_a6.loc["After 12 AM"].sum()) if "After 12 AM" in tab_a6.index else 0

        st.markdown(
            f"""
**Key Insights**
* This chart links *sleep timing* (bedtime) with *sleep duration risk* (short/adequate/long).
* Late bedtime groups (especially **After 12 AM**) contain a high concentration of **short sleepers**, suggesting reduced sleep opportunity.
* In the **After 12 AM** group, **{after12_short} out of {after12_total} students ({pct(after12_short, after12_total):.1f}%)** are short sleepers (<6h).

**Conclusion**
* Students who go to bed late are more likely to fall into the short-sleep category, reinforcing late bedtime as a key behavioural driver of sleep deprivation.
* Interventions that encourage earlier bedtime (or better time management at night) may improve sleep duration outcomes.
            """.strip()
        )
    else:
        st.warning("BedTime or SleepDurationCategory is missing. Please verify Nazifa cleaning module.")


render()
