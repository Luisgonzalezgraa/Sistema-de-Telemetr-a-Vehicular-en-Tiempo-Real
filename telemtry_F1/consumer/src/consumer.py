import os
import json
import time
import psycopg2

INPUT_PATH = "/out/telemetry.jsonl"
EVENTS_PATH = "/out/events.jsonl"

print("[consumer] Waiting for telemetry...")
conn = psycopg2.connect(
    host="db",
    database="telemetry",
    user="telemetry",
    password="telemetry"
)

cursor = conn.cursor()

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
# Esperar a que exista el archivo
while not os.path.exists(INPUT_PATH):
    time.sleep(1)

with open(INPUT_PATH, "r") as infile:
    infile.seek(0, 2)  # ir al final (modo tail)

    while True:
        line = infile.readline()
        if not line:
            time.sleep(0.5)
            continue

        data = json.loads(line)

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

            with open(EVENTS_PATH, "a") as f:
                f.write(json.dumps(event_record) + "\n")