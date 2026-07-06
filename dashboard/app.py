"""
Air Quality Intelligence Dashboard
-----------------------------------
Run with:
    streamlit run dashboard/app.py

Reads data/air_quality.csv (latest snapshot per city) and
data/history.csv (hourly log) produced by scripts/fetch_data.py,
scripts/scheduler.py, or scripts/generate_sample_data.py.
"""

import os
import sys
import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
from aqi_utils import CITIES, aqi_category, health_recommendation  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LATEST_CSV = os.path.join(BASE_DIR, "data", "air_quality.csv")
HISTORY_CSV = os.path.join(BASE_DIR, "data", "history.csv")

POLLUTANTS = ["pm2_5", "pm10", "co", "no2", "so2", "o3"]
POLLUTANT_LABELS = {
    "pm2_5": "PM2.5", "pm10": "PM10", "co": "CO",
    "no2": "NO2", "so2": "SO2", "o3": "O3",
}

st.set_page_config(
    page_title="Air Quality Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
)

# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    if not os.path.isfile(LATEST_CSV) or not os.path.isfile(HISTORY_CSV):
        return None, None
    latest = pd.read_csv(LATEST_CSV, parse_dates=["timestamp"])
    history = pd.read_csv(HISTORY_CSV, parse_dates=["timestamp"])
    return latest, history


latest_df, history_df = load_data()

