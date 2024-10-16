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
    volume = df["volume"].iloc[0]
    # Create a figure with datetime as the x-axis
    p = figure(
        x_axis_type="datetime",
        title=f"Volume based Candlestick Chart {product_id}, Volume: {volume}",
        width=800,
        height=400,
    )

    # Plot each candlestick with variable width based on start_time and end_time
    for _index, row in df.iterrows():
        # Candle width is the difference between start_time and end_time
        candle_width = (
            row["end_time"] - row["start_time"]
        ).total_seconds() * 1000  # Convert to milliseconds

        # Determine the color of the candle based on if it was an up or down day
        if row["close"] > row["open"]:
            color = "green"
        else:
            color = "red"

        # Candle body (rectangle)
        p.rect(
            x=row["start_time"],
            y=(row["open"] + row["close"]) / 2,
            width=candle_width,
            height=abs(row["close"] - row["open"]),
            fill_color=color,
            line_color=color,
        )

        # Candle wicks (high/low lines)
        p.segment(
            x0=row["start_time"],
            y0=row["high"],
            x1=row["start_time"],
            y1=row["low"],
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
