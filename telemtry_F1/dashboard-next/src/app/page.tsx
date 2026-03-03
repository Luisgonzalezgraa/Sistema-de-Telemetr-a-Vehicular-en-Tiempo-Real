import { apiGet } from "./lib/api";

type LatestResp = { data: any | null };
type SummaryResp = { telemetry: any | null; events: { event_type: string; count: number }[] };

export default async function Page() {
  const latest = await apiGet<LatestResp>("/telemetry/latest");
  const summary = await apiGet<SummaryResp>("/summary/session");

  const t = latest.data;
  const s = summary.telemetry;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Telemetry system status and key metrics.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Speed</div>
          <div className="text-2xl font-semibold">{t ? `${t.speed_kmh.toFixed(1)} km/h` : "-"}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">RPM</div>
          <div className="text-2xl font-semibold">{t ? t.rpm : "-"}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Top speed (session)</div>
          <div className="text-2xl font-semibold">{s ? `${Number(s.top_speed_kmh).toFixed(1)} km/h` : "-"}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Events (session)</div>
          <div className="text-2xl font-semibold">{summary.events.reduce((a, b) => a + b.count, 0)}</div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border p-4">
          <h2 className="font-semibold mb-3">Session summary</h2>
          {s ? (
            <ul className="text-sm space-y-2">
              <li><span className="text-muted-foreground">Avg speed:</span> {Number(s.avg_speed_kmh).toFixed(1)} km/h</li>
              <li><span className="text-muted-foreground">Avg RPM:</span> {Number(s.avg_rpm).toFixed(0)}</li>
              <li><span className="text-muted-foreground">Avg throttle:</span> {Number(s.avg_throttle_pct).toFixed(1)}%</li>
              <li><span className="text-muted-foreground">Avg brake:</span> {Number(s.avg_brake_pct).toFixed(1)}%</li>
            </ul>
          ) : (
            <div className="text-sm text-muted-foreground">No telemetry yet.</div>
          )}
        </div>

        <div className="rounded-2xl border p-4">
          <h2 className="font-semibold mb-3">Event counts</h2>
          {summary.events.length ? (
            <ul className="text-sm space-y-2">
              {summary.events.map((e) => (
                <li key={e.event_type} className="flex items-center justify-between">
                  <span>{e.event_type}</span>
                  <span className="font-semibold">{e.count}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-sm text-muted-foreground">No events yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}