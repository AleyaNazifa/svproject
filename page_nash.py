import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio

from data_loader import display_sidebar_info, get_df

pio.templates.default = "plotly_white"

TEXT = "#1F2937"
GRID = "rgba(148,163,184,0.25)"

GOOD = "#22C55E"
WARN = "#F59E0B"
RISK = "#EF4444"
NEUTRAL = "#64748B"


def pct(n, total):
    return (n / total * 100) if total else 0


def style(fig, title, xlab=None, ylab=None):
    fig.update_layout(
        title=title,
        font=dict(color=TEXT),
        title_font=dict(size=22, color=TEXT),
        margin=dict(l=10, r=10, t=55, b=10),
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False),
        legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    if xlab:
        fig.update_xaxes(title_text=xlab)
    if ylab:
        fig.update_yaxes(title_text=ylab)
    return fig


def render():
    display_sidebar_info()
    df = get_df()

    if df is None or len(df) == 0:
        st.error("No data available.")
        return

    total = len(df)

    st.title("🏃 Lifestyle Factors Analysis (Nash)")
    st.markdown("This page explores lifestyle behaviours linked to insomnia: **device usage**, **caffeine**, **exercise**, and **stress**.")

    # Objective: per-page
    st.markdown(
        """
<div class="card">
  <div class="card-title">Objective (Lifestyle Factors)</div>
  <div class="interpretation">
    To investigate lifestyle and stress-related factors associated with sleep disruption by visualising:
    (C1) device usage frequency, (C2) overall lifestyle risk profile, (C3) behaviour hierarchy (stress→caffeine→device),
    (C4) lifestyle risk vs insomnia severity, and (C5) coupling between device use and caffeine consumption.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # =========================
    # C1 Bar — Device usage
    # =========================
    device_counts = df["DeviceUsage"].value_counts().reset_index()
    device_counts.columns = ["DeviceUsage", "Count"]

    fig = px.bar(device_counts, x="DeviceUsage", y="Count", color_discrete_sequence=[NEUTRAL])
    fig = style(fig, "Device Usage Before Sleep", "Frequency", "Number of Students")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Figure C1. Bar chart of device usage frequency before bedtime.")

    heavy = df["DeviceUsage"].astype(str).str.contains("Always|Often", na=False).sum()
    st.markdown(
        f"**Interpretation (C1).** **{heavy} students ({pct(heavy,total):.1f}%)** report frequent device use before sleep. "
        "High screen exposure may delay sleep onset via blue light and mental stimulation, contributing to poorer sleep hygiene."
    )

    # =========================
    # C2 Radar — Lifestyle risk profile
    # =========================
    risk = {
        "Device Use": (df["DeviceUsage"].astype(str).str.contains("Always|Often", na=False)).mean(),
        "Caffeine": (df["CaffeineConsumption"].astype(str).str.contains("Always|Often", na=False)).mean(),
        "Stress": (df["StressLevel"].astype(str).str.contains("High|Extremely", na=False)).mean(),
        "Inactivity": (df["PhysicalActivity"].astype(str).str.contains("Never|Rarely", na=False)).mean(),
    }
    radar_df = pd.DataFrame({"Factor": list(risk.keys()), "Score": list(risk.values())})

    fig = px.line_polar(radar_df, r="Score", theta="Factor", line_close=True, color_discrete_sequence=[WARN])
    fig = style(fig, "Average Lifestyle Risk Profile")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Figure C2. Radar chart summarizing prevalence of key lifestyle risks.")

    st.markdown(
        "**Interpretation (C2).** Higher values indicate a greater proportion of students exposed to that lifestyle risk. "
        "Stress and device use often dominate, suggesting interventions targeting these factors may yield meaningful sleep improvements."
    )

    # =========================
    # C3 Sunburst — Stress → Caffeine → Device
    # =========================
    fig = px.sunburst(
        df,
        path=["StressLevel", "CaffeineConsumption", "DeviceUsage"],
        color="StressLevel",
        color_discrete_sequence=[GOOD, WARN, RISK, NEUTRAL],
    )
    fig = style(fig, "Stress → Caffeine → Device Usage (Behaviour Hierarchy)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Figure C3. Sunburst chart showing co-occurrence of stress, caffeine use, and device usage.")

    st.markdown(
        "**Interpretation (C3).** The hierarchy highlights how higher stress may co-occur with increased caffeine use and device usage. "
        "These behaviours can reinforce each other and amplify sleep disruption, supporting multi-pronged sleep hygiene strategies."
    )

    # =========================
    # C4 Bubble — Lifestyle_Risk vs ISI
    # =========================
    fig = px.scatter(
        df,
        x="Lifestyle_Risk",
        y="InsomniaSeverity_index",
        size="Lifestyle_Risk",
        color="StressLevel",
        opacity=0.85,
        color_discrete_sequence=[GOOD, WARN, RISK, NEUTRAL],
    )
    fig = style(fig, "Lifestyle Risk Score vs Insomnia Severity", "Lifestyle Risk (0–11)", "ISI Score (0–28)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Figure C4. Bubble plot of lifestyle risk score versus insomnia severity (colored by stress).")

    st.markdown(
        "**Interpretation (C4).** Students with higher lifestyle risk scores generally show higher insomnia severity, "
        "suggesting behavioural risks accumulate. Stress colouring reinforces psychological load as a key driver of sleep disruption."
    )

    # =========================
    # C5 Heatmap — Device × Caffeine
    # =========================
    heat = pd.crosstab(df["DeviceUsage"], df["CaffeineConsumption"])
    fig = px.imshow(heat, text_auto=True, color_continuous_scale=["#ECFDF5", WARN, RISK])
    fig = style(fig, "Device Usage vs Caffeine Consumption")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Figure C5. Heatmap of device usage frequency against caffeine consumption frequency.")

    st.markdown(
        "**Interpretation (C5).** Concentration of counts in higher device and higher caffeine categories indicates behavioural coupling. "
        "This pairing may jointly worsen sleep outcomes by delaying bedtime and reducing sleep depth, strengthening the case for targeted behaviour change."
    )


render()
