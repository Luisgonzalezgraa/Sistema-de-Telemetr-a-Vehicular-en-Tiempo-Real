import os
import json
import time

import psycopg2
from psycopg2 import OperationalError

INPUT_PATH = "/out/telemetry.jsonl"

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
                password="telemetry",
            )
            print("[consumer] Connected to DB ✅")
            return conn
        except OperationalError as e:
            print(f"[consumer] DB not ready yet... retry in 2s. ({e})")
            time.sleep(2)


conn = connect_with_retry()
cursor = conn.cursor()

# 3) Crear tablas si no existen
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    ts TIMESTAMPTZ,
    vehicle_id TEXT,
    event_type TEXT
);
""")

conn.commit()
print("[consumer] Tables ready ✅")

# 4) (Opcional) Convertir a hypertables si Timescale está disponible
#    Si ya las creaste antes, esto simplemente no hará nada.
try:
    cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
    conn.commit()

    cursor.execute("SELECT create_hypertable('telemetry', 'ts', if_not_exists => TRUE);")
    cursor.execute("SELECT create_hypertable('events', 'ts', if_not_exists => TRUE);")
    conn.commit()

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_vehicle_ts ON telemetry (vehicle_id, ts DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_vehicle_ts ON events (vehicle_id, ts DESC);")
    conn.commit()

    print("[consumer] Hypertables/indexes ready ✅")
except Exception as e:
    # Si Timescale no está habilitado por alguna razón, igual seguimos con PostgreSQL normal.
    print(f"[consumer] Timescale/hypertable setup skipped: {e}")

# 5) Loop: leer stream del archivo e insertar
with open(INPUT_PATH, "r", encoding="utf-8") as infile:
    infile.seek(0, 2)  # tail: leer solo nuevas líneas

    while True:
        line = infile.readline()
        if not line:
            time.sleep(0.5)
            continue

        data = json.loads(line)

        # Insert telemetría
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

        # Detectar eventos
        events = []
        if data["brake_pct"] > 60:
            events.append("HARSH_BRAKE")
        if data["g_lon"] > 0.4:
            events.append("HARD_ACCEL")
        if data["speed_kmh"] > 120:
            events.append("OVERSPEED")

        # Insert eventos (1 fila por evento)
        if events:
            for ev in events:
                cursor.execute("""
                INSERT INTO events (ts, vehicle_id, event_type)
                VALUES (%s, %s, %s)
                """, (
                    data["ts"],
                    data["vehicle_id"],
                    ev
                ))
            print("[EVENT DETECTED]", {"ts": data["ts"], "vehicle_id": data["vehicle_id"], "events": events})

        # Commit una vez por ciclo
        conn.commit()