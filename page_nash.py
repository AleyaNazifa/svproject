import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio

from data_loader import display_sidebar_info, get_df

pio.templates.default = "plotly_white"


# ==========================================
# Helper
# ==========================================
def pct(n, total):
    return (n / total * 100) if total else 0.0


# ==========================================
# Main Page
# ==========================================
def render():
    display_sidebar_info()

    df = get_df()
    if df is None or df.empty:
        st.error("No data available.")
        return

    total = len(df)

    st.title("Lifestyle & Stress Factors and Insomnia Severity")
    st.markdown(
        """
This dashboard investigates how **specific lifestyle behaviours** and **academic stress levels**
are associated with **insomnia severity** among university students.  
The focus is on identifying *which behaviours show stronger visual links* to higher insomnia scores.
        """
    )
    st.divider()

    # ==========================================
    # Key Metrics
    # ==========================================
    st.subheader("Overview of Lifestyle Risk Prevalence")

    col1, col2, col3, col4 = st.columns(4)

    high_device = df["DeviceUsage"].astype(str).str.contains("Always|Often", na=False).sum()
    high_caffeine = df["CaffeineConsumption"].astype(str).str.contains("Always|Often", na=False).sum()
    low_activity = df["PhysicalActivity"].astype(str).str.contains("Never|Rarely", na=False).sum()
    high_stress = df["StressLevel"].astype(str).str.contains("High|Extremely", na=False).sum()

    col1.metric("📱 Frequent Device Use", f"{pct(high_device, total):.1f}%")
    col2.metric("☕ High Caffeine Intake", f"{pct(high_caffeine, total):.1f}%")
    col3.metric("🏃 Low Physical Activity", f"{pct(low_activity, total):.1f}%")
    col4.metric("🎓 High Academic Stress", f"{pct(high_stress, total):.1f}%")

    st.divider()

    # ==========================================
    # Figure C1 — Device Usage Distribution
    # ==========================================
    st.subheader("Figure C1 — Device Usage Before Sleep")

    device_counts = df["DeviceUsage"].value_counts().reset_index()
    device_counts.columns = ["DeviceUsage", "Count"]

    fig1 = px.bar(
        device_counts,
        x="DeviceUsage",
        y="Count",
        title="Distribution of Device Usage Frequency Before Sleep",
    )
    fig1.update_layout(
        xaxis_title="Device Usage Frequency",
        yaxis_title="Number of Students"
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown(
        """
**Key Insights**
- The bar chart shows that device usage before sleep is **not evenly distributed**.
- A visibly larger group of students reports using devices **often or always** compared to those who rarely or never use devices.
- This indicates that pre-bed screen exposure is a **common behaviour**, not a marginal one.

**Conclusion**
- Since frequent device use is widespread, it represents a **population-level risk factor**.
- Any association found later between device use and insomnia severity affects a **substantial portion of students**, increasing its practical importance.
        """
    )

    st.divider()

    # ==========================================
    # Figure C2 — Device Usage vs Insomnia Severity
    # ==========================================
    st.subheader("Figure C2 — Insomnia Severity by Device Usage")

    fig2 = px.box(
        df,
        x="DeviceUsage",
        y="InsomniaSeverity_index",
        title="Insomnia Severity Across Device Usage Levels",
    )
    fig2.update_layout(
        xaxis_title="Device Usage Before Sleep",
        yaxis_title="Insomnia Severity Index (ISI)"
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(
        """
**Key Insights**
- Median insomnia scores increase as device usage frequency increases.
- Students who report **always using devices** before sleep show **higher central ISI values** and wider score spread.
- Lower device-use groups show tighter distributions with generally lower ISI scores.

**Conclusion**
- This pattern suggests that **frequent pre-bed device use is associated with more severe insomnia symptoms**.
- The increasing spread also indicates that heavy device use may exacerbate sleep problems for some students more than others.
        """
    )

    st.divider()

    # ==========================================
    # Figure C3 — Caffeine Consumption vs ISI
    # ==========================================
    st.subheader("Figure C3 — Insomnia Severity by Caffeine Consumption")

    fig3 = px.box(
        df,
        x="CaffeineConsumption",
        y="InsomniaSeverity_index",
        title="Insomnia Severity Across Caffeine Consumption Levels",
    )
    fig3.update_layout(
        xaxis_title="Caffeine Consumption Frequency",
        yaxis_title="Insomnia Severity Index (ISI)"
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown(
        """
**Key Insights**
- Students with **frequent caffeine consumption** show noticeably higher median insomnia severity.
- Occasional or rare caffeine users tend to cluster at lower ISI scores.
- The difference is not driven by a few outliers but by a **shift in the entire distribution**.

**Conclusion**
- Regular caffeine intake appears to be a **consistent contributor** to increased insomnia severity.
- This supports the idea that stimulant exposure, especially later in the day, can systematically worsen sleep outcomes.
        """
    )

    st.divider()

    # ==========================================
    # Figure C4 — Stress Level vs Insomnia Severity
    # ==========================================
    st.subheader("Figure C4 — Insomnia Severity by Academic Stress Level")

    fig4 = px.violin(
        df,
        x="StressLevel",
        y="InsomniaSeverity_index",
        box=True,
        title="Insomnia Severity Across Academic Stress Levels",
    )
    fig4.update_layout(
        xaxis_title="Academic Stress Level",
        yaxis_title="Insomnia Severity Index (ISI)"
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown(
        """
**Key Insights**
- The violin plot shows a **clear upward shift** in insomnia severity as stress levels increase.
- High and extremely stressed students have both **higher medians** and **wider distributions**, indicating more severe and variable sleep problems.
- Low-stress students cluster strongly at lower ISI values.

**Conclusion**
- Academic stress demonstrates the **strongest visual association** with insomnia severity among all factors examined.
- This suggests stress is not only linked to sleep problems but may also amplify the effects of other lifestyle risks.
        """
    )

    st.divider()

    # ==========================================
    # Figure C5 — Lifestyle Risk Score vs ISI
    # ==========================================
    st.subheader("Figure C5 — Combined Lifestyle Risk vs Insomnia Severity")

    fig5 = px.scatter(
        df,
        x="Lifestyle_Risk",
        y="InsomniaSeverity_index",
        opacity=0.75,
        title="Accumulated Lifestyle Risk Score vs Insomnia Severity",
    )
    fig5.update_layout(
        xaxis_title="Lifestyle Risk Score",
        yaxis_title="Insomnia Severity Index (ISI)"
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown(
        """
**Key Insights**
- Points trend upward as lifestyle risk score increases, indicating a **positive association**.
- Students with low risk scores rarely show high insomnia severity.
- High insomnia scores become increasingly common as multiple risk behaviours accumulate.

**Conclusion**
- Insomnia severity appears to be **cumulative**, increasing as multiple unhealthy behaviours co-occur.
- This reinforces the importance of **multi-factor interventions**, rather than focusing on a single lifestyle behaviour.
        """
    )

    st.success(
        "Overall conclusion: Academic stress, frequent device usage, and regular caffeine consumption show clear and interpretable "
        "associations with increased insomnia severity. Sleep problems among students are best understood as the result of "
        "multiple interacting lifestyle and stress-related factors."
    )


render()