if latest_df is None:
    st.error(
        "No data found yet. Run `python scripts/generate_sample_data.py` for a demo, "
        "or `python scripts/fetch_data.py` with a live OPENWEATHER_API_KEY."
    )
    st.stop()

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.title("🌍 Air Quality Intelligence Dashboard")
last_updated = latest_df["timestamp"].max()
st.caption(f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M UTC')}")

# ---------------------------------------------------------------------
# Sidebar: city selector
# ---------------------------------------------------------------------
st.sidebar.header("Controls")
city_list = sorted(latest_df["city"].unique().tolist())
selected_city = st.sidebar.selectbox("Select a city", city_list, index=0)
st.sidebar.markdown("---")
st.sidebar.caption(
    "Data source: OpenWeather Air Pollution & Weather APIs. "
    "AQI computed using US EPA breakpoint formulas."
)

city_row = latest_df[latest_df["city"] == selected_city].iloc[0]

# =======================================================================
# 10. KPI ROW
# =======================================================================
worst_row = latest_df.loc[latest_df["aqi"].idxmax()]
best_row = latest_df.loc[latest_df["aqi"].idxmin()]
avg_aqi = latest_df["aqi"].mean()
highest_pm25_row = latest_df.loc[latest_df["pm2_5"].idxmax()]
highest_no2_row = latest_df.loc[latest_df["no2"].idxmax()]

kpi_cols = st.columns(6)
kpi_cols[0].metric(f"Current AQI ({selected_city})", int(city_row["aqi"]))
kpi_cols[1].metric("Worst City Today", worst_row["city"], f"AQI {int(worst_row['aqi'])}")
kpi_cols[2].metric("Cleanest City", best_row["city"], f"AQI {int(best_row['aqi'])}")
kpi_cols[3].metric("Average AQI (all cities)", round(avg_aqi, 1))
kpi_cols[4].metric("Highest PM2.5", highest_pm25_row["city"], f"{highest_pm25_row['pm2_5']} µg/m³")
kpi_cols[5].metric("Highest NO2", highest_no2_row["city"], f"{highest_no2_row['no2']} µg/m³")

st.markdown("---")

# =======================================================================
# Layout: Map + Live AQI card / Health risk
# =======================================================================
map_col, side_col = st.columns([2, 1])

with map_col:
    st.subheader("🗺️ Interactive AQI Map")

    m = folium.Map(location=[9.0, 8.0], zoom_start=6, tiles="CartoDB positron")
    for _, row in latest_df.iterrows():
        label, emoji, color = aqi_category(row["aqi"])
        popup_html = f"""
        <b>{row['city']}</b><br>
        AQI: {int(row['aqi'])} ({label})<br>
        PM2.5: {row['pm2_5']} µg/m³<br>
        PM10: {row['pm10']} µg/m³<br>
        CO: {row['co']} µg/m³<br>
        NO2: {row['no2']} µg/m³<br>
        SO2: {row['so2']} µg/m³<br>
        O3: {row['o3']} µg/m³
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=14,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{row['city']}: AQI {int(row['aqi'])} ({label})",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            weight=2,
        ).add_to(m)

    map_state = st_folium(m, height=460, use_container_width=True)

    # Legend
    legend_cols = st.columns(6)
    legend_items = [
        ("🟢 Good", "0-50"), ("🟡 Moderate", "51-100"),
        ("🟠 USG", "101-150"), ("🔴 Unhealthy", "151-200"),
        ("🟣 Very Unhealthy", "201-300"), ("🟤 Hazardous", "301-500"),
    ]
    for col, (label, rng) in zip(legend_cols, legend_items):
        col.caption(f"{label}\n({rng})")

with side_col:
    st.subheader("📈 Live AQI Card")
    label, emoji, color = aqi_category(city_row["aqi"])
    st.markdown(
        f"""
        <div style="background-color:{color}22;border-left:8px solid {color};
                    border-radius:10px;padding:20px;text-align:center;">
            <div style="font-size:15px;color:#555;">{selected_city}</div>
            <div style="font-size:56px;font-weight:800;color:{color};">{int(city_row['aqi'])}</div>
            <div style="font-size:20px;font-weight:700;">{emoji} {label.upper()}</div>
            <div style="font-size:13px;color:#777;margin-top:8px;">
                Last Updated: {city_row['timestamp'].strftime('%I:%M %p')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("🚨 Health Risk Indicator")
    st.markdown(f"**AQI:** {int(city_row['aqi'])}  \n**Status:** {label}")
    st.info(health_recommendation(label))

st.markdown("---")

# =======================================================================
# Pollutant breakdown + Weather integration
# =======================================================================
poll_col, weather_col = st.columns([2, 1])

with poll_col:
    st.subheader(f"📊 Pollutant Breakdown — {selected_city}")
    poll_values = [city_row[p] for p in POLLUTANTS]
    poll_labels = [POLLUTANT_LABELS[p] for p in POLLUTANTS]
    fig_bar = px.bar(
        x=poll_labels, y=poll_values,
        labels={"x": "Pollutant", "y": "Concentration (µg/m³)"},
        color=poll_values, color_continuous_scale="YlOrRd",
        text=[f"{v:.1f}" for v in poll_values],
    )
    fig_bar.update_layout(showlegend=False, coloraxis_showscale=False, height=380)
    st.plotly_chart(fig_bar, use_container_width=True)

with weather_col:
    st.subheader("🌡️ Weather Integration")
    st.metric("Temperature", f"{city_row['temperature']} °C")
    st.metric("Humidity", f"{city_row['humidity']} %")
    st.metric("Wind Speed", f"{city_row['wind_speed']} m/s")
    st.metric("Pressure", f"{city_row['pressure']} hPa")

st.markdown("---")

# =======================================================================
# AQI History (line chart)
# =======================================================================
st.subheader(f"📉 AQI History — {selected_city}")
city_hist = history_df[history_df["city"] == selected_city].sort_values("timestamp")

range_choice = st.radio(
    "Range", ["Last 24 hours", "Last 7 days", "All available"],
    horizontal=True, index=1,
)
if range_choice == "Last 24 hours":
    cutoff = city_hist["timestamp"].max() - pd.Timedelta(hours=24)
    plot_df = city_hist[city_hist["timestamp"] >= cutoff]
elif range_choice == "Last 7 days":
    cutoff = city_hist["timestamp"].max() - pd.Timedelta(days=7)
    plot_df = city_hist[city_hist["timestamp"] >= cutoff]
else:
    plot_df = city_hist

fig_line = px.line(plot_df, x="timestamp", y="aqi", markers=False)
fig_line.update_traces(line_color="#2E7D32")
for low, high, label, emoji, color in [
    (0, 50, "Good", "", "#00E400"), (51, 100, "Moderate", "", "#FFFF00"),
    (101, 150, "USG", "", "#FF7E00"), (151, 200, "Unhealthy", "", "#FF0000"),
]:
    fig_line.add_hrect(y0=low, y1=high, fillcolor=color, opacity=0.08, line_width=0)
fig_line.update_layout(height=380, xaxis_title="Time", yaxis_title="AQI")
st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

# =======================================================================
# City comparison table
# =======================================================================
st.subheader("📍 City Comparison")
compare_df = latest_df[["city", "aqi", "pm2_5", "pm10", "co", "no2", "so2", "o3"]].copy()
compare_df = compare_df.sort_values("aqi", ascending=False).reset_index(drop=True)
compare_df.columns = ["City", "AQI", "PM2.5", "PM10", "CO", "NO2", "SO2", "O3"]
st.dataframe(
    compare_df.style.background_gradient(subset=["AQI"], cmap="YlOrRd"),
    use_container_width=True, hide_index=True,
)

st.markdown("---")

# =======================================================================
# Historical trends: daily / weekly / monthly averages
# =======================================================================
st.subheader("📅 Historical Trends")
trend_tabs = st.tabs(["Daily Averages", "Weekly Averages", "Monthly Averages"])

city_hist_indexed = city_hist.set_index("timestamp")

with trend_tabs[0]:
    daily_avg = city_hist_indexed["aqi"].resample("D").mean().reset_index()
    fig_daily = px.bar(daily_avg, x="timestamp", y="aqi", labels={"timestamp": "Day", "aqi": "Avg AQI"})
    st.plotly_chart(fig_daily, use_container_width=True)

with trend_tabs[1]:
    weekly_avg = city_hist_indexed["aqi"].resample("W").mean().reset_index()
    fig_weekly = px.bar(weekly_avg, x="timestamp", y="aqi", labels={"timestamp": "Week", "aqi": "Avg AQI"})
    st.plotly_chart(fig_weekly, use_container_width=True)

with trend_tabs[2]:
    monthly_avg = city_hist_indexed["aqi"].resample("ME").mean().reset_index()
    fig_monthly = px.bar(monthly_avg, x="timestamp", y="aqi", labels={"timestamp": "Month", "aqi": "Avg AQI"})
    st.plotly_chart(fig_monthly, use_container_width=True)
    if len(monthly_avg) < 2:
        st.caption("Monthly trend becomes meaningful once the scheduler has been running for a few months.")

st.markdown("---")

# =======================================================================
# Pollution hotspots
# =======================================================================
st.subheader("🚩 Pollution Hotspots (Ranked)")
hotspot_df = latest_df.sort_values("aqi", ascending=False).reset_index(drop=True)
for i, row in hotspot_df.iterrows():
    label, emoji, color = aqi_category(row["aqi"])
    st.markdown(
        f"**{i+1}. {row['city']}** — AQI {int(row['aqi'])} {emoji} *{label}*"
    )

st.caption(
    "Built with Streamlit, Plotly, and Folium · Data via OpenWeather Air Pollution & Weather APIs"
)
