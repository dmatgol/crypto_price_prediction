import streamlit as st
from backend import get_features_from_the_store
from settings.config import settings

st.write("Features Dashboard")

data = data = get_features_from_the_store(
    feature_group_name=settings.app_settings.feature_group,
    feature_group_version=settings.app_settings.feature_group_version,
    feature_view_name=settings.app_settings.feature_view,
    feature_view_version=settings.app_settings.feature_view_version,
)


st.table(data)
