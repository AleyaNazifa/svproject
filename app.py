import streamlit as st

st.set_page_config(
    page_title="UMK Insomnia Dashboard",
    page_icon="😴",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
/* ---- App background ---- */
.main {
    background: #F8FAFC; /* slate-50 */
}

/* ---- Sidebar background ---- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%); /* slate-900 -> slate-800 */
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: #E2E8F0 !important; /* slate-200 */
}

/* Sidebar group header ("Menu") */
[data-testid="stSidebar"] h2 {
    color: #F1F5F9 !important; /* slate-100 */
    font-weight: 800 !important;
    letter-spacing: 0.2px;
}

/* ---- Sidebar menu links ---- */
[data-testid="stSidebar"] a {
    border-radius: 12px;
    padding: 10px 12px;
    margin: 2px 0px;
    text-decoration: none;
    transition: background 120ms ease-in-out;
}

/* Hover */
[data-testid="stSidebar"] a:hover {
    background: rgba(148,163,184,0.18);
}

/* Selected item */
[data-testid="stSidebar"] [aria-current="page"] {
    background: rgba(148,163,184,0.22) !important;
    border-radius: 12px;
}

/* ---- Headings ---- */
h1, h2, h3 {
    color: #0F172A; /* slate-900 */
}

/* ---- Card container ---- */
.card {
    background: white;
    border: 1px solid rgba(148,163,184,0.25);
    border-radius: 16px;
    padding: 18px 18px 10px 18px;
    box-shadow: 0 6px 18px rgba(15,23,42,0.06);
    margin-bottom: 16px;
}

/* Card title */
.card-title {
    font-size: 16px;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 6px;
}

/* Figure caption */
.figure-caption {
    font-size: 13px;
    color: #475569;
    margin-top: -6px;
}

/* Interpretation */
.interpretation {
    color: #334155;
    line-height: 1.6;
    font-size: 14px;
}

/* Divider */
.hr {
    height: 1px;
    background: rgba(148,163,184,0.35);
    margin: 14px 0px;
    border-radius: 5px;
}
</style>
""",
    unsafe_allow_html=True,
)

home = st.Page("home.py", title="Homepage", icon="🏠", default=True)
aleya_nazifa = st.Page("page_aleya_nazifa.py", title="Sleep Patterns", icon="😴")
nash = st.Page("page_nash.py", title="Lifestyle Factors", icon="🏃")
aleya_aelyana = st.Page("page_aleya_aelyana.py", title="Academic Impact", icon="📚")

pg = st.navigation({"Menu": [home, aleya_nazifa, nash, aleya_aelyana]})
pg.run()
