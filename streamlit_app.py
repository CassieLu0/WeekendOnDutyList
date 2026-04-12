import streamlit as st

st.title(" Weekend Regional Support Specialist Scheduler")
st.write(
    "Type in Month and it will generate the Weekends's duty list for GOFO Regional Support Specialist Department"
)

import calendar
import random
from datetime import date
import pandas as pd
import streamlit as st

FIXED_NAMES = [
    "Hanfei Qi",
    "Mengnan You",
    "Yan Zou",
    "Peng Sun",
    "Ziye Zhang",
    "Jasmine Dong",
    "Ling Lu",
    "Xiao Han",
    "Enze Zhang",
    "Wenli Gai",
    "Miguel Angel Correa",
    "Yizhou Miao"
]

st.subheader("Regional Support Specialist Team")
cover_name_df = pd.DataFrame({"Name": FIXED_NAMES})
st.dataframe(cover_name_df, use_container_width=True, hide_index=True)

# ---------- Helpers ----------
def get_weekend_dates(year: int, month: int) -> list[dict]:
    """Return all Saturday and Sunday dates for a given month."""
    cal = calendar.Calendar(firstweekday=0)
    weekends = []

    for d in cal.itermonthdates(year, month):
        if d.month == month and d.weekday() in [5, 6]:  # Saturday=5, Sunday=6
            weekends.append(
                {
                    "Date": d,
                    "Day": calendar.day_name[d.weekday()],
                    "Weekday Number": d.weekday(),
                }
            )
    return weekends


def build_fair_assignment(names: list[str], total_slots: int, seed: int | None = None, rotate_start: int = 0) -> list[str]:
    """
    Build an assignment list where each person appears as evenly as possible.
    Difference between max and min assignments is at most 1.
    """
    if not names:
        return []

    clean_names = [n.strip() for n in names if n.strip()]
    if not clean_names:
        return []

    n = len(clean_names)
    base = total_slots // n
    remainder = total_slots % n

    counts = {name: base for name in clean_names}

    # Rotate who gets the extra slots so it can stay fair month to month if needed
    ordered_names = clean_names[rotate_start % n :] + clean_names[: rotate_start % n]
    for i in range(remainder):
        counts[ordered_names[i]] += 1

    assignments = []
    for name in clean_names:
        assignments.extend([name] * counts[name])

    # Shuffle for a more natural distribution while keeping counts fair
    rng = random.Random(seed)
    rng.shuffle(assignments)

    return assignments


def generate_schedule(year: int, month: int, names: list[str], seed: int | None, rotate_start: int) -> pd.DataFrame:
    weekends = get_weekend_dates(year, month)
    assignments = build_fair_assignment(names, len(weekends), seed=seed, rotate_start=rotate_start)

    rows = []
    for i, item in enumerate(weekends):
        assigned_to = assignments[i] if i < len(assignments) else "Unassigned"
        rows.append(
            {
                "Date": item["Date"].strftime("%Y-%m-%d"),
                "Day": item["Day"],
                "Assigned RSS": assigned_to,
            }
        )

    return pd.DataFrame(rows)


def assignment_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Assigned RSS", "Weekend Count"])

    summary = (
        df.groupby("Assigned RSS", dropna=False)
        .size()
        .reset_index(name="Weekend Count")
        .sort_values(["Weekend Count", "Assigned RSS"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return summary



# ---------- Sidebar Inputs ----------
st.sidebar.header("Inputs")

today = date.today()
year = st.sidebar.number_input("Year", min_value=2000, max_value=2100, value=today.year, step=1)
month = st.sidebar.number_input("Month", min_value=1, max_value=12, value=today.month, step=1)

name_text = st.sidebar.text_area(
    "Department Name List",
    value="Alice\nBob\nCathy\nDavid\nEmma\nFrank",
    height=220,
    help="Enter one name per line.",
)

seed_input = st.sidebar.text_input(
    "Shuffle Seed (optional)",
    value="42",
    help="Use the same seed to reproduce the same result.",
)

rotate_start = st.sidebar.number_input(
    "Rotation Start Index",
    min_value=0,
    value=0,
    step=1,
    help="Use this to rotate who gets the extra assignment when weekends are not perfectly divisible.",
)

names = [line.strip() for line in name_text.splitlines() if line.strip()]
seed = None
if seed_input.strip() != "":
    try:
        seed = int(seed_input.strip())
    except ValueError:
        seed = None


# ---------- Main Action ----------
col1, col2 = st.columns([1, 1])
with col1:
    generate_btn = st.button("Generate Weekend Schedule", type="primary")

if generate_btn:
    if not names:
        st.error("Please enter at least one name.")
    else:
        df = generate_schedule(int(year), int(month), names, seed, int(rotate_start))
        summary_df = assignment_summary(df)

        month_name = calendar.month_name[int(month)]
        st.subheader(f"Weekend Schedule for {month_name} {int(year)}")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Assignment Summary")
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Schedule CSV",
            data=csv_data,
            file_name=f"weekend_schedule_{year}_{month}.csv",
            mime="text/csv",
        )

        summary_csv = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Summary CSV",
            data=summary_csv,
            file_name=f"weekend_summary_{year}_{month}.csv",
            mime="text/csv",
        )

        # Extra visibility into fairness
        if not summary_df.empty:
            max_count = int(summary_df["Weekend Count"].max())
            min_count = int(summary_df["Weekend Count"].min())
            if max_count - min_count <= 1:
                st.success(f"Assignments are balanced. Max difference is {max_count - min_count}.")
            else:
                st.warning(f"Assignments are not fully balanced. Max difference is {max_count - min_count}.")


