import os
import json
import time

import psycopg2
from psycopg2 import OperationalError

INPUT_PATH = "/out/telemetry.jsonl"
EVENTS_PATH = "/out/events.jsonl"

print("[consumer] Starting...")

# 1) Esperar archivo de telemetría
print("[consumer] Waiting for telemetry file...")
while not os.path.exists(INPUT_PATH):
    time.sleep(1)

print("[consumer] Telemetry file found ✅")

# 2) Conectar a DB con reintento
def connect_with_retry():
    while True:
        try:
            conn = psycopg2.connect(
                host="db",
                database="telemetry",
                user="telemetry",
                password="telemetry"
            )
            print("[consumer] Connected to DB ✅")
            return conn
        except OperationalError as e:
            print(f"[consumer] DB not ready yet... retry in 2s. ({e})")
            time.sleep(2)

conn = connect_with_retry()
cursor = conn.cursor()

# 3) Crear tabla si no existe
cursor.execute("""
CREATE TABLE IF NOT EXISTS telemetry (
    ts TIMESTAMPTZ,
    vehicle_id TEXT,
    speed_kmh FLOAT,
    rpm INT,
    throttle_pct FLOAT,
    brake_pct FLOAT,
    steer_deg FLOAT,
    g_lat FLOAT,
    g_lon FLOAT
);
""")
conn.commit()

print("[consumer] Table ready ✅")

with open(INPUT_PATH, "r", encoding="utf-8") as infile:
    infile.seek(0, 2)  # tail: leer solo nuevas líneas

    while True:
        line = infile.readline()
        if not line:
            time.sleep(0.5)
            continue

        data = json.loads(line)

        # Insert a DB
        cursor.execute("""
        INSERT INTO telemetry (ts, vehicle_id, speed_kmh, rpm, throttle_pct, brake_pct, steer_deg, g_lat, g_lon)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["ts"],
            data["vehicle_id"],
            data["speed_kmh"],
            data["rpm"],
            data["throttle_pct"],
            data["brake_pct"],
            data["steer_deg"],
            data["g_lat"],
            data["g_lon"],
        ))
        conn.commit()

        # Event detection
        events = []
        if data["brake_pct"] > 60:
            events.append("HARSH_BRAKE")
        if data["g_lon"] > 0.4:
            events.append("HARD_ACCEL")
        if data["speed_kmh"] > 120:
            events.append("OVERSPEED")

        if events:
            event_record = {
                "ts": data["ts"],
                "vehicle_id": data["vehicle_id"],
                "events": events
            }
            print("[EVENT DETECTED]", event_record)

            with open(EVENTS_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_record, ensure_ascii=False) + "\n")