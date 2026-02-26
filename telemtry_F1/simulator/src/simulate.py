import os
import json
import time
import math
import random
from datetime import datetime, timezone

import numpy as np


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def main():
    vehicle_id = env("VEHICLE_ID", "demo_vehicle")
    rate_hz = float(env("RATE_HZ", "1"))
    out_path = env("OUT_PATH", "/out/telemetry.jsonl")
    seed = int(env("SEED", "0"))

    random.seed(seed)
    np.random.seed(seed)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    dt = 1.0 / rate_hz
    t = 0.0

    # Estado inicial
    speed = 0.0          # km/h
    rpm = 900.0          # ralentí
    steer = 0.0          # grados
    throttle = 0.0       # %
    brake = 0.0          # %

    print(f"[simulator] Writing telemetry to {out_path} at {rate_hz} Hz (vehicle_id={vehicle_id})")

    while True:
        # Perfil de conducción "realista":
        # - aceleraciones suaves
        # - frenadas ocasionales
        # - curvas ocasionales
        phase = (math.sin(t * 0.05) + 1) / 2  # 0..1

        # decide si frena (poco frecuente)
        if random.random() < 0.03:
            brake = random.uniform(20, 80)
        else:
            brake = max(0.0, brake - random.uniform(5, 15))

        # throttle depende de la fase y si está frenando
        target_throttle = 10 + 70 * phase
        if brake > 5:
            target_throttle = 0

        throttle += (target_throttle - throttle) * 0.15
        throttle = clamp(throttle + np.random.normal(0, 1.5), 0, 100)

        # steer: pequeñas oscilaciones + eventos de curva
        steer += (np.random.normal(0, 0.6) - steer * 0.05)
        if random.random() < 0.05:
            steer += random.uniform(-8, 8)
        steer = clamp(steer, -25, 25)

        # dinámica simple: aceleración proporcional a throttle y frenado por brake
        accel = (throttle / 100) * 3.0 - (brake / 100) * 6.0  # m/s^2 aprox
        # convertir speed km/h a m/s para integrar
        v_ms = speed / 3.6
        v_ms = max(0.0, v_ms + accel * dt)
        speed = v_ms * 3.6

        # rpm correlacionado con velocidad + throttle
        rpm = 900 + speed * 35 + throttle * 20 + np.random.normal(0, 50)
        rpm = clamp(rpm, 800, 6500)

        # fuerzas G simples (longitudinal por accel, lateral por steer y velocidad)
        g_lon = clamp(accel / 9.81, -1.5, 1.5)
        g_lat = clamp((abs(steer) / 25) * (v_ms / 40), 0, 2.5) * (1 if steer >= 0 else -1)

        payload = {
            "ts": now_iso(),
            "vehicle_id": vehicle_id,
            "speed_kmh": round(float(speed), 2),
            "rpm": int(rpm),
            "throttle_pct": round(float(throttle), 1),
            "brake_pct": round(float(brake), 1),
            "steer_deg": round(float(steer), 2),
            "g_lat": round(float(g_lat), 3),
            "g_lon": round(float(g_lon), 3),
        }

        line = json.dumps(payload, ensure_ascii=False)

        # append seguro
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        # también imprime una línea resumida para ver que corre
        print(f"[{payload['ts']}] v={payload['speed_kmh']} km/h rpm={payload['rpm']} thr={payload['throttle_pct']} brk={payload['brake_pct']}")

        time.sleep(dt)
        t += dt


if __name__ == "__main__":
    main()