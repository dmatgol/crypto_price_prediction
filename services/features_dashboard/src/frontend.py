from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from backend import get_features_from_the_store
from bokeh.plotting import figure
from settings.config import settings


def plot_volume_candles(df: pd.DataFrame):
    """Plot the volume based candlestick chart."""
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])

    product_id = df["product_id"].iloc[0]

    # Calculate the middle point for each candle (to plot the bar in the center)
    df["middle_time"] = (
        df["start_time"] + (df["end_time"] - df["start_time"]) / 2
    )

    # Calculate the width of each candle (in milliseconds)
    df["width"] = (
        df["end_time"] - df["start_time"]
    ).dt.total_seconds() * 1000  # Convert to milliseconds

    # Determine which candles are increasing or decreasing
    inc = df.close > df.open
    dec = df.open > df.close

    # Set x-axis range with a small buffer around the min and max times
    p = figure(
        x_axis_type="datetime",
        width=1000,
        title=f"Tick imbalanced Candlestick for {product_id}",
    )
    p.grid.grid_line_alpha = 0.3

    # Plot the candle wicks (high/low lines)
    p.segment(df.middle_time, df.high, df.middle_time, df.low, color="black")

    # Plot the increasing candles (green)
    p.vbar(
        x=df.middle_time[inc],
        width=df.width[inc],
        bottom=df.open[inc],
        top=df.close[inc],
        fill_color="#70bd40",
        line_color="black",
    )

    # Plot the decreasing candles (red)
    p.vbar(
        x=df.middle_time[dec],
        width=df.width[dec],
        bottom=df.open[dec],
        top=df.close[dec],
        fill_color="#F2583E",
        line_color="black",
    )

    # Set axis labels
    p.xaxis.axis_label = "Time"
    p.yaxis.axis_label = "Price"
    return p


st.title("Features Dashboard quick vizualization")
online_or_offline = st.sidebar.selectbox(
    "Select the feature store", ("Online", "Offline")
)
product_id = st.sidebar.selectbox(
    "Select the product", settings.supported_coins
)
today = datetime.today()
thirty_days_ago = today - timedelta(days=30)

# Sidebar: Time Filter
st.sidebar.header("Filter by Timeframe")

start_date = st.sidebar.date_input("Start date", thirty_days_ago)
end_date = st.sidebar.date_input("End date", today)

data = get_features_from_the_store(
    feature_group_name=settings.app_settings.feature_group,
    feature_group_version=settings.app_settings.feature_group_version,
    feature_view_name=settings.app_settings.feature_view,
    feature_view_version=settings.app_settings.feature_view_version,
    time_range=(start_date, end_date),
    product_id=product_id,
    online=True if online_or_offline == "Online" else False,
)

st.bokeh_chart(plot_volume_candles(data))
