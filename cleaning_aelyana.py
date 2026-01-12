cleaning_aelyana.py
from __future__ import annotations

import re
import numpy as np
import pandas as pd


# -----------------------------
# Helpers
# -----------------------------
def _norm_col(col: str) -> str:
    """
    Normalize header text robustly:
    - handles trailing spaces, multiple spaces, newlines/tabs
    - handles non-breaking spaces from Google Sheets/Forms
    """
    s = str(col).replace("\u00A0", " ")
    s = s.replace("\n", " ").replace("\t", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _map_freq(x: object) -> int:
    """
    Frequency mapping (robust to minor wording differences).
    Produces 0..4.
    """
    s = str(x).strip()
    mapping = {
        "Never": 0,
        "Rarely (1–2 times a month)": 1,
        "Rarely (1–2 times a week)": 1,
        "Rarely (1-2 times a month)": 1,
        "Rarely (1-2 times a week)": 1,
        "Rarely": 1,
        "Occasionally": 2,
        "Sometimes (3–4 times a week)": 2,
        "Sometimes (3-4 times a week)": 2,
        "Sometimes": 2,
        "Frequently": 3,
        "Often (5–6 times a week)": 3,
        "Often (5-6 times a week)": 3,
        "Often": 3,
        "Always (every night)": 4,
        "Always": 4,
    }
    return mapping.get(s, 0)


def _sleep_hours_to_est(val: object) -> float:
    """
    Convert sleep duration response to numeric estimate (hours).
    Handles your dataset variants.
    """
    if pd.isna(val):
        return np.nan

    x = str(val).strip()

    mapping = {
        "Less than 4 hours": 3.5,
        "Less than 5 hours": 4.5,
        "4–5 hours": 4.5,
        "4-5 hours": 4.5,
        "5–6 hours": 5.5,
        "5-6 hours": 5.5,
        "6–7 hours": 6.5,
        "6-7 hours": 6.5,
        "7–8 hours": 7.5,
        "7-8 hours": 7.5,
        "8–9 hours": 8.5,
        "8-9 hours": 8.5,
        "More than 8 hours": 9.0,
        "9 or more hours": 9.0,
    }
    if x in mapping:
        return float(mapping[x])

    # fallback: parse numbers and average
    nums = re.findall(r"\d+\.?\d*", x.replace("–", "-"))
    if len(nums) == 1:
        return float(nums[0])
    if len(nums) >= 2:
        return (float(nums[0]) + float(nums[1])) / 2.0

    return np.nan


def _categorize_insomnia(score: float) -> str | float:
    if pd.isna(score):
        return np.nan
    if score <= 4:
        return "Low / No Insomnia"
    if score <= 8:
        return "Moderate Insomnia"
    return "Severe Insomnia"


# -----------------------------
# Main function used by Streamlit page
# -----------------------------
def prepare_aelyana_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare cleaned dataframe for Aelyana (Academic Impact page).

    Accepts:
      - raw Google Forms dataframe (long question headers), OR
      - dataframe already renamed by data_loader.py (short column names)

    Returns:
      - dataframe with Aelyana-specific engineered variables:
        InsomniaSeverity_index, Insomnia_Category, + numeric academic impact features.
    """
    if df is None or len(df) == 0:
        return df

    out = df.copy()
    out.columns = [_norm_col(c) for c in out.columns]

    # Rename long Google Form questions -> short names (only if short names missing)
    rename_candidates = {
        "Timestamp": "Timestamp",
        "How often do you have difficulty falling asleep at night?": "DifficultyFallingAsleep",
        "How often do you wake up during the night and have trouble falling back asleep?": "NightWakeups",
        "How would you rate the overall quality of your sleep?": "SleepQuality",
        "How often do you feel fatigued during the day, affecting your ability to study or attend classes?": "DaytimeFatigue",
        "On average, how many hours of sleep do you get on a typical day?": "SleepHours",
        "How often do you experience difficulty concentrating during lectures or studying due to lack of sleep?": "ConcentrationDifficulty",
        "How often do you miss or skip classes due to sleep-related issues (e.g., insomnia, feeling tired)?": "MissedClasses",
        "How would you describe the impact of insufficient sleep on your ability to complete assignments and meet deadlines?": "AssignmentImpact",
        "How would you rate your overall academic performance (GPA or grades) in the past semester?": "AcademicPerformance",
        "What is your GPA range for the most recent semester?": "GPA",
        "What is your CGPA range for the most recent semester?": "CGPA",
    }

    rename_dict = {}
    for long_name, short_name in rename_candidates.items():
        long_key = _norm_col(long_name)
        if short_name not in out.columns and long_key in out.columns:
            rename_dict[long_key] = short_name

    if rename_dict:
        out = out.rename(columns=rename_dict)

    # Timestamp -> datetime
    if "Timestamp" in out.columns:
        out["Timestamp"] = pd.to_datetime(out["Timestamp"], errors="coerce")

    # -----------------------------
    # ISI-like index (0..16-ish in your original method)
    # -----------------------------
    # SleepQuality is numeric 1..5 (5=excellent). Convert to risk points.
    if "SleepQuality" in out.columns:
        sq_num = pd.to_numeric(out["SleepQuality"], errors="coerce")
        out["SleepQuality_Score"] = (5 - sq_num).clip(lower=0, upper=4).fillna(0)
    else:
        out["SleepQuality_Score"] = 0

    out["FallingAsleep_Score"] = out["DifficultyFallingAsleep"].map(_map_freq).fillna(0) if "DifficultyFallingAsleep" in out.columns else 0
    out["NightWakeups_Score"] = out["NightWakeups"].map(_map_freq).fillna(0) if "NightWakeups" in out.columns else 0
    out["Fatigue_Score"] = out["DaytimeFatigue"].map(_map_freq).fillna(0) if "DaytimeFatigue" in out.columns else 0

    out["InsomniaSeverity_index"] = (
        out["FallingAsleep_Score"]
        + out["NightWakeups_Score"]
        + out["SleepQuality_Score"]
        + out["Fatigue_Score"]
    ).astype(float)

    out["Insomnia_Category"] = out["InsomniaSeverity_index"].apply(_categorize_insomnia)

    # -----------------------------
    # Feature engineering for analytics
    # -----------------------------
    if "SleepHours" in out.columns and "SleepHours_est" not in out.columns:
        out["SleepHours_est"] = out["SleepHours"].apply(_sleep_hours_to_est)

    academic_map = {"Poor": 0, "Fair": 1, "Average": 2, "Good": 3, "Very good": 4, "Excellent": 5}
    if "AcademicPerformance" in out.columns:
        out["AcademicPerformance_numeric"] = out["AcademicPerformance"].map(academic_map)

    freq_simple = {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}
    if "DaytimeFatigue" in out.columns:
        out["DaytimeFatigue_numeric"] = out["DaytimeFatigue"].astype(str).map(freq_simple).fillna(0)

    if "ConcentrationDifficulty" in out.columns:
        out["ConcentrationDifficulty_numeric"] = out["ConcentrationDifficulty"].astype(str).map(freq_simple).fillna(0)

    missed_map = {
        "Never": 0,
        "Rarely (1–2 times a month)": 1,
        "Rarely (1-2 times a month)": 1,
        "Sometimes (3–4 times a month)": 2,
        "Sometimes (3-4 times a month)": 2,
        "Often (5–6 times a month)": 3,
        "Often (5-6 times a month)": 3,
        "Always (every day)": 4,
    }
    if "MissedClasses" in out.columns:
        out["MissedClasses_numeric"] = out["MissedClasses"].astype(str).map(missed_map).fillna(0)

    gpa_map = {
        "Below 2.00": 1.5,
        "2.00 - 2.99": 2.5,
        "3.00 - 3.69": 3.35,
        "3.70 - 4.00": 3.85,
    }
    if "GPA" in out.columns:
        out["GPA_numeric"] = out["GPA"].map(gpa_map)
    if "CGPA" in out.columns:
        out["CGPA_numeric"] = out["CGPA"].map(gpa_map)

    return out
