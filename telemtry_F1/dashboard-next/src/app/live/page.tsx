import { apiGet } from "../lib/api";

type WindowResp = { data: any[] };

export default async function LivePage() {
  const win = await apiGet<WindowResp>("/telemetry/window?seconds=120");
  const last = win.data.length ? win.data[win.data.length - 1] : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Live Telemetry</h1>
        <p className="text-sm text-muted-foreground">Last 120 seconds window.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Speed</div>
          <div className="text-2xl font-semibold">{last ? `${Number(last.speed_kmh).toFixed(1)} km/h` : "-"}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">RPM</div>
          <div className="text-2xl font-semibold">{last ? last.rpm : "-"}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Throttle</div>
          <div className="text-2xl font-semibold">{last ? `${Number(last.throttle_pct).toFixed(1)}%` : "-"}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Brake</div>
          <div className="text-2xl font-semibold">{last ? `${Number(last.brake_pct).toFixed(1)}%` : "-"}</div>
        </div>
      </div>

      <div className="rounded-2xl border p-4">
        <h2 className="font-semibold mb-3">Raw window (preview)</h2>
        <div className="text-xs overflow-auto max-h-[420px]">
          <pre>{JSON.stringify(win.data.slice(-60), null, 2)}</pre>
        </div>
      </div>
    </div>
  );
}