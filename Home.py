"""
Home - enter an area and a time, get the Safety Score and what drives it.
Run:  streamlit run app/Home.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))   

import pandas as pd
import plotly.express as px
import streamlit as st

import ui
import config
from src import common, emergency

ui.setup("Human Safety Intelligence Platform")
st.caption("Human safety intelligence: choose an area and a time of day.")

scores, areas = ui.load("area_scores"), ui.load("areas")
hour_risk, windows = ui.load("hour_risk"), ui.load("risk_windows")
trend, resources = ui.load("trend_forecast"), ui.load("resources")

with st.sidebar:
    st.header("Where and when?")
    area = st.selectbox("Area", sorted(scores["area"]))
    hour = st.slider("Time of day (hour)", 0, 23, 21, format="%d:00")

row = scores[scores["area"] == area].iloc[0]
h = hour_risk[(hour_risk["area"] == area) & (hour_risk["hour"] == hour)]["hour_index"]
hour_index = float(h.iloc[0]) if len(h) else 1.0
adjusted = common.adjusted_score(row["safety_score"], hour_index)
t = trend[trend["area"] == area].iloc[0]
w = windows[windows["area"] == area].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Safety Score at {hour:02d}:00", f"{adjusted:.0f} / 100",
          f"{adjusted - row['safety_score']:+.1f} vs area average")
c2.metric("Area grade", common.grade(adjusted))
c3.metric("City rank", f"{int(row['rank'])} of {len(scores)}")
c4.metric("Trend (next 3 months)", t["trend_label"], f"{t['pct_change']:+.1f}%", delta_color="inverse")

left, right = st.columns([1, 1])
with left:
    ui.show(ui.gauge(adjusted, f"{area} - {hour:02d}:00"))
with right:
    labels = {"frequency": "Crime frequency", "time_risk": "Night-time risk",
              "response": "Emergency response", "trend": "Recent trend"}
    pts = pd.DataFrame({"Factor": [labels[k] for k in config.SCORE_WEIGHTS],
                        "Points lost": [100 * config.SCORE_WEIGHTS[k] * row[f"norm_{k}"]
                                        for k in config.SCORE_WEIGHTS]})
    fig = px.bar(pts, x="Points lost", y="Factor", orientation="h",
                 title="What lowers this area's score?", text_auto=".1f")
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=50, b=10), yaxis_title=None)
    ui.show(fig)

st.subheader("When is it riskiest?")
st.info(f"Highest-risk window in **{area}**: **{w['peak_window']}** "
        f"({w['window_share_pct']}% of severity-weighted incidents). "
        f"Busiest hours: {w['top_hours']}. Riskiest weekday: **{w['riskiest_day']}**.")

st.subheader("Nearest help")
a = areas[areas["area"] == area].iloc[0]
cols = st.columns(2)
for col, kind in zip(cols, ["Police Station", "Hospital"]):
    near = emergency.nearest_resources(a["latitude"], a["longitude"], resources, 3, kind)
    col.markdown(f"**Nearest {kind.lower()}s**")
    col.dataframe(near[["name", "distance_km"]] if len(near) else near, hide_index=True)
st.markdown("**Emergency helplines**")
st.dataframe(pd.DataFrame(config.HELPLINES), hide_index=True)
