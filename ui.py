"""Shared dashboard helpers (data loading, charts, map defaults)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src import common

MAP_STYLE = "open-street-map"          # free tiles, no API token needed
GRADE_COLORS = {"Safe": "#2e9e5b", "Moderate": "#e0a800", "Risky": "#d64545"}
TREND_COLORS = {"Improving": "#2e9e5b", "Stable": "#6c757d", "Worsening": "#d64545"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@st.cache_data(show_spinner=False, ttl=600)
def load(name: str, parse_dates=None) -> pd.DataFrame:
    return common.read_table(name, parse_dates=parse_dates)


def load_incidents() -> pd.DataFrame:
    df = load("incidents", ["datetime"]).copy()
    df["is_night"] = df["is_night"].astype(bool)
    return df


def setup(title: str, icon: str = ""):
    """Page config + friendly error if the pipeline has not been run yet."""
    st.set_page_config(page_title=f"{title} - SafeSphere", page_icon=icon, layout="wide")
    try:
        load("area_scores")
    except Exception:
        st.error("Database not found or empty. Run `python run_pipeline.py --sample` "
                 "(or with your own data) first, then refresh this page.")
        st.stop()
    st.title(f"{icon} {title}")


def show(fig, container=None):
    """st.plotly_chart across Streamlit versions (optionally inside a column)."""
    target = container if container is not None else st
    try:
        target.plotly_chart(fig, width="stretch")
    except TypeError:
        target.plotly_chart(fig, use_container_width=True)


def map_layout(fig, lat, lon, zoom=11, height=520):
    fig.update_layout(map=dict(style=MAP_STYLE, center=dict(lat=float(lat), lon=float(lon)), zoom=zoom),
                      margin=dict(l=0, r=0, t=0, b=0), height=height)
    return fig


def gauge(value: float, title: str = "Safety Score"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, title={"text": title},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#333333"},
               "steps": [{"range": [0, 50], "color": "#f4c7c3"},
                         {"range": [50, 70], "color": "#fbe8a6"},
                         {"range": [70, 100], "color": "#bfe3c9"}]}))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=60, b=10))
    return fig
