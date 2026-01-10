import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import display_sidebar_info, get_df


# -----------------------------
# Helpers
# -----------------------------
def pct(n, total):
    return (n / total * 100) if total else 0


def safe_mean(series, default=None):
    x = pd.to_numeric(series, errors="coerce")
    return float(x.mean()) if x.notna().any() else default


def style_plotly(fig, x_title=None, y_title=None):
    fig.update_layout(
        margin=dict(l=10, r=10, t=60, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=18),
        legend_title_text="",
    )
    if x_title:
        fig.update_xaxes(title_text=x_title)
    if y_title:
        fig.update_yaxes(title_text=y_title)
    return fig


# -----------------------------
# Main Page
# -----------------------------
def render():
    display_sidebar_info()
    df = get_df()

    if df is None or len(df) == 0:
        st.error("No data available.")
        return

    total = len(df)

    # Optional status info
    last_updated = None
    if "Timestamp" in df.columns:
        ts = pd.to_datetime(df["Timestamp"], errors="coerce")
        last_updated = ts.max()

    faculties_n = int(df["Faculty"].nunique()) if "Faculty" in df.columns else 0

    # =========================
    # HERO HEADER
    # =========================
    st.title("🎓 UMK Insomnia & Educational Outcomes Dashboard")
    st.markdown(
        "An interactive visualization of **sleep patterns**, **academic impact**, and **lifestyle factors** among UMK students."
    )

    # Hero card (pretty intro + navigation hint)
    st.markdown(
        f"""
<div class="card">
  <div class="card-title">Dashboard Overview</div>
  <div class="interpretation">
    This dashboard summarises survey findings and provides interpretation-ready visualisations for reporting.
    Use the sidebar menu to explore:
    <ul>
      <li><b>Sleep Patterns</b> (Nazifa): duration, bedtime timing, sleep quality, and insomnia symptom overlap.</li>
      <li><b>Academic Impact</b> (Aelyana): how insomnia relates to focus, fatigue, assignment performance, and grades.</li>
      <li><b>Lifestyle Factors</b> (Nash): device use, caffeine, physical activity, stress, and combined lifestyle risk.</li>
    </ul>
    <div class="hr"></div>
    <b>Dataset snapshot:</b> {total:,} responses{f", {faculties_n} faculties" if faculties_n else ""}{f", last updated: {last_updated.strftime('%Y-%m-%d %H:%M')}" if last_updated is not None else ""}.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # =========================
    # KEY METRICS
    # =========================
    st.subheader("Key Summary Metrics")
    col1, col2, col3, col4 = st.columns(4)

    avg_sleep = safe_mean(df["SleepHours_est"], default=None) if "SleepHours_est" in df.columns else None

    high_isi = None
    if "InsomniaSeverity_index" in df.columns:
        isi = pd.to_numeric(df["InsomniaSeverity_index"], errors="coerce")
        high_isi = int((isi >= 15).sum())

    high_stress = None
    if "StressLevel" in df.columns:
        high_stress = int(
            df["StressLevel"].astype(str).str.contains("High|Extremely", na=False).sum()
        )

    col1.metric("Total Responses", f"{total:,}", border=True)
    col2.metric("Avg Sleep Duration", f"{avg_sleep:.2f} hours" if avg_sleep is not None else "N/A", border=True)
    col3.metric(
        "High Insomnia Risk (ISI ≥ 15)",
        f"{high_isi:,}" if high_isi is not None else "N/A",
        f"{pct(high_isi, total):.1f}%" if high_isi is not None else None,
        help="Count and percentage of students in moderate-to-severe insomnia range (threshold used for overview).",
        border=True,
    )
    col4.metric(
        "High Stress Levels",
        f"{high_stress:,}" if high_stress is not None else "N/A",
        f"{pct(high_stress, total):.1f}%" if high_stress is not None else None,
        help='Students reporting "High" or "Extremely High" stress.',
        border=True,
    )

    st.divider()

    # =========================
    # OVERVIEW VISUALIZATIONS
    # =========================
    st.subheader("Overall Data Overview")
    col_left, col_right = st.columns(2)

    # O1: ISI Distribution
    with col_left:
        if "InsomniaSeverity_index" in df.columns:
            fig = px.histogram(
                df,
                x="InsomniaSeverity_index",
                nbins=10,
                title="Insomnia Severity Index (ISI) Distribution",
                color_discrete_sequence=px.colors.sequential.Sunset,
            )
            fig = style_plotly(fig, "ISI Score", "Number of Students")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Figure O1. Distribution of insomnia severity index (ISI) scores among UMK students.")
        else:
            st.info("ISI score is not available in the dataset yet.")

    # O2: Faculty Distribution
    with col_right:
        if "Faculty" in df.columns:
            faculty_counts = df["Faculty"].value_counts().head(10).reset_index()
            faculty_counts.columns = ["Faculty", "Count"]

            fig = px.bar(
                faculty_counts,
                x="Count",
                y="Faculty",
                orientation="h",
                title="Top Faculties Represented in Survey (Top 10)",
                color_discrete_sequence=px.colors.sequential.Sunset,
            )
            fig = style_plotly(fig, "Number of Students", "Faculty")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Figure O2. Distribution of survey respondents across faculties (top 10).")
        else:
            st.info("Faculty column is not available in the dataset yet.")

    st.divider()

    # =========================
    # RAW DATA
    # =========================
    with st.expander("📋 View Raw Survey Data", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            label="📥 Download Dataset (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="umk_insomnia_survey_data.csv",
            mime="text/csv",
            use_container_width=True,
        )


render()
