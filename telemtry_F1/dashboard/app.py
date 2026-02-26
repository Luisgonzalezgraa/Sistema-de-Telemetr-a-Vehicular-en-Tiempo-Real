import time
import psycopg2
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Telemetry Dashboard", layout="wide")
st.title("🏎️ Telemetry Dashboard (F1-style)")

@st.cache_resource
def get_conn():
    return psycopg2.connect(
        host="db",
        database="telemetry",
        user="telemetry",
        password="telemetry"
    )

conn = get_conn()

refresh_s = st.sidebar.slider("Refresh (seconds)", 1, 5, 1)
window_s = st.sidebar.slider("Window (seconds)", 30, 300, 120)

while True:
    # Último dato
    last = pd.read_sql("""
        SELECT ts, vehicle_id, speed_kmh, rpm, throttle_pct, brake_pct, steer_deg, g_lat, g_lon
        FROM telemetry
        ORDER BY ts DESC
        LIMIT 1
    """, conn)

    if last.empty:
        st.warning("No hay datos todavía.")
        time.sleep(refresh_s)
        continue

    ts_last = last.loc[0, "ts"]
    speed = float(last.loc[0, "speed_kmh"])
    rpm = int(last.loc[0, "rpm"])
    thr = float(last.loc[0, "throttle_pct"])
    brk = float(last.loc[0, "brake_pct"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Speed (km/h)", f"{speed:.1f}")
    c2.metric("RPM", f"{rpm}")
    c3.metric("Throttle (%)", f"{thr:.1f}")
    c4.metric("Brake (%)", f"{brk:.1f}")

    # Ventana de tiempo
    df = pd.read_sql(f"""
        SELECT ts, speed_kmh, rpm, throttle_pct, brake_pct, g_lon
        FROM telemetry
        WHERE ts >= (NOW() - INTERVAL '{window_s} seconds')
        ORDER BY ts ASC
    """, conn)

    left, right = st.columns(2)

    with left:
        fig1 = px.line(df, x="ts", y="speed_kmh", title=f"Speed last {window_s}s")
        st.plotly_chart(fig1, use_container_width=True)

    with right:
        fig2 = px.line(df, x="ts", y="rpm", title=f"RPM last {window_s}s")
        st.plotly_chart(fig2, use_container_width=True)

    st.caption(f"Last update: {ts_last}")

    time.sleep(refresh_s)
    st.rerun()