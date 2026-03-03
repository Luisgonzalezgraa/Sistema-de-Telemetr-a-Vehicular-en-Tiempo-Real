import os
import psycopg2
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "telemetry")
DB_USER = os.getenv("DB_USER", "telemetry")
DB_PASS = os.getenv("DB_PASS", "telemetry")

app = FastAPI(title="Telemetry API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod: restringir al dominio del dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/telemetry/latest")
def telemetry_latest():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT ts, vehicle_id, speed_kmh, rpm, throttle_pct, brake_pct, steer_deg, g_lat, g_lon
        FROM telemetry
        ORDER BY ts DESC
        LIMIT 1
    """, conn)
    conn.close()
    if df.empty:
        return {"data": None}
    return {"data": df.iloc[0].to_dict()}

@app.get("/telemetry/window")
def telemetry_window(seconds: int = Query(120, ge=10, le=3600)):
    conn = get_conn()
    df = pd.read_sql(f"""
        SELECT ts, speed_kmh, rpm, throttle_pct, brake_pct, g_lon, g_lat, steer_deg
        FROM telemetry
        WHERE ts >= (NOW() - INTERVAL '{seconds} seconds')
        ORDER BY ts ASC
    """, conn)
    conn.close()
    return {"data": df.to_dict(orient="records")}

@app.get("/events/recent")
def events_recent(limit: int = Query(20, ge=1, le=500)):
    conn = get_conn()
    df = pd.read_sql(f"""
        SELECT ts, vehicle_id, event_type
        FROM events
        ORDER BY ts DESC
        LIMIT {limit}
    """, conn)
    conn.close()
    return {"data": df.to_dict(orient="records")}

@app.get("/summary/session")
def summary_session():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT
          min(ts) AS start_ts,
          max(ts) AS end_ts,
          avg(speed_kmh) AS avg_speed_kmh,
          max(speed_kmh) AS top_speed_kmh,
          avg(rpm) AS avg_rpm,
          max(rpm) AS top_rpm,
          avg(throttle_pct) AS avg_throttle_pct,
          avg(brake_pct) AS avg_brake_pct
        FROM telemetry
    """, conn)

    ev = pd.read_sql("""
        SELECT event_type, count(*)::int AS count
        FROM events
        GROUP BY event_type
        ORDER BY count DESC
    """, conn)

    conn.close()
    return {
        "telemetry": df.iloc[0].to_dict() if not df.empty else None,
        "events": ev.to_dict(orient="records"),
    }