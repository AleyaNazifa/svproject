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

    st.title("Exploration Dashboard: Sleep Patterns & Insomnia Symptoms (Nazifa)")
    st.markdown(
        "This page explores **sleep duration**, **bedtime timing**, **sleep quality**, and **core insomnia symptoms** "
        "to identify sleep-risk patterns among UMK students."
    )

    st.markdown(
        """
<div class="card">
  <div class="card-title">🎯Objective 1 (Sleep Patterns)</div>
  <div class="interpretation">
    To analyze sleep patterns and insomnia severity among UMK students by examining sleep duration categories,
    bedtime habits, sleep quality across bedtimes, symptom co-occurrence, and how bedtime relates to sleep duration.
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

    # ============================================================
    # Figure A1 (OLD A2) — Sleep Duration Categories
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

        fig_a1 = px.bar(
            cat_counts,
            x="Category",
            y="Count",
            text="Count",
            title="Sleep Duration Category Distribution",
            category_orders={"Category": SLEEP_CAT_ORDER},
            color_discrete_sequence=SUNSET,
        )
        fig_a1.update_traces(textposition="outside", cliponaxis=False)
        fig_a1.update_layout(
            xaxis_title="Sleep Duration Category",
            yaxis_title="Number of Students",
            showlegend=False,
        )
        st.plotly_chart(fig_a1, use_container_width=True)

        st.markdown(
            """
**Key Insights**
- The majority of students fall into the **short sleep** category, indicating widespread insufficient sleep.
- A smaller group achieves **adequate sleep**, while **long sleep duration** is relatively uncommon.
- This distribution suggests meeting recommended sleep duration is not typical among respondents.

**Conclusion**
- Insufficient sleep appears to be the **dominant pattern** among UMK students.
- Sleep duration is a key risk factor that may contribute to fatigue, reduced concentration, and weaker academic functioning.
            """.strip()
        )
    else:
        st.warning("SleepDurationCategory is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # ============================================================
    # Figure A2 (OLD A3) — Weekday Bedtime Distribution
    # ============================================================
    st.subheader("Figure A2 — Weekday Bedtime Distribution")
    if "BedTime" in df.columns:
        tmp = df.copy()

        # Clean/standardize bedtime labels, avoid "null" in plot
        tmp["BedTime"] = tmp["BedTime"].astype(str).str.strip()
        tmp.loc[tmp["BedTime"].isin(["nan", "None", "null", ""]), "BedTime"] = np.nan
        tmp = tmp.dropna(subset=["BedTime"])

        # Enforce category order
        tmp["BedTime"] = pd.Categorical(tmp["BedTime"], categories=BEDTIME_ORDER, ordered=True)

        fig_a2 = px.pie(
            tmp,
            names="BedTime",
            hole=0.45,
            title="Bedtime Distribution (Weekdays)",
            color_discrete_sequence=SUNSET,
        )
        fig_a2.update_layout(showlegend=True)
        st.plotly_chart(fig_a2, use_container_width=True)

        st.markdown(
            """
**Key Insights**
- Most students report **very late bedtimes**, particularly after midnight on weekdays.
- Bedtimes before 11 PM are uncommon, showing a strong shift toward delayed sleep schedules.
- This pattern suggests limited opportunity for sufficient sleep on academic days.

**Conclusion**
- Late bedtime habits are a **central behavioural contributor** to short sleep duration.
- Improving sleep timing (not only sleep hours) is important for improving sleep health among students.
            """.strip()
        )
    else:
        st.warning("BedTime is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # ============================================================
    # Figure A3 (OLD A4) — Sleep Quality by Bedtime
    # ============================================================
    st.subheader("Figure A3 — Sleep Quality by Bedtime")
    if {"BedTime", "SleepQuality_num"}.issubset(df.columns):
        df_plot = df.copy()
        df_plot["BedTime"] = df_plot["BedTime"].astype(str).str.strip()
        df_plot.loc[df_plot["BedTime"].isin(["nan", "None", "null", ""]), "BedTime"] = np.nan
        df_plot = df_plot.dropna(subset=["BedTime"])

        df_plot["BedTime"] = pd.Categorical(df_plot["BedTime"], categories=BEDTIME_ORDER, ordered=True)

        fig_a3 = px.violin(
            df_plot,
            x="BedTime",
            y="SleepQuality_num",
            box=True,
            points=False,
            title="Sleep Quality Across Bedtime Categories",
            category_orders={"BedTime": BEDTIME_ORDER},
            color_discrete_sequence=SUNSET,
        )
        fig_a3.update_layout(
            xaxis_title="Bedtime Category",
            yaxis_title="Sleep Quality (1=Poor, 5=Excellent)",
            showlegend=False,
        )
        st.plotly_chart(fig_a3, use_container_width=True)

        st.markdown(
            """
**Key Insights**
- Sleep quality varies noticeably across bedtime groups.
- Later bedtime groups tend to show lower and more inconsistent sleep quality ratings.
- Earlier bedtime groups show more stable and generally better sleep experiences.

**Conclusion**
- Delayed sleep timing is associated with **poorer perceived sleep quality**.
- Encouraging earlier and consistent bedtimes is a practical sleep hygiene recommendation.
            """.strip()
        )
    else:
        st.warning("BedTime or SleepQuality_num is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # ============================================================
    # Figure A4 (OLD A5) — Co-occurrence of Insomnia Symptoms
    # ============================================================
    st.subheader("Figure A4 — Co-occurrence of Insomnia Symptoms")
    if {"DifficultyFallingAsleep", "NightWakeups"}.issubset(df.columns):
        heat = pd.crosstab(df["DifficultyFallingAsleep"], df["NightWakeups"])

        fig_a4 = px.imshow(
            heat,
            text_auto=True,
            title="Difficulty Falling Asleep vs Night Wakeups",
            color_continuous_scale=SUNSET,
        )
        fig_a4.update_layout(
            xaxis_title="Night Wakeups Frequency",
            yaxis_title="Difficulty Falling Asleep Frequency",
        )
        st.plotly_chart(fig_a4, use_container_width=True)

        st.markdown(
            """
**Key Insights**
- Insomnia symptoms often **overlap**, rather than appearing independently.
- Higher frequencies of difficulty falling asleep frequently align with more frequent night wakeups.
- This suggests compounded sleep disruption for a subset of students.

**Conclusion**
- Co-occurring symptoms may reflect **more severe sleep disturbance**.
- Students experiencing overlapping symptoms may benefit from targeted support beyond general sleep advice.
            """.strip()
        )
    else:
        st.warning("DifficultyFallingAsleep or NightWakeups is missing. Please verify Nazifa cleaning module.")

    st.divider()

    # ============================================================
    # Figure A5 (OLD A6) — Bedtime vs Sleep Duration Category
    # ============================================================
    st.subheader("Figure A5 — Bedtime vs Sleep Duration Category")
    if {"BedTime", "SleepDurationCategory"}.issubset(df.columns):
        tmp2 = df.copy()
        tmp2["BedTime"] = tmp2["BedTime"].astype(str).str.strip()
        tmp2.loc[tmp2["BedTime"].isin(["nan", "None", "null", ""]), "BedTime"] = np.nan
        tmp2 = tmp2.dropna(subset=["BedTime"])

        tmp2["BedTime"] = pd.Categorical(tmp2["BedTime"], categories=BEDTIME_ORDER, ordered=True)
        tmp2["SleepDurationCategory"] = pd.Categorical(
            tmp2["SleepDurationCategory"].astype(str).str.strip(),
            categories=SLEEP_CAT_ORDER,
            ordered=True,
        )

        # Stacked bar across bedtime groups
        fig_a5 = px.histogram(
            tmp2,
            x="BedTime",
            color="SleepDurationCategory",
            barmode="stack",
            title="Sleep Duration Category Distribution Across Bedtime Groups",
            category_orders={"BedTime": BEDTIME_ORDER, "SleepDurationCategory": SLEEP_CAT_ORDER},
            color_discrete_sequence=SUNSET,
        )
        fig_a5.update_layout(
            xaxis_title="Weekday Bedtime",
            yaxis_title="Number of Students",
            legend_title_text="Sleep Duration Category",
        )
        st.plotly_chart(fig_a5, use_container_width=True)

        st.markdown(
            """
**Key Insights**
- Sleep duration patterns change clearly across bedtime groups.
- Later bedtimes, especially after midnight, tend to align with a higher concentration of short sleepers.
- Earlier bedtime groups show a more balanced distribution and a higher presence of adequate sleep.

**Conclusion**
- Bedtime timing appears to be a strong behavioural factor shaping sleep duration.
- Encouraging earlier bedtimes may help students move from short-sleep patterns toward more adequate sleep.
            """.strip()
        )
    else:
        st.warning("BedTime or SleepDurationCategory is missing. Please verify Nazifa cleaning module.")


render()
