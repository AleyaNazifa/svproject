import pandas as pd
import numpy as np
import re


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


def _sleep_hours_to_est(val) -> float:
    """Convert sleep duration response to numeric estimate (hours)."""
    if pd.isna(val):
        return np.nan

    x = str(val).strip()

    mapping = {
        "Less than 4 hours": 3.5,
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
        "More than 8 hours": 8.5,
        "9 or more hours": 9.0,
    }
    if x in mapping:
        return mapping[x]

    # fallback: parse numbers and average
    nums = re.findall(r"\d+\.?\d*", x)
    if len(nums) == 1:
        return float(nums[0])
    if len(nums) >= 2:
        return (float(nums[0]) + float(nums[1])) / 2.0

    return np.nan


def _calculate_isi_like(df: pd.DataFrame) -> pd.Series:
    """
    Simple ISI-like scoring using:
    - DifficultyFallingAsleep (0–4)
    - NightWakeups (0–4)
    - SleepQuality (1 poor -> 4 points, 5 excellent -> 0 points)
    Scaled to ~0–28.
    """
    freq_map = {
        "Never": 0,
        "Rarely (1–2 times a week)": 1,
        "Sometimes (3–4 times a week)": 2,
        "Often (5–6 times a week)": 3,
        "Always (every night)": 4,
    }
    quality_points = {"1": 4, "2": 3, "3": 2, "4": 1, "5": 0}

    score = pd.Series(0.0, index=df.index)

    score += df["DifficultyFallingAsleep"].astype(str).map(freq_map).fillna(0)
    score += df["NightWakeups"].astype(str).map(freq_map).fillna(0)
    score += df["SleepQuality"].astype(str).map(quality_points).fillna(0)

    return (score / 12.0 * 28.0).round(1)


def _isi_category(x):
    if pd.isna(x):
        return np.nan
    if x < 8:
        return "No insomnia (0–7)"
    if x < 15:
        return "Subthreshold (8–14)"
    if x < 22:
        return "Moderate (15–21)"
    return "Severe (22–28)"


# -----------------------------
# Main function used by Streamlit page
# -----------------------------
def prepare_nazifa_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare cleaned dataframe for Nazifa (Sleep Patterns page).

    Accepts:
      - raw Google Forms dataframe (long question headers w/ spaces), OR
      - dataframe already renamed by data_loader.py (short column names)

    Returns:
      - dataframe with Nazifa-specific engineered variables.
    """
    if df is None or len(df) == 0:
        return df

    out = df.copy()

    # Normalize headers
    out.columns = [_norm_col(c) for c in out.columns]

    # Rename long Google Form questions -> short names (only if short names missing)
    rename_candidates = {
        "Timestamp": "Timestamp",
        "What is your gender?": "Gender",
        "What is your age group?": "AgeGroup",
        "What is your year of study?": "YearOfStudy",
        "Which faculty are you currently enrolled in?": "Faculty",
        "How often do you have difficulty falling asleep at night?": "DifficultyFallingAsleep",
        "On average, how many hours of sleep do you get on a typical day?": "SleepHours",
        "How often do you wake up during the night and have trouble falling back asleep?": "NightWakeups",
        "How would you rate the overall quality of your sleep?": "SleepQuality",
        "At what time do you usually go to bed on weekdays?": "BedTime",
        "Do you usually nap during the day?": "DayNap",
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

    # SleepHours_est
    if "SleepHours" in out.columns:
        out["SleepHours_est"] = out["SleepHours"].apply(_sleep_hours_to_est)
    else:
        out["SleepHours_est"] = np.nan

    # SleepQuality_num
    if "SleepQuality" in out.columns:
        out["SleepQuality_num"] = pd.to_numeric(out["SleepQuality"], errors="coerce")
    else:
        out["SleepQuality_num"] = np.nan

    # SleepDurationCategory (Nazifa Figure A2)
    out["SleepDurationCategory"] = pd.cut(
        out["SleepHours_est"],
        bins=[-np.inf, 5.99, 8.0, np.inf],
        labels=["Short (<6h)", "Adequate (6–8h)", "Long (>8h)"],
    )

    # BedTime_order for sorting
    bedtime_order = ["9–10 PM", "10–11 PM", "11 PM–12 AM", "After 12 AM"]
    if "BedTime" in out.columns:
        out["BedTime"] = out["BedTime"].astype(str).str.strip()
        out["BedTime_order"] = pd.Categorical(out["BedTime"], categories=bedtime_order, ordered=True)
    else:
        out["BedTime"] = np.nan
        out["BedTime_order"] = pd.Categorical([np.nan] * len(out), categories=bedtime_order, ordered=True)

    # Symptom flags
    freq_pattern = r"Often|Always"
    if "DifficultyFallingAsleep" in out.columns:
        out["FrequentDifficultyFallingAsleep"] = out["DifficultyFallingAsleep"].astype(str).str.contains(freq_pattern, na=False)
    else:
        out["FrequentDifficultyFallingAsleep"] = False

    if "NightWakeups" in out.columns:
        out["FrequentNightWakeups"] = out["NightWakeups"].astype(str).str.contains(freq_pattern, na=False)
    else:
        out["FrequentNightWakeups"] = False

    # ISI-like index + category
    required = {"DifficultyFallingAsleep", "NightWakeups", "SleepQuality"}
    if required.issubset(out.columns):
        out["InsomniaSeverity_index"] = _calculate_isi_like(out)
    else:
        out["InsomniaSeverity_index"] = np.nan

    out["ISI_Category"] = out["InsomniaSeverity_index"].apply(_isi_category)

    return out
